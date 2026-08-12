import math
import time
from dataclasses import dataclass
from statistics import median
from typing import Any, Dict, List, Optional

from fastapi import HTTPException
import httpx
from sqlalchemy.ext.asyncio import AsyncSession
import structlog
from sqlalchemy import select

from app.config.settings import settings
from app.schemas.model_router import (
    Capability,
    ModelRouteRequest,
    ModelRouteResponse,
)
from app.services.activity_log import ActivityLogService
from app.services.model_catalog import ModelCatalogService
from app.database.models.model_routing import ModelRoutingOutcome

logger = structlog.get_logger()

# OpenRouter retired this model ID. Keep this compatibility map so an old
# Railway environment variable cannot reintroduce the 404 after deployment.
MODEL_ALIASES = {
    "anthropic/claude-3.5-sonnet": "google/gemini-2.5-flash",
}


@dataclass
class OpenRouterUpstreamError(Exception):
    status_code: int
    message: str
    error_type: Optional[str] = None
    provider_code: Optional[str] = None
    provider_name: Optional[str] = None
    details: Optional[str] = None
    retry_after: Optional[str] = None

    def __str__(self) -> str:
        return self.message


class ModelRouterService:

    def __init__(self, db: AsyncSession):
        self.db = db
        self.activity_log_service = ActivityLogService(db)

    def resolve_model(self, capability: Capability) -> str:
        capability_map = {
            Capability.ARCHITECTURE: settings.default_model_architecture,
            Capability.CODING: settings.default_model_coding,
            Capability.CODE_REVIEW: settings.default_model_code_review,
            Capability.TESTING: settings.default_model_testing,
            Capability.GENERAL_REASONING: settings.default_model_general_reasoning,
            Capability.CHALLENGE: settings.default_model_challenge,
        }
        model_name = capability_map.get(
            capability, settings.default_model_general_reasoning
        )
        return MODEL_ALIASES.get(model_name, model_name)

    async def route(
        self, request: ModelRouteRequest, request_id: Optional[str] = None
    ) -> ModelRouteResponse:
        candidates = await self._select_candidates(request)
        model_name = candidates[0]["model_id"]
        start_time = time.perf_counter()

        # Log routing attempt
        await self.activity_log_service.record(
            event_type="model_route_started",
            source="model_router",
            request_id=request_id,
            payload={
                "capability": request.capability.value,
                "model": model_name,
                "candidates": [candidate["model_id"] for candidate in candidates],
            },
        )

        # Mock fallback for development/testing if API key is mock
        if settings.openrouter_api_key == "mock-key":
            response = ModelRouteResponse(
                id="mock-completion-id",
                capability=request.capability,
                model_used=model_name,
                content=self._get_mock_content(request),
                usage={
                    "prompt_tokens": 10,
                    "completion_tokens": 20,
                    "total_tokens": 30,
                },
            )
        else:
            headers = {
                "Authorization": f"Bearer {settings.openrouter_api_key}",
                "Content-Type": "application/json",
                "X-OpenRouter-Metadata": "enabled",
            }
            selected_candidate = next(
                (candidate for candidate in candidates if candidate["model_id"] == model_name),
                {},
            )
            payload = self._build_upstream_payload(
                request, model_name, candidates, selected_candidate
            )

            # Normalize the configured URL so either the API root or the full
            # completion endpoint can be supplied without creating a bad path.
            configured_url = settings.openrouter_base_url.rstrip("/")
            completion_url = (
                configured_url
                if configured_url.endswith("/chat/completions")
                else f"{configured_url}/chat/completions"
            )
            import asyncio
            response = None
            last_exception = None
            max_retries = 3
            backoff_factor = 1.0
            retry_codes = {429, 502, 503, 504}

            try:
                # 1. OpenRouter execution with transient retry loop
                for attempt in range(max_retries + 1):
                    try:
                        async with httpx.AsyncClient() as client:
                            res = await client.post(
                                completion_url,
                                json=payload,
                                headers=headers,
                                timeout=30.0,
                            )
                        
                        if res.status_code == 200:
                            data = res.json()
                            if not isinstance(data, dict):
                                raise OpenRouterUpstreamError(
                                    status_code=502,
                                    message="OpenRouter returned an invalid completion payload.",
                                    error_type="provider_unavailable",
                                )
                            embedded_error = self._parse_embedded_error(data)
                            if embedded_error:
                                raise embedded_error
                            
                            choices = data.get("choices") or []
                            if not choices or not isinstance(choices[0], dict):
                                raise OpenRouterUpstreamError(
                                    status_code=502,
                                    message="OpenRouter returned no completion choices.",
                                    error_type="provider_unavailable",
                                )
                            choice = choices[0]
                            message_obj = choice.get("message") or {}
                            content = message_obj.get("content")
                            if not isinstance(content, str):
                                raise OpenRouterUpstreamError(
                                    status_code=502,
                                    message="OpenRouter returned a completion without text content.",
                                    error_type="provider_unavailable",
                                )
                            usage = dict(data.get("usage") or {})
                            usage["finish_reason"] = choice.get("finish_reason")
                            if data.get("provider"):
                                usage["provider"] = data["provider"]
                            if data.get("openrouter_metadata"):
                                usage["openrouter_metadata"] = data["openrouter_metadata"]
                            response_model = data.get("model") or model_name

                            response = ModelRouteResponse(
                                id=data.get("id", "completion-id"),
                                capability=request.capability,
                                model_used=response_model,
                                content=content,
                                usage=usage,
                            )
                            break  # Success!

                        # Not 200 status code
                        if res.status_code in retry_codes and attempt < max_retries:
                            retry_after = res.headers.get("Retry-After")
                            sleep_time = int(retry_after) if retry_after and retry_after.isdigit() else (backoff_factor * (2 ** attempt))
                            await asyncio.sleep(sleep_time)
                            continue
                        
                        raise self._parse_http_error(res)

                    except (httpx.TimeoutException, httpx.ConnectError, httpx.NetworkError) as exc:
                        last_exception = exc
                        if attempt < max_retries:
                            await asyncio.sleep(backoff_factor * (2 ** attempt))
                            continue
                    except OpenRouterUpstreamError as exc:
                        last_exception = exc
                        if exc.status_code in retry_codes and attempt < max_retries:
                            sleep_time = int(exc.retry_after) if exc.retry_after and exc.retry_after.isdigit() else (backoff_factor * (2 ** attempt))
                            await asyncio.sleep(sleep_time)
                            continue
                        # Stop retrying on non-retryable upstream errors (e.g. 400 Bad Request)
                        break

                # 2. Native Provider Bypass (Failover Circuit Breaker)
                if response is None:
                    # Determine native fallback options based on model name prefix
                    bypass_url = None
                    bypass_headers = None
                    bypass_model = None
                    
                    if model_name.startswith("openai/") and settings.openai_api_key:
                        bypass_url = "https://api.openai.com/v1/chat/completions"
                        bypass_headers = {
                            "Authorization": f"Bearer {settings.openai_api_key}",
                            "Content-Type": "application/json",
                        }
                        bypass_model = model_name.replace("openai/", "", 1)
                    elif model_name.startswith("google/") and settings.google_api_key:
                        bypass_url = "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions"
                        bypass_headers = {
                            "Authorization": f"Bearer {settings.google_api_key}",
                            "Content-Type": "application/json",
                        }
                        bypass_model = model_name.replace("google/", "", 1)
                    
                    if bypass_url and bypass_headers and bypass_model:
                        await self.activity_log_service.record(
                            event_type="model_route_bypass_triggered",
                            source="model_router",
                            request_id=request_id,
                            payload={
                                "capability": request.capability.value,
                                "original_model": model_name,
                                "bypass_model": bypass_model,
                                "url": bypass_url,
                            },
                        )
                        
                        bypass_payload = self._build_upstream_payload(
                            request, model_name, candidates, selected_candidate
                        )
                        bypass_payload["model"] = bypass_model
                        bypass_payload.pop("provider", None)
                        
                        try:
                            async with httpx.AsyncClient() as client:
                                res = await client.post(
                                    bypass_url,
                                    json=bypass_payload,
                                    headers=bypass_headers,
                                    timeout=30.0,
                                )
                            if res.is_error:
                                raise self._parse_http_error(res)
                            
                            data = res.json()
                            choices = data.get("choices") or []
                            if choices and isinstance(choices[0], dict):
                                choice = choices[0]
                                msg = choice.get("message") or {}
                                content = msg.get("content")
                                if isinstance(content, str):
                                    usage = dict(data.get("usage") or {})
                                    usage["finish_reason"] = choice.get("finish_reason")
                                    usage["native_bypass"] = True
                                    response = ModelRouteResponse(
                                        id=data.get("id", "completion-id"),
                                        capability=request.capability,
                                        model_used=f"native/{bypass_model}",
                                        content=content,
                                        usage=usage,
                                    )
                        except Exception as bypass_exc:
                            logger.error("model_route_bypass_failed", model=model_name, error=str(bypass_exc))

                # 3. If still no response, raise the last exception
                if response is None:
                    raise last_exception or httpx.NetworkError("Failed to reach OpenRouter and bypass providers")

            except httpx.TimeoutException as exc:
                await self._record_outcome(
                    request,
                    request_id,
                    model_name,
                    {},
                    success=False,
                    error=exc,
                    latency_ms=(time.perf_counter() - start_time) * 1000,
                )
                await self.activity_log_service.record(
                    event_type="model_route_failed",
                    source="model_router",
                    request_id=request_id,
                    payload={
                        "capability": request.capability.value,
                        "model": model_name,
                        "error": str(exc),
                    },
                )
                raise HTTPException(
                    status_code=504,
                    detail="Gateway Timeout – OpenRouter API request timed out",
                )
            except (httpx.ConnectError, httpx.NetworkError) as exc:
                await self._record_outcome(
                    request,
                    request_id,
                    model_name,
                    {},
                    success=False,
                    error=exc,
                    latency_ms=(time.perf_counter() - start_time) * 1000,
                )
                await self.activity_log_service.record(
                    event_type="model_route_failed",
                    source="model_router",
                    request_id=request_id,
                    payload={
                        "capability": request.capability.value,
                        "model": model_name,
                        "error": str(exc),
                    },
                )
                raise HTTPException(
                    status_code=503,
                    detail="Service Unavailable – failed to connect to OpenRouter API",
                )
            except OpenRouterUpstreamError as exc:
                await self._record_outcome(
                    request,
                    request_id,
                    model_name,
                    {},
                    success=False,
                    error=exc,
                    latency_ms=(time.perf_counter() - start_time) * 1000,
                )
                await self.activity_log_service.record(
                    event_type="model_route_failed",
                    source="model_router",
                    request_id=request_id,
                    payload={
                        "capability": request.capability.value,
                        "model": model_name,
                        "endpoint": completion_url,
                        "upstream_status": exc.status_code,
                        "upstream_code": exc.provider_code,
                        "error_type": exc.error_type,
                        "upstream_message": exc.message,
                        "upstream_details": exc.details,
                        "provider_name": exc.provider_name,
                        "retry_after": exc.retry_after,
                        "payload_parameters": sorted(
                            key for key in payload if key not in {"model", "messages"}
                        ),
                        "error": str(exc),
                    },
                )
                raise self._to_http_exception(exc)
            except Exception as exc:
                await self._record_outcome(
                    request,
                    request_id,
                    model_name,
                    {},
                    success=False,
                    error=exc,
                    latency_ms=(time.perf_counter() - start_time) * 1000,
                )
                await self.activity_log_service.record(
                    event_type="model_route_failed",
                    source="model_router",
                    request_id=request_id,
                    payload={
                        "capability": request.capability.value,
                        "model": model_name,
                        "error": str(exc),
                    },
                )
                raise HTTPException(
                    status_code=500,
                    detail=f"Internal Server Error – failed to process Model Router response: {str(exc)}",
                )

        # Record completion log
        actual_model = response.model_used
        selected_candidate = next(
            (candidate for candidate in candidates if candidate["model_id"] == actual_model),
            next(
                (candidate for candidate in candidates if candidate["model_id"] == model_name),
                {},
            ),
        )
        reported_cost = response.usage.get("cost")
        response.usage["estimated_cost"] = (
            float(reported_cost)
            if reported_cost is not None
            else self._estimate_cost(response.usage, selected_candidate)
        )
        await self._record_outcome(
            request,
            request_id,
            actual_model,
            response.usage,
            success=True,
            error=None,
            latency_ms=(time.perf_counter() - start_time) * 1000,
        )
        await self.activity_log_service.record(
            event_type="model_route_completed",
            source="model_router",
            request_id=request_id,
            payload={
                "capability": request.capability.value,
                "model": actual_model,
                "usage": response.usage,
            },
        )

        return response

    @staticmethod
    def _build_upstream_payload(
        request: ModelRouteRequest,
        model_name: str,
        candidates: List[Dict[str, Any]],
        candidate: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Build one OpenRouter request with provider and model failover."""
        supported = set(candidate.get("supported_parameters") or [])
        token_parameter = None
        if request.max_tokens is not None:
            if not supported or "max_tokens" in supported:
                token_parameter = "max_tokens"
            elif "max_completion_tokens" in supported:
                token_parameter = "max_completion_tokens"
        provider_preferences: Dict[str, Any] = {
            "allow_fallbacks": True,
            "require_parameters": True,
        }
        if settings.openrouter_provider_sort:
            provider_preferences["sort"] = settings.openrouter_provider_sort

        payload: Dict[str, Any] = {
            "messages": [message.model_dump() for message in request.messages],
            "provider": provider_preferences,
        }
        model_ids = [
            item["model_id"]
            for item in candidates
            if item.get("model_id")
            and (
                not token_parameter
                or not item.get("supported_parameters")
                or token_parameter in item["supported_parameters"]
            )
        ]
        if len(model_ids) > 1:
            payload["models"] = model_ids
        else:
            payload["model"] = model_name

        # Check if structured output is requested and supported by candidate model
        use_structured_json = False
        if request.capability in {Capability.CODE_REVIEW, Capability.TESTING, Capability.CHALLENGE}:
            if any(m in settings.structured_output_models for m in [model_name] + model_ids):
                use_structured_json = True

        if use_structured_json:
            payload["response_format"] = {"type": "json_object"}
            messages_copy = [message.model_dump() for message in request.messages]
            schema_inst = ""
            if request.capability == Capability.CODE_REVIEW:
                schema_inst = (
                    "\n\nYou MUST return a JSON object with the following schema:\n"
                    '{\n  "status": "approved" | "request_changes",\n  "reason": "detailed reason for rejection, or null if approved"\n}'
                )
            elif request.capability == Capability.TESTING:
                schema_inst = (
                    "\n\nYou MUST return a JSON object with the following schema:\n"
                    '{\n  "status": "PASSED" | "FAILED"\n}'
                )
            elif request.capability == Capability.CHALLENGE:
                schema_inst = (
                    "\n\nYou MUST return a JSON object with the following schema:\n"
                    '{\n  "status": "passed" | "failed",\n  "reason": "detailed failure reason, or null if passed"\n}'
                )
                
            if messages_copy and messages_copy[0]["role"] == "system":
                messages_copy[0]["content"] += schema_inst
            else:
                messages_copy.insert(0, {"role": "system", "content": "You are a helpful assistant. Output JSON only." + schema_inst})
            payload["messages"] = messages_copy

        # Older catalog records may not include supported_parameters. Preserve
        # the OpenAI-compatible defaults in that case.
        if not supported or "temperature" in supported:
            if request.temperature is not None:
                payload["temperature"] = request.temperature

        if request.max_tokens is not None and token_parameter:
            payload[token_parameter] = request.max_tokens

        return payload

    @staticmethod
    def _parse_http_error(response: httpx.Response) -> OpenRouterUpstreamError:
        try:
            payload = response.json()
        except ValueError:
            payload = None
        return ModelRouterService._parse_error_payload(
            payload,
            response.status_code,
            response.headers.get("Retry-After"),
            response.text[:500].strip() or None,
        )

    @staticmethod
    def _parse_embedded_error(payload: Dict[str, Any]) -> Optional[OpenRouterUpstreamError]:
        error = payload.get("error")
        choices = payload.get("choices") or []
        if not error and choices and isinstance(choices[0], dict):
            error = choices[0].get("error")
            if not error and choices[0].get("finish_reason") == "error":
                error = {"message": "OpenRouter returned finish_reason=error."}
        if not error:
            return None
        return ModelRouterService._parse_error_payload(error, 502, None, None)

    @staticmethod
    def _parse_error_payload(
        payload: Any,
        status_code: int,
        retry_after: Optional[str],
        fallback_message: Optional[str],
    ) -> OpenRouterUpstreamError:
        if isinstance(payload, dict):
            error = payload.get("error", payload)
        elif payload:
            error = {"message": str(payload)}
        else:
            error = {}
        if not isinstance(error, dict):
            error = {"message": str(error)}
        metadata = error.get("metadata") or {}
        if not isinstance(metadata, dict):
            metadata = {}
        routing_metadata = (
            payload.get("openrouter_metadata")
            if isinstance(payload, dict) and isinstance(payload.get("openrouter_metadata"), dict)
            else {}
        )
        raw_message = error.get("message") or fallback_message or "Unknown OpenRouter error"
        raw_code = error.get("code")
        detail = (
            metadata.get("raw")
            or metadata.get("provider_error")
            or metadata.get("provider_code")
        )
        provider_code = metadata.get("provider_code")
        if not provider_code and raw_code is not None and str(raw_code) != str(status_code):
            provider_code = str(raw_code)
        provider_name = metadata.get("provider_name")
        if not provider_name:
            attempts = routing_metadata.get("attempts") or []
            if isinstance(attempts, list) and attempts:
                provider_name = attempts[-1].get("provider") if isinstance(attempts[-1], dict) else None
        if not provider_name:
            endpoints = routing_metadata.get("endpoints") or {}
            available = endpoints.get("available") if isinstance(endpoints, dict) else []
            if isinstance(available, list):
                selected = next(
                    (entry for entry in available if isinstance(entry, dict) and entry.get("selected")),
                    None,
                )
                provider_name = selected.get("provider") if selected else None
        return OpenRouterUpstreamError(
            status_code=status_code,
            message=str(raw_message)[:1000],
            error_type=(
                metadata.get("error_type")
                or error.get("error_type")
                or error.get("type")
            ),
            provider_code=provider_code,
            provider_name=provider_name,
            details=str(detail)[:1000] if detail else None,
            retry_after=retry_after,
        )

    @staticmethod
    def _to_http_exception(error: OpenRouterUpstreamError) -> HTTPException:
        if error.error_type == "payment_required" or error.status_code == 402:
            status_code = 402
        elif error.error_type == "rate_limit_exceeded" or error.status_code == 429:
            status_code = 429
        elif error.error_type == "timeout" or error.status_code == 408:
            status_code = 504
        elif error.status_code in {500, 502, 503, 504}:
            status_code = 503
        else:
            status_code = 502
        headers = {}
        if error.retry_after and status_code in {429, 503}:
            headers["Retry-After"] = error.retry_after
        if 400 <= error.status_code < 500 and error.status_code not in {402, 408, 429}:
            status_code = error.status_code
        detail = f"OpenRouter error ({error.error_type or error.status_code}): {error.message}"
        if error.provider_code:
            detail += f" [provider_code={error.provider_code}]"
        return HTTPException(status_code=status_code, detail=detail, headers=headers or None)

    async def _select_candidates(
        self, request: ModelRouteRequest, force_refresh: bool = False
    ) -> List[Dict[str, Any]]:
        override = request.metadata.get("model_override") if request.metadata else None
        preferred = MODEL_ALIASES.get(override, override) if override else None
        if settings.openrouter_api_key == "mock-key":
            return [
                {
                    "model_id": preferred or self.resolve_model(request.capability),
                    "input_price_per_million": 0.0,
                    "output_price_per_million": 0.0,
                }
            ]
        catalog = await ModelCatalogService(self.db).get_candidates(force_refresh=force_refresh)
        prompt_tokens = max(1, sum(len(message.content) for message in request.messages) // 4)
        eligible = [
            candidate
            for candidate in catalog
            if not candidate.get("max_completion_tokens")
            or not request.max_tokens
            or candidate["max_completion_tokens"] >= request.max_tokens
        ]
        eligible = [
            candidate
            for candidate in eligible
            if (
                not candidate.get("raw_metadata")
                or (
                    candidate.get("supported_parameters")
                    and set(candidate["supported_parameters"]).intersection(
                        {"max_tokens", "max_completion_tokens"}
                    )
                    and (
                        request.temperature is None
                        or "temperature" in candidate["supported_parameters"]
                    )
                )
            )
        ]
        eligible = [
            candidate
            for candidate in eligible
            if not candidate.get("context_length")
            or prompt_tokens + (request.max_tokens or 2000) <= candidate["context_length"]
        ]

        scored = []
        for candidate in eligible:
            score = await self._score_candidate(
                request,
                candidate,
                prompt_tokens,
                request.max_tokens or 2000,
            )
            scored.append((score, candidate))
        scored.sort(key=lambda item: item[0], reverse=True)
        candidates = [candidate for _, candidate in scored]

        if preferred:
            preferred_entry = next(
                (candidate for candidate in candidates if candidate["model_id"] == preferred),
                {"model_id": preferred, "input_price_per_million": 0.0, "output_price_per_million": 0.0},
            )
            candidates = [preferred_entry] + [
                candidate for candidate in candidates if candidate["model_id"] != preferred
            ]

        if not candidates:
            candidates = [
                {
                    "model_id": self.resolve_model(request.capability),
                    "input_price_per_million": 0.0,
                    "output_price_per_million": 0.0,
                }
            ]
        # OpenRouter accepts at most three model fallbacks in one request.
        candidate_limit = min(3, max(1, settings.model_route_max_candidates))
        return candidates[:candidate_limit]

    async def _score_candidate(
        self,
        request: ModelRouteRequest,
        candidate: Dict[str, Any],
        prompt_tokens: int,
        max_tokens: int,
    ) -> float:
        quality_prior = self._quality_prior(candidate)
        result = await self.db.execute(
            select(ModelRoutingOutcome)
            .where(
                ModelRoutingOutcome.capability == request.capability.value,
                ModelRoutingOutcome.model_id == candidate["model_id"],
            )
            .order_by(ModelRoutingOutcome.created_at.desc())
            .limit(30)
        )
        outcomes = list(result.scalars().all())
        target_features = self._task_features(request)
        similar_outcomes = [
            row
            for row in outcomes
            if self._features_match(row.task_features, target_features)
        ]
        if len(similar_outcomes) >= 2:
            outcomes = similar_outcomes
        observed = [row.quality_score for row in outcomes if row.quality_score is not None]
        prior_weight = 4.0
        quality = (
            (quality_prior * prior_weight + sum(observed))
            / (prior_weight + len(observed))
        )
        successes = sum(1 for row in outcomes if row.success)
        reliability = (successes + 2.0) / (len(outcomes) + 4.0)
        latencies = [row.latency_ms for row in outcomes if row.latency_ms is not None]
        latency_score = (
            1.0 / (1.0 + median(latencies) / 3000.0)
            if latencies
            else 0.5
        )
        exploration_bonus = min(0.08, 0.20 / math.sqrt(len(outcomes) + 1))
        estimated_cost = self._estimate_cost(
            {"prompt_tokens": prompt_tokens, "completion_tokens": max_tokens}, candidate
        )
        cost_score = 1.0 / (1.0 + math.log1p(max(0.0, estimated_cost) * 1000.0))
        return (
            quality * 0.48
            + reliability * 0.22
            + cost_score * 0.18
            + latency_score * 0.10
            + exploration_bonus * 0.02
        )

    @staticmethod
    def _quality_prior(candidate: Dict[str, Any]) -> float:
        """Return a catalog prior without assuming anything from model names."""
        values: List[float] = []

        def collect(value: Any, key: str = "") -> None:
            if isinstance(value, dict):
                for child_key, child_value in value.items():
                    collect(child_value, str(child_key).lower())
            elif isinstance(value, (int, float)) and key in {
                "win_rate",
                "quality",
                "score",
                "overall",
                "intelligence_index",
            }:
                normalized = float(value) / 100 if value > 1 else float(value)
                values.append(max(0.0, min(1.0, normalized)))
            elif isinstance(value, list):
                for child in value:
                    collect(child, key)

        collect(candidate.get("benchmarks") or {})
        if not values:
            return 0.55
        return sum(values) / len(values)

    @staticmethod
    def _estimate_cost(usage: Dict[str, Any], candidate: Dict[str, Any]) -> float:
        prompt = float(usage.get("prompt_tokens") or 0)
        completion = float(usage.get("completion_tokens") or 0)
        input_price = float(candidate.get("input_price_per_million") or 0)
        output_price = float(candidate.get("output_price_per_million") or 0)
        return (prompt * input_price + completion * output_price) / 1_000_000

    async def _record_outcome(
        self,
        request: ModelRouteRequest,
        request_id: Optional[str],
        model_name: str,
        usage: Dict[str, Any],
        success: bool,
        error: Optional[Exception],
        latency_ms: Optional[float] = None,
    ) -> None:
        quality_score = request.metadata.get("quality_score") if request.metadata else None
        error_code = None
        if error:
            error_code = getattr(error, "error_type", None) or getattr(
                error, "provider_code", None
            )
        self.db.add(
            ModelRoutingOutcome(
                request_id=request_id,
                capability=request.capability.value,
                model_id=model_name,
                prompt_tokens=usage.get("prompt_tokens"),
                completion_tokens=usage.get("completion_tokens"),
                estimated_cost=usage.get("estimated_cost"),
                latency_ms=latency_ms,
                success=success,
                quality_score=quality_score,
                finish_reason=usage.get("finish_reason"),
                error_code=error_code,
                error_message=str(error)[:500] if error else None,
                task_features=self._task_features(request),
            )
        )
        await self.db.commit()

    async def record_quality_feedback(
        self,
        request_id: str,
        model_id: str,
        capability: Capability,
        quality_score: float,
    ) -> None:
        result = await self.db.execute(
            select(ModelRoutingOutcome)
            .where(
                ModelRoutingOutcome.request_id == request_id,
                ModelRoutingOutcome.model_id == model_id,
                ModelRoutingOutcome.capability == capability.value,
            )
            .order_by(ModelRoutingOutcome.created_at.desc())
            .limit(1)
        )
        outcome = result.scalar_one_or_none()
        if outcome:
            outcome.quality_score = max(0.0, min(1.0, quality_score))
            await self.db.commit()

    @staticmethod
    def _task_features(request: ModelRouteRequest) -> Dict[str, Any]:
        prompt = "\n".join(message.content for message in request.messages)
        prompt_lower = prompt.lower()
        prompt_tokens = max(1, len(prompt) // 4)
        return {
            "prompt_size": (
                "small" if prompt_tokens < 1000 else
                "medium" if prompt_tokens < 4000 else "large"
            ),
            "max_tokens": (
                "small" if (request.max_tokens or 2000) < 1500 else
                "medium" if (request.max_tokens or 2000) < 3500 else "large"
            ),
            "contains_code": any(
                marker in prompt_lower
                for marker in ("code", "function", "python", "typescript", "javascript")
            ),
            "structured_output": any(
                marker in prompt_lower
                for marker in ("json", "xml", "mermaid", "schema", "specification")
            ),
        }

    @staticmethod
    def _features_match(
        observed: Optional[Dict[str, Any]], target: Dict[str, Any]
    ) -> bool:
        if not observed:
            return False
        return sum(observed.get(key) == value for key, value in target.items()) >= 3

    def _get_mock_content(self, request: ModelRouteRequest) -> str:
        # Determine caller by scanning messages
        system_prompt = ""
        user_prompt = ""
        for msg in request.messages:
            if msg.role == "system":
                system_prompt = msg.content
            elif msg.role == "user":
                user_prompt = msg.content

        # 0. Challenger/Verifier Agent
        if "Challenger/Verifier" in system_prompt or "verifier" in system_prompt.lower() or "challenger" in system_prompt.lower():
            if "intentionally_fail" in user_prompt or "mock_challenge_fail" in user_prompt:
                return '<challenge status="failed" reason="Intentionally failed challenge verification check for testing."></challenge>'
            return '<challenge status="passed"></challenge>'

        # 1. Intake Coordinator / Specification Writer
        if "Intake Coordinator" in system_prompt or "Specification Writer" in system_prompt:
            last_user_msg = ""
            for msg in reversed(request.messages):
                if msg.role == "user":
                    last_user_msg = msg.content
                    break
            
            user_msgs = [m for m in request.messages if m.role == "user"]
            
            # Extract title if any
            project_title = "Operational Performance Monitor"
            for msg in user_msgs:
                content_lower = msg.content.lower()
                if "payment" in content_lower or "stripe" in content_lower:
                    project_title = "Payment Integration Service"
                    break
                elif "auth" in content_lower or "login" in content_lower or "permission" in content_lower:
                    project_title = "Role-Based Authentication Module"
                    break
                elif "dashboard" in content_lower or "analytics" in content_lower or "portal" in content_lower:
                    project_title = "Analytics Portal Upgrade"
                    break

            is_validating = False
            if "Specification Writer" in system_prompt:
                is_validating = True
            elif last_user_msg:
                msg_clean = last_user_msg.lower().strip()
                if any(kw in msg_clean for kw in ["validate", "yes", "confirm", "proceed", "approve", "go ahead", "start"]):
                    is_validating = True
                elif len(last_user_msg) > 150:
                    is_validating = True
            
            if is_validating:
                return "VALIDATED\n" + self._generate_mock_specification(project_title)
            else:
                return (
                    "I am the Engineering Intake Coordinator. I've analyzed your project idea. [Mock Response]\n\n"
                    "To generate a validated Engineering Specification, please provide or confirm details for:\n"
                    "- **Request Summary, Objectives, Scope, and Non-Goals**: What should be built and what is out of scope.\n"
                    "- **Requirements, Constraints, and Assumptions**: Functional behavior, quality requirements, stack, deployment, and defaults.\n"
                    "- **Agent Responsibilities**: Coordinator, Architect, Builder, Reviewer, QA, and Platform expectations.\n"
                    "- **Phase Plan**: Numbered phases with Objectives, Tasks, Timeline, Resources, and Deliverables.\n"
                    "- **Missing Inputs & Upload Requests**: Documentation, credentials, exports, examples, screenshots, logs, schemas, repository links, or files that may need upload.\n"
                    "- **Validation Checklist, Risks and Blockers, and Acceptance Criteria**: How the build will be verified.\n\n"
                    "*(Tip: You can type 'validate' or 'yes' to generate the engineering specification immediately!)*"
                )

        # 2. Coordinator (Build plan or Passport Compilation)
        elif "Coordinator for the Shipyard" in system_prompt:
            if "engineering_passport" in user_prompt or "Engineering Passport" in user_prompt:
                return self._compile_engineering_passport(user_prompt)
            else:
                project_title = "Operational Performance Monitor"
                if "Payment" in user_prompt or "payment" in user_prompt:
                    project_title = "Payment Integration Service"
                elif "Auth" in user_prompt or "auth" in user_prompt:
                    project_title = "Role-Based Authentication Module"
                return self._generate_mock_build_plan(project_title)

        # 3. Architect
        elif "Architect for the Shipyard" in system_prompt:
            project_title = "Operational Performance Monitor"
            if "Payment" in user_prompt or "payment" in user_prompt:
                project_title = "Payment Integration Service"
            elif "Auth" in user_prompt or "auth" in user_prompt:
                project_title = "Role-Based Authentication Module"
            return self._generate_mock_architecture(project_title)

        # 4. Builder
        elif "Builder for the Shipyard" in system_prompt:
            project_title = "Operational Performance Monitor"
            if "Payment" in user_prompt or "payment" in user_prompt:
                project_title = "Payment Integration Service"
            elif "Auth" in user_prompt or "auth" in user_prompt:
                project_title = "Role-Based Authentication Module"
            return self._generate_mock_builder_code(project_title)

        # 5. Reviewer
        elif "Reviewer for the Shipyard" in system_prompt:
            return self._generate_mock_reviewer_feedback()

        # 6. QA
        elif "QA Engineer" in system_prompt:
            return self._generate_mock_qa_feedback()

        # 7. Platform
        elif "Platform Engineer" in system_prompt:
            return self._generate_mock_platform_feedback()

        # Fallback default
        return f"[Mock Response for {request.capability.value} using {self.resolve_model(request.capability)}]"

    def _generate_mock_specification(self, project_title: str) -> str:
        return f"""# Live Engineering Specification: {project_title}

## Request Summary
Implement **{project_title}** as a FastAPI service integrated with the existing Shipyard platform.

## Objectives
- Provide structured request handling, persistence, and operational visibility.
- Preserve provider-agnostic boundaries for infrastructure and model integrations.

## Scope
- API handlers, service layer behavior, database persistence, activity logging, tests, and deployment configuration.

## Non-Goals
- Replacing the existing workflow engine or model router.
- Building a separate frontend outside the current Shipyard interface.

## Requirements
- **FR-001**: Implement structured JSON payload intake with schema validation.
- **FR-002**: Generate detailed activity trails and log them to the Engineering Journal.
- **FR-003**: Provide dashboard-ready adapter status and health-check data.
- **FR-004**: Expose standardized health (`/healthz`) and readiness (`/readyz`) endpoints.
- **NFR-001**: Average API response latency must be less than 150ms under normal concurrent workloads.
- **NFR-002**: Enforce JWT verification for protected `/api/v1/` endpoints.

## Constraints
- **Language**: Python 3.11+
- **Framework**: FastAPI with asynchronous routers and handlers.
- **Database**: PostgreSQL through SQLAlchemy 2.x and Alembic migrations.
- **Deployment**: Docker container deployed on Railway.
- **Environment Variables**: `DATABASE_URL`, `JWT_SECRET_KEY`, `APP_ENV`.

## Assumptions
- Existing authentication, database session, activity logging, and adapter patterns remain available.
- Missing external credentials can be supplied through environment variables before deployment.

## Agent Responsibilities

### Coordinator
Create a numbered build plan with phase objectives, tasks, timelines, resources, and deliverables.

### Architect
Produce Mermaid diagrams and ADRs that map requirements to Shipyard components and data flow.

### Builder
Implement code and tests within the existing FastAPI, SQLAlchemy, and adapter patterns.

### Reviewer
Check security, maintainability, error handling, architectural compliance, and test adequacy.

### QA
Verify acceptance criteria, regression coverage, endpoint behavior, and failure handling.

### Platform
Review deployment configuration, runtime limits, observability, cost, and knowledge-candidate recommendations.

## Phase Plan

### Phase 1: Service Foundation

#### Objectives
- Establish core API and service boundaries.

#### Tasks
- Add schemas, service functions, routes, and logging events.
- Add migrations when persistent state is required.

#### Timeline
- 1 engineering pass.

#### Resources
- Existing FastAPI app, SQLAlchemy session, activity log service, and tests.

#### Deliverables
- Working service code, migration if needed, and focused unit tests.

## Missing Inputs & Upload Requests
- None currently known.

## Validation Checklist
- Required sections are present.
- Agent responsibilities are explicit.
- Acceptance criteria are testable.
- Missing uploads are listed or explicitly marked as none.

## Risks and Blockers
- External credentials or provider-specific settings may block deployment until supplied.

## Acceptance Criteria
- All protected endpoints enforce authentication.
- New tests pass in the repository test suite.
- The implementation follows the architecture and deployment constraints above.
"""

    def _generate_mock_build_plan(self, project_title: str) -> str:
        return f"""# Engineering Build Plan: {project_title}

This plan details the phases for building {project_title}.

## Phase 1: Core Service Setup
### Objectives
- Establish the service boundary and request validation model.

### Tasks
- Initialize classes in `app/core/service.py`
- Setup validation logic and exception raising

### Timeline
- 1 implementation pass.

### Resources
- Engineering Specification, existing service patterns, and FastAPI routing conventions.

### Deliverables
- Core service module and validation behavior.

## Phase 2: Integration & DB
### Objectives
- Connect persistence and integration points.

### Tasks
- Bind database interface configurations
- Configure asynchronous session context managers

### Timeline
- 1 implementation pass.

### Resources
- SQLAlchemy session utilities and existing adapter interfaces.

### Deliverables
- Database integration code and migration plan if persistence changes.

## Phase 3: Validation Testing
### Objectives
- Verify behavior and acceptance criteria.

### Tasks
- Implement async unit tests in `tests/test_service.py`
- Validate performance and boundaries

### Timeline
- 1 verification pass.

### Resources
- Pytest, anyio, and existing test fixtures.

### Deliverables
- Passing tests and documented verification results.
"""

    def _generate_mock_architecture(self, project_title: str) -> str:
        return f"""# Architectural Design for {project_title}

We have designed a modular, interface-driven layout to implement the {project_title} requirements.

<diagram>
```mermaid
graph TD
    Client[Web Frontend / Client API] -->|HTTPS / JWT| Gateway[FastAPI API Gateway]
    Gateway -->|Async Middleware| MainApp[Core Application Logic]
    MainApp -->|Adapter Interface| DB[(PostgreSQL Database)]
    MainApp -->|Adapter Interface| Cache[(Redis Cache)]
    MainApp -->|Adapter Interface| Storage[S3 Object Store]
```
</diagram>

<adr id="ADR-001">
# ADR-001: Asynchronous Database Choice

## Context
The system needs to persist project records, activity journals, and adapter logs. The data must remain relational and indexable.

## Decision
We choose PostgreSQL as the database provider, interacting through SQLAlchemy 2.0 async session pools.

## Rationale
Ensures ACID transactions and horizontal scaling. Swappable behind the Database Interface to SQLite for tests.
</adr>

<adr id="ADR-002">
# ADR-002: Adapter Registry Pattern for Replaceable Infrastructure

## Context
We need to swap between mock stubs and real providers for third-party services like models, repositories, and deployments.

## Decision
We enforce the Adapter registry pattern where concrete providers (GitHub, Railway, Claude, Gemini) implement the base interface.

## Rationale
No technology choice is hardcoded. It protects the core workflow systems from vendor lock-in.
</adr>
"""

    def _generate_mock_builder_code(self, project_title: str) -> str:
        return """# Builder Implementation Code

I have built the source files and test suites following the architecture constraints.

<file path="app/core/service.py">
import structlog
from typing import Dict, Any, Optional

logger = structlog.get_logger()

class CoreEngineeringService:
    \"\"\"Handles core execution workflow validation and event logging.\"\"\"
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.active = True

    async def process_task(self, task_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        logger.info("processing_task_started", task_id=task_id)
        if not payload:
            raise ValueError("Empty execution payload")
        
        result = {
            "status": "success",
            "task_id": task_id,
            "processed_at": "2026-08-10T10:54:00Z",
            "output": f"Processed payload of size {len(payload)}"
        }
        logger.info("processing_task_completed", task_id=task_id, result=result)
        return result
</file>

<file path="tests/test_service.py">
import pytest
from app.core.service import CoreEngineeringService

@pytest.mark.anyio
async def test_process_task_success():
    service = CoreEngineeringService({"env": "testing"})
    res = await service.process_task("test-123", {"action": "build"})
    assert res["status"] == "success"
    assert res["task_id"] == "test-123"

@pytest.mark.anyio
async def test_process_task_validation_error():
    service = CoreEngineeringService({"env": "testing"})
    with pytest.raises(ValueError):
        await service.process_task("test-123", {})
</file>

<test_results>
============================= test session starts =============================
platform win32 -- Python 3.11.0, pytest-7.4.0, pluggy-1.3.0
rootdir: c:\\Users\\burns\\OneDrive\\Documents\\GitHub\\Shipyard
plugins: anyio-4.2.0, cov-4.1.0
collected 2 items

tests/test_service.py ..                                                 [100%]

============================== 2 passed in 0.08s ===============================
</test_results>
"""

    def _generate_mock_reviewer_feedback(self) -> str:
        return """# Code Review Analysis

I have completed the review of the builder's code changes.

## Findings
- **Architecture Compliant**: Code resides in `app/core/service.py` under clean service abstractions.
- **Vulnerabilities**: Input payload keys are verified. No direct string interpolation in SQL queries.
- **Testing**: Tests include async setup and verify both happy paths and exception paths.

<review status="approved"></review>
"""

    def _generate_mock_qa_feedback(self) -> str:
        return """# QA Verification Report

We ran automated functional and regression validation checks.

## Metrics
- **Unit Tests**: 2/2 Passed
- **Code Coverage**: 100.0%
- **Latency SLA Check**: Passed (Average response 42ms)
- **Accessibility Check**: Passed (100% compliant)

<qa_status>PASSED</qa_status>
"""

    def _generate_mock_platform_feedback(self) -> str:
        return """# Platform Recommendations

Pipeline operations metrics have been collected and processed.

<recommendations>
- Configure PostgreSQL connection pool `max_overflow` limit to 10 for peak usage periods.
- Enforce structlog JSON output formatting in non-development environments.
</recommendations>

<knowledge_candidate>
### Asynchronous Database Pools in FastAPI

When defining database adapters with SQLAlchemy, ensure the engine is created globally and disposal is registered on the FastAPI shutdown hook. This prevents orphaned open connection streams on redeployments.
</knowledge_candidate>
"""

    def _compile_engineering_passport(self, user_prompt: str) -> str:
        import os
        import re
        
        # Extract files from prompt context
        files_match = re.search(r"['\"]files['\"]: \[(.*?)\]", user_prompt)
        if files_match:
            files_list = [f.strip(" '\"") for f in files_match.group(1).split(",")]
        else:
            files_list = ["app/core/service.py", "tests/test_service.py"]
            
        # Extract commit hash
        commit_match = re.search(r"['\"]commit_hash['\"]: ['\"](.*?)['\"]", user_prompt)
        commit_hash = commit_match.group(1) if commit_match else "7a8f9c1d2e3f0b"
        
        # Extract title
        title_match = re.search(r"['\"]title['\"]: ['\"](.*?)['\"]", user_prompt)
        project_title = title_match.group(1) if title_match else "Operational Performance Monitor"
        
        files_str = "\n".join(f"- `{f}`" for f in files_list)
        
        repo_tour = (
            "The repository is organized following clean architecture boundaries:\n"
            f"- `app/core/`: Contains the core service implementations. Specifically, `app/core/service.py` contains the business logic for task processing.\n"
            f"- `tests/`: Contains isolated test suites. `tests/test_service.py` validates processing outcomes and bounds checking.\n"
            "- `app/infrastructure/`: Hosts technology-specific adapters (database, storage, repository gateways)."
        )

        explain_project = (
            "### 👔 For Executives\n"
            "This project modernizes our core execution pipeline, shifting to async database pooling. This decreases infrastructure overhead by 40% and ensures stable operations during transaction spikes.\n\n"
            "### 📋 For Product Managers\n"
            "The changes support higher API throughput, enabling the product to scale to thousands of active concurrent sessions without lag or degradation.\n\n"
            "### 🛠️ For Engineering Managers\n"
            "We've established clean adapter boundaries. If we decide to swap S3 for Google Cloud Storage or move databases, developers can do so in a single config change without touching core logic.\n\n"
            "### 💻 For Developers\n"
            "You can run the service locally by initializing `CoreEngineeringService(config)`. Tests are written using pytest and are fully async.\n\n"
            "### 🔒 For Security Teams\n"
            "No credentials are hardcoded. Input boundaries are strictly checked and exceptions are cleanly handled to prevent stack trace leaks.\n\n"
            "### 👥 For Customers\n"
            "Ensures transactions are processed instantly and reliably, backed by a robust backend architecture."
        )

        timeline = (
            f"- **Intake Completed**: Engineering Specification approved and finalized.\n"
            f"- **Architecture Verified**: Component diagrams and ADRs designed.\n"
            f"- **Build Completed**: Code committed under branch hash `{commit_hash[:8]}`.\n"
            f"- **Review Signed-off**: Security checks and code standards verified.\n"
            f"- **QA Validated**: Async and unit verification suites passed."
        )

        passport = f"""# Engineering Passport — {project_title}

## Executive Summary
This document serves as the official release and blueprint dossier for the **{project_title}** project. It outlines the architectural patterns, files built, quality verification, and handoff instructions.

## What Was Built
The engineering team implemented the core files corresponding to the specification:
{files_str}

## Architecture & Repository Tour
### Request Flow & Diagram
```mermaid
graph TD
    Client[Web Frontend / Client API] -->|HTTPS / JWT| Gateway[FastAPI API Gateway]
    Gateway --> CoreAPI[Core Service Node]
    CoreAPI --> DB[(PostgreSQL Database)]
```

### Repository Tour
{repo_tour}

## Technology Stack
- **Backend Language**: Python 3.11+
- **Web Framework**: FastAPI (Async routes)
- **Database Connection**: SQLAlchemy 2.0 Async (asyncpg)
- **Logging**: Structlog JSON logging
- **Testing Framework**: Pytest with Asyncio

## Engineering Decisions
The Architect established the following design records:
- **ADR-001**: Asynchronous PostgreSQL Database with pgvector
- **ADR-002**: Adapter Pattern for Replaceable Infrastructure

## AI Engineering Summary
- **Coordinator**: Directed execution phases, compiled build plan, and compiled this passport.
- **Architect**: Modeled systems, drew Mermaid schemas, and wrote Architecture Decision Records.
- **Builder**: Programmed python classes, compiled test files, and pushed to the repository.
- **Reviewer**: Evaluated code quality, performance impacts, and security vulnerabilities.
- **QA**: Verified compliance with functional specs and validated readiness.
- **Platform**: Gathers logs, monitored SLAs, and formulated learning recommendations.

## Deployment Guide
### Release Blueprint
- **Release Tag**: `rel_{commit_hash[:8]}`
- **Commit Hash**: `{commit_hash}`

### Execution Steps
1. **Source Code**: Pull branch matching the commit `{commit_hash[:8]}`.
2. **Configuration**: Set up env parameters in `.env` (ports, credentials).
3. **Database Setup**: Execute migration upgrades: `alembic upgrade head`.
4. **Run Containers**: Startup the application services `docker compose up -d`.
5. **Verification**: Run diagnostic validation checks: `/healthz` and `/readyz`.

## External Dependencies & Risks
- **PostgreSQL Database**: Port 5432 must be open.
- **Security Access**: JWT secret token must be configured in environment variables.

## Explain This Project
{explain_project}

## Engineering Timeline
{timeline}
"""
        return passport

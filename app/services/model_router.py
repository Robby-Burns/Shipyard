from typing import Any, Dict, Optional

import httpx
from sqlalchemy.ext.asyncio import AsyncSession
import structlog

from app.config.settings import settings
from app.schemas.model_router import (
    Capability,
    ModelRouteRequest,
    ModelRouteResponse,
)
from app.services.activity_log import ActivityLogService

logger = structlog.get_logger()


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
        }
        return capability_map.get(
            capability, settings.default_model_general_reasoning
        )

    async def route(
        self, request: ModelRouteRequest, request_id: Optional[str] = None
    ) -> ModelRouteResponse:
        model_name = self.resolve_model(request.capability)

        # Log routing attempt
        await self.activity_log_service.record(
            event_type="model_route_started",
            source="model_router",
            request_id=request_id,
            payload={"capability": request.capability.value, "model": model_name},
        )

        # Mock fallback for development/testing if API key is mock
        if settings.openrouter_api_key == "mock-key":
            response = ModelRouteResponse(
                id="mock-completion-id",
                capability=request.capability,
                model_used=model_name,
                content=(
                    f"[Mock Response for {request.capability.value} using"
                    f" {model_name}]"
                ),
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
            }
            payload = {
                "model": model_name,
                "messages": [msg.model_dump() for msg in request.messages],
                "temperature": request.temperature,
                "max_tokens": request.max_tokens,
            }

            async with httpx.AsyncClient() as client:
                res = await client.post(
                    f"{settings.openrouter_base_url}/chat/completions",
                    json=payload,
                    headers=headers,
                    timeout=30.0,
                )
                res.raise_for_status()
                data = res.json()

                content = data["choices"][0]["message"]["content"]
                usage = data.get("usage", {})

                response = ModelRouteResponse(
                    id=data.get("id", "completion-id"),
                    capability=request.capability,
                    model_used=model_name,
                    content=content,
                    usage=usage,
                )

        # Record completion log
        await self.activity_log_service.record(
            event_type="model_route_completed",
            source="model_router",
            request_id=request_id,
            payload={
                "capability": request.capability.value,
                "model": model_name,
                "usage": response.usage,
            },
        )

        return response

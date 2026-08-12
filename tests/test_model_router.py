import httpx
import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
import jwt
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.database.session import get_db
from app.config.settings import settings
from app.database.session import Base
from app.main import app
from app.schemas.model_router import (
    Capability,
    ChatMessage,
    ModelRouteRequest,
)
from app.services.activity_log import ActivityLogService
from app.services.model_router import (
    MODEL_ALIASES,
    ModelRouterService,
    OpenRouterUpstreamError,
)

client = TestClient(app)


@pytest.fixture
async def async_session():
    test_engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async_session_factory = sessionmaker(
        test_engine, class_=AsyncSession, expire_on_commit=False
    )
    async with async_session_factory() as session:
        yield session

    await test_engine.dispose()


@pytest.mark.anyio
async def test_capability_resolution(async_session: AsyncSession):
    service = ModelRouterService(async_session)

    assert (
        service.resolve_model(Capability.CODING) == settings.default_model_coding
    )
    assert (
        service.resolve_model(Capability.ARCHITECTURE)
        == settings.default_model_architecture
    )
    assert (
        service.resolve_model(Capability.CODE_REVIEW)
        == settings.default_model_code_review
    )
    assert (
        service.resolve_model(Capability.TESTING)
        == settings.default_model_testing
    )
    assert (
        service.resolve_model(Capability.GENERAL_REASONING)
        == settings.default_model_general_reasoning
    )


def test_retired_openrouter_model_alias_is_normalized():
    assert MODEL_ALIASES["anthropic/claude-3.5-sonnet"] == "google/gemini-2.5-flash"


def test_model_router_matches_catalog_supported_parameters():
    request = ModelRouteRequest(
        capability=Capability.GENERAL_REASONING,
        messages=[ChatMessage(role="user", content="hello")],
        temperature=0.2,
        max_tokens=3500,
    )
    payload = ModelRouterService(None)._build_upstream_payload(
        request,
        "provider/model",
        [
            {"model_id": "provider/model"},
            {"model_id": "provider/fallback"},
        ],
        {"supported_parameters": ["max_completion_tokens"]},
    )

    assert payload["max_completion_tokens"] == 3500
    assert "max_tokens" not in payload
    assert "temperature" not in payload
    assert payload["models"] == ["provider/model", "provider/fallback"]
    assert payload["provider"]["require_parameters"] is True


def test_model_router_parses_provider_error_metadata():
    error = ModelRouterService._parse_error_payload(
        {
            "error": {
                "code": 502,
                "message": "Provider returned error",
                "metadata": {
                    "error_type": "provider_unavailable",
                    "provider_code": "upstream_500",
                },
            }
        },
        502,
        "3",
        None,
    )

    assert isinstance(error, OpenRouterUpstreamError)
    assert error.error_type == "provider_unavailable"
    assert error.provider_code == "upstream_500"
    assert error.retry_after == "3"


def test_model_router_detects_embedded_completion_error():
    error = ModelRouterService._parse_embedded_error(
        {
            "choices": [
                {
                    "finish_reason": "error",
                    "error": {
                        "message": "Provider failed during generation",
                        "metadata": {"error_type": "provider_unavailable"},
                    },
                }
            ]
        }
    )

    assert error is not None
    assert error.error_type == "provider_unavailable"


def test_model_router_uses_catalog_evidence_without_name_heuristics():
    neutral = ModelRouterService._quality_prior(
        {"model_id": "vendor/flagship-model", "benchmarks": {}}
    )
    benchmarked = ModelRouterService._quality_prior(
        {"model_id": "vendor/unknown-model", "benchmarks": {"win_rate": 80}}
    )

    assert neutral == 0.55
    assert benchmarked == 0.8


@pytest.mark.anyio
async def test_model_router_service_execution(async_session: AsyncSession):
    service = ModelRouterService(async_session)
    activity_service = ActivityLogService(async_session)

    request = ModelRouteRequest(
        capability=Capability.CODING,
        messages=[ChatMessage(role="user", content="Write a quicksort in Python")],
    )

    response = await service.route(request, request_id="test-req-123")
    assert response.capability == Capability.CODING
    assert response.model_used == settings.default_model_coding
    assert "Mock Response for coding" in response.content

    # Verify ActivityLog entries created
    logs = await activity_service.search(
        filters=type(
            "Filter",
            (),
            {
                "event_type": None,
                "source": "model_router",
                "request_id": "test-req-123",
                "limit": 10,
                "offset": 0,
            },
        )()
    )
    assert len(logs) == 2
    event_types = {log.event_type for log in logs}
    assert "model_route_started" in event_types
    assert "model_route_completed" in event_types


@pytest.mark.anyio
async def test_model_router_normalizes_base_url_and_surfaces_upstream_error(
    async_session: AsyncSession, monkeypatch
):
    service = ModelRouterService(async_session)
    monkeypatch.setattr(settings, "openrouter_api_key", "real-key")
    monkeypatch.setattr(
        settings, "openrouter_base_url", "https://openrouter.ai/api/v1/"
    )

    requested_urls = []
    requested_headers = []

    async def mock_get(self, url, **kwargs):
        return httpx.Response(
            200,
            json={
                "data": [
                    {
                        "id": "google/gemini-2.5-flash",
                        "name": "Gemini 2.5 Flash",
                        "context_length": 1000000,
                        "pricing": {"prompt": "0.0000003", "completion": "0.0000025"},
                        "top_provider": {"max_completion_tokens": 8192},
                        "supported_parameters": ["max_tokens", "temperature"],
                        "architecture": {"output_modalities": ["text"]},
                    }
                ]
            },
            request=httpx.Request("GET", url),
        )

    async def mock_post(self, url, **kwargs):
        requested_urls.append(url)
        requested_headers.append(kwargs.get("headers"))
        return httpx.Response(
            404,
            json={
                "error": {
                    "code": "not_found",
                    "message": "No such model",
                }
            },
            request=httpx.Request("POST", url),
        )

    monkeypatch.setattr(httpx.AsyncClient, "post", mock_post)
    monkeypatch.setattr(httpx.AsyncClient, "get", mock_get)

    request = ModelRouteRequest(
        capability=Capability.GENERAL_REASONING,
        messages=[ChatMessage(role="user", content="hello")],
    )

    with pytest.raises(HTTPException) as exc_info:
        await service.route(request, request_id="not-found-id")

    assert requested_urls == ["https://openrouter.ai/api/v1/chat/completions"]
    assert requested_headers[0]["X-OpenRouter-Metadata"] == "enabled"
    assert exc_info.value.status_code == 404
    assert "No such model" in exc_info.value.detail


def test_model_router_maps_retryable_upstream_errors_and_retry_after():
    error = OpenRouterUpstreamError(
        status_code=429,
        message="Too many requests",
        error_type="rate_limit_exceeded",
        retry_after="7",
    )

    mapped = ModelRouterService._to_http_exception(error)

    assert mapped.status_code == 429
    assert mapped.headers == {"Retry-After": "7"}


def test_model_router_drops_incompatible_model_fallbacks():
    request = ModelRouteRequest(
        capability=Capability.GENERAL_REASONING,
        messages=[ChatMessage(role="user", content="hello")],
        max_tokens=3500,
    )
    payload = ModelRouterService(None)._build_upstream_payload(
        request,
        "provider/model",
        [
            {"model_id": "provider/model", "supported_parameters": ["max_tokens"]},
            {
                "model_id": "provider/completion-only",
                "supported_parameters": ["max_completion_tokens"],
            },
        ],
        {"supported_parameters": ["max_tokens"]},
    )

    assert payload["model"] == "provider/model"
    assert "models" not in payload
    assert payload["max_tokens"] == 3500


def test_model_router_endpoint_unauthenticated():
    response = client.post(
        "/api/v1/model-router/completion",
        json={
            "capability": "coding",
            "messages": [{"role": "user", "content": "Hello"}],
        },
    )
    assert response.status_code == 401


def test_model_router_endpoint_authenticated():
    test_engine = create_async_engine("sqlite+aiosqlite:///:memory:")

    async def init_and_override():
        async with test_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        async_session = sessionmaker(
            test_engine, class_=AsyncSession, expire_on_commit=False
        )
        async with async_session() as session:
            yield session

    app.dependency_overrides[get_db] = init_and_override
    try:
        token = jwt.encode(
            {"sub": "test_user", "exp": 9999999999},
            settings.jwt_secret_key,
            algorithm=settings.jwt_algorithm,
        )
        response = client.post(
            "/api/v1/model-router/completion",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "capability": "testing",
                "messages": [{"role": "user", "content": "Generate test plan"}],
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["capability"] == "testing"
        assert data["model_used"] == settings.default_model_testing
        assert "Mock Response for testing" in data["content"]
    finally:
        app.dependency_overrides.clear()

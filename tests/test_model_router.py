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
from app.services.model_router import MODEL_ALIASES, ModelRouterService

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
        {"supported_parameters": ["max_completion_tokens"]},
    )

    assert payload["max_completion_tokens"] == 3500
    assert "max_tokens" not in payload
    assert "temperature" not in payload


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
                        "supported_parameters": ["max_tokens"],
                    }
                ]
            },
            request=httpx.Request("GET", url),
        )

    async def mock_post(self, url, **kwargs):
        requested_urls.append(url)
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
    assert exc_info.value.status_code == 502
    assert "No such model" in exc_info.value.detail


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

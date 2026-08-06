from fastapi.testclient import TestClient
import jwt
import pytest
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.api.health import get_db
from app.config.settings import settings
from app.database.session import Base
from app.main import app
from app.schemas.model_router import (
    Capability,
    ChatMessage,
    ModelRouteRequest,
)
from app.services.activity_log import ActivityLogService
from app.services.model_router import ModelRouterService

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
            {"sub": "test_user"},
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

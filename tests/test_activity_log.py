from fastapi.testclient import TestClient
import jwt
import pytest
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.api.health import get_db
from app.config.settings import settings
from app.database.session import Base
from app.main import app
from app.schemas.activity_log import ActivityLogFilter
from app.services.activity_log import ActivityLogService

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
async def test_activity_log_service_record_and_search(async_session: AsyncSession):
    service = ActivityLogService(async_session)

    log1 = await service.record(
        event_type="model_request",
        source="model_router",
        request_id="req-101",
        payload={"model": "gpt-4o"},
    )
    assert log1.id is not None
    assert log1.event_type == "model_request"

    log2 = await service.record(
        event_type="tool_execution",
        source="tool_gateway",
        request_id="req-102",
        payload={"tool": "github"},
    )
    assert log2.id is not None

    # Search by event_type
    filtered_events = await service.search(
        ActivityLogFilter(event_type="model_request")
    )
    assert len(filtered_events) == 1
    assert filtered_events[0].source == "model_router"

    # Search by source
    filtered_source = await service.search(
        ActivityLogFilter(source="tool_gateway")
    )
    assert len(filtered_source) == 1
    assert filtered_source[0].event_type == "tool_execution"

    # Search by request_id
    filtered_req = await service.search(ActivityLogFilter(request_id="req-101"))
    assert len(filtered_req) == 1
    assert filtered_req[0].payload == {"model": "gpt-4o"}


def test_activity_log_endpoint_unauthenticated():
    response = client.get("/api/v1/activity-logs")
    assert response.status_code == 401


def test_activity_log_endpoint_authenticated():
    test_engine = create_async_engine("sqlite+aiosqlite:///:memory:")

    async def init_and_override():
        async with test_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        async_session = sessionmaker(
            test_engine, class_=AsyncSession, expire_on_commit=False
        )
        async with async_session() as session:
            service = ActivityLogService(session)
            await service.record(
                event_type="user_login",
                source="auth_service",
                request_id="req-auth-1",
            )
            yield session

    app.dependency_overrides[get_db] = init_and_override
    try:
        token = jwt.encode(
            {"sub": "admin_user"},
            settings.jwt_secret_key,
            algorithm=settings.jwt_algorithm,
        )
        response = client.get(
            "/api/v1/activity-logs?event_type=user_login",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 1
        assert data[0]["event_type"] == "user_login"
        assert data[0]["source"] == "auth_service"
    finally:
        app.dependency_overrides.clear()

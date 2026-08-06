from fastapi.testclient import TestClient
import jwt
import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.database.session import get_db
from app.config.settings import settings
from app.database.models.tool_log import ToolExecutionLog
from app.database.session import Base
from app.main import app
from app.schemas.tool_gateway import ToolExecutionRequest, ToolName
from app.services.tool_gateway import ToolGatewayService

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
async def test_tool_gateway_service_execution(async_session: AsyncSession):
    service = ToolGatewayService(async_session)

    request = ToolExecutionRequest(
        tool=ToolName.GITHUB,
        action="create_pull_request",
        payload={"title": "Feature branch PR", "base": "main"},
    )

    response = await service.execute(request, request_id="tool-req-1")

    assert response.tool == ToolName.GITHUB
    assert response.action == "create_pull_request"
    assert response.is_success is True
    assert response.status_code == 200
    assert response.execution_time_ms >= 0.0
    assert response.response["executed"] is True

    # Verify audit record in database
    result = await async_session.execute(
        select(ToolExecutionLog).where(
            ToolExecutionLog.request_id == "tool-req-1"
        )
    )
    logs = list(result.scalars().all())
    assert len(logs) == 1
    assert logs[0].tool_name == "github"
    assert logs[0].action == "create_pull_request"
    assert logs[0].is_success is True


def test_tool_gateway_endpoint_unauthenticated():
    response = client.post(
        "/api/v1/tool-gateway/execute",
        json={"tool": "docker", "action": "build_image", "payload": {}},
    )
    assert response.status_code == 401


def test_tool_gateway_endpoint_authenticated():
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
            {"sub": "dev_user", "exp": 9999999999},
            settings.jwt_secret_key,
            algorithm=settings.jwt_algorithm,
        )
        response = client.post(
            "/api/v1/tool-gateway/execute",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "tool": "railway",
                "action": "deploy_service",
                "payload": {"service": "shipyard-api"},
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["tool"] == "railway"
        assert data["action"] == "deploy_service"
        assert data["is_success"] is True
        assert data["status_code"] == 200
    finally:
        app.dependency_overrides.clear()

from fastapi.testclient import TestClient
import jwt
import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.database.session import get_db
from app.config.settings import settings
from app.database.models.activity_log import ActivityLog
from app.database.session import Base
from app.main import app
from app.schemas.agent import AgentExecutionRequest, DisciplineRole
from app.services.agents.architect import ArchitectAgent
from app.services.agents.coordinator import CoordinatorAgent

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
async def test_coordinator_agent_direct_execution(
    async_session: AsyncSession,
):
    agent = CoordinatorAgent(async_session)
    request = AgentExecutionRequest(
        role=DisciplineRole.COORDINATOR,
        task_input="Break down auth service migration",
        context={"target_phase": "Phase 1"},
    )
    response = await agent.run(request, request_id="coord-req-1")

    assert response.role == DisciplineRole.COORDINATOR
    assert response.status == "success"
    assert len(response.output_text) > 0
    assert response.model_used == settings.default_model_general_reasoning

    # Verify ActivityLog entries
    res = await async_session.execute(
        select(ActivityLog).where(ActivityLog.request_id == "coord-req-1")
    )
    logs = list(res.scalars().all())
    sources = {log.source for log in logs}
    assert "agent_coordinator" in sources


@pytest.mark.anyio
async def test_architect_agent_direct_execution(async_session: AsyncSession):
    agent = ArchitectAgent(async_session)
    request = AgentExecutionRequest(
        role=DisciplineRole.ARCHITECT,
        task_input="Design event streaming interface",
        context={"broker": "Kafka"},
    )
    response = await agent.run(request, request_id="arch-req-1")

    assert response.role == DisciplineRole.ARCHITECT
    assert response.status == "success"
    assert len(response.output_text) > 0
    assert response.model_used == settings.default_model_architecture

    # Verify ActivityLog entries
    res = await async_session.execute(
        select(ActivityLog).where(ActivityLog.request_id == "arch-req-1")
    )
    logs = list(res.scalars().all())
    sources = {log.source for log in logs}
    assert "agent_architect" in sources


def test_agent_endpoints_unauthenticated():
    coord_res = client.post(
        "/api/v1/agents/coordinator/run",
        json={
            "role": "coordinator",
            "task_input": "Test plan generation",
        },
    )
    assert coord_res.status_code == 401

    arch_res = client.post(
        "/api/v1/agents/architect/run",
        json={
            "role": "architect",
            "task_input": "Test architecture generation",
        },
    )
    assert arch_res.status_code == 401


def test_agent_endpoints_authenticated():
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
            {"sub": "lead_eng"},
            settings.jwt_secret_key,
            algorithm=settings.jwt_algorithm,
        )
        headers = {"Authorization": f"Bearer {token}"}

        # Coordinator endpoint
        coord_res = client.post(
            "/api/v1/agents/coordinator/run",
            headers=headers,
            json={
                "role": "coordinator",
                "task_input": "Generate build plan for user dashboard",
                "context": {"deadline": "2026-Q3"},
            },
        )
        assert coord_res.status_code == 200
        coord_data = coord_res.json()
        assert coord_data["role"] == "coordinator"
        assert coord_data["status"] == "success"

        # Architect endpoint
        arch_res = client.post(
            "/api/v1/agents/architect/run",
            headers=headers,
            json={
                "role": "architect",
                "task_input": "Define schema for user preferences API",
                "context": {"format": "JSON"},
            },
        )
        assert arch_res.status_code == 200
        arch_data = arch_res.json()
        assert arch_data["role"] == "architect"
        assert arch_data["status"] == "success"
    finally:
        app.dependency_overrides.clear()

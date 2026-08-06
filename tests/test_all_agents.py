from fastapi.testclient import TestClient
import jwt
import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.config.settings import settings
from app.database.models.activity_log import ActivityLog
from app.database.session import Base, get_db
from app.main import app
from app.schemas.agent import AgentExecutionRequest, DisciplineRole
from app.services.agents import (
    BuilderAgent,
    PlatformAgent,
    QAAgent,
    ReviewerAgent,
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
async def test_builder_agent_execution(async_session: AsyncSession):
    agent = BuilderAgent(async_session)
    request = AgentExecutionRequest(
        role=DisciplineRole.BUILDER,
        task_input="Write user registration service",
    )
    response = await agent.run(request, request_id="builder-req-1")

    assert response.role == DisciplineRole.BUILDER
    assert response.status == "success"
    assert response.model_used == settings.default_model_coding

    res = await async_session.execute(
        select(ActivityLog).where(ActivityLog.request_id == "builder-req-1")
    )
    logs = list(res.scalars().all())
    assert len(logs) >= 2


@pytest.mark.anyio
async def test_reviewer_agent_execution(async_session: AsyncSession):
    agent = ReviewerAgent(async_session)
    request = AgentExecutionRequest(
        role=DisciplineRole.REVIEWER,
        task_input="Review pull request #42 for security flaws",
    )
    response = await agent.run(request, request_id="reviewer-req-1")

    assert response.role == DisciplineRole.REVIEWER
    assert response.status == "success"
    assert response.model_used == settings.default_model_code_review


@pytest.mark.anyio
async def test_qa_agent_execution(async_session: AsyncSession):
    agent = QAAgent(async_session)
    request = AgentExecutionRequest(
        role=DisciplineRole.QA,
        task_input="Generate integration test cases for payments",
    )
    response = await agent.run(request, request_id="qa-req-1")

    assert response.role == DisciplineRole.QA
    assert response.status == "success"
    assert response.model_used == settings.default_model_testing


@pytest.mark.anyio
async def test_platform_agent_execution(async_session: AsyncSession):
    agent = PlatformAgent(async_session)
    request = AgentExecutionRequest(
        role=DisciplineRole.PLATFORM,
        task_input="Analyze pipeline latency metrics",
    )
    response = await agent.run(request, request_id="platform-req-1")

    assert response.role == DisciplineRole.PLATFORM
    assert response.status == "success"
    assert response.model_used == settings.default_model_general_reasoning


def test_all_discipline_endpoints_authenticated():
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
            {"sub": "eng_lead"},
            settings.jwt_secret_key,
            algorithm=settings.jwt_algorithm,
        )
        headers = {"Authorization": f"Bearer {token}"}

        endpoints = [
            ("builder", DisciplineRole.BUILDER),
            ("reviewer", DisciplineRole.REVIEWER),
            ("qa", DisciplineRole.QA),
            ("platform", DisciplineRole.PLATFORM),
        ]

        for path_segment, role_enum in endpoints:
            res = client.post(
                f"/api/v1/agents/{path_segment}/run",
                headers=headers,
                json={
                    "role": role_enum.value,
                    "task_input": f"Execute test task for {role_enum.value}",
                },
            )
            assert res.status_code == 200
            data = res.json()
            assert data["role"] == role_enum.value
            assert data["status"] == "success"
    finally:
        app.dependency_overrides.clear()

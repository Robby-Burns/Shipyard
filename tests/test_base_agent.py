import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.database.models.activity_log import ActivityLog
from app.database.session import Base
from app.schemas.agent import AgentExecutionRequest, DisciplineRole
from app.schemas.model_router import Capability
from app.services.agents.base import BaseAgent


class DummyAgent(BaseAgent):

    def get_system_prompt(self) -> str:
        return "You are a test builder agent."


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
async def test_base_agent_execution_and_activity_logging(
    async_session: AsyncSession,
):
    agent = DummyAgent(
        role=DisciplineRole.BUILDER,
        capability=Capability.CODING,
        db=async_session,
    )

    request = AgentExecutionRequest(
        role=DisciplineRole.BUILDER,
        task_input="Implement user login component",
        context={"feature": "auth"},
    )

    response = await agent.run(request, request_id="agent-req-123")

    assert response.role == DisciplineRole.BUILDER
    assert response.status == "success"
    assert len(response.output_text) > 0
    assert response.model_used is not None
    assert response.execution_time_ms >= 0.0

    # Verify ActivityLog entries
    res = await async_session.execute(
        select(ActivityLog).where(ActivityLog.request_id == "agent-req-123")
    )
    logs = list(res.scalars().all())
    assert len(logs) >= 2

    event_types = {log.event_type for log in logs}
    assert "agent_execution_started" in event_types
    assert "agent_execution_completed" in event_types

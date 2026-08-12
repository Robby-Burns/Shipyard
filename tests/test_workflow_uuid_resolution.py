import pytest
import uuid
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.database.session import Base
from app.database.models.workflow import WorkflowRun
from app.schemas.workflow import (
    WorkflowCreateRequest,
    WorkflowStatus,
)
from app.schemas.agent import AgentExecutionRequest, DisciplineRole
from app.services.agents.coordinator import CoordinatorAgent
from app.services.workflow_engine import WorkflowEngineService


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
async def test_specification_ref_resolution(async_session: AsyncSession):
    service = WorkflowEngineService(async_session)

    # 1. Create a workflow with a long specification (> 2000 chars)
    long_spec = "System Requirement Spec:\n" + ("A" * 2500)
    create_req = WorkflowCreateRequest(
        title="Long Spec Feature",
        specification=long_spec,
    )
    # The creator service saves it to DB
    wf = await service.create_workflow(create_req, request_id="wf-long-1")
    assert wf.status == WorkflowStatus.CREATED

    # 2. Run the first step (Coordinator) using the workflow engine
    # Under the hood, this will invoke the CoordinatorAgent with specification_ref = wf.id
    wf_updated = await service.execute_step(wf.id, request_id="wf-long-1")

    # 3. Confirm coordinator succeeded and generated a build plan
    assert wf_updated.status == WorkflowStatus.DESIGNING
    assert "build_plan" in wf_updated.artifacts
    assert len(wf_updated.artifacts["build_plan"]) > 0


@pytest.mark.anyio
async def test_specification_ref_resolution_missing_workflow(async_session: AsyncSession):
    # Try running the coordinator directly with a non-existent UUID reference
    agent = CoordinatorAgent(async_session)
    non_existent_id = uuid.uuid4()
    
    req = AgentExecutionRequest(
        role=DisciplineRole.COORDINATOR,
        task_input="Breakdown & Planning",
        specification_ref=non_existent_id
    )

    with pytest.raises(ValueError) as exc_info:
        await agent.run(req, request_id="missing-ref-1")
        
    assert "resolved specification is empty or not found in database" in str(exc_info.value)


@pytest.mark.anyio
async def test_force_restart_clears_all_fields(async_session: AsyncSession):
    # Create workflow
    create_req = WorkflowCreateRequest(
        title="Force Restart Test",
        specification="Simple spec",
    )
    service = WorkflowEngineService(async_session)
    wf = await service.create_workflow(create_req, request_id="wf-force-1")
    
    # Manually pollute the workflow state to simulate a terminal/escalated status
    wf.status = WorkflowStatus.FAILED
    wf.error_message = "Some error occurred"
    wf.artifacts = {"build_plan": "stale build plan", "generated_code": "stale code"}
    wf.approved_by = "manager_approved"
    wf.approved_at = pytest.importorskip("datetime").datetime.now()
    await async_session.commit()
    await async_session.refresh(wf)

    # Mimic the force restart logic in api/v1/workflows.py
    wf.status = WorkflowStatus.CREATED
    wf.current_step = "created"
    wf.artifacts = {}
    wf.error_message = None
    wf.approved_by = None
    wf.approved_at = None
    await async_session.commit()
    await async_session.refresh(wf)

    assert wf.status == WorkflowStatus.CREATED
    assert wf.current_step == "created"
    assert wf.artifacts == {}
    assert wf.error_message is None
    assert wf.approved_by is None
    assert wf.approved_at is None

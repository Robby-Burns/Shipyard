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
from app.schemas.workflow import (
    WorkflowCreateRequest,
    WorkflowEscalationRequest,
    WorkflowResolutionRequest,
    WorkflowStatus,
)
from app.services.workflow_engine import WorkflowEngineService

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
async def test_workflow_escalation_and_resolution_flow(
    async_session: AsyncSession,
):
    service = WorkflowEngineService(async_session)

    # Create workflow
    wf = await service.create_workflow(
        WorkflowCreateRequest(
            title="High-Risk Security Feature",
            specification="Implement custom cryptographic protocol",
        ),
        request_id="esc-req-1",
    )

    # Execute first step (PLANNING -> DESIGNING)
    wf = await service.execute_step(wf.id, request_id="esc-req-1")
    assert wf.status == WorkflowStatus.DESIGNING

    # Escalate workflow
    esc_req = WorkflowEscalationRequest(
        reason="Security reviewer identified potential side-channel vulnerability",
        escalated_by="reviewer_agent",
    )
    wf_escalated = await service.escalate_workflow(
        wf.id, esc_req, request_id="esc-req-1"
    )

    assert wf_escalated.status == WorkflowStatus.ESCALATED
    assert "reviewer_agent" in wf_escalated.error_message

    # Verify attempting to run step on ESCALATED workflow raises ValueError
    with pytest.raises(ValueError) as exc_info:
        await service.execute_step(wf.id, request_id="esc-req-1")
    assert "cannot execute step in status 'escalated'" in str(exc_info.value)

    # Resolve escalation via "resume"
    res_req = WorkflowResolutionRequest(
        resolved_by="security_lead",
        resolution_notes="Approved with standard AES-256-GCM implementation",
        action="resume",
    )
    wf_resolved = await service.resolve_escalation(
        wf.id, res_req, request_id="esc-req-1"
    )

    assert wf_resolved.status in [WorkflowStatus.PLANNING, WorkflowStatus.BUILDING]
    assert wf_resolved.error_message is None

    # Verify ActivityLog entries
    res = await async_session.execute(
        select(ActivityLog).where(ActivityLog.request_id == "esc-req-1")
    )
    logs = list(res.scalars().all())
    event_types = {log.event_type for log in logs}
    assert "workflow_escalated" in event_types
    assert "workflow_escalation_resolved" in event_types


def test_escalation_and_resolution_api_endpoints():
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
            {"sub": "sec_operator"},
            settings.jwt_secret_key,
            algorithm=settings.jwt_algorithm,
        )
        headers = {"Authorization": f"Bearer {token}"}

        # 1. Create workflow
        create_res = client.post(
            "/api/v1/workflows",
            headers=headers,
            json={
                "title": "Payment Gateway Integration",
                "specification": "Add Stripe Connect endpoints",
            },
        )
        assert create_res.status_code == 201
        wf_id = create_res.json()["id"]

        # 2. Escalate via API
        esc_res = client.post(
            f"/api/v1/workflows/{wf_id}/escalate",
            headers=headers,
            json={
                "reason": "Missing compliance clearance for webhook handling",
                "escalated_by": "qa_agent",
            },
        )
        assert esc_res.status_code == 200
        assert esc_res.json()["status"] == "escalated"

        # 3. Attempt to run pipeline on escalated workflow (should fail 400)
        run_res = client.post(
            f"/api/v1/workflows/{wf_id}/run", headers=headers
        )
        assert run_res.status_code == 400
        assert "cannot execute step" in run_res.json()["detail"]

        # 4. Resolve via API (restart action)
        res_res = client.post(
            f"/api/v1/workflows/{wf_id}/resolve",
            headers=headers,
            json={
                "resolved_by": "compliance_officer",
                "resolution_notes": "Compliance clear; restart workflow",
                "action": "restart",
            },
        )
        assert res_res.status_code == 200
        assert res_res.json()["status"] == "created"
    finally:
        app.dependency_overrides.clear()

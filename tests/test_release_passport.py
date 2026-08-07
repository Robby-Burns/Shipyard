import os
import shutil
import pytest
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.database.session import Base
from app.database.models.workflow import WorkflowRun
from app.schemas.workflow import (
    WorkflowApprovalRequest,
    WorkflowStatus,
)
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
async def test_workflow_approval_compiles_passport_and_guide(
    async_session: AsyncSession,
):
    service = WorkflowEngineService(async_session)

    # 1. Create a workflow run in AWAITING_APPROVAL status
    wf = WorkflowRun(
        title="Payment Gateway Upgrade",
        specification="Upgrade from Stripe API v2 to v3",
        status=WorkflowStatus.AWAITING_APPROVAL,
        current_step="awaiting_human_production_approval",
        owner_id="test_owner",
        artifacts={
            "build_plan": "# Build Plan\n1. Modify Stripe capture router\n",
            "architecture_doc": "# Architectural Specifications\nDesign details\n",
            "generated_code": "class StripeUpgrade:\n    pass\n",
            "qa_report": "All tests PASSED",
            "platform_recommendations": "Upgrade dependencies regularly.",
        },
    )
    async_session.add(wf)
    await async_session.commit()
    await async_session.refresh(wf)

    # 2. Approve production deployment
    approved_wf = await service.approve_production_deployment(
        wf.id,
        WorkflowApprovalRequest(approved_by="release_lead"),
        request_id="approve-req-999",
    )

    assert approved_wf.status == WorkflowStatus.COMPLETED
    assert approved_wf.current_step == "completed_and_deployed"
    assert approved_wf.approved_by == "release_lead"
    assert approved_wf.approved_at is not None

    # Assert artifact paths populated in DB
    artifacts = approved_wf.artifacts
    assert "engineering_passport_path" in artifacts
    assert "deployment_guide_path" in artifacts
    assert "engineering_passport" in artifacts

    # Verify files created on disk
    passport_path = artifacts["engineering_passport_path"]
    guide_path = artifacts["deployment_guide_path"]

    assert os.path.exists(passport_path)
    assert os.path.exists(guide_path)

    # Clean up generated artifacts directory
    target_dir = os.path.dirname(passport_path)
    if os.path.exists(target_dir):
        shutil.rmtree(target_dir)

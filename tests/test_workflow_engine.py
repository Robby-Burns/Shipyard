from fastapi.testclient import TestClient
import jwt
import pytest
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.config.settings import settings
from app.database.session import Base, get_db
from app.main import app
from app.schemas.workflow import (
    WorkflowApprovalRequest,
    WorkflowCreateRequest,
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
async def test_workflow_engine_full_pipeline_execution(
    async_session: AsyncSession,
):
    service = WorkflowEngineService(async_session)

    # 1. Create workflow
    create_req = WorkflowCreateRequest(
        title="Payment Service Feature",
        specification="Build a idempotent payment processing microservice",
    )
    wf = await service.create_workflow(create_req, request_id="wf-req-1")

    assert wf.id is not None
    assert wf.status == WorkflowStatus.CREATED
    assert wf.current_step == "created"

    # 2. Run full automated pipeline (pauses at AWAITING_APPROVAL)
    wf_paused = await service.run_full_pipeline(wf.id, request_id="wf-req-1")

    assert wf_paused.status == WorkflowStatus.AWAITING_APPROVAL
    assert wf_paused.current_step == "awaiting_human_production_approval"

    # Check generated artifacts across discipline steps
    assert "build_plan" in wf_paused.artifacts
    assert "architecture_doc" in wf_paused.artifacts
    assert "generated_code" in wf_paused.artifacts
    assert "code_review" in wf_paused.artifacts
    assert "qa_report" in wf_paused.artifacts

    # 3. Approve production deployment
    approval_req = WorkflowApprovalRequest(
        approved_by="vp_engineering", comments="LGT1 for production deployment"
    )
    wf_completed = await service.approve_production_deployment(
        wf.id, approval_req, request_id="wf-req-1"
    )

    assert wf_completed.status == WorkflowStatus.COMPLETED
    assert wf_completed.current_step == "completed_and_deployed"
    assert wf_completed.approved_by == "vp_engineering"
    assert wf_completed.approved_at is not None


def test_workflow_endpoints_unauthenticated():
    res = client.get("/api/v1/workflows")
    assert res.status_code == 401


def test_workflow_endpoints_authenticated():
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
            {"sub": "workflow_admin"},
            settings.jwt_secret_key,
            algorithm=settings.jwt_algorithm,
        )
        headers = {"Authorization": f"Bearer {token}"}

        # 1. Create workflow via POST /api/v1/workflows
        create_res = client.post(
            "/api/v1/workflows",
            headers=headers,
            json={
                "title": "Auth Refactor",
                "specification": "Migrate auth service to OAuth2/OIDC",
            },
        )
        assert create_res.status_code == 201
        wf_data = create_res.json()
        wf_id = wf_data["id"]
        assert wf_data["status"] == "created"

        # 2. Get workflow
        get_res = client.get(f"/api/v1/workflows/{wf_id}", headers=headers)
        assert get_res.status_code == 200
        assert get_res.json()["title"] == "Auth Refactor"

        # 3. Run full automated pipeline via POST /api/v1/workflows/{id}/run
        run_res = client.post(
            f"/api/v1/workflows/{wf_id}/run", headers=headers
        )
        assert run_res.status_code == 200
        run_data = run_res.json()
        assert run_data["status"] == "awaiting_approval"
        assert "build_plan" in run_data["artifacts"]

        # 4. Approve production deployment via POST /api/v1/workflows/{id}/approve
        approve_res = client.post(
            f"/api/v1/workflows/{wf_id}/approve",
            headers=headers,
            json={
                "approved_by": "lead_architect",
                "comments": "Approved for release",
            },
        )
        assert approve_res.status_code == 200
        approved_data = approve_res.json()
        assert approved_data["status"] == "completed"
        assert approved_data["approved_by"] == "lead_architect"

        # 5. List workflows
        list_res = client.get("/api/v1/workflows", headers=headers)
        assert list_res.status_code == 200
        wf_list = list_res.json()
        assert len(wf_list) == 1
        assert wf_list[0]["id"] == wf_id
    finally:
        app.dependency_overrides.clear()

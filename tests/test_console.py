from fastapi.testclient import TestClient
import jwt
import pytest
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.config.settings import settings
from app.database.models.activity_log import ActivityLog
from app.database.models.knowledge import KnowledgeItem
from app.database.models.workflow import WorkflowRun
from app.database.session import Base, get_db
from app.main import app
from app.schemas.knowledge import KnowledgeStatus, MemoryTier
from app.schemas.workflow import WorkflowStatus

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
async def test_console_service_queries(async_session: AsyncSession):
    # Seed workflows
    w_active = WorkflowRun(
        title="Active Feature",
        specification="In progress feature",
        status=WorkflowStatus.DESIGNING,
        current_step="architect_designing",
    )
    w_approval = WorkflowRun(
        title="Pending Release",
        specification="Ready for production deployment",
        status=WorkflowStatus.AWAITING_APPROVAL,
        current_step="awaiting_human_production_approval",
    )
    w_completed = WorkflowRun(
        title="Completed Task",
        specification="Finished task",
        status=WorkflowStatus.COMPLETED,
        current_step="completed_and_deployed",
    )
    async_session.add_all([w_active, w_approval, w_completed])

    # Seed knowledge items
    k_cand = KnowledgeItem(
        title="Proposed Pattern",
        tier=MemoryTier.CANDIDATE,
        category="adr",
        status=KnowledgeStatus.PROPOSED,
        content="Candidate content",
    )
    async_session.add(k_cand)

    # Seed activity log
    log = ActivityLog(
        event_type="workflow_created",
        source="workflow_engine",
        payload={"title": "Active Feature"},
    )
    async_session.add(log)

    await async_session.commit()

    # Test via Console API endpoints
    test_engine = create_async_engine("sqlite+aiosqlite:///:memory:")

    async def init_and_override():
        yield async_session

    app.dependency_overrides[get_db] = init_and_override
    try:
        token = jwt.encode(
            {"sub": "console_operator"},
            settings.jwt_secret_key,
            algorithm=settings.jwt_algorithm,
        )
        headers = {"Authorization": f"Bearer {token}"}

        # Overview endpoint
        res_overview = client.get("/api/v1/console/overview", headers=headers)
        assert res_overview.status_code == 200
        overview_data = res_overview.json()

        assert overview_data["system_status"] == "operational"
        assert overview_data["active_workflow_count"] == 2
        assert overview_data["pending_approval_count"] == 1
        assert overview_data["candidate_knowledge_count"] == 1
        assert len(overview_data["pending_approvals"]) == 1

        # Active workflows endpoint
        res_active = client.get("/api/v1/console/workflows/active", headers=headers)
        assert res_active.status_code == 200
        active_list = res_active.json()
        assert len(active_list) == 2
        active_titles = {w["title"] for w in active_list}
        assert "Active Feature" in active_titles
        assert "Pending Release" in active_titles
        assert "Completed Task" not in active_titles

        # Approvals endpoint
        res_approvals = client.get("/api/v1/console/approvals", headers=headers)
        assert res_approvals.status_code == 200
        approval_list = res_approvals.json()
        assert len(approval_list) == 1
        assert approval_list[0]["title"] == "Pending Release"
        assert approval_list[0]["status"] == "awaiting_approval"

    finally:
        app.dependency_overrides.clear()


def test_console_endpoints_unauthenticated():
    assert client.get("/api/v1/console/overview").status_code == 401
    assert client.get("/api/v1/console/workflows/active").status_code == 401
    assert client.get("/api/v1/console/approvals").status_code == 401

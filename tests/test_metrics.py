from fastapi.testclient import TestClient
import jwt
import pytest
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.config.settings import settings
from app.database.models.activity_log import ActivityLog
from app.database.models.tool_log import ToolExecutionLog
from app.database.models.workflow import WorkflowRun
from app.database.session import Base, get_db
from app.main import app
from app.schemas.workflow import WorkflowStatus
from app.services.metrics import MetricsService

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
async def test_metrics_service_aggregation(async_session: AsyncSession):
    # 1. Seed workflows
    w1 = WorkflowRun(
        title="W1",
        specification="Spec 1",
        status=WorkflowStatus.COMPLETED,
        current_step="completed_and_deployed",
    )
    w2 = WorkflowRun(
        title="W2",
        specification="Spec 2",
        status=WorkflowStatus.COMPLETED,
        current_step="completed_and_deployed",
    )
    w3 = WorkflowRun(
        title="W3",
        specification="Spec 3",
        status=WorkflowStatus.DESIGNING,
        current_step="architect_designing",
    )
    w4 = WorkflowRun(
        title="W4",
        specification="Spec 4",
        status=WorkflowStatus.ESCALATED,
        current_step="builder_building",
    )
    async_session.add_all([w1, w2, w3, w4])

    # 2. Seed tool logs
    t1 = ToolExecutionLog(
        tool_name="github",
        action="create_pr",
        is_success=True,
        execution_time_ms=100.0,
    )
    t2 = ToolExecutionLog(
        tool_name="docker",
        action="build_image",
        is_success=True,
        execution_time_ms=200.0,
    )
    t3 = ToolExecutionLog(
        tool_name="railway",
        action="deploy",
        is_success=False,
        execution_time_ms=300.0,
    )
    async_session.add_all([t1, t2, t3])

    # 3. Seed activity logs
    a1 = ActivityLog(
        event_type="model_route_completed",
        source="model_router",
        payload={"capability": "coding"},
    )
    a2 = ActivityLog(
        event_type="model_route_completed",
        source="model_router",
        payload={"capability": "coding"},
    )
    a3 = ActivityLog(
        event_type="model_route_completed",
        source="model_router",
        payload={"capability": "architecture"},
    )
    a4 = ActivityLog(
        event_type="workflow_escalated",
        source="workflow_engine",
        payload={"reason": "security review flag"},
    )
    async_session.add_all([a1, a2, a3, a4])

    await async_session.commit()

    service = MetricsService(async_session)
    dashboard = await service.get_dashboard_metrics()

    # Verify workflow metrics
    assert dashboard.workflows.total_runs == 4
    assert dashboard.workflows.completed_count == 2
    assert dashboard.workflows.active_count == 1
    assert dashboard.workflows.escalated_count == 1
    assert dashboard.workflows.completion_rate_pct == 50.0

    # Verify tool metrics
    assert dashboard.tools.total_executions == 3
    assert dashboard.tools.successful_executions == 2
    assert dashboard.tools.failed_executions == 1
    assert dashboard.tools.success_rate_pct == 66.67
    assert dashboard.tools.avg_execution_time_ms == 200.0

    # Verify model metrics
    assert dashboard.models.total_requests == 3
    assert dashboard.models.by_capability["coding"] == 2
    assert dashboard.models.by_capability["architecture"] == 1

    # Verify recent errors
    assert len(dashboard.recent_errors) >= 1
    assert dashboard.recent_errors[0]["event_type"] == "workflow_escalated"


def test_metrics_endpoint_unauthenticated():
    res = client.get("/api/v1/metrics/dashboard")
    assert res.status_code == 401


def test_metrics_endpoint_authenticated():
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
            {"sub": "observability_admin"},
            settings.jwt_secret_key,
            algorithm=settings.jwt_algorithm,
        )
        headers = {"Authorization": f"Bearer {token}"}

        res = client.get("/api/v1/metrics/dashboard", headers=headers)
        assert res.status_code == 200
        data = res.json()

        assert data["system_status"] == "operational"
        assert "uptime_seconds" in data
        assert "workflows" in data
        assert "tools" in data
        assert "models" in data
        assert "recent_errors" in data
    finally:
        app.dependency_overrides.clear()

from fastapi.testclient import TestClient
import jwt
import pytest
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.config.settings import settings
from app.database.session import Base, get_db
from app.main import app

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


def test_shipyard_e2e_full_platform_lifecycle():
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
        # Auth headers
        token = jwt.encode(
            {"sub": "e2e_lead_engineer"},
            settings.jwt_secret_key,
            algorithm=settings.jwt_algorithm,
        )
        headers = {"Authorization": f"Bearer {token}"}

        # ---------------------------------------------------------------------
        # 1. WORKFLOW CREATION & AUTOMATED PIPELINE EXECUTION
        # ---------------------------------------------------------------------
        create_res = client.post(
            "/api/v1/workflows",
            headers=headers,
            json={
                "title": "E2E E-Commerce Microservice Spec",
                "specification": (
                    "Build a high-throughput product catalog and checkout service"
                    " with PostgreSQL storage"
                ),
            },
        )
        assert create_res.status_code == 201
        wf = create_res.json()
        wf_id = wf["id"]
        assert wf["status"] == "created"
        assert wf["current_step"] == "created"

        # Execute automated multi-agent pipeline
        run_res = client.post(
            f"/api/v1/workflows/{wf_id}/run", headers=headers
        )
        assert run_res.status_code == 200
        run_data = run_res.json()

        # ---------------------------------------------------------------------
        # 2. DISCIPLINE ARTIFACT GENERATION & HUMAN GATE ENFORCEMENT
        # ---------------------------------------------------------------------
        assert run_data["status"] == "awaiting_approval"
        assert (
            run_data["current_step"] == "awaiting_human_production_approval"
        )

        artifacts = run_data["artifacts"]
        assert "build_plan" in artifacts  # Coordinator Agent output
        assert "architecture_doc" in artifacts  # Architect Agent output
        assert "generated_code" in artifacts  # Builder Agent output
        assert "code_review" in artifacts  # Reviewer Agent output
        assert "qa_report" in artifacts  # QA Agent output

        # ---------------------------------------------------------------------
        # 3. HUMAN PRODUCTION APPROVAL GATE
        # ---------------------------------------------------------------------
        approve_res = client.post(
            f"/api/v1/workflows/{wf_id}/approve",
            headers=headers,
            json={
                "approved_by": "vp_engineering_sarah",
                "comments": "E2E release readiness verified",
            },
        )
        assert approve_res.status_code == 200
        approved_data = approve_res.json()
        assert approved_data["status"] == "completed"
        assert approved_data["current_step"] == "completed_and_deployed"
        assert approved_data["approved_by"] == "e2e_lead_engineer"
        assert approved_data["approved_at"] is not None

        # ---------------------------------------------------------------------
        # 4. OBSERVABILITY & OPERATIONS CONSOLE VERIFICATION
        # ---------------------------------------------------------------------
        console_res = client.get("/api/v1/console/overview", headers=headers)
        assert console_res.status_code == 200
        console_data = console_res.json()
        assert console_data["system_status"] == "operational"

        metrics_res = client.get("/api/v1/metrics/dashboard", headers=headers)
        assert metrics_res.status_code == 200
        metrics_data = metrics_res.json()
        assert metrics_data["workflows"]["total_runs"] == 1
        assert metrics_data["workflows"]["completed_count"] == 1
        assert metrics_data["workflows"]["completion_rate_pct"] == 100.0
        assert metrics_data["models"]["total_requests"] >= 5

        # ---------------------------------------------------------------------
        # 5. ORGANIZATIONAL KNOWLEDGE GOVERNANCE PROMOTION FLOW
        # ---------------------------------------------------------------------
        propose_res = client.post(
            "/api/v1/knowledge/propose",
            headers=headers,
            json={
                "title": "Shipyard Microservice Architecture Standard",
                "tier": "candidate",
                "category": "adr",
                "content": "All core services must expose FastAPI endpoints and structlog context tracing",
            },
        )
        assert propose_res.status_code == 200
        item_id = propose_res.json()["id"]

        approve_k_res = client.post(
            f"/api/v1/knowledge/{item_id}/approve",
            headers=headers,
            json={
                "approved_by": "principal_architect_bob",
                "comments": "Approved as global engineering standard",
            },
        )
        assert approve_k_res.status_code == 200
        assert approve_k_res.json()["tier"] == "shared"
        assert approve_k_res.json()["status"] == "approved"

        shared_res = client.get(
            "/api/v1/knowledge/shared?category=adr", headers=headers
        )
        assert shared_res.status_code == 200
        shared_items = shared_res.json()
        assert len(shared_items) == 1
        assert (
            shared_items[0]["title"]
            == "Shipyard Microservice Architecture Standard"
        )

    finally:
        app.dependency_overrides.clear()

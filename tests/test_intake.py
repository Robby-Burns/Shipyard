import os
import shutil
import uuid
import jwt
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.config.settings import settings
from app.database.session import Base
from app.database.models.intake import IntakeSession
from app.database.session import get_db
from app.main import app
from app.schemas.model_router import ModelRouteResponse
from app.services.intake import IntakeService

client = TestClient(app)


@pytest.fixture
def auth_headers():
    token = jwt.encode(
        {"sub": "test_user"},
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def other_user_headers():
    token = jwt.encode(
        {"sub": "other_user"},
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
async def async_session():
    # Setup in-memory SQLite for testing
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
async def test_intake_service_lifecycle(async_session: AsyncSession):
    service = IntakeService(async_session)

    # 1. Create session
    session = await service.create_session(title="New Project Intake", owner_id="test_user")
    assert session.title == "New Project Intake"
    assert session.status == "in_progress"
    assert len(session.messages) == 1
    assert "Welcome to Shipyard!" in session.messages[0]["content"]

    # 2. Retrieve session
    fetched = await service.get_session(session.id)
    assert fetched is not None
    assert fetched.id == session.id

    # Clean up test artifacts dir if created
    if os.path.exists(service.artifacts_dir):
        shutil.rmtree(service.artifacts_dir)


@pytest.mark.anyio
async def test_intake_uses_large_output_budget_for_spec_generation(
    async_session: AsyncSession,
):
    service = IntakeService(async_session)
    captured_request = None

    async def mock_route(route_request, request_id=None):
        nonlocal captured_request
        captured_request = route_request
        return ModelRouteResponse(
            id="test-completion",
            capability=route_request.capability,
            model_used="test-model",
            content="Please provide more details.",
            usage={},
        )

    service.model_router.route = mock_route
    session = await service.create_session(title="Spec Budget Test")
    await service.send_chat_message(session.id, "I want to build a service")

    assert captured_request is not None
    assert captured_request.max_tokens == 8000


def test_intake_endpoints_full_flow(auth_headers, other_user_headers):
    # Setup database override for endpoint testing
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
        # 1. Create Intake Session
        res = client.post(
            "/api/v1/intake",
            headers=auth_headers,
            json={"title": "Test FastAPI App"},
        )
        assert res.status_code == 201
        data = res.json()
        session_id = data["id"]
        assert data["title"] == "Test FastAPI App"
        assert data["status"] == "in_progress"
        assert len(data["messages"]) == 1

        # 2. Get Intake Session (Authenticated owner)
        res = client.get(
            f"/api/v1/intake/{session_id}",
            headers=auth_headers,
        )
        assert res.status_code == 200
        assert res.json()["title"] == "Test FastAPI App"

        # 3. Get Intake Session (Forbidden for other user)
        res = client.get(
            f"/api/v1/intake/{session_id}",
            headers=other_user_headers,
        )
        assert res.status_code == 403

        # 4. Send Message (Unauthenticated)
        res = client.post(
            f"/api/v1/intake/{session_id}/chat",
            json={"message": "I want a new backend service"},
        )
        assert res.status_code == 401

        # 5. Send Message (Owner - first response is mock completion)
        res = client.post(
            f"/api/v1/intake/{session_id}/chat",
            headers=auth_headers,
            json={"message": "I want to build a backend system with Postgres"},
        )
        assert res.status_code == 200
        data = res.json()
        assert len(data["messages"]) == 3  # welcome + user + assistant
        assert data["messages"][1]["content"] == "I want to build a backend system with Postgres"
        assert "Mock Response" in data["messages"][2]["content"]

        # 6. Upload Text File (Owner)
        from io import BytesIO
        file_content = b"This is a test spec file content."
        file_obj = BytesIO(file_content)
        res = client.post(
            f"/api/v1/intake/{session_id}/upload",
            headers=auth_headers,
            files={"file": ("test_spec.txt", file_obj, "text/plain")},
        )
        assert res.status_code == 200
        data = res.json()
        assert len(data["messages"]) == 5  # previous 3 + user upload + assistant reply
        assert "[Uploaded File: test_spec.txt]" in data["messages"][3]["content"]
        assert "This is a test spec file content." in data["messages"][3]["content"]
        assert "Mock Response" in data["messages"][4]["content"]

        # 7. Trigger validation via keyword "validate"
        res = client.post(
            f"/api/v1/intake/{session_id}/chat",
            headers=auth_headers,
            json={"message": "please validate the specification now"},
        )
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "completed"
        assert "validated and generated successfully" in data["messages"][-1]["content"]

        # 8. Continue discussing the generated specification before approval
        completed_specification = data["specification"]
        res = client.post(
            f"/api/v1/intake/{session_id}/chat",
            headers=auth_headers,
            json={"message": "Can you explain the database choice?"},
        )
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "completed"
        assert data["specification"] == completed_specification
        assert "Can you explain the database choice?" in data["messages"][-2]["content"]

    finally:
        app.dependency_overrides.clear()
        if os.path.exists("artifacts/specifications"):
            shutil.rmtree("artifacts/specifications")


def test_intake_transition_by_turn_count(auth_headers):
    # Setup database override for turn count test
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
        # Create session
        res = client.post(
            "/api/v1/intake",
            headers=auth_headers,
            json={"title": "Turn Count Validation Test"},
        )
        session_id = res.json()["id"]

        # Send 7 messages (which will keep status as in_progress)
        for i in range(7):
            res = client.post(
                f"/api/v1/intake/{session_id}/chat",
                headers=auth_headers,
                json={"message": f"Requirement turn {i+1}"},
            )
            assert res.json()["status"] == "in_progress"

        # The 8th message triggers validation automatically
        res = client.post(
            f"/api/v1/intake/{session_id}/chat",
            headers=auth_headers,
            json={"message": "Final Requirement turn 8"},
        )
        data = res.json()
        assert data["status"] == "completed"
        assert "validated and generated successfully" in data["messages"][-1]["content"]

    finally:
        app.dependency_overrides.clear()
        if os.path.exists("artifacts/specifications"):
            shutil.rmtree("artifacts/specifications")

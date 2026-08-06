from fastapi.testclient import TestClient
import jwt
import pytest
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.database.session import get_db
from app.config.settings import settings
from app.database.session import Base
from app.main import app
from app.schemas.memory import MemoryRecordCreate, MemorySearchRequest
from app.services.memory_gateway import MemoryGatewayService

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
async def test_memory_gateway_service_store_and_retrieve(
    async_session: AsyncSession,
):
    service = MemoryGatewayService(async_session)

    item1 = await service.store(
        MemoryRecordCreate(
            category="candidate",
            content="FastAPI architectural decision record",
            metadata_json={"author": "architect"},
        )
    )
    assert item1.id is not None
    assert item1.category == "candidate"

    item2 = await service.store(
        MemoryRecordCreate(
            category="shared",
            content="PostgreSQL vector memory pattern",
            metadata_json={"tags": ["db", "vector"]},
        )
    )
    assert item2.id is not None

    # Retrieve all
    all_items = await service.retrieve(MemorySearchRequest())
    assert len(all_items) == 2

    # Retrieve by category
    candidate_items = await service.retrieve(
        MemorySearchRequest(category="candidate")
    )
    assert len(candidate_items) == 1
    assert candidate_items[0].content == "FastAPI architectural decision record"


def test_memory_gateway_endpoints_unauthenticated():
    response_store = client.post(
        "/api/v1/memory-gateway/store",
        json={"category": "private", "content": "secret context"},
    )
    assert response_store.status_code == 401

    response_retrieve = client.post(
        "/api/v1/memory-gateway/retrieve", json={"category": "private"}
    )
    assert response_retrieve.status_code == 401


def test_memory_gateway_endpoints_authenticated():
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
            {"sub": "memory_user"},
            settings.jwt_secret_key,
            algorithm=settings.jwt_algorithm,
        )
        headers = {"Authorization": f"Bearer {token}"}

        # Store memory
        store_res = client.post(
            "/api/v1/memory-gateway/store",
            headers=headers,
            json={
                "category": "shared",
                "content": "Shared platform standards",
                "metadata_json": {"version": "1.0"},
            },
        )
        assert store_res.status_code == 200
        stored_data = store_res.json()
        assert stored_data["category"] == "shared"
        assert stored_data["content"] == "Shared platform standards"

        # Retrieve memory
        retrieve_res = client.post(
            "/api/v1/memory-gateway/retrieve",
            headers=headers,
            json={"category": "shared"},
        )
        assert retrieve_res.status_code == 200
        retrieved_list = retrieve_res.json()
        assert len(retrieved_list) == 1
        assert retrieved_list[0]["content"] == "Shared platform standards"
    finally:
        app.dependency_overrides.clear()

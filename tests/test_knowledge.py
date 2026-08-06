from fastapi.testclient import TestClient
import jwt
import pytest
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.api.health import get_db
from app.config.settings import settings
from app.database.session import Base
from app.main import app
from app.schemas.knowledge import (
    KnowledgeItemCreate,
    KnowledgePromotionRequest,
    KnowledgeStatus,
    MemoryTier,
)
from app.services.knowledge_service import KnowledgeService

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
async def test_knowledge_service_lifecycle(async_session: AsyncSession):
    service = KnowledgeService(async_session)

    # 1. Propose a candidate item
    item_in = KnowledgeItemCreate(
        title="Async DB Session Standard",
        tier=MemoryTier.CANDIDATE,
        category="coding_standard",
        content="Always yield DB sessions within context managers",
        metadata_json={"author": "dev_lead"},
    )
    proposed_item = await service.propose_candidate(item_in)
    assert proposed_item.id is not None
    assert proposed_item.tier == MemoryTier.CANDIDATE
    assert proposed_item.status == KnowledgeStatus.PROPOSED
    assert proposed_item.approved_by is None

    # 2. List candidates
    candidates = await service.list_candidates()
    assert len(candidates) == 1
    assert candidates[0].id == proposed_item.id

    # 3. Approve and promote candidate to Shared Knowledge
    promotion_req = KnowledgePromotionRequest(
        approved_by="tech_lead_alice", comments="Approved for team-wide use"
    )
    promoted_item = await service.approve_and_promote(
        proposed_item.id, promotion_req
    )
    assert promoted_item is not None
    assert promoted_item.tier == MemoryTier.SHARED
    assert promoted_item.status == KnowledgeStatus.APPROVED
    assert promoted_item.approved_by == "tech_lead_alice"
    assert promoted_item.approved_at is not None

    # 4. Search shared knowledge
    shared_items = await service.search_shared_knowledge(
        category="coding_standard"
    )
    assert len(shared_items) == 1
    assert shared_items[0].id == proposed_item.id


def test_knowledge_endpoints_unauthenticated():
    response = client.get("/api/v1/knowledge/candidates")
    assert response.status_code == 401


def test_knowledge_endpoints_authenticated():
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
            {"sub": "architect_bob", "exp": 9999999999},
            settings.jwt_secret_key,
            algorithm=settings.jwt_algorithm,
        )
        headers = {"Authorization": f"Bearer {token}"}

        # Propose candidate
        propose_res = client.post(
            "/api/v1/knowledge/propose",
            headers=headers,
            json={
                "title": "PostgreSQL Vector Guide",
                "tier": "candidate",
                "category": "playbook",
                "content": "Use pgvector HNSW indexing for high dimension vectors",
            },
        )
        assert propose_res.status_code == 200
        item_data = propose_res.json()
        item_id = item_data["id"]
        assert item_data["tier"] == "candidate"
        assert item_data["status"] == "proposed"

        # List candidates
        candidates_res = client.get(
            "/api/v1/knowledge/candidates", headers=headers
        )
        assert candidates_res.status_code == 200
        cand_list = candidates_res.json()
        assert len(cand_list) == 1
        assert cand_list[0]["id"] == item_id

        # Approve and promote candidate
        approve_res = client.post(
            f"/api/v1/knowledge/{item_id}/approve",
            headers=headers,
            json={"approved_by": "lead_architect", "comments": "LGT1"},
        )
        assert approve_res.status_code == 200
        approved_data = approve_res.json()
        assert approved_data["tier"] == "shared"
        assert approved_data["status"] == "approved"
        assert approved_data["approved_by"] == "lead_architect"

        # Search shared knowledge
        shared_res = client.get(
            "/api/v1/knowledge/shared?category=playbook", headers=headers
        )
        assert shared_res.status_code == 200
        shared_list = shared_res.json()
        assert len(shared_list) == 1
        assert shared_list[0]["title"] == "PostgreSQL Vector Guide"
    finally:
        app.dependency_overrides.clear()

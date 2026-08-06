from datetime import datetime, timedelta, timezone
from fastapi.testclient import TestClient
import jwt
import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.api.health import get_db
from app.config.settings import settings
from app.database.models.knowledge import KnowledgeItem
from app.database.models.memory import MemoryRecord
from app.database.session import Base
from app.main import app
from app.schemas.knowledge import KnowledgeStatus, MemoryTier
from app.services.memory_cleanup import MemoryCleanupService

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
async def test_cleanup_expired_private_memories(async_session: AsyncSession):
    now = datetime.now(timezone.utc)
    old_cutoff = now - timedelta(days=10)
    recent_time = now - timedelta(days=1)

    # 1. Old private memory (should be purged)
    old_private = MemoryRecord(
        category="private",
        content="Expired scratch context",
        created_at=old_cutoff,
    )
    # 2. Recent private memory (should be kept)
    recent_private = MemoryRecord(
        category="private",
        content="Active scratch context",
        created_at=recent_time,
    )
    # 3. Old shared memory (should NOT be purged by private cleanup)
    old_shared = MemoryRecord(
        category="shared",
        content="Permanent shared record",
        created_at=old_cutoff,
    )

    async_session.add_all([old_private, recent_private, old_shared])
    await async_session.commit()

    service = MemoryCleanupService(async_session)
    deleted_count = await service.cleanup_expired_private_memories()

    assert deleted_count == 1

    # Verify remaining records
    res = await async_session.execute(select(MemoryRecord))
    records = list(res.scalars().all())
    assert len(records) == 2
    contents = {r.content for r in records}
    assert "Active scratch context" in contents
    assert "Permanent shared record" in contents
    assert "Expired scratch context" not in contents


@pytest.mark.anyio
async def test_archive_stale_candidates(async_session: AsyncSession):
    now = datetime.now(timezone.utc)
    stale_time = now - timedelta(days=35)
    recent_time = now - timedelta(days=5)

    stale_candidate = KnowledgeItem(
        title="Old Candidate ADR",
        tier=MemoryTier.CANDIDATE,
        category="adr",
        status=KnowledgeStatus.PROPOSED,
        content="Obsolete candidate proposal",
        created_at=stale_time,
    )
    recent_candidate = KnowledgeItem(
        title="Recent Candidate ADR",
        tier=MemoryTier.CANDIDATE,
        category="adr",
        status=KnowledgeStatus.PROPOSED,
        content="Fresh candidate proposal",
        created_at=recent_time,
    )

    async_session.add_all([stale_candidate, recent_candidate])
    await async_session.commit()

    service = MemoryCleanupService(async_session)
    archived_count = await service.archive_or_purge_stale_candidates()

    assert archived_count == 1

    await async_session.refresh(stale_candidate)
    await async_session.refresh(recent_candidate)

    assert stale_candidate.status == KnowledgeStatus.ARCHIVED
    assert recent_candidate.status == KnowledgeStatus.PROPOSED


def test_maintenance_endpoint_unauthenticated():
    response = client.post("/api/v1/maintenance/cleanup-memory")
    assert response.status_code == 401


def test_maintenance_endpoint_authenticated():
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
            {"sub": "sys_admin", "exp": 9999999999},
            settings.jwt_secret_key,
            algorithm=settings.jwt_algorithm,
        )
        headers = {"Authorization": f"Bearer {token}"}

        response = client.post(
            "/api/v1/maintenance/cleanup-memory", headers=headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "deleted_private_memories" in data
        assert "archived_stale_candidates" in data
        assert "executed_at" in data
    finally:
        app.dependency_overrides.clear()

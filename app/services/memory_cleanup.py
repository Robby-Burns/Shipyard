from datetime import datetime, timedelta, timezone

from sqlalchemy import delete, select, func
from sqlalchemy.ext.asyncio import AsyncSession
import structlog

from app.config.settings import settings
from app.database.models.knowledge import KnowledgeItem
from app.database.models.memory import MemoryRecord
from app.schemas.knowledge import KnowledgeStatus, MemoryTier

logger = structlog.get_logger()


class MemoryCleanupService:

    def __init__(self, db: AsyncSession):
        self.db = db

    async def cleanup_expired_private_memories(self) -> int:
        """Purge private memory records older than private_memory_retention_days."""
        cutoff = datetime.now(timezone.utc) - timedelta(
            days=settings.private_memory_retention_days
        )

        stmt = delete(MemoryRecord).where(
            func.lower(MemoryRecord.category) == "private", MemoryRecord.created_at < cutoff
        )
        result = await self.db.execute(stmt)
        await self.db.commit()

        deleted_count = result.rowcount
        logger.info(
            "cleaned_expired_private_memories",
            count=deleted_count,
            cutoff=cutoff.isoformat(),
        )
        return deleted_count

    async def archive_or_purge_stale_candidates(self) -> int:
        """Archive proposed candidates older than proposed_candidate_retention_days."""
        cutoff = datetime.now(timezone.utc) - timedelta(
            days=settings.proposed_candidate_retention_days
        )

        stmt = select(KnowledgeItem).where(
            KnowledgeItem.tier == MemoryTier.CANDIDATE,
            KnowledgeItem.status == KnowledgeStatus.PROPOSED,
            KnowledgeItem.created_at < cutoff,
        )
        result = await self.db.execute(stmt)
        stale_items = list(result.scalars().all())

        for item in stale_items:
            item.status = KnowledgeStatus.ARCHIVED

        await self.db.commit()
        logger.info(
            "archived_stale_candidates",
            count=len(stale_items),
            cutoff=cutoff.isoformat(),
        )
        return len(stale_items)

    async def run_all_cleanups(self) -> dict:
        """Execute all memory retention rules."""
        private_count = await self.cleanup_expired_private_memories()
        stale_candidate_count = await self.archive_or_purge_stale_candidates()

        return {
            "deleted_private_memories": private_count,
            "archived_stale_candidates": stale_candidate_count,
            "executed_at": datetime.now(timezone.utc).isoformat(),
        }

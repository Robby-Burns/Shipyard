from datetime import datetime, timezone
from typing import List, Optional
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models.knowledge import KnowledgeItem
from app.schemas.knowledge import (
    KnowledgeItemCreate,
    KnowledgePromotionRequest,
    KnowledgeRejectionRequest,
    KnowledgeStatus,
    MemoryTier,
)


class KnowledgeService:

    def __init__(self, db: AsyncSession):
        self.db = db

    async def propose_candidate(self, item_in: KnowledgeItemCreate) -> KnowledgeItem:
        """Create a candidate knowledge entry pending human review."""
        knowledge_item = KnowledgeItem(
            title=item_in.title,
            tier=item_in.tier,
            category=item_in.category,
            status=(
                KnowledgeStatus.PROPOSED
                if item_in.tier == MemoryTier.CANDIDATE
                else KnowledgeStatus.APPROVED
            ),
            content=item_in.content,
            metadata_json=item_in.metadata_json,
            embedding=item_in.embedding,
        )
        self.db.add(knowledge_item)
        await self.db.commit()
        await self.db.refresh(knowledge_item)
        return knowledge_item

    async def approve_and_promote(
        self, item_id: uuid.UUID, promotion_req: KnowledgePromotionRequest
    ) -> Optional[KnowledgeItem]:
        """Promote a candidate knowledge item to Shared Knowledge upon human approval."""
        result = await self.db.execute(
            select(KnowledgeItem).where(KnowledgeItem.id == item_id)
        )
        item = result.scalar_one_or_none()

        if not item:
            return None

        # Promote status and tier
        item.status = KnowledgeStatus.APPROVED
        item.tier = MemoryTier.SHARED
        item.approved_by = promotion_req.approved_by
        item.approved_at = datetime.now(timezone.utc)

        await self.db.commit()
        await self.db.refresh(item)
        return item

    async def search_shared_knowledge(
        self,
        category: Optional[str] = None,
        query_embedding: Optional[List[float]] = None,
        limit: int = 10,
    ) -> List[KnowledgeItem]:
        """Query curated, human-approved Shared Knowledge."""
        query = select(KnowledgeItem).where(
            KnowledgeItem.tier == MemoryTier.SHARED,
            KnowledgeItem.status == KnowledgeStatus.APPROVED,
        )

        if category:
            query = query.where(KnowledgeItem.category == category)

        if (
            query_embedding
            and getattr(self.db, "bind", None) is not None
            and getattr(self.db.bind, "dialect", None) is not None
            and self.db.bind.dialect.name == "postgresql"
        ):
            query = query.order_by(
                KnowledgeItem.embedding.l2_distance(query_embedding)
            )
        else:
            query = query.order_by(KnowledgeItem.created_at.desc())

        query = query.limit(limit)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def list_candidates(self) -> List[KnowledgeItem]:
        """Retrieve candidate knowledge items pending review."""
        query = (
            select(KnowledgeItem)
            .where(
                KnowledgeItem.tier == MemoryTier.CANDIDATE,
                KnowledgeItem.status == KnowledgeStatus.PROPOSED,
            )
            .order_by(KnowledgeItem.created_at.desc())
        )

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def reject_candidate(
        self, item_id: uuid.UUID, reject_req: KnowledgeRejectionRequest
    ) -> Optional[KnowledgeItem]:
        """Reject a candidate knowledge item."""
        result = await self.db.execute(
            select(KnowledgeItem).where(KnowledgeItem.id == item_id)
        )
        item = result.scalar_one_or_none()

        if not item:
            return None

        # Archive status to REJECTED
        item.status = KnowledgeStatus.REJECTED
        
        # Serialize rejection details into metadata JSON
        meta = dict(item.metadata_json) if item.metadata_json else {}
        meta["rejection_comments"] = reject_req.comments
        meta["rejected_by"] = reject_req.rejected_by
        meta["rejected_at"] = datetime.now(timezone.utc).isoformat()
        item.metadata_json = meta

        await self.db.commit()
        await self.db.refresh(item)
        return item

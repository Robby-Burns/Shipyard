from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models.memory import MemoryRecord
from app.schemas.memory import MemoryRecordCreate, MemorySearchRequest


class MemoryGatewayService:

    def __init__(self, db: AsyncSession):
        self.db = db

    async def store(self, record_in: MemoryRecordCreate) -> MemoryRecord:
        """Persist a memory record (with optional vector embedding)."""
        memory_item = MemoryRecord(
            category=record_in.category,
            content=record_in.content,
            metadata_json=record_in.metadata_json,
            embedding=record_in.embedding,
        )
        self.db.add(memory_item)
        await self.db.commit()
        await self.db.refresh(memory_item)
        return memory_item

    async def retrieve(
        self, search_req: MemorySearchRequest
    ) -> List[MemoryRecord]:
        """Retrieve memory records with optional category filtering or vector distance sorting."""
        query = select(MemoryRecord)

        if search_req.category:
            query = query.where(MemoryRecord.category == search_req.category)

        # Check dialect safely to support pgvector on PostgreSQL
        from app.config.settings import settings
        is_postgresql = settings.database_url.startswith("postgresql") or settings.database_url.startswith("postgres")

        if search_req.query_embedding and is_postgresql:
            query = query.order_by(
                MemoryRecord.embedding.l2_distance(search_req.query_embedding)
            )
        else:
            query = query.order_by(MemoryRecord.created_at.desc())

        query = query.limit(search_req.limit)
        result = await self.db.execute(query)
        return list(result.scalars().all())

from typing import Any, Dict, List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models.activity_log import ActivityLog
from app.schemas.activity_log import ActivityLogFilter


class ActivityLogService:

    def __init__(self, db: AsyncSession):
        self.db = db

    async def record(
        self,
        event_type: str,
        source: str,
        request_id: Optional[str] = None,
        payload: Optional[Dict[str, Any]] = None,
    ) -> ActivityLog:
        """Record an operational event in the immutable activity log."""
        log_entry = ActivityLog(
            event_type=event_type,
            source=source,
            request_id=request_id,
            payload=payload,
        )
        self.db.add(log_entry)
        await self.db.commit()
        await self.db.refresh(log_entry)
        return log_entry

    async def search(self, filters: ActivityLogFilter) -> List[ActivityLog]:
        """Query historical activity logs with optional filters."""
        query = select(ActivityLog)

        if filters.event_type:
            query = query.where(ActivityLog.event_type == filters.event_type)
        if filters.source:
            query = query.where(ActivityLog.source == filters.source)
        if filters.request_id:
            query = query.where(ActivityLog.request_id == filters.request_id)

        query = (
            query.order_by(ActivityLog.created_at.desc())
            .offset(filters.offset)
            .limit(filters.limit)
        )
        result = await self.db.execute(query)
        return list(result.scalars().all())

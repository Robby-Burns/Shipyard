from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.schemas.activity_log import ActivityLogFilter, ActivityLogResponse
from app.services.activity_log import ActivityLogService
from app.services.auth import get_current_user

router = APIRouter(prefix="/api/v1/activity-logs", tags=["Activity Logs"])


@router.get("", response_model=List[ActivityLogResponse])
async def list_activity_logs(
    event_type: Optional[str] = Query(None),
    source: Optional[str] = Query(None),
    request_id: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    service = ActivityLogService(db)
    filters = ActivityLogFilter(
        event_type=event_type,
        source=source,
        request_id=request_id,
        limit=limit,
        offset=offset,
    )
    return await service.search(filters)

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.services.auth import get_current_user
from app.services.memory_cleanup import MemoryCleanupService

router = APIRouter(prefix="/api/v1/maintenance", tags=["Maintenance & Cleanup"])


@router.post("/cleanup-memory")
async def trigger_memory_cleanup(
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    service = MemoryCleanupService(db)
    return await service.run_all_cleanups()

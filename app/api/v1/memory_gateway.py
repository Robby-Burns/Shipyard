from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.schemas.memory import (
    MemoryRecordCreate,
    MemoryRecordResponse,
    MemorySearchRequest,
)
from app.services.auth import get_current_user
from app.services.memory_gateway import MemoryGatewayService

router = APIRouter(prefix="/api/v1/memory-gateway", tags=["Memory Gateway"])


@router.post("/store", response_model=MemoryRecordResponse)
async def store_memory(
    record_in: MemoryRecordCreate,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    service = MemoryGatewayService(db)
    return await service.store(record_in)


@router.post("/retrieve", response_model=List[MemoryRecordResponse])
async def retrieve_memory(
    search_req: MemorySearchRequest,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    service = MemoryGatewayService(db)
    return await service.retrieve(search_req)

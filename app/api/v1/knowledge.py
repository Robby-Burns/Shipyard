from typing import List, Optional
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.schemas.knowledge import (
    KnowledgeItemCreate,
    KnowledgeItemResponse,
    KnowledgePromotionRequest,
    KnowledgeRejectionRequest,
)
from app.services.auth import get_current_user
from app.services.knowledge_service import KnowledgeService

router = APIRouter(prefix="/api/v1/knowledge", tags=["Organizational Knowledge"])


@router.post("/propose", response_model=KnowledgeItemResponse)
async def propose_knowledge(
    item_in: KnowledgeItemCreate,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    service = KnowledgeService(db)
    return await service.propose_candidate(item_in)


@router.get("/candidates", response_model=List[KnowledgeItemResponse])
async def list_candidates(
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    service = KnowledgeService(db)
    return await service.list_candidates()


@router.post("/{item_id}/approve", response_model=KnowledgeItemResponse)
async def approve_knowledge(
    item_id: uuid.UUID,
    promotion_req: KnowledgePromotionRequest,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    service = KnowledgeService(db)
    updated_item = await service.approve_and_promote(item_id, promotion_req)
    if not updated_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Knowledge item not found"
        )
    return updated_item


@router.post("/{item_id}/reject", response_model=KnowledgeItemResponse)
async def reject_knowledge(
    item_id: uuid.UUID,
    rejection_req: KnowledgeRejectionRequest,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    service = KnowledgeService(db)
    updated_item = await service.reject_candidate(item_id, rejection_req)
    if not updated_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Knowledge item not found"
        )
    return updated_item


@router.get("/shared", response_model=List[KnowledgeItemResponse])
async def search_shared(
    category: Optional[str] = Query(None),
    limit: int = Query(10, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    service = KnowledgeService(db)
    return await service.search_shared_knowledge(category=category, limit=limit)

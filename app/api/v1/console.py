from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.schemas.console import ConsoleOverviewResponse
from app.schemas.workflow import WorkflowRunResponse
from app.services.auth import get_current_user
from app.services.console import ConsoleService

router = APIRouter(prefix="/api/v1/console", tags=["Operations Console"])


@router.get("/overview", response_model=ConsoleOverviewResponse)
async def get_console_overview(
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    service = ConsoleService(db)
    return await service.get_overview_summary()


@router.get("/workflows/active", response_model=List[WorkflowRunResponse])
async def list_active_workflows(
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    service = ConsoleService(db)
    return await service.get_active_workflows()


@router.get("/approvals", response_model=List[WorkflowRunResponse])
async def list_pending_approvals(
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    service = ConsoleService(db)
    return await service.get_pending_approvals()

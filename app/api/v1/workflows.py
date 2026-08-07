from typing import List
import uuid

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.schemas.workflow import (
    WorkflowApprovalRequest,
    WorkflowCreateRequest,
    WorkflowEscalationRequest,
    WorkflowResolutionRequest,
    WorkflowRunResponse,
)
from app.services.auth import get_current_user
from app.services.workflow_engine import WorkflowEngineService

router = APIRouter(prefix="/api/v1/workflows", tags=["Workflow Engine"])


@router.post(
    "", response_model=WorkflowRunResponse, status_code=status.HTTP_201_CREATED
)
async def create_workflow(
    req: WorkflowCreateRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    service = WorkflowEngineService(db)
    return await service.create_workflow(
        req,
        owner_id=user.get("sub"),
        request_id=getattr(request.state, "request_id", None),
    )


@router.get("", response_model=List[WorkflowRunResponse])
async def list_workflows(
    limit: int = 100,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    service = WorkflowEngineService(db)
    return await service.list_workflows(
        owner_id=user.get("sub"), limit=limit, offset=offset
    )


@router.get("/{workflow_id}", response_model=WorkflowRunResponse)
async def get_workflow(
    workflow_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    service = WorkflowEngineService(db)
    wf = await service.get_workflow(workflow_id)
    if not wf:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Workflow run not found"
        )
    # Ownership check
    if wf.owner_id != user.get("sub"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden"
        )
    return wf


@router.post("/{workflow_id}/run", response_model=WorkflowRunResponse)
async def run_full_pipeline(
    workflow_id: uuid.UUID,
    request: Request,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    service = WorkflowEngineService(db)
    try:
        return await service.run_full_pipeline(
            workflow_id, request_id=getattr(request.state, "request_id", None)
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/{workflow_id}/escalate", response_model=WorkflowRunResponse)
async def escalate_workflow(
    workflow_id: uuid.UUID,
    req: WorkflowEscalationRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    service = WorkflowEngineService(db)
    try:
        return await service.escalate_workflow(
            workflow_id, req, request_id=getattr(request.state, "request_id", None)
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/{workflow_id}/resolve", response_model=WorkflowRunResponse)
async def resolve_escalation(
    workflow_id: uuid.UUID,
    req: WorkflowResolutionRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    service = WorkflowEngineService(db)
    try:
        return await service.resolve_escalation(
            workflow_id, req, request_id=getattr(request.state, "request_id", None)
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/{workflow_id}/approve", response_model=WorkflowRunResponse)
async def approve_workflow(
    workflow_id: uuid.UUID,
    req: WorkflowApprovalRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    service = WorkflowEngineService(db)
    try:
        return await service.approve_production_deployment(
            workflow_id, req, request_id=getattr(request.state, "request_id", None)
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

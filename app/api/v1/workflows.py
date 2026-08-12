from typing import List, Optional
import uuid

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
import structlog

from app.config.settings import settings
from app.database.session import AsyncSessionLocal, get_db
from app.schemas.workflow import (
    WorkflowApprovalRequest,
    WorkflowCreateRequest,
    WorkflowEscalationRequest,
    WorkflowResolutionRequest,
    WorkflowRunResponse,
    WorkflowStatus,
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
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
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


logger = structlog.get_logger()


async def background_run_pipeline(
    workflow_id: uuid.UUID, request_id: Optional[str] = None
):
    async with AsyncSessionLocal() as db:
        service = WorkflowEngineService(db)
        try:
            await service.run_full_pipeline(workflow_id, request_id=request_id)
        except Exception as e:
            logger.error(
                "background_pipeline_execution_failed",
                workflow_id=str(workflow_id),
                error=str(e),
            )
            # Update workflow status to FAILED in the DB so client/frontend stops polling
            try:
                from sqlalchemy import select
                from app.database.models.workflow import WorkflowRun
                result = await db.execute(
                    select(WorkflowRun).where(WorkflowRun.id == workflow_id)
                )
                workflow = result.scalar_one_or_none()
                if workflow:
                    workflow.status = WorkflowStatus.FAILED
                    workflow.error_message = str(e)
                    await db.commit()
            except Exception as db_err:
                logger.error(
                    "failed_to_mark_workflow_as_failed_in_db",
                    workflow_id=str(workflow_id),
                    error=str(db_err),
                )


@router.post("/{workflow_id}/run", response_model=WorkflowRunResponse)
async def run_full_pipeline(
    workflow_id: uuid.UUID,
    request: Request,
    background_tasks: BackgroundTasks,
    force: bool = False,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    from sqlalchemy import select
    from app.database.models.workflow import WorkflowRun
    service = WorkflowEngineService(db)
    
    # Use SELECT ... FOR UPDATE to lock the row and prevent concurrent double-triggers
    result = await db.execute(
        select(WorkflowRun)
        .where(WorkflowRun.id == workflow_id)
        .with_for_update()
    )
    wf = result.scalar_one_or_none()
    
    if not wf:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Workflow run not found"
        )
    # Ownership check
    if wf.owner_id != user.get("sub"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden"
        )

    # If force=True, reset the workflow state to CREATED first so it can execute
    if force:
        wf.status = WorkflowStatus.CREATED
        wf.current_step = "created"
        wf.artifacts = {}
        wf.error_message = None
        wf.approved_by = None
        wf.approved_at = None
        await db.commit()

    # Prevent execution from terminal, awaiting approval, or escalated statuses
    if wf.status not in [
        WorkflowStatus.CREATED,
        WorkflowStatus.PLANNING,
        WorkflowStatus.DESIGNING,
        WorkflowStatus.BUILDING,
        WorkflowStatus.REVIEWING,
        WorkflowStatus.TESTING,
    ]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Workflow run {workflow_id} cannot execute step in status '{wf.status.value}'"
        )

    request_id = getattr(request.state, "request_id", None)
    
    # In testing environment, run synchronously to utilize the overridden in-memory SQLite database
    is_testing = (settings.app_env == "testing")
    if is_testing:
        try:
            await db.commit()
            return await service.run_full_pipeline(
                workflow_id, request_id=request_id
            )
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
            )

    # Queue the workflow run in a background task for development/production to prevent proxy timeouts
    await db.commit()
    background_tasks.add_task(
        background_run_pipeline, workflow_id, request_id
    )

    # Return the current workflow status immediately so client doesn't time out
    return wf


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
    req.approved_by = user.get("sub", "unknown")
    service = WorkflowEngineService(db)
    try:
        return await service.approve_production_deployment(
            workflow_id, req, request_id=getattr(request.state, "request_id", None)
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/{workflow_id}/pause", response_model=WorkflowRunResponse)
async def pause_workflow(
    workflow_id: uuid.UUID,
    request: Request,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    service = WorkflowEngineService(db)
    wf = await service.get_workflow(workflow_id)
    if not wf:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Workflow run not found"
        )
    if wf.owner_id != user.get("sub"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden"
        )
    
    # Can only pause if it is actively running
    if wf.status not in [
        WorkflowStatus.PLANNING,
        WorkflowStatus.DESIGNING,
        WorkflowStatus.BUILDING,
        WorkflowStatus.REVIEWING,
        WorkflowStatus.TESTING,
    ]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot pause workflow run in status '{wf.status.value}'"
        )

    wf.status = WorkflowStatus.ESCALATED
    wf.error_message = "Workflow execution paused by user."
    await db.commit()
    await db.refresh(wf)
    return wf


@router.post("/{workflow_id}/terminate", response_model=WorkflowRunResponse)
async def terminate_workflow(
    workflow_id: uuid.UUID,
    request: Request,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    service = WorkflowEngineService(db)
    wf = await service.get_workflow(workflow_id)
    if not wf:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Workflow run not found"
        )
    if wf.owner_id != user.get("sub"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden"
        )

    # Can only terminate if not already in final state
    if wf.status in [WorkflowStatus.COMPLETED, WorkflowStatus.FAILED]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Workflow run is already in final state: '{wf.status.value}'"
        )

    wf.status = WorkflowStatus.FAILED
    wf.error_message = "Workflow execution terminated by user."
    await db.commit()
    await db.refresh(wf)
    return wf

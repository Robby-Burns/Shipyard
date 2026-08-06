from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.schemas.agent import AgentExecutionRequest, AgentExecutionResponse
from app.services.agents import (
    ArchitectAgent,
    BuilderAgent,
    CoordinatorAgent,
    PlatformAgent,
    QAAgent,
    ReviewerAgent,
)
from app.services.auth import get_current_user

router = APIRouter(prefix="/api/v1/agents", tags=["Engineering Agents"])


@router.post("/coordinator/run", response_model=AgentExecutionResponse)
async def run_coordinator(
    exec_req: AgentExecutionRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    return await CoordinatorAgent(db).run(
        exec_req, request_id=getattr(request.state, "request_id", None)
    )


@router.post("/architect/run", response_model=AgentExecutionResponse)
async def run_architect(
    exec_req: AgentExecutionRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    return await ArchitectAgent(db).run(
        exec_req, request_id=getattr(request.state, "request_id", None)
    )


@router.post("/builder/run", response_model=AgentExecutionResponse)
async def run_builder(
    exec_req: AgentExecutionRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    return await BuilderAgent(db).run(
        exec_req, request_id=getattr(request.state, "request_id", None)
    )


@router.post("/reviewer/run", response_model=AgentExecutionResponse)
async def run_reviewer(
    exec_req: AgentExecutionRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    return await ReviewerAgent(db).run(
        exec_req, request_id=getattr(request.state, "request_id", None)
    )


@router.post("/qa/run", response_model=AgentExecutionResponse)
async def run_qa(
    exec_req: AgentExecutionRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    return await QAAgent(db).run(
        exec_req, request_id=getattr(request.state, "request_id", None)
    )


@router.post("/platform/run", response_model=AgentExecutionResponse)
async def run_platform(
    exec_req: AgentExecutionRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    return await PlatformAgent(db).run(
        exec_req, request_id=getattr(request.state, "request_id", None)
    )

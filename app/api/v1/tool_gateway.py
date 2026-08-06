from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.schemas.tool_gateway import ToolExecutionRequest, ToolExecutionResponse
from app.services.auth import get_current_user
from app.services.tool_gateway import ToolGatewayService

router = APIRouter(prefix="/api/v1/tool-gateway", tags=["Tool Gateway"])


@router.post("/execute", response_model=ToolExecutionResponse)
async def execute_tool(
    exec_request: ToolExecutionRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    request_id = getattr(request.state, "request_id", None)
    service = ToolGatewayService(db)
    return await service.execute(exec_request, request_id=request_id)

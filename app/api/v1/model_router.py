from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.schemas.model_router import ModelRouteRequest, ModelRouteResponse
from app.services.auth import get_current_user
from app.services.model_router import ModelRouterService

router = APIRouter(prefix="/api/v1/model-router", tags=["Model Router"])


@router.post("/completion", response_model=ModelRouteResponse)
async def route_completion(
    route_request: ModelRouteRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    request_id = getattr(request.state, "request_id", None)
    service = ModelRouterService(db)
    return await service.route(route_request, request_id=request_id)

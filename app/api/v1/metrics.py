from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.schemas.metrics import PlatformDashboardMetrics
from app.services.auth import get_current_user
from app.services.metrics import MetricsService

router = APIRouter(prefix="/api/v1/metrics", tags=["Metrics & Observability"])


@router.get("/dashboard", response_model=PlatformDashboardMetrics)
async def get_dashboard_metrics(
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    service = MetricsService(db)
    return await service.get_dashboard_metrics()

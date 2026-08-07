from typing import Any, Dict, List, Optional
import time

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
import structlog

from app.database.models.activity_log import ActivityLog
from app.database.models.tool_log import ToolExecutionLog
from app.database.models.workflow import WorkflowRun
from app.schemas.metrics import (
    ModelUsageMetrics,
    PlatformDashboardMetrics,
    ToolExecutionMetrics,
    WorkflowMetrics,
)
from app.schemas.workflow import WorkflowStatus

logger = structlog.get_logger()

# Track module startup timestamp for system uptime calculations
_SYSTEM_START_TIME = time.time()


class MetricsService:

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_workflow_metrics(self) -> WorkflowMetrics:
        """Calculate workflow lifecycle counts and completion percentage using DB aggregation."""
        # Total runs
        total_runs = await self.db.scalar(select(func.count()).select_from(WorkflowRun))
        if not total_runs:
            return WorkflowMetrics()
        # Conditional counts
        completed_count = await self.db.scalar(
            select(func.count()).where(WorkflowRun.status == WorkflowStatus.COMPLETED)
        )
        failed_count = await self.db.scalar(
            select(func.count()).where(WorkflowRun.status == WorkflowStatus.FAILED)
        )
        escalated_count = await self.db.scalar(
            select(func.count()).where(WorkflowRun.status == WorkflowStatus.ESCALATED)
        )
        active_count = total_runs - (completed_count + failed_count + escalated_count)
        completion_rate_pct = round((completed_count / total_runs) * 100, 2) if total_runs else 0.0
        return WorkflowMetrics(
            total_runs=total_runs,
            active_count=active_count,
            completed_count=completed_count,
            failed_count=failed_count,
            escalated_count=escalated_count,
            completion_rate_pct=completion_rate_pct,
        )

    async def get_tool_execution_metrics(self) -> ToolExecutionMetrics:
        """Calculate total tool invocations, success %, and mean execution time."""
        res = await self.db.execute(select(ToolExecutionLog))
        tool_logs = list(res.scalars().all())

        total_executions = len(tool_logs)
        if total_executions == 0:
            return ToolExecutionMetrics()

        successful_executions = sum(1 for log in tool_logs if log.is_success)
        failed_executions = total_executions - successful_executions

        success_rate_pct = round(
            (successful_executions / total_executions) * 100, 2
        )
        total_time_ms = sum(log.execution_time_ms for log in tool_logs)
        avg_execution_time_ms = round(total_time_ms / total_executions, 2)

        return ToolExecutionMetrics(
            total_executions=total_executions,
            successful_executions=successful_executions,
            failed_executions=failed_executions,
            success_rate_pct=success_rate_pct,
            avg_execution_time_ms=avg_execution_time_ms,
        )

    async def get_model_usage_metrics(self) -> ModelUsageMetrics:
        """Aggregate model routing activity by capability."""
        res = await self.db.execute(
            select(ActivityLog).where(
                ActivityLog.event_type == "model_route_completed"
            )
        )
        model_logs = list(res.scalars().all())

        total_requests = len(model_logs)
        by_capability: Dict[str, int] = {}

        for log in model_logs:
            cap = None
            if log.payload and isinstance(log.payload, dict):
                cap = log.payload.get("capability")
            cap_key = cap if cap else "general_reasoning"
            by_capability[cap_key] = by_capability.get(cap_key, 0) + 1

        return ModelUsageMetrics(
            total_requests=total_requests, by_capability=by_capability
        )

    async def get_recent_errors(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Fetch recent operational error logs."""
        res = await self.db.execute(
            select(ActivityLog)
            .where(
                ActivityLog.event_type.like("%failed%")
                | ActivityLog.event_type.like("%error%")
                | ActivityLog.event_type.like("%escalated%")
            )
            .order_by(ActivityLog.created_at.desc())
            .limit(limit)
        )
        logs = list(res.scalars().all())

        return [
            {
                "id": str(log.id),
                "event_type": log.event_type,
                "source": log.source,
                "request_id": log.request_id,
                "payload": log.payload,
                "created_at": log.created_at.isoformat() if log.created_at else None,
            }
            for log in logs
        ]

    async def get_dashboard_metrics(self) -> PlatformDashboardMetrics:
        """Compile all sub-metrics into a unified observability dashboard payload."""
        workflows = await self.get_workflow_metrics()
        tools = await self.get_tool_execution_metrics()
        models = await self.get_model_usage_metrics()
        errors = await self.get_recent_errors()

        uptime_seconds = round(time.time() - _SYSTEM_START_TIME, 2)

        return PlatformDashboardMetrics(
            system_status="operational",
            uptime_seconds=uptime_seconds,
            workflows=workflows,
            tools=tools,
            models=models,
            recent_errors=errors,
        )

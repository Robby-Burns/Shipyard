from typing import Any, Dict, List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
import structlog

from app.database.models.activity_log import ActivityLog
from app.database.models.knowledge import KnowledgeItem
from app.database.models.workflow import WorkflowRun
from app.schemas.console import ConsoleOverviewResponse
from app.schemas.knowledge import KnowledgeStatus, MemoryTier
from app.schemas.workflow import WorkflowRunResponse, WorkflowStatus

logger = structlog.get_logger()


class ConsoleService:

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_active_workflows(self) -> List[WorkflowRun]:
        """Retrieve workflows in active non-terminal states."""
        terminal_statuses = [WorkflowStatus.COMPLETED, WorkflowStatus.FAILED]
        res = await self.db.execute(
            select(WorkflowRun)
            .where(WorkflowRun.status.not_in(terminal_statuses))
            .order_by(WorkflowRun.created_at.desc())
        )
        return list(res.scalars().all())

    async def get_pending_approvals(self) -> List[WorkflowRun]:
        """Retrieve workflows currently paused at AWAITING_APPROVAL."""
        res = await self.db.execute(
            select(WorkflowRun)
            .where(WorkflowRun.status == WorkflowStatus.AWAITING_APPROVAL)
            .order_by(WorkflowRun.created_at.desc())
        )
        return list(res.scalars().all())

    async def get_candidate_knowledge_count(self) -> int:
        """Count candidate knowledge items pending review."""
        from sqlalchemy import func
        return await self.db.scalar(
            select(func.count()).select_from(KnowledgeItem).where(
                KnowledgeItem.tier == MemoryTier.CANDIDATE,
                KnowledgeItem.status == KnowledgeStatus.PROPOSED,
            )
        ) or 0

    async def get_recent_activities(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Fetch recent operational activity log entries."""
        res = await self.db.execute(
            select(ActivityLog)
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

    async def get_recent_error_count(self) -> int:
        """Count recent operational error and escalation logs."""
        from sqlalchemy import func
        return await self.db.scalar(
            select(func.count()).select_from(ActivityLog).where(
                ActivityLog.event_type.like("%failed%")
                | ActivityLog.event_type.like("%error%")
                | ActivityLog.event_type.like("%escalated%")
            )
        ) or 0

    async def get_overview_summary(self) -> ConsoleOverviewResponse:
        """Compile a high-level summary of active system state for the Operations Console."""
        active_workflows = await self.get_active_workflows()
        pending_approvals = await self.get_pending_approvals()
        candidate_count = await self.get_candidate_knowledge_count()
        recent_activities = await self.get_recent_activities()
        recent_error_count = await self.get_recent_error_count()

        pending_approval_list = [
            {
                "id": str(wf.id),
                "title": wf.title,
                "current_step": wf.current_step,
                "created_at": wf.created_at.isoformat() if wf.created_at else None,
            }
            for wf in pending_approvals
        ]

        return ConsoleOverviewResponse(
            system_status="operational",
            active_workflow_count=len(active_workflows),
            pending_approval_count=len(pending_approvals),
            recent_error_count=recent_error_count,
            candidate_knowledge_count=candidate_count,
            recent_activities=recent_activities,
            pending_approvals=pending_approval_list,
        )

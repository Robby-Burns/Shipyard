from datetime import datetime, timezone
from typing import List, Optional
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
import structlog

from app.database.models.workflow import WorkflowRun
from app.schemas.agent import AgentExecutionRequest
from app.schemas.workflow import (
    WorkflowApprovalRequest,
    WorkflowCreateRequest,
    WorkflowEscalationRequest,
    WorkflowResolutionRequest,
    WorkflowStatus,
)
from app.services.activity_log import ActivityLogService
from app.services.agents import (
    ArchitectAgent,
    BuilderAgent,
    CoordinatorAgent,
    QAAgent,
    ReviewerAgent,
)

logger = structlog.get_logger()


class WorkflowEngineService:

    def __init__(self, db: AsyncSession):
        self.db = db
        self.activity_log = ActivityLogService(db)

    async def create_workflow(
        self, req: WorkflowCreateRequest, owner_id: Optional[str] = None, request_id: Optional[str] = None
    ) -> WorkflowRun:
        """Initialize a new engineering workflow run from a spec."""
        workflow = WorkflowRun(
            title=req.title,
            specification=req.specification,
            status=WorkflowStatus.CREATED,
            current_step="created",
            artifacts={},
            owner_id=owner_id,
        )
        self.db.add(workflow)
        await self.db.commit()
        await self.db.refresh(workflow)

        await self.activity_log.record(
            event_type="workflow_created",
            source="workflow_engine",
            request_id=request_id,
            payload={"workflow_id": str(workflow.id), "title": workflow.title},
        )
        return workflow

    async def execute_step(
        self, workflow_id: uuid.UUID, request_id: Optional[str] = None
    ) -> WorkflowRun:
        """Advance the workflow run through its current state step."""
        result = await self.db.execute(
            select(WorkflowRun).where(WorkflowRun.id == workflow_id)
        )
        workflow = result.scalar_one_or_none()

        if not workflow:
            raise ValueError(f"Workflow run {workflow_id} not found")

        if workflow.status in [
            WorkflowStatus.ESCALATED,
            WorkflowStatus.FAILED,
            WorkflowStatus.COMPLETED,
            WorkflowStatus.AWAITING_APPROVAL,
        ]:
            raise ValueError(
                f"Workflow run {workflow_id} cannot execute step in status '{workflow.status.value}'"
            )

        # Step 1: CREATED -> PLANNING (Coordinator)
        if workflow.status == WorkflowStatus.CREATED:
            workflow.status = WorkflowStatus.PLANNING
            workflow.current_step = "coordinator_planning"
            specification = workflow.specification
            await self.db.commit()
            await self.db.close()

            agent = CoordinatorAgent(self.db)
            exec_res = await agent.run(
                AgentExecutionRequest(
                    role=agent.role, task_input=specification
                ),
                request_id=request_id,
            )

            result = await self.db.execute(
                select(WorkflowRun).where(WorkflowRun.id == workflow_id)
            )
            workflow = result.scalar_one()
            new_artifacts = dict(workflow.artifacts)
            new_artifacts["build_plan"] = exec_res.output_text
            workflow.artifacts = new_artifacts
            workflow.status = WorkflowStatus.DESIGNING
            workflow.current_step = "architect_designing"
            await self.db.commit()

        # Step 2: DESIGNING -> BUILDING (Architect)
        elif workflow.status == WorkflowStatus.DESIGNING:
            specification = workflow.specification
            build_plan = workflow.artifacts.get("build_plan")
            await self.db.commit()
            await self.db.close()

            agent = ArchitectAgent(self.db)
            exec_res = await agent.run(
                AgentExecutionRequest(
                    role=agent.role,
                    task_input=specification,
                    context={"build_plan": build_plan},
                ),
                request_id=request_id,
            )

            result = await self.db.execute(
                select(WorkflowRun).where(WorkflowRun.id == workflow_id)
            )
            workflow = result.scalar_one()
            new_artifacts = dict(workflow.artifacts)
            new_artifacts["architecture_doc"] = exec_res.output_text
            workflow.artifacts = new_artifacts
            workflow.status = WorkflowStatus.BUILDING
            workflow.current_step = "builder_building"
            await self.db.commit()

        # Step 3: BUILDING -> REVIEWING (Builder)
        elif workflow.status == WorkflowStatus.BUILDING:
            specification = workflow.specification
            build_plan = workflow.artifacts.get("build_plan")
            architecture_doc = workflow.artifacts.get("architecture_doc")
            await self.db.commit()
            await self.db.close()

            agent = BuilderAgent(self.db)
            exec_res = await agent.run(
                AgentExecutionRequest(
                    role=agent.role,
                    task_input=specification,
                    context={
                        "build_plan": build_plan,
                        "architecture_doc": architecture_doc,
                    },
                ),
                request_id=request_id,
            )

            result = await self.db.execute(
                select(WorkflowRun).where(WorkflowRun.id == workflow_id)
            )
            workflow = result.scalar_one()
            new_artifacts = dict(workflow.artifacts)
            new_artifacts["generated_code"] = exec_res.output_text
            workflow.artifacts = new_artifacts
            workflow.status = WorkflowStatus.REVIEWING
            workflow.current_step = "reviewer_reviewing"
            await self.db.commit()

        # Step 4: REVIEWING -> TESTING (Reviewer)
        elif workflow.status == WorkflowStatus.REVIEWING:
            generated_code = workflow.artifacts.get("generated_code")
            architecture_doc = workflow.artifacts.get("architecture_doc")
            await self.db.commit()
            await self.db.close()

            agent = ReviewerAgent(self.db)
            exec_res = await agent.run(
                AgentExecutionRequest(
                    role=agent.role,
                    task_input="Review generated code and implementation",
                    context={
                        "generated_code": generated_code,
                        "architecture_doc": architecture_doc,
                    },
                ),
                request_id=request_id,
            )

            result = await self.db.execute(
                select(WorkflowRun).where(WorkflowRun.id == workflow_id)
            )
            workflow = result.scalar_one()
            new_artifacts = dict(workflow.artifacts)
            new_artifacts["code_review"] = exec_res.output_text
            workflow.artifacts = new_artifacts
            workflow.status = WorkflowStatus.TESTING
            workflow.current_step = "qa_testing"
            await self.db.commit()

        # Step 5: TESTING -> AWAITING_APPROVAL (QA)
        elif workflow.status == WorkflowStatus.TESTING:
            generated_code = workflow.artifacts.get("generated_code")
            code_review = workflow.artifacts.get("code_review")
            await self.db.commit()
            await self.db.close()

            agent = QAAgent(self.db)
            exec_res = await agent.run(
                AgentExecutionRequest(
                    role=agent.role,
                    task_input=(
                        "Verify acceptance criteria and perform release"
                        " validation"
                    ),
                    context={
                        "generated_code": generated_code,
                        "code_review": code_review,
                    },
                ),
                request_id=request_id,
            )

            result = await self.db.execute(
                select(WorkflowRun).where(WorkflowRun.id == workflow_id)
            )
            workflow = result.scalar_one()
            new_artifacts = dict(workflow.artifacts)
            new_artifacts["qa_report"] = exec_res.output_text
            workflow.artifacts = new_artifacts
            workflow.status = WorkflowStatus.AWAITING_APPROVAL
            workflow.current_step = "awaiting_human_production_approval"
            await self.db.commit()

        await self.db.refresh(workflow)
        return workflow

    async def run_full_pipeline(
        self, workflow_id: uuid.UUID, request_id: Optional[str] = None
    ) -> WorkflowRun:
        """Run workflow continuously through all automated steps until AWAITING_APPROVAL gate."""
        workflow = await self.execute_step(workflow_id, request_id)
        while workflow.status in [
            WorkflowStatus.DESIGNING,
            WorkflowStatus.BUILDING,
            WorkflowStatus.REVIEWING,
            WorkflowStatus.TESTING,
        ]:
            workflow = await self.execute_step(workflow_id, request_id)
        return workflow

    async def escalate_workflow(
        self,
        workflow_id: uuid.UUID,
        req: WorkflowEscalationRequest,
        request_id: Optional[str] = None,
    ) -> WorkflowRun:
        """Escalate a workflow due to blocked tasks, review rejections, or high risks."""
        result = await self.db.execute(
            select(WorkflowRun).where(WorkflowRun.id == workflow_id)
        )
        workflow = result.scalar_one_or_none()

        if not workflow:
            raise ValueError(f"Workflow run {workflow_id} not found")

        if workflow.status in [WorkflowStatus.COMPLETED, WorkflowStatus.FAILED]:
            raise ValueError(
                f"Cannot escalate workflow run {workflow_id} in final state '{workflow.status.value}'"
            )

        workflow.status = WorkflowStatus.ESCALATED
        workflow.error_message = f"Escalated by {req.escalated_by}: {req.reason}"

        await self.db.commit()
        await self.db.refresh(workflow)

        await self.activity_log.record(
            event_type="workflow_escalated",
            source="workflow_engine",
            request_id=request_id,
            payload={
                "workflow_id": str(workflow.id),
                "escalated_by": req.escalated_by,
                "reason": req.reason,
            },
        )
        return workflow

    async def resolve_escalation(
        self,
        workflow_id: uuid.UUID,
        req: WorkflowResolutionRequest,
        request_id: Optional[str] = None,
    ) -> WorkflowRun:
        """Human management resolution for an escalated workflow."""
        result = await self.db.execute(
            select(WorkflowRun).where(WorkflowRun.id == workflow_id)
        )
        workflow = result.scalar_one_or_none()

        if not workflow or workflow.status != WorkflowStatus.ESCALATED:
            raise ValueError("Workflow is not in an escalated state")

        if req.action == "resume":
            # Resume to current step state prior to escalation
            workflow.status = (
                WorkflowStatus.BUILDING
                if "builder" in workflow.current_step
                else WorkflowStatus.PLANNING
            )
        elif req.action == "restart":
            workflow.status = WorkflowStatus.CREATED
            workflow.current_step = "created"
            workflow.artifacts = {}
            workflow.approved_by = None
            workflow.approved_at = None
        elif req.action == "terminate":
            workflow.status = WorkflowStatus.FAILED
        else:
            raise ValueError(f"Invalid resolution action: {req.action}")

        workflow.error_message = None
        await self.db.commit()
        await self.db.refresh(workflow)

        await self.activity_log.record(
            event_type="workflow_escalation_resolved",
            source="workflow_engine",
            request_id=request_id,
            payload={
                "workflow_id": str(workflow.id),
                "resolved_by": req.resolved_by,
                "action": req.action,
                "notes": req.resolution_notes,
            },
        )
        return workflow

    async def approve_production_deployment(
        self,
        workflow_id: uuid.UUID,
        req: WorkflowApprovalRequest,
        request_id: Optional[str] = None,
    ) -> WorkflowRun:
        """Human approval gate transition to COMPLETED."""
        result = await self.db.execute(
            select(WorkflowRun).where(WorkflowRun.id == workflow_id)
        )
        workflow = result.scalar_one_or_none()

        if not workflow or workflow.status != WorkflowStatus.AWAITING_APPROVAL:
            raise ValueError(
                "Workflow is not awaiting human production approval"
            )

        workflow.status = WorkflowStatus.COMPLETED
        workflow.current_step = "completed_and_deployed"
        workflow.approved_by = req.approved_by
        workflow.approved_at = datetime.now(timezone.utc)

        await self.db.commit()
        await self.db.refresh(workflow)

        await self.activity_log.record(
            event_type="workflow_approved_and_completed",
            source="workflow_engine",
            request_id=request_id,
            payload={
                "workflow_id": str(workflow.id),
                "approved_by": req.approved_by,
            },
        )
        return workflow

    async def get_workflow(self, workflow_id: uuid.UUID) -> Optional[WorkflowRun]:
        result = await self.db.execute(
            select(WorkflowRun).where(WorkflowRun.id == workflow_id)
        )
        return result.scalar_one_or_none()

    async def list_workflows(
        self, owner_id: Optional[str] = None, limit: int = 100, offset: int = 0
    ) -> List[WorkflowRun]:
        stmt = select(WorkflowRun)
        if owner_id:
            stmt = stmt.where(WorkflowRun.owner_id == owner_id)
        stmt = stmt.order_by(WorkflowRun.created_at.desc(), WorkflowRun.id.desc())
        stmt = stmt.limit(limit).offset(offset)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

from datetime import datetime, timezone
from typing import List, Optional
import os
import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm.attributes import flag_modified
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
    PlatformAgent,
    ChallengerAgent,
)
from app.config.settings import settings

logger = structlog.get_logger()


class WorkflowEngineService:

    def __init__(self, db: AsyncSession):
        self.db = db
        self.activity_log = ActivityLogService(db)

    async def create_workflow(
        self, req: WorkflowCreateRequest, owner_id: Optional[str] = None, request_id: Optional[str] = None
    ) -> WorkflowRun:
        """Initialize a new engineering workflow run from a spec."""
        initial_artifacts = {}
        if req.repository_url:
            initial_artifacts["repository_url"] = req.repository_url

        workflow = WorkflowRun(
            title=req.title,
            specification=req.specification,
            status=WorkflowStatus.CREATED,
            current_step="created",
            artifacts=initial_artifacts,
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

        # Step 1: CREATED or PLANNING -> PLANNING (Coordinator)
        if workflow.status in [WorkflowStatus.CREATED, WorkflowStatus.PLANNING]:
            workflow.status = WorkflowStatus.PLANNING
            workflow.current_step = "coordinator_planning"
            specification = workflow.specification
            await self.db.commit()

            # Retrieve retry count and feedback
            retries = workflow.artifacts.get("coordinator_planning_retries", 0)
            feedback = workflow.artifacts.get("coordinator_planning_feedback", "")

            task_input = "Breakdown & Planning"
            if feedback:
                task_input += f"\n\n[Correction Feedback from Challenger (Attempt {retries}):]\n{feedback}"

            agent = CoordinatorAgent(self.db)
            exec_res = await agent.run(
                AgentExecutionRequest(
                    role=agent.role,
                    task_input=task_input,
                    specification_ref=workflow_id,
                ),
                request_id=request_id,
            )

            # Challenger runs to verify the plan
            challenger = ChallengerAgent(self.db)
            chal_res = await challenger.run_challenge(
                step_name="coordinator_planning",
                primary_output=exec_res.output_text,
                specification_ref=workflow_id,
                model_override=settings.default_model_challenge_coordinator,
                primary_model=exec_res.model_used,
                request_id=request_id,
            )

            chal_status = chal_res.artifacts.get("challenge_status", "passed")
            chal_reason = chal_res.artifacts.get("challenge_reason")

            if chal_status == "failed":
                retries += 1
                result = await self.db.execute(
                    select(WorkflowRun).where(WorkflowRun.id == workflow_id)
                )
                workflow = result.scalar_one()
                new_artifacts = dict(workflow.artifacts)
                new_artifacts["coordinator_planning_retries"] = retries
                new_artifacts["coordinator_planning_feedback"] = chal_reason
                new_artifacts["build_plan"] = exec_res.output_text
                workflow.artifacts = new_artifacts

                if retries > 2:
                    workflow.status = WorkflowStatus.ESCALATED
                    workflow.error_message = f"Planning failed challenge verification check after 2 retries. Challenger feedback: {chal_reason}"
                    await self.db.commit()
                    await self.activity_log.record(
                        event_type="workflow_escalated",
                        source="workflow_engine",
                        request_id=request_id,
                        payload={
                            "workflow_id": str(workflow.id),
                            "escalated_by": "challenger",
                            "reason": workflow.error_message,
                        },
                    )
                else:
                    await self.db.commit()
            else:
                result = await self.db.execute(
                    select(WorkflowRun).where(WorkflowRun.id == workflow_id)
                )
                workflow = result.scalar_one()
                new_artifacts = dict(workflow.artifacts)
                new_artifacts["build_plan"] = exec_res.output_text
                # Clear retry state
                new_artifacts.pop("coordinator_planning_retries", None)
                new_artifacts.pop("coordinator_planning_feedback", None)
                workflow.artifacts = new_artifacts
                workflow.status = WorkflowStatus.DESIGNING
                workflow.current_step = "architect_designing"
                await self.db.commit()

        # Step 2: DESIGNING -> BUILDING (Architect)
        elif workflow.status == WorkflowStatus.DESIGNING:
            specification = workflow.specification
            build_plan = workflow.artifacts.get("build_plan")
            await self.db.commit()

            # Retrieve retry count and feedback
            retries = workflow.artifacts.get("architect_designing_retries", 0)
            feedback = workflow.artifacts.get("architect_designing_feedback", "")

            task_input = "System Blueprints & ADRs"
            if feedback:
                task_input += f"\n\n[Correction Feedback from Challenger (Attempt {retries}):]\n{feedback}"

            agent = ArchitectAgent(self.db)
            exec_res = await agent.run(
                AgentExecutionRequest(
                    role=agent.role,
                    task_input=task_input,
                    specification_ref=workflow_id,
                    context={
                        "build_plan": build_plan,
                        "workflow_id": str(workflow_id),
                    },
                ),
                request_id=request_id,
            )

            # Challenger runs to verify the architecture
            challenger = ChallengerAgent(self.db)
            chal_res = await challenger.run_challenge(
                step_name="architect_designing",
                primary_output=exec_res.output_text,
                specification_ref=workflow_id,
                model_override=settings.default_model_challenge_architect,
                primary_model=exec_res.model_used,
                request_id=request_id,
            )

            chal_status = chal_res.artifacts.get("challenge_status", "passed")
            chal_reason = chal_res.artifacts.get("challenge_reason")

            if chal_status == "failed":
                retries += 1
                result = await self.db.execute(
                    select(WorkflowRun).where(WorkflowRun.id == workflow_id)
                )
                workflow = result.scalar_one()
                new_artifacts = dict(workflow.artifacts)
                new_artifacts["architect_designing_retries"] = retries
                new_artifacts["architect_designing_feedback"] = chal_reason
                new_artifacts["architecture_doc"] = exec_res.output_text
                workflow.artifacts = new_artifacts

                if retries > 2:
                    workflow.status = WorkflowStatus.ESCALATED
                    workflow.error_message = f"Architecture design failed challenge verification check after 2 retries. Challenger feedback: {chal_reason}"
                    await self.db.commit()
                    await self.activity_log.record(
                        event_type="workflow_escalated",
                        source="workflow_engine",
                        request_id=request_id,
                        payload={
                            "workflow_id": str(workflow.id),
                            "escalated_by": "challenger",
                            "reason": workflow.error_message,
                        },
                    )
                else:
                    await self.db.commit()
            else:
                result = await self.db.execute(
                    select(WorkflowRun).where(WorkflowRun.id == workflow_id)
                )
                workflow = result.scalar_one()
                new_artifacts = dict(workflow.artifacts)
                new_artifacts["architecture_doc"] = exec_res.output_text
                if exec_res.artifacts:
                    new_artifacts.update(exec_res.artifacts)
                # Clear retry state
                new_artifacts.pop("architect_designing_retries", None)
                new_artifacts.pop("architect_designing_feedback", None)
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

            # Retrieve retry count and feedback
            retries = workflow.artifacts.get("builder_building_retries", 0)
            feedback = workflow.artifacts.get("builder_building_feedback", "")

            task_input = "Feature Implementation"
            if feedback:
                task_input += f"\n\n[Correction Feedback from Challenger (Attempt {retries}):]\n{feedback}"

            agent = BuilderAgent(self.db)
            exec_res = await agent.run(
                AgentExecutionRequest(
                    role=agent.role,
                    task_input=task_input,
                    specification_ref=workflow_id,
                    context={
                        "build_plan": build_plan,
                        "architecture_doc": architecture_doc,
                        "repository_url": workflow.artifacts.get("repository_url"),
                    },
                ),
                request_id=request_id,
            )

            # Challenger runs to verify the generated code
            challenger = ChallengerAgent(self.db)
            chal_res = await challenger.run_challenge(
                step_name="builder_building",
                primary_output=exec_res.output_text,
                specification_ref=workflow_id,
                model_override=settings.default_model_challenge_builder,
                primary_model=exec_res.model_used,
                request_id=request_id,
            )

            chal_status = chal_res.artifacts.get("challenge_status", "passed")
            chal_reason = chal_res.artifacts.get("challenge_reason")

            if chal_status == "failed":
                retries += 1
                result = await self.db.execute(
                    select(WorkflowRun).where(WorkflowRun.id == workflow_id)
                )
                workflow = result.scalar_one()
                new_artifacts = dict(workflow.artifacts)
                new_artifacts["builder_building_retries"] = retries
                new_artifacts["builder_building_feedback"] = chal_reason
                new_artifacts["generated_code"] = exec_res.output_text
                workflow.artifacts = new_artifacts

                if retries > 2:
                    workflow.status = WorkflowStatus.ESCALATED
                    workflow.error_message = f"Code implementation failed challenge verification check after 2 retries. Challenger feedback: {chal_reason}"
                    await self.db.commit()
                    await self.activity_log.record(
                        event_type="workflow_escalated",
                        source="workflow_engine",
                        request_id=request_id,
                        payload={
                            "workflow_id": str(workflow.id),
                            "escalated_by": "challenger",
                            "reason": workflow.error_message,
                        },
                    )
                else:
                    await self.db.commit()
            else:
                result = await self.db.execute(
                    select(WorkflowRun).where(WorkflowRun.id == workflow_id)
                )
                workflow = result.scalar_one()
                new_artifacts = dict(workflow.artifacts)
                new_artifacts["generated_code"] = exec_res.output_text
                if exec_res.artifacts:
                    new_artifacts.update(exec_res.artifacts)
                # Clear retry state
                new_artifacts.pop("builder_building_retries", None)
                new_artifacts.pop("builder_building_feedback", None)
                workflow.artifacts = new_artifacts
                workflow.status = WorkflowStatus.REVIEWING
                workflow.current_step = "reviewer_reviewing"
                await self.db.commit()

        # Step 4: REVIEWING -> TESTING (Reviewer)
        elif workflow.status == WorkflowStatus.REVIEWING:
            generated_code = workflow.artifacts.get("generated_code")
            architecture_doc = workflow.artifacts.get("architecture_doc")
            specification = workflow.specification
            await self.db.commit()

            # Retrieve retry count and feedback
            retries = workflow.artifacts.get("reviewer_reviewing_retries", 0)
            feedback = workflow.artifacts.get("reviewer_reviewing_feedback", "")

            task_input = "Review generated code and implementation"
            if feedback:
                task_input += f"\n\n[Correction Feedback from Challenger (Attempt {retries}):]\n{feedback}"

            agent = ReviewerAgent(self.db)
            exec_res = await agent.run(
                AgentExecutionRequest(
                    role=agent.role,
                    task_input=task_input,
                    context={
                        "generated_code": generated_code,
                        "architecture_doc": architecture_doc,
                    },
                    specification_ref=workflow_id,
                ),
                request_id=request_id,
            )

            # Challenger runs to verify the review
            challenger = ChallengerAgent(self.db)
            chal_res = await challenger.run_challenge(
                step_name="reviewer_reviewing",
                primary_output=exec_res.output_text,
                specification_ref=workflow_id,
                model_override=settings.default_model_challenge_reviewer,
                primary_model=exec_res.model_used,
                request_id=request_id,
            )

            chal_status = chal_res.artifacts.get("challenge_status", "passed")
            chal_reason = chal_res.artifacts.get("challenge_reason")

            if chal_status == "failed":
                retries += 1
                result = await self.db.execute(
                    select(WorkflowRun).where(WorkflowRun.id == workflow_id)
                )
                workflow = result.scalar_one()
                new_artifacts = dict(workflow.artifacts)
                new_artifacts["reviewer_reviewing_retries"] = retries
                new_artifacts["reviewer_reviewing_feedback"] = chal_reason
                new_artifacts["code_review"] = exec_res.output_text
                workflow.artifacts = new_artifacts

                if retries > 2:
                    workflow.status = WorkflowStatus.ESCALATED
                    workflow.error_message = f"Code review failed challenge verification check after 2 retries. Challenger feedback: {chal_reason}"
                    await self.db.commit()
                    await self.activity_log.record(
                        event_type="workflow_escalated",
                        source="workflow_engine",
                        request_id=request_id,
                        payload={
                            "workflow_id": str(workflow.id),
                            "escalated_by": "challenger",
                            "reason": workflow.error_message,
                        },
                    )
                else:
                    await self.db.commit()
            else:
                result = await self.db.execute(
                    select(WorkflowRun).where(WorkflowRun.id == workflow_id)
                )
                workflow = result.scalar_one()
                new_artifacts = dict(workflow.artifacts)
                new_artifacts["code_review"] = exec_res.output_text
                if exec_res.artifacts:
                    new_artifacts.update(exec_res.artifacts)
                # Clear retry state
                new_artifacts.pop("reviewer_reviewing_retries", None)
                new_artifacts.pop("reviewer_reviewing_feedback", None)
                workflow.artifacts = new_artifacts

                # Handle code review rejection / request changes
                review_status = exec_res.artifacts.get("status") if exec_res.artifacts else "approved"
                if review_status == "request_changes":
                    workflow.status = WorkflowStatus.ESCALATED
                    workflow.error_message = f"Code Review Rejected: {exec_res.artifacts.get('reason', 'changes requested')}"
                    await self.db.commit()
                    # Log the escalation event
                    await self.activity_log.record(
                        event_type="workflow_escalated",
                        source="workflow_engine",
                        request_id=request_id,
                        payload={
                            "workflow_id": str(workflow.id),
                            "escalated_by": "reviewer",
                            "reason": workflow.error_message,
                        },
                    )
                else:
                    workflow.status = WorkflowStatus.TESTING
                    workflow.current_step = "qa_testing"
                    await self.db.commit()

        # Step 5: TESTING -> AWAITING_APPROVAL (QA & Platform)
        elif workflow.status == WorkflowStatus.TESTING:
            generated_code = workflow.artifacts.get("generated_code")
            code_review = workflow.artifacts.get("code_review")
            specification = workflow.specification
            await self.db.commit()

            # Retrieve retry count and feedback for QA
            retries = workflow.artifacts.get("qa_testing_retries", 0)
            feedback = workflow.artifacts.get("qa_testing_feedback", "")

            task_input = "Verify acceptance criteria and perform release validation"
            if feedback:
                task_input += f"\n\n[Correction Feedback from Challenger (Attempt {retries}):]\n{feedback}"

            agent = QAAgent(self.db)
            exec_res = await agent.run(
                AgentExecutionRequest(
                    role=agent.role,
                    task_input=task_input,
                    context={
                        "generated_code": generated_code,
                        "code_review": code_review,
                    },
                    specification_ref=workflow_id,
                ),
                request_id=request_id,
            )

            # Challenger runs to verify the QA Report
            challenger = ChallengerAgent(self.db)
            chal_res = await challenger.run_challenge(
                step_name="qa_testing",
                primary_output=exec_res.output_text,
                specification_ref=workflow_id,
                model_override=settings.default_model_challenge_qa,
                primary_model=exec_res.model_used,
                request_id=request_id,
            )

            chal_status = chal_res.artifacts.get("challenge_status", "passed")
            chal_reason = chal_res.artifacts.get("challenge_reason")

            if chal_status == "failed":
                retries += 1
                result = await self.db.execute(
                    select(WorkflowRun).where(WorkflowRun.id == workflow_id)
                )
                workflow = result.scalar_one()
                new_artifacts = dict(workflow.artifacts)
                new_artifacts["qa_testing_retries"] = retries
                new_artifacts["qa_testing_feedback"] = chal_reason
                new_artifacts["qa_report"] = exec_res.output_text
                workflow.artifacts = new_artifacts

                if retries > 2:
                    workflow.status = WorkflowStatus.ESCALATED
                    workflow.error_message = f"QA testing failed challenge verification check after 2 retries. Challenger feedback: {chal_reason}"
                    await self.db.commit()
                    await self.activity_log.record(
                        event_type="workflow_escalated",
                        source="workflow_engine",
                        request_id=request_id,
                        payload={
                            "workflow_id": str(workflow.id),
                            "escalated_by": "challenger",
                            "reason": workflow.error_message,
                        },
                    )
                else:
                    await self.db.commit()
            else:
                result = await self.db.execute(
                    select(WorkflowRun).where(WorkflowRun.id == workflow_id)
                )
                workflow = result.scalar_one()
                new_artifacts = dict(workflow.artifacts)
                new_artifacts["qa_report"] = exec_res.output_text
                if exec_res.artifacts:
                    new_artifacts.update(exec_res.artifacts)
                
                # Clear QA retry state
                new_artifacts.pop("qa_testing_retries", None)
                new_artifacts.pop("qa_testing_feedback", None)
                workflow.artifacts = new_artifacts

                qa_status = exec_res.artifacts.get("qa_status") if exec_res.artifacts else "PASSED"
                if qa_status == "FAILED":
                    workflow.status = WorkflowStatus.ESCALATED
                    workflow.error_message = "QA Verification Failed: acceptance criteria not satisfied."
                    await self.db.commit()
                    await self.activity_log.record(
                        event_type="workflow_escalated",
                        source="workflow_engine",
                        request_id=request_id,
                        payload={
                            "workflow_id": str(workflow.id),
                            "escalated_by": "qa",
                            "reason": workflow.error_message,
                        },
                    )
                else:
                    # Retrieve retry count and feedback for Platform
                    plat_retries = workflow.artifacts.get("platform_reporting_retries", 0)
                    plat_feedback = workflow.artifacts.get("platform_reporting_feedback", "")

                    plat_task_input = "Analyze pipeline latency metrics and operational recommendations"
                    if plat_feedback:
                        plat_task_input += f"\n\n[Correction Feedback from Challenger (Attempt {plat_retries}):]\n{plat_feedback}"

                    # QA Passed -> Execute Platform Agent to gather metrics & log recommendations
                    platform_agent = PlatformAgent(self.db)
                    # Retrieve activity logs for this request_id to calculate metrics
                    logs = []
                    if request_id:
                        from app.schemas.activity_log import ActivityLogFilter
                        logs = await self.activity_log.search(
                            ActivityLogFilter(request_id=request_id, limit=100)
                        )
                    
                    # Compute model usage metrics
                    metrics = {
                        "steps": [],
                        "total_cost": 0.0,
                        "total_latency_ms": 0.0,
                    }
                    for log in logs:
                        if log.event_type == "model_route_completed" and log.payload:
                            payload = log.payload
                            step_latency = payload.get("latency_ms", 0.0)
                            step_usage = payload.get("usage") or {}
                            step_cost = step_usage.get("estimated_cost", 0.0)
                            
                            metrics["total_cost"] += float(step_cost)
                            metrics["total_latency_ms"] += float(step_latency)
                            metrics["steps"].append({
                                "capability": payload.get("capability"),
                                "model": payload.get("model"),
                                "latency_ms": step_latency,
                                "cost": step_cost,
                            })

                    platform_res = await platform_agent.run(
                        AgentExecutionRequest(
                            role=platform_agent.role,
                            task_input=plat_task_input,
                            context={
                                "workflow_id": str(workflow_id),
                                "qa_report": exec_res.output_text,
                                "pipeline_metrics": metrics,
                            }
                        ),
                        request_id=request_id
                    )

                    # Challenger runs to verify the Platform recommendations
                    platform_chal_res = await challenger.run_challenge(
                        step_name="platform_reporting",
                        primary_output=platform_res.output_text,
                        specification_ref=workflow_id,
                        model_override=settings.default_model_challenge_platform,
                        primary_model=platform_res.model_used,
                        request_id=request_id,
                    )
                    
                    plat_chal_status = platform_chal_res.artifacts.get("challenge_status", "passed")
                    plat_chal_reason = platform_chal_res.artifacts.get("challenge_reason")

                    if plat_chal_status == "failed":
                        plat_retries += 1
                        new_artifacts["platform_reporting_retries"] = plat_retries
                        new_artifacts["platform_reporting_feedback"] = plat_chal_reason
                        new_artifacts["platform_recommendations"] = platform_res.output_text
                        workflow.artifacts = new_artifacts
                        
                        if plat_retries > 2:
                            workflow.status = WorkflowStatus.ESCALATED
                            workflow.error_message = f"Platform analysis failed challenge verification check after 2 retries. Challenger feedback: {plat_chal_reason}"
                            await self.db.commit()
                            await self.activity_log.record(
                                event_type="workflow_escalated",
                                source="workflow_engine",
                                request_id=request_id,
                                payload={
                                    "workflow_id": str(workflow.id),
                                    "escalated_by": "challenger",
                                    "reason": workflow.error_message,
                                },
                            )
                        else:
                            await self.db.commit()
                    else:
                        new_artifacts["platform_recommendations"] = platform_res.output_text
                        if platform_res.artifacts:
                            new_artifacts.update(platform_res.artifacts)
                        
                        # Clear platform retry state
                        new_artifacts.pop("platform_reporting_retries", None)
                        new_artifacts.pop("platform_reporting_feedback", None)
                        workflow.artifacts = new_artifacts

                        # Propose candidates for Shared Knowledge if identified
                        knowledge_candidate = platform_res.artifacts.get("knowledge_candidate") if platform_res.artifacts else None
                        if knowledge_candidate:
                            from app.services.knowledge_service import KnowledgeService
                            from app.schemas.knowledge import KnowledgeItemCreate, MemoryTier
                            ks = KnowledgeService(self.db)
                            await ks.propose_candidate(KnowledgeItemCreate(
                                title=f"Platform Knowledge Candidate for run {workflow_id}",
                                tier=MemoryTier.CANDIDATE,
                                category="platform",
                                content=knowledge_candidate,
                            ))

                        # Log Platform Recommendations to the journal
                        await self.activity_log.record(
                            event_type="platform_recommendation",
                            source="agent_platform",
                            request_id=request_id,
                            payload={
                                "workflow_id": str(workflow.id),
                                "recommendation": platform_res.output_text,
                            },
                        )

                        workflow.status = WorkflowStatus.AWAITING_APPROVAL
                        workflow.current_step = "awaiting_human_production_approval"
                        await self.db.commit()

        await self.db.refresh(workflow)
        return workflow

    async def run_full_pipeline(
        self, workflow_id: uuid.UUID, request_id: Optional[str] = None
    ) -> WorkflowRun:
        """Run workflow continuously through all automated steps until AWAITING_APPROVAL gate."""
        # 1. Fetch initial status from DB
        result = await self.db.execute(
            select(WorkflowRun).where(WorkflowRun.id == workflow_id)
        )
        workflow = result.scalar_one_or_none()
        if not workflow or workflow.status in [
            WorkflowStatus.ESCALATED,
            WorkflowStatus.FAILED,
            WorkflowStatus.COMPLETED,
            WorkflowStatus.AWAITING_APPROVAL,
        ]:
            return workflow

        # 2. Run the first step
        try:
            workflow = await self.execute_step(workflow_id, request_id)
        except Exception as e:
            workflow = await self._handle_step_failure(workflow_id, e, request_id)
            return workflow

        # 3. Execution loop with iteration cap to prevent runaway loops
        MAX_STEPS = 15
        steps_executed = 0
        while steps_executed < MAX_STEPS:
            # Refresh workflow state from DB to check for pause/terminate signals
            await self.db.refresh(workflow)
            if workflow.status not in [
                WorkflowStatus.PLANNING,
                WorkflowStatus.DESIGNING,
                WorkflowStatus.BUILDING,
                WorkflowStatus.REVIEWING,
                WorkflowStatus.TESTING,
            ]:
                break
            try:
                workflow = await self.execute_step(workflow_id, request_id)
            except Exception as e:
                workflow = await self._handle_step_failure(workflow_id, e, request_id)
                break
            steps_executed += 1
        else:
            # Runaway loop detected
            logger.error("workflow_runaway_loop_detected", workflow_id=str(workflow_id), max_steps=MAX_STEPS)
            workflow.status = WorkflowStatus.ESCALATED
            workflow.error_message = f"Execution exceeded maximum safety loop of {MAX_STEPS} steps."
            await self.db.commit()
            
        return workflow

    async def _handle_step_failure(
        self, workflow_id: uuid.UUID, exc: Exception, request_id: Optional[str] = None
    ) -> WorkflowRun:
        """Helper to cleanly transition workflow run status to FAILED on step crash/exception."""
        logger.error(
            "workflow_step_execution_failed",
            workflow_id=str(workflow_id),
            error=str(exc),
        )
        result = await self.db.execute(
            select(WorkflowRun).where(WorkflowRun.id == workflow_id)
        )
        workflow = result.scalar_one_or_none()
        if workflow:
            workflow.status = WorkflowStatus.FAILED
            workflow.error_message = f"Step execution failed: {str(exc)}"
            await self.db.commit()
            
            await self.activity_log.record(
                event_type="workflow_failed",
                source="workflow_engine",
                request_id=request_id,
                payload={
                    "workflow_id": str(workflow_id),
                    "error": str(exc),
                },
            )
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
            # Resume to the step that was active prior to escalation.
            # Mapping based on the naming convention of current_step values.
            step_to_status = {
                "builder": WorkflowStatus.BUILDING,
                "reviewer": WorkflowStatus.REVIEWING,
                "qa": WorkflowStatus.TESTING,
                "coordinator": WorkflowStatus.PLANNING,
                "architect": WorkflowStatus.DESIGNING,
            }
            # Extract the component before the first '_' if present
            step_key = workflow.current_step.split('_')[0] if workflow.current_step else ""
            workflow.status = step_to_status.get(step_key, WorkflowStatus.PLANNING)
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

        # Compile Engineering Passport using Coordinator Agent
        coordinator = CoordinatorAgent(self.db)
        pass_res = await coordinator.run(
            AgentExecutionRequest(
                role=coordinator.role,
                task_input="Compile the final Engineering Passport and Deployment Guide based on all pipeline execution artifacts.",
                context=dict(workflow.artifacts)
            ),
            request_id=request_id
        )

        # Write to disk
        import anyio
        target_dir = os.path.join("artifacts/passports", str(workflow.id))
        os.makedirs(target_dir, exist_ok=True)

        passport_path = os.path.join(target_dir, "engineering_passport.md")
        passport_anyio = anyio.Path(passport_path)
        await passport_anyio.write_text(pass_res.output_text, encoding="utf-8")

        guide_path = os.path.join(target_dir, "deployment_guide.md")
        guide_content = (
            "# Production Deployment Guide\n\n"
            f"Release Tag: rel_{str(workflow.id)[:8]}\n"
            f"Commit Hash: {workflow.artifacts.get('commit_hash', 'mock-hash')}\n"
            "Steps:\n"
            "1. Pull the repository branch containing the commit.\n"
            "2. Run database migrations: `alembic upgrade head`.\n"
            "3. Run healthchecks: `/healthz` and `/readyz`.\n"
            "4. Verify application operations."
        )
        guide_anyio = anyio.Path(guide_path)
        await guide_anyio.write_text(guide_content, encoding="utf-8")
        new_artifacts = dict(workflow.artifacts)
        new_artifacts["engineering_passport_path"] = passport_path
        new_artifacts["deployment_guide_path"] = guide_path
        new_artifacts["engineering_passport"] = pass_res.output_text
        workflow.artifacts = new_artifacts

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
                "engineering_passport_path": passport_path,
                "deployment_guide_path": guide_path,
            },
        )
        return workflow

    async def get_workflow(self, workflow_id: uuid.UUID) -> Optional[WorkflowRun]:
        result = await self.db.execute(
            select(WorkflowRun).where(WorkflowRun.id == workflow_id)
        )
        return result.scalar_one_or_none()

    async def list_workflows(
        self,
        owner_id: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
        include_hidden: bool = False,
    ) -> List[WorkflowRun]:
        stmt = select(WorkflowRun)
        if owner_id:
            stmt = stmt.where(WorkflowRun.owner_id == owner_id)
        stmt = stmt.order_by(WorkflowRun.created_at.desc(), WorkflowRun.id.desc())
        result = await self.db.execute(stmt)
        workflows = list(result.scalars().all())
        if not include_hidden:
            workflows = [
                workflow
                for workflow in workflows
                if not workflow.artifacts.get("portfolio_hidden")
            ]
        return workflows[offset:offset + limit]

    async def hide_workflow_from_portfolio(
        self,
        workflow_id: uuid.UUID,
        hidden_by: Optional[str] = None,
        request_id: Optional[str] = None,
    ) -> WorkflowRun:
        result = await self.db.execute(
            select(WorkflowRun).where(WorkflowRun.id == workflow_id)
        )
        workflow = result.scalar_one_or_none()
        if not workflow:
            raise ValueError("Workflow run not found")
        if workflow.status != WorkflowStatus.FAILED:
            raise ValueError("Only terminated projects can be removed from the portfolio")

        artifacts = dict(workflow.artifacts or {})
        artifacts["portfolio_hidden"] = True
        artifacts["portfolio_hidden_at"] = datetime.now(timezone.utc).isoformat()
        if hidden_by:
            artifacts["portfolio_hidden_by"] = hidden_by
        workflow.artifacts = artifacts
        flag_modified(workflow, "artifacts")
        await self.db.commit()
        await self.db.refresh(workflow)

        await self.activity_log.record(
            event_type="workflow_portfolio_hidden",
            source="workflow_engine",
            request_id=request_id,
            payload={
                "workflow_id": str(workflow.id),
                "hidden_by": hidden_by,
            },
        )
        return workflow

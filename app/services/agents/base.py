import time
from typing import Any, Dict, Optional

from sqlalchemy.ext.asyncio import AsyncSession
import structlog

from app.schemas.agent import (
    AgentExecutionRequest,
    AgentExecutionResponse,
    DisciplineRole,
)
from app.schemas.model_router import Capability, ChatMessage, ModelRouteRequest
from app.services.activity_log import ActivityLogService
from app.services.model_router import ModelRouterService
from app.services.tool_gateway import ToolGatewayService

logger = structlog.get_logger()


class BaseAgent:

    def __init__(
        self, role: DisciplineRole, capability: Capability, db: AsyncSession
    ):
        self.role = role
        self.capability = capability
        self.db = db
        self.model_router = ModelRouterService(db)
        self.tool_gateway = ToolGatewayService(db)
        self.activity_log = ActivityLogService(db)

    def get_system_prompt(self) -> str:
        raise NotImplementedError("Subclasses must define get_system_prompt()")

    async def run(
        self, request: AgentExecutionRequest, request_id: Optional[str] = None
    ) -> AgentExecutionResponse:
        start_time = time.time()

        # Log agent execution start
        await self.activity_log.record(
            event_type="agent_execution_started",
            source=f"agent_{self.role.value}",
            request_id=request_id,
            payload={"task_input": request.task_input, "role": self.role.value},
        )

        system_prompt = self.get_system_prompt()
        user_message = f"Task: {request.task_input}\nContext: {request.context}"

        route_req = ModelRouteRequest(
            capability=self.capability,
            messages=[
                ChatMessage(role="system", content=system_prompt),
                ChatMessage(role="user", content=user_message),
            ],
        )

        route_res = await self.model_router.route(route_req, request_id=request_id)
        execution_time_ms = round((time.time() - start_time) * 1000, 2)

        # Log agent completion
        await self.activity_log.record(
            event_type="agent_execution_completed",
            source=f"agent_{self.role.value}",
            request_id=request_id,
            payload={"role": self.role.value, "model_used": route_res.model_used},
        )

        return AgentExecutionResponse(
            role=self.role,
            status="success",
            output_text=route_res.content,
            artifacts={},
            model_used=route_res.model_used,
            execution_time_ms=execution_time_ms,
        )

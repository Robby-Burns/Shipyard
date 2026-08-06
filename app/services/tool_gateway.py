from typing import Any, Dict, Optional
import time

from sqlalchemy.ext.asyncio import AsyncSession
import structlog

from app.database.models.tool_log import ToolExecutionLog
from app.schemas.tool_gateway import (
    ToolExecutionRequest,
    ToolExecutionResponse,
    ToolName,
)

logger = structlog.get_logger()


class ToolGatewayService:

    def __init__(self, db: AsyncSession):
        self.db = db

    async def execute(
        self, request: ToolExecutionRequest, request_id: Optional[str] = None
    ) -> ToolExecutionResponse:
        start_time = time.time()

        # Execute tool capability (using mock handler for development/testing)
        try:
            result_payload = await self._dispatch_tool_action(
                request.tool, request.action, request.payload
            )
            is_success = True
            error_message = None
            status_code = 200
        except Exception as exc:
            logger.error(
                "tool_execution_failed",
                tool=request.tool,
                action=request.action,
                error=str(exc),
            )
            result_payload = {}
            is_success = False
            error_message = str(exc)
            status_code = 500

        execution_time_ms = round((time.time() - start_time) * 1000, 2)

        # Record mandatory audit record in tool_execution_logs
        tool_log = ToolExecutionLog(
            tool_name=request.tool.value,
            action=request.action,
            payload=request.payload,
            response=result_payload,
            status_code=status_code,
            is_success=is_success,
            error_message=error_message,
            execution_time_ms=execution_time_ms,
            request_id=request_id,
        )
        self.db.add(tool_log)
        await self.db.commit()

        return ToolExecutionResponse(
            tool=request.tool,
            action=request.action,
            status_code=status_code,
            is_success=is_success,
            response=result_payload,
            error_message=error_message,
            execution_time_ms=execution_time_ms,
        )

    async def _dispatch_tool_action(
        self, tool: ToolName, action: str, payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Dispatch action to external tool SDK or return mock response."""
        # For Phase 2, mock implementation guarantees safety and testability
        return {
            "executed": True,
            "tool": tool.value,
            "action": action,
            "details": (
                f"Successfully executed action '{action}' on tool '{tool.value}'"
            ),
        }

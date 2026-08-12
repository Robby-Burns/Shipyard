import re
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.agent import AgentExecutionRequest, AgentExecutionResponse, DisciplineRole
from app.schemas.model_router import Capability
from app.services.agents.base import BaseAgent


class ReviewerAgent(BaseAgent):

    def __init__(self, db: AsyncSession):
        super().__init__(
            role=DisciplineRole.REVIEWER,
            capability=Capability.CODE_REVIEW,
            db=db,
        )

    def get_system_prompt(self) -> str:
        return (
            "You are the Reviewer for the Shipyard Engineering Organization.\n"
            "Mission: Evaluate code changes for security, reliability, maintainability, and architectural compliance.\n"
            "Responsibilities:\n"
            "- Inspect code for vulnerabilities, edge cases, and performance anti-patterns\n"
            "- Ensure alignment with Shared Knowledge guidelines\n"
            "- Require deterministic behavior and adequate error handling\n"
            "- Reject code that introduces unnecessary complexity.\n\n"
            "Formatting Constraints:\n"
            "You must output your decision tag on a separate line at the end of your review:\n"
            "- For approval: <review status=\"approved\"></review>\n"
            "- For changes requested: <review status=\"request_changes\" reason=\"detailed explanation of changes needed\"></review>\n"
            "Strictly output this XML tag so the system can parse your decision."
        )

    async def run(
        self, request: AgentExecutionRequest, request_id: Optional[str] = None
    ) -> AgentExecutionResponse:
        # Run base agent logic
        response = await super().run(request, request_id)

        if response.status == "success":
            content = response.output_text
            
            from app.utils.tag_parser import parse_agent_decision
            from app.config.settings import settings

            # Parse review status
            result = parse_agent_decision(content, "review")
            status = result.get("status")
            reason = result.get("reason")

            if status:
                status = status.lower()
            elif settings.openrouter_api_key != "mock-key":
                raise ValueError("Reviewer output was missing required structural <review> tags or JSON fields.")
            else:
                status = "approved"

            response.artifacts = {
                "status": status,
                "reason": reason if reason else "No specific rejection reason provided."
            }

        return response

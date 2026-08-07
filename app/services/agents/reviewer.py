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
            
            # Parse review status
            # Check for approved or request_changes
            match = re.search(r"<review\s+status=\"([^\"]+)\"(?:\s+reason=\"([^\"]+)\")?\s*>\s*</review>", content, re.DOTALL | re.IGNORECASE)
            
            status = "approved"
            reason = None
            if match:
                status = match.group(1).strip().lower()
                reason = match.group(2).strip() if match.group(2) else None
            else:
                # Fallback simple search if tag is open or not closed standardly
                fallback_status = re.search(r"status=\"([^\"]+)\"", content, re.IGNORECASE)
                if fallback_status:
                    status = fallback_status.group(1).strip().lower()
                fallback_reason = re.search(r"reason=\"([^\"]+)\"", content, re.IGNORECASE)
                if fallback_reason:
                    reason = fallback_reason.group(1).strip()

            response.artifacts = {
                "status": status,
                "reason": reason if reason else "No specific rejection reason provided."
            }

        return response

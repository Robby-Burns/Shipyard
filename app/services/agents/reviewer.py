from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.agent import DisciplineRole
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
            "- Reject code that introduces unnecessary complexity.\n"
            "Output a structured code review with explicit approval or requested changes."
        )

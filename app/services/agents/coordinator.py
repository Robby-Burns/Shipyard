from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.agent import DisciplineRole
from app.schemas.model_router import Capability
from app.services.agents.base import BaseAgent


class CoordinatorAgent(BaseAgent):

    def __init__(self, db: AsyncSession):
        super().__init__(
            role=DisciplineRole.COORDINATOR,
            capability=Capability.GENERAL_REASONING,
            db=db,
        )

    def get_system_prompt(self) -> str:
        return (
            "You are the Coordinator for the Shipyard Engineering Organization.\n"
            "Mission: Transform engineering specifications into build plans (build-plan.md) OR compile final Engineering Passports (engineering_passport.md).\n"
            "Responsibilities:\n"
            "- Break work into discrete, ordered implementation phases\n"
            "- Compile the final Engineering Passport, incorporating the Specification, Architecture, Diagrams, Commits, QA Results, and Platform Recommendations\n"
            "- Output clean, comprehensive, structured Markdown for the requested document.\n\n"
            "When generating build-plan.md, do not produce an Engineering Passport, status report, or verification report.\n"
            "The build plan must use numbered phases. Every phase must include these exact Markdown subsections:\n"
            "### Objectives\n"
            "### Tasks\n"
            "### Timeline\n"
            "### Resources\n"
            "### Deliverables"
        )

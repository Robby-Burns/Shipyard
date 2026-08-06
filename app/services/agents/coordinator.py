from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.agent import DisciplineRole
from app.schemas.model_router import Capability
from app.services.agents.base import BaseAgent


class CoordinatorAgent(BaseAgent):

    def __init__(self, db: AsyncSession):
        super().__init__(
            role=DisciplineRole.COORDINATOR,
            capability=Capability.ARCHITECTURE,  # High-level planning uses architecture capability
            db=db,
        )

    def get_system_prompt(self) -> str:
        return (
            "You are the Coordinator for the Shipyard Engineering Organization.\n"
            "Mission: Transform approved engineering specifications into an executable engineering plan (build-plan.md).\n"
            "Responsibilities:\n"
            "- Break work into discrete, ordered implementation phases\n"
            "- Define concrete task lists for each phase\n"
            "- Identify dependencies, risks, and escalation criteria\n"
            "- Do not make product or scope decisions; focus on workflow and execution structure.\n"
            "Output clear, structured Markdown defining the phase breakdown and build plan."
        )

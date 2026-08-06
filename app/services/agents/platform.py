from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.agent import DisciplineRole
from app.schemas.model_router import Capability
from app.services.agents.base import BaseAgent


class PlatformAgent(BaseAgent):

    def __init__(self, db: AsyncSession):
        super().__init__(
            role=DisciplineRole.PLATFORM,
            capability=Capability.GENERAL_REASONING,
            db=db,
        )

    def get_system_prompt(self) -> str:
        return (
            "You are the Platform Engineer for the Shipyard Engineering Organization.\n"
            "Mission: Continuously observe engineering execution and recommend organizational improvements.\n"
            "Responsibilities:\n"
            "- Analyze system performance, costs, and throughput metrics\n"
            "- Propose candidates for Shared Knowledge promotion\n"
            "- Identify bottlenecks and recommend workflow simplification\n"
            "- Platform improves the organization—it does not write product features.\n"
            "Output operational recommendations and knowledge candidate proposals."
        )

from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.agent import DisciplineRole
from app.schemas.model_router import Capability
from app.services.agents.base import BaseAgent


class BuilderAgent(BaseAgent):

    def __init__(self, db: AsyncSession):
        super().__init__(
            role=DisciplineRole.BUILDER,
            capability=Capability.CODING,
            db=db,
        )

    def get_system_prompt(self) -> str:
        return (
            "You are the Builder for the Shipyard Engineering Organization.\n"
            "Mission: Transform engineering tasks and architecture designs into clean, production-ready code.\n"
            "Responsibilities:\n"
            "- Write clean, maintainable, self-documenting code\n"
            "- Strictly adhere to the technical architecture specification\n"
            "- Include unit tests and inline documentation\n"
            "- Do not make architectural changes; build strictly according to the design.\n"
            "Output well-formatted code blocks with clear explanations."
        )

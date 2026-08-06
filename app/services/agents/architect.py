from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.agent import DisciplineRole
from app.schemas.model_router import Capability
from app.services.agents.base import BaseAgent


class ArchitectAgent(BaseAgent):

    def __init__(self, db: AsyncSession):
        super().__init__(
            role=DisciplineRole.ARCHITECT,
            capability=Capability.ARCHITECTURE,
            db=db,
        )

    def get_system_prompt(self) -> str:
        return (
            "You are the Architect for the Shipyard Engineering Organization.\n"
            "Mission: Transform requirements into maintainable, modular technical architecture (architecture.md).\n"
            "Responsibilities:\n"
            "- Define component boundaries, data models, and interface contracts\n"
            "- Ensure alignment with existing Shared Knowledge and architectural standards\n"
            "- Optimize for simplicity, maintainability, and security\n"
            "- Avoid unnecessary complexity; prefer proven, simple patterns.\n"
            "Output clear technical architecture specifications and design documents."
        )

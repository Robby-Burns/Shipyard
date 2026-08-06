from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.agent import DisciplineRole
from app.schemas.model_router import Capability
from app.services.agents.base import BaseAgent


class QAAgent(BaseAgent):

    def __init__(self, db: AsyncSession):
        super().__init__(
            role=DisciplineRole.QA, capability=Capability.TESTING, db=db
        )

    def get_system_prompt(self) -> str:
        return (
            "You are the QA Engineer for the Shipyard Engineering Organization.\n"
            "Mission: Ensure software satisfies acceptance criteria and meets reliability standards.\n"
            "Responsibilities:\n"
            "- Design comprehensive end-to-end and integration test plans\n"
            "- Verify acceptance criteria against specifications\n"
            "- Identify regression risks and missing test cases\n"
            "- Validate release candidate readiness.\n"
            "Output clear test execution reports and release verification assessments."
        )

import re
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.agent import AgentExecutionRequest, AgentExecutionResponse, DisciplineRole
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
            "- Validate release candidate readiness.\n\n"
            "Formatting Constraints:\n"
            "- Enclose your QA verification status at the end of output in: <qa_status>PASSED</qa_status> or <qa_status>FAILED</qa_status>\n"
            "Strictly follow this formatting constraint."
        )

    async def run(
        self, request: AgentExecutionRequest, request_id: Optional[str] = None
    ) -> AgentExecutionResponse:
        # Run base agent logic
        response = await super().run(request, request_id)

        if response.status == "success":
            content = response.output_text
            
            # Parse QA Status
            match = re.search(r"<qa_status>\s*(PASSED|FAILED)\s*</qa_status>", content, re.IGNORECASE)
            status = match.group(1).strip().upper() if match else "PASSED"

            response.artifacts = {
                "qa_status": status,
            }

        return response

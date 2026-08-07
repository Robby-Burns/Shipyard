import re
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.agent import AgentExecutionRequest, AgentExecutionResponse, DisciplineRole
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
            "- Platform improves the organization—it does not write product features.\n\n"
            "Formatting Constraints:\n"
            "- Enclose operational recommendations in: <recommendations>\n...\n</recommendations>\n"
            "- Enclose proposals for Shared Knowledge in: <knowledge_candidate>\n...\n</knowledge_candidate>\n"
            "Strictly output these XML tags so the system can parse your output."
        )

    async def run(
        self, request: AgentExecutionRequest, request_id: Optional[str] = None
    ) -> AgentExecutionResponse:
        # Run base agent logic
        response = await super().run(request, request_id)

        if response.status == "success":
            content = response.output_text
            
            # Parse recommendations
            rec_match = re.search(r"<recommendations>\s*(.*?)\s*</recommendations>", content, re.DOTALL | re.IGNORECASE)
            recommendations = rec_match.group(1).strip() if rec_match else content

            # Parse knowledge candidate
            knowledge_match = re.search(r"<knowledge_candidate>\s*(.*?)\s*</knowledge_candidate>", content, re.DOTALL | re.IGNORECASE)
            knowledge_candidate = knowledge_match.group(1).strip() if knowledge_match else None

            response.artifacts = {
                "recommendations": recommendations,
                "knowledge_candidate": knowledge_candidate,
            }

        return response

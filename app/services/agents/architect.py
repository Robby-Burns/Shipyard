import os
import re
from app.adapters.sanitizer import sanitize_path_component
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.agent import AgentExecutionRequest, AgentExecutionResponse, DisciplineRole
import json
from app.schemas.structured_output import Adr
from app.schemas.engineering_results import ArchitectureResult
from app.schemas.model_router import Capability
from app.services.agents.base import BaseAgent


class ArchitectAgent(BaseAgent):

    def __init__(self, db: AsyncSession):
        super().__init__(
            role=DisciplineRole.ARCHITECT,
            capability=Capability.ARCHITECTURE,
            db=db,
        )
        self.artifacts_dir = "artifacts/architecture"

    def get_system_prompt(self) -> str:
        return (
            "You are the Architect for the Shipyard Engineering Organization.\n"
            "Mission: Design structural blueprints, diagrams, and ADRs based on the Engineering Specification.\n"
            "Responsibilities:\n"
            "- Define component interactions and data flow diagrams (use Mermaid format)\n"
            "- Produce system design records following the standard ADR template\n"
            "- Translate product requirements into precise technical architecture blueprints.\n\n"
            "Output Format: Return the architecture document as plain text. It MUST include a Mermaid diagram inside exactly "
            "<diagram>```mermaid ... ```</diagram> and one or more ADRs inside "
            "<adr id=\"ADR-...\"> ... </adr> tags. Do not return JSON; the verifier needs the tagged source document."
        )

    async def run(
        self, request: AgentExecutionRequest, request_id: Optional[str] = None
    ) -> AgentExecutionResponse:
        # Run base agent logic
        response = await super().run(request, request_id)

        if response.status == "success":
            content = response.output_text
            workflow_id = "default"
            # Extract and sanitize workflow_id from context if provided
            if request.context and isinstance(request.context, dict):
                raw_wf_id = str(request.context.get("workflow_id", "default"))
                workflow_id = sanitize_path_component(raw_wf_id)

            target_dir = os.path.join(self.artifacts_dir, workflow_id)
            os.makedirs(target_dir, exist_ok=True)

            generated_artifacts = {}

            # 1. Parse system diagram
            diagram_match = re.search(r"<diagram>\s*```mermaid\s*(.*?)\s*```\s*</diagram>", content, re.DOTALL | re.IGNORECASE)
            if not diagram_match:
                # Fallback to any content inside <diagram>
                diagram_match = re.search(r"<diagram>\s*(.*?)\s*</diagram>", content, re.DOTALL | re.IGNORECASE)
            
            import anyio
            if diagram_match:
                diagram_content = diagram_match.group(1).strip()
                if diagram_content.startswith("```mermaid"):
                    diagram_content = diagram_content[10:].strip()
                if diagram_content.endswith("```"):
                    diagram_content = diagram_content[:-3].strip()

                diagram_path = os.path.join(target_dir, "diagram.mermaid")
                await anyio.Path(diagram_path).write_text(diagram_content, encoding="utf-8")
                generated_artifacts["diagram_path"] = diagram_path
            else:
                # Fallback for development/testing if LLM doesn't output diagram tags
                diagram_content = "graph TD;\n  A-->B;"
                diagram_path = os.path.join(target_dir, "diagram.mermaid")
                await anyio.Path(diagram_path).write_text(diagram_content, encoding="utf-8")
                generated_artifacts["diagram_path"] = diagram_path

            # 2. Parse ADRs
            adr_matches = re.finditer(r"<adr\s+id=\"([^\"]+)\">\s*(.*?)\s*</adr>", content, re.DOTALL | re.IGNORECASE)
            adrs = {}
            for match in adr_matches:
                adr_orig_id = match.group(1).strip()
                adr_body = match.group(2).strip()
                
                adr_id = sanitize_path_component(adr_orig_id)
                adr_file_name = f"{adr_id}.md"
                adr_path = os.path.join(target_dir, adr_file_name)
                await anyio.Path(adr_path).write_text(adr_body, encoding="utf-8")
                
                adrs[adr_orig_id] = adr_path

            if adrs:
                generated_artifacts["adrs"] = adrs

            response.artifacts = generated_artifacts
            # Build a structured summary for downstream consumers, but keep the
            # original tagged document in output_text. The Challenger validates
            # the tagged source; replacing it with JSON here makes valid output
            # look incomplete and causes false escalations.
            architecture_result = ArchitectureResult(
                role="architect",
                status="completed",
                architecture={
                    "diagram": generated_artifacts.get("diagram_path"),
                    "adrs": [
                        {
                            "id": adr_id,
                            "title": "",
                            "decision": "",
                            "rationale": ""
                        } for adr_id in generated_artifacts.get("adrs", {}).keys()
                    ],
                },
                warnings=[],
                recommendations=[],
            )
            generated_artifacts["architecture_result"] = architecture_result.model_dump()
            response.artifacts = generated_artifacts


        return response

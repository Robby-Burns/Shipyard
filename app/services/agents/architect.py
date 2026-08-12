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

            from app.utils.tag_parser import extract_tags
            from app.config.settings import settings
            import anyio

            # 1. Parse system diagram
            diagrams = extract_tags(content, "diagram")
            if diagrams:
                diagram_content = diagrams[0]["content"]
                diagram_path = os.path.join(target_dir, "diagram.mermaid")
                await anyio.Path(diagram_path).write_text(diagram_content, encoding="utf-8")
                generated_artifacts["diagram_path"] = diagram_path
            else:
                if settings.openrouter_api_key == "mock-key":
                    # Fallback for development/testing if LLM doesn't output diagram tags in mock mode
                    diagram_content = "graph TD;\n  A-->B;"
                    diagram_path = os.path.join(target_dir, "diagram.mermaid")
                    await anyio.Path(diagram_path).write_text(diagram_content, encoding="utf-8")
                    generated_artifacts["diagram_path"] = diagram_path
                else:
                    raise ValueError("Architect output was missing required structural <diagram> tags.")

            # 2. Parse ADRs
            adr_list = extract_tags(content, "adr")
            adrs = {}
            for item in adr_list:
                adr_orig_id = item["attributes"].get("id", "").strip()
                if not adr_orig_id:
                    # Try fallback to extract id from heading inside content if attribute missing
                    header_match = re.search(r"^#\s+(ADR-\d+)", item["content"], re.MULTILINE)
                    adr_orig_id = header_match.group(1).strip() if header_match else f"ADR-{hash(item['content']) % 1000:03d}"
                
                adr_body = item["content"]
                adr_id = sanitize_path_component(adr_orig_id)
                adr_file_name = f"{adr_id}.md"
                adr_path = os.path.join(target_dir, adr_file_name)
                await anyio.Path(adr_path).write_text(adr_body, encoding="utf-8")
                adrs[adr_orig_id] = adr_path

            if adrs:
                generated_artifacts["adrs"] = adrs
            elif settings.openrouter_api_key != "mock-key":
                raise ValueError("Architect output was missing required structural <adr> tags.")

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

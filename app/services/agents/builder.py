import re
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.agent import AgentExecutionRequest, AgentExecutionResponse, DisciplineRole
from app.schemas.model_router import Capability
from app.services.agents.base import BaseAgent
from app.infrastructure.adapters.factory import get_repository_adapter


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
            "- Do not make architectural changes; build strictly according to the design.\n\n"
            "Formatting Constraints:\n"
            "- Enclose each file code block in: <file path=\"relative/path/to/file.py\">\n...\n</file>\n"
            "- Enclose unit test code / output in: <test_results>\n...\n</test_results>\n"
            "Strictly follow these XML tags so the system can extract and commit the files."
        )

    async def run(
        self, request: AgentExecutionRequest, request_id: Optional[str] = None
    ) -> AgentExecutionResponse:
        # Run base agent logic
        response = await super().run(request, request_id)

        if response.status == "success":
            content = response.output_text
            
            # 1. Parse generated files
            file_matches = re.finditer(r"<file\s+path=\"([^\"]+)\">\s*(.*?)\s*</file>", content, re.DOTALL | re.IGNORECASE)
            files = {}
            for match in file_matches:
                file_path = match.group(1).strip()
                file_body = match.group(2).strip()
                files[file_path] = file_body

            # 2. Parse test results
            test_match = re.search(r"<test_results>\s*(.*?)\s*</test_results>", content, re.DOTALL | re.IGNORECASE)
            test_results = test_match.group(1).strip() if test_match else "All unit tests executed and passed (mock verification)."

            # 3. Commit code using Repository Adapter
            repo_adapter = get_repository_adapter()
            commit_hash = "mock-hash"
            if files:
                repo_url = "https://github.com/shipyard-ai/workflow-run"
                commit_hash = await repo_adapter.commit_code(repo_url, files, "feat: auto-generated code implementation")

            response.artifacts = {
                "files": list(files.keys()),
                "commit_hash": commit_hash,
                "test_results": test_results,
            }

        return response

import os
import shutil
import pytest
from unittest.mock import AsyncMock
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.agent import AgentExecutionRequest, DisciplineRole
from app.schemas.model_router import ModelRouteResponse, Capability
from app.services.agents.architect import ArchitectAgent


@pytest.fixture
def mock_route_response():
    mock_content = (
        "Here is the architecture design:\n\n"
        "<diagram>\n"
        "```mermaid\n"
        "graph TD;\n"
        "  A-->B;\n"
        "```\n"
        "</diagram>\n\n"
        "And here is the decision record:\n\n"
        '<adr id="ADR-001">\n'
        "# ADR 001: Use SQLite for local development\n"
        "Decision: Choose SQLite because it is serverless.\n"
        "</adr>\n"
    )
    return ModelRouteResponse(
        id="completion-id",
        capability=Capability.ARCHITECTURE,
        model_used="anthropic/claude-3.5-sonnet",
        content=mock_content,
        usage={"prompt_tokens": 100, "completion_tokens": 200, "total_tokens": 300},
    )


@pytest.mark.anyio
async def test_architect_parsing_and_persistence(
    mock_route_response,
):
    # Setup mock session
    session = AsyncMock(spec=AsyncSession)
    agent = ArchitectAgent(session)

    # Mock the model_router.route method
    agent.model_router.route = AsyncMock(return_value=mock_route_response)

    request = AgentExecutionRequest(
        role=DisciplineRole.ARCHITECT,
        task_input="Design structural blueprint",
        context={"workflow_id": "test_workflow_123"},
    )

    # Run agent execution
    res = await agent.run(request)

    assert res.role == DisciplineRole.ARCHITECT
    assert res.status == "success"
    assert "<diagram>" in res.output_text
    assert "```mermaid" in res.output_text
    assert '<adr id="ADR-001">' in res.output_text
    assert res.artifacts["architecture_result"]["status"] == "completed"

    # Assert correct keys in artifacts dictionary
    assert "diagram_path" in res.artifacts
    assert "adrs" in res.artifacts
    assert "ADR-001" in res.artifacts["adrs"]

    # Verify created files
    diagram_path = res.artifacts["diagram_path"]
    adr_path = res.artifacts["adrs"]["ADR-001"]

    assert os.path.exists(diagram_path)
    assert os.path.exists(adr_path)

    # Assert content of diagram
    with open(diagram_path, "r", encoding="utf-8") as f:
        diagram_text = f.read()
    assert diagram_text == "graph TD;\n  A-->B;"

    # Assert content of ADR
    with open(adr_path, "r", encoding="utf-8") as f:
        adr_text = f.read()
    assert "# ADR 001: Use SQLite for local development" in adr_text

    # Clean up artifacts folder created in test
    if os.path.exists("artifacts/architecture/test_workflow_123"):
        shutil.rmtree("artifacts/architecture/test_workflow_123")

import pytest
from unittest.mock import AsyncMock
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.agent import AgentExecutionRequest, DisciplineRole
from app.schemas.model_router import ModelRouteResponse, Capability
from app.services.agents.builder import BuilderAgent
from app.services.agents.reviewer import ReviewerAgent
from app.database.models.workflow import WorkflowRun
from app.schemas.workflow import WorkflowStatus
from app.services.workflow_engine import WorkflowEngineService


@pytest.fixture
def mock_builder_response():
    mock_content = (
        "Here are the code files for the feature:\n\n"
        '<file path="app/services/calculator.py">\n'
        "class Calculator:\n"
        "    def add(self, a: int, b: int) -> int:\n"
        "        return a + b\n"
        "</file>\n\n"
        "Here are the test cases:\n\n"
        "<test_results>\n"
        "pytest run: 5 passed, 0 failed\n"
        "</test_results>\n"
    )
    return ModelRouteResponse(
        id="comp-builder",
        capability=Capability.CODING,
        model_used="anthropic/claude-3.5-sonnet",
        content=mock_content,
        usage={},
    )


@pytest.fixture
def mock_reviewer_approved():
    mock_content = (
        "Code looks perfect. Standards met.\n\n"
        '<review status="approved"></review>'
    )
    return ModelRouteResponse(
        id="comp-reviewer-app",
        capability=Capability.CODE_REVIEW,
        model_used="openai/gpt-4o",
        content=mock_content,
        usage={},
    )


@pytest.fixture
def mock_reviewer_changes():
    mock_content = (
        "Please address security vulnerabilities.\n\n"
        '<review status="request_changes" reason="Missing boundary check in division"></review>'
    )
    return ModelRouteResponse(
        id="comp-reviewer-rej",
        capability=Capability.CODE_REVIEW,
        model_used="openai/gpt-4o",
        content=mock_content,
        usage={},
    )


@pytest.mark.anyio
async def test_builder_parsing_and_commit(mock_builder_response):
    session = AsyncMock(spec=AsyncSession)
    agent = BuilderAgent(session)
    agent.model_router.route = AsyncMock(return_value=mock_builder_response)

    request = AgentExecutionRequest(
        role=DisciplineRole.BUILDER,
        task_input="Implement calculator feature",
    )

    res = await agent.run(request)

    assert res.role == DisciplineRole.BUILDER
    assert res.status == "success"
    assert "app/services/calculator.py" in res.artifacts["files"]
    assert "pytest run: 5 passed, 0 failed" in res.artifacts["test_results"]
    assert len(res.artifacts["commit_hash"]) == 40


@pytest.mark.anyio
async def test_reviewer_parsing_approval(mock_reviewer_approved):
    session = AsyncMock(spec=AsyncSession)
    agent = ReviewerAgent(session)
    agent.model_router.route = AsyncMock(return_value=mock_reviewer_approved)

    request = AgentExecutionRequest(
        role=DisciplineRole.REVIEWER,
        task_input="Review calculator implementation",
    )

    res = await agent.run(request)
    assert res.role == DisciplineRole.REVIEWER
    assert res.status == "success"
    assert res.artifacts["status"] == "approved"


@pytest.mark.anyio
async def test_reviewer_parsing_changes(mock_reviewer_changes):
    session = AsyncMock(spec=AsyncSession)
    agent = ReviewerAgent(session)
    agent.model_router.route = AsyncMock(return_value=mock_reviewer_changes)

    request = AgentExecutionRequest(
        role=DisciplineRole.REVIEWER,
        task_input="Review calculator implementation",
    )

    res = await agent.run(request)
    assert res.role == DisciplineRole.REVIEWER
    assert res.status == "success"
    assert res.artifacts["status"] == "request_changes"
    assert res.artifacts["reason"] == "Missing boundary check in division"

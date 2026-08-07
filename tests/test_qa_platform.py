import pytest
from unittest.mock import AsyncMock
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.agent import AgentExecutionRequest, DisciplineRole
from app.schemas.model_router import ModelRouteResponse, Capability
from app.services.agents.qa import QAAgent
from app.services.agents.platform import PlatformAgent
from app.database.models.workflow import WorkflowRun
from app.schemas.workflow import WorkflowStatus
from app.services.workflow_engine import WorkflowEngineService


@pytest.fixture
def mock_qa_passed():
    mock_content = (
        "All integration test suites executed successfully.\n"
        "<qa_status>PASSED</qa_status>\n"
    )
    return ModelRouteResponse(
        id="comp-qa-pass",
        capability=Capability.TESTING,
        model_used="openai/gpt-4o-mini",
        content=mock_content,
        usage={},
    )


@pytest.fixture
def mock_qa_failed():
    mock_content = (
        "Functional test failures in payment capture routing.\n"
        "<qa_status>FAILED</qa_status>\n"
    )
    return ModelRouteResponse(
        id="comp-qa-fail",
        capability=Capability.TESTING,
        model_used="openai/gpt-4o-mini",
        content=mock_content,
        usage={},
    )


@pytest.fixture
def mock_platform_response():
    mock_content = (
        "Operational recommendations:\n"
        "<recommendations>\n"
        "Reduce model router temperature for coding roles.\n"
        "</recommendations>\n\n"
        "Curated standard practice proposal:\n"
        "<knowledge_candidate>\n"
        "Always use transaction wrapper blocks for multi-statement DB ops.\n"
        "</knowledge_candidate>\n"
    )
    return ModelRouteResponse(
        id="comp-platform",
        capability=Capability.GENERAL_REASONING,
        model_used="google/gemini-2.5-flash",
        content=mock_content,
        usage={},
    )


@pytest.mark.anyio
async def test_qa_parsing_pass(mock_qa_passed):
    session = AsyncMock(spec=AsyncSession)
    agent = QAAgent(session)
    agent.model_router.route = AsyncMock(return_value=mock_qa_passed)

    request = AgentExecutionRequest(
        role=DisciplineRole.QA,
        task_input="Execute test suite",
    )

    res = await agent.run(request)
    assert res.role == DisciplineRole.QA
    assert res.status == "success"
    assert res.artifacts["qa_status"] == "PASSED"


@pytest.mark.anyio
async def test_qa_parsing_fail(mock_qa_failed):
    session = AsyncMock(spec=AsyncSession)
    agent = QAAgent(session)
    agent.model_router.route = AsyncMock(return_value=mock_qa_failed)

    request = AgentExecutionRequest(
        role=DisciplineRole.QA,
        task_input="Execute test suite",
    )

    res = await agent.run(request)
    assert res.role == DisciplineRole.QA
    assert res.status == "success"
    assert res.artifacts["qa_status"] == "FAILED"


@pytest.mark.anyio
async def test_platform_parsing(mock_platform_response):
    session = AsyncMock(spec=AsyncSession)
    agent = PlatformAgent(session)
    agent.model_router.route = AsyncMock(return_value=mock_platform_response)

    request = AgentExecutionRequest(
        role=DisciplineRole.PLATFORM,
        task_input="Analyze operational metrics",
    )

    res = await agent.run(request)
    assert res.role == DisciplineRole.PLATFORM
    assert res.status == "success"
    assert "Reduce model router temperature" in res.artifacts["recommendations"]
    assert "Always use transaction wrapper blocks" in res.artifacts["knowledge_candidate"]

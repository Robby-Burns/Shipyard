import pytest
import uuid
import httpx
from fastapi import HTTPException
from unittest.mock import AsyncMock, patch, MagicMock
from sqlalchemy.ext.asyncio import AsyncSession

from app.utils.tag_parser import extract_tags, parse_agent_decision
from app.schemas.model_router import Capability, ChatMessage, ModelRouteRequest
from app.services.model_router import ModelRouterService, OpenRouterUpstreamError
from app.services.workflow_engine import WorkflowEngineService
from app.database.models.workflow import WorkflowRun
from app.schemas.workflow import WorkflowStatus
from app.config.settings import settings
from app.api.v1.workflows import run_full_pipeline, active_runs

# --- 1. Tag Parsing Robustness Tests ---

def test_extract_tags_robustness():
    # Test spaces, quotes, casing, unclosed tags
    content = """
    <diagram   attr='val'  other="another">
    ```mermaid
    graph TD; A-->B;
    ```
    </diagram>
    <adr id=ADR-001>
    ADR Body
    </adr>
    <unclosed id="999">
    Some Content
    """
    diagrams = extract_tags(content, "diagram")
    assert len(diagrams) == 1
    assert "graph TD; A-->B;" in diagrams[0]["content"]
    assert diagrams[0]["attributes"]["attr"] == "val"
    assert diagrams[0]["attributes"]["other"] == "another"

    adrs = extract_tags(content, "adr")
    assert len(adrs) == 1
    assert adrs[0]["content"] == "ADR Body"
    assert adrs[0]["attributes"]["id"] == "ADR-001"

    unclosed = extract_tags(content, "unclosed")
    assert len(unclosed) == 1
    assert "Some Content" in unclosed[0]["content"]
    assert unclosed[0]["attributes"]["id"] == "999"


def test_parse_agent_decision_hybrid():
    # JSON input
    json_content = '{"status": "approved", "reason": "Looks good"}'
    res = parse_agent_decision(json_content, "review")
    assert res["status"] == "approved"
    assert res["reason"] == "Looks good"
    assert res["format"] == "json"

    # JSON input wrapped in markdown code fence
    fence_json = "```json\n{\n  \"status\": \"request_changes\",\n  \"reason\": \"fix naming\"\n}\n```"
    res = parse_agent_decision(fence_json, "review")
    assert res["status"] == "request_changes"
    assert res["reason"] == "fix naming"
    assert res["format"] == "json"

    # XML fallback
    xml_content = '<review status="approved" reason="good code"></review>'
    res = parse_agent_decision(xml_content, "review")
    assert res["status"] == "approved"
    assert res["reason"] == "good code"
    assert res["format"] == "xml"


# --- 2. Concurrency Locking / HTTP 409 Conflict Tests ---

@pytest.mark.asyncio
async def test_concurrency_double_trigger():
    workflow_id = uuid.uuid4()
    active_runs.add(workflow_id)
    
    request = MagicMock()
    request.state = MagicMock()
    request.state.request_id = "req-123"
    
    background_tasks = MagicMock()
    db = MagicMock(spec=AsyncSession)
    
    # Try triggering running workflow. It should raise 409 Conflict
    with pytest.raises(HTTPException) as exc_info:
        await run_full_pipeline(
            workflow_id=workflow_id,
            request=request,
            background_tasks=background_tasks,
            db=db,
            user={"sub": "user_123"}
        )
    assert exc_info.value.status_code == 409
    assert "Workflow run is already active" in exc_info.value.detail
    
    active_runs.discard(workflow_id)


# --- 3. Structured Outputs Config / Schema Injection Tests ---

def test_structured_outputs_payload_injection():
    router = ModelRouterService(db=MagicMock())
    request = ModelRouteRequest(
        capability=Capability.CODE_REVIEW,
        messages=[ChatMessage(role="system", content="You are a reviewer.")],
        temperature=0.7,
        max_tokens=100
    )
    
    # Test configured model
    model_name = "openai/gpt-4o"
    candidates = [{"model_id": "openai/gpt-4o", "supported_parameters": ["temperature", "max_tokens"]}]
    candidate = candidates[0]
    
    payload = router._build_upstream_payload(request, model_name, candidates, candidate)
    
    assert payload["response_format"] == {"type": "json_object"}
    # Verify JSON instructions injected into system prompt
    assert "You MUST return a JSON object" in payload["messages"][0]["content"]
    assert "request_changes" in payload["messages"][0]["content"]


# --- 4. Retries and Native API Bypass Failover Tests ---

@pytest.mark.asyncio
async def test_transient_retries_and_bypass():
    router = ModelRouterService(db=MagicMock())
    router.activity_log_service = AsyncMock()
    router._select_candidates = AsyncMock(return_value=[{"model_id": "openai/gpt-4o-mini"}])
    router._record_outcome = AsyncMock()
    
    request = ModelRouteRequest(
        capability=Capability.CODE_REVIEW,
        messages=[ChatMessage(role="system", content="Test")],
    )

    # Mock settings to enable bypass
    orig_or_key = settings.openrouter_api_key
    settings.openrouter_api_key = "temp-openrouter-key"
    settings.openai_api_key = "sk-direct-openai-key"
    
    try:
        # We mock HTTP failures on OpenRouter (e.g. 502 Bad Gateway) and check that it bypasses
        # We mock httpx.AsyncClient.post to raise connect error or status 502, then succeed on OpenAI URL
        async def mock_post(url, **kwargs):
            mock_response = MagicMock()
            if "openrouter.ai" in url:
                # OpenRouter is down
                mock_response.status_code = 502
                mock_response.is_error = True
                return mock_response
            elif "api.openai.com" in url:
                # Direct OpenAI succeeds
                mock_response.status_code = 200
                mock_response.is_error = False
                mock_response.json = MagicMock(return_value={
                    "id": "direct-openai-id",
                    "choices": [{
                        "message": {"content": "{\"status\": \"approved\"}"},
                        "finish_reason": "stop"
                    }],
                    "model": "gpt-4o-mini",
                    "usage": {"prompt_tokens": 5, "completion_tokens": 5}
                })
                return mock_response
            
        with patch("httpx.AsyncClient.post", side_effect=mock_post):
            response = await router.route(request, request_id="req-direct")
            
            assert response.id == "direct-openai-id"
            assert response.model_used == "native/gpt-4o-mini"
            assert "approved" in response.content
            assert response.usage.get("native_bypass") is True
    finally:
        settings.openrouter_api_key = orig_or_key


# --- 5. Data Starvation & Step Safety Failure Tests ---

@pytest.mark.asyncio
async def test_step_failure_transition():
    db = MagicMock(spec=AsyncSession)
    engine = WorkflowEngineService(db)
    
    # Mock db.execute to return a mock workflow
    mock_wf = WorkflowRun(
        id=uuid.uuid4(),
        status=WorkflowStatus.PLANNING,
        current_step="coordinator_planning",
        specification="Original Spec Requirements",
        artifacts={}
    )
    
    db.execute = AsyncMock(return_value=MagicMock(scalar_one_or_none=MagicMock(return_value=mock_wf)))
    db.commit = AsyncMock()
    
    # Trigger a step failure
    await engine._handle_step_failure(mock_wf.id, ValueError("Tag parsing error example"), "req-fail")
    
    # Verify it transitioned status to FAILED with error message
    assert mock_wf.status == WorkflowStatus.FAILED
    assert "Tag parsing error example" in mock_wf.error_message
    db.commit.assert_called()

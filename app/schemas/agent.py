from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class DisciplineRole(str, Enum):
    COORDINATOR = "coordinator"
    ARCHITECT = "architect"
    BUILDER = "builder"
    REVIEWER = "reviewer"
    QA = "qa"
    PLATFORM = "platform"


class AgentExecutionRequest(BaseModel):
    role: Optional[DisciplineRole] = Field(
        None,
        description="[Deprecated] Ignored. Will be removed in v2.",
    )
    task_input: str = Field(
        ...,
        max_length=2000,
        description="The task instruction for the agent to execute. Max 2000 characters.",
    )
    context: Optional[Dict[str, Any]] = Field(default_factory=dict)
    shared_knowledge_ids: Optional[List[str]] = None


class AgentExecutionResponse(BaseModel):
    role: DisciplineRole
    status: str  # "success", "failed", "escalated"
    output_text: str
    artifacts: Dict[str, Any] = Field(default_factory=dict)
    model_used: str
    execution_time_ms: float = 0.0

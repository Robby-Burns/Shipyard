from enum import Enum
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field


class ToolName(str, Enum):
    GITHUB = "github"
    RAILWAY = "railway"
    DOCKER = "docker"
    SUPABASE = "supabase"
    MOCK = "mock"


class ToolExecutionRequest(BaseModel):
    tool: ToolName
    action: str = Field(..., max_length=100)
    payload: Dict[str, Any] = Field(default_factory=dict)


class ToolExecutionResponse(BaseModel):
    tool: ToolName
    action: str
    status_code: int = 200
    is_success: bool = True
    response: Dict[str, Any] = Field(default_factory=dict)
    error_message: Optional[str] = None
    execution_time_ms: float = 0.0

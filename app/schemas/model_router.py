from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class Capability(str, Enum):
    ARCHITECTURE = "architecture"
    CODING = "coding"
    CODE_REVIEW = "code_review"
    TESTING = "testing"
    GENERAL_REASONING = "general_reasoning"


class ChatMessage(BaseModel):
    role: str  # "system", "user", "assistant"
    content: str


class ModelRouteRequest(BaseModel):
    capability: Capability
    messages: List[ChatMessage] = Field(..., min_length=1)
    temperature: Optional[float] = 0.2
    max_tokens: Optional[int] = 2000
    metadata: Optional[Dict[str, Any]] = None


class ModelRouteResponse(BaseModel):
    id: str
    capability: Capability
    model_used: str
    content: str
    usage: Dict[str, Any] = Field(default_factory=dict)

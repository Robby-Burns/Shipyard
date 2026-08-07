from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ConsoleOverviewResponse(BaseModel):
    system_status: str = "operational"
    active_workflow_count: int = 0
    pending_approval_count: int = 0
    recent_error_count: int = 0
    candidate_knowledge_count: int = 0
    recent_activities: List[Dict[str, Any]] = Field(default_factory=list)
    pending_approvals: List[Dict[str, Any]] = Field(default_factory=list)

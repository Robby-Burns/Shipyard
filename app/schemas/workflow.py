from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional
import uuid

from pydantic import BaseModel, ConfigDict


class WorkflowStatus(str, Enum):
    CREATED = "created"
    PLANNING = "planning"  # Coordinator
    DESIGNING = "designing"  # Architect
    BUILDING = "building"  # Builder
    REVIEWING = "reviewing"  # Reviewer
    TESTING = "testing"  # QA
    AWAITING_APPROVAL = "awaiting_approval"  # Human Gate
    COMPLETED = "completed"
    ESCALATED = "escalated"
    FAILED = "failed"


class WorkflowCreateRequest(BaseModel):
    title: str
    specification: str
    metadata_json: Optional[Dict[str, Any]] = None


class WorkflowApprovalRequest(BaseModel):
    approved_by: str
    comments: Optional[str] = None


class WorkflowEscalationRequest(BaseModel):
    reason: str
    escalated_by: str  # e.g., 'reviewer', 'qa', or human operator


class WorkflowResolutionRequest(BaseModel):
    resolved_by: str
    resolution_notes: str
    action: str  # 'resume', 'restart', or 'terminate'


class WorkflowRunResponse(BaseModel):
    id: uuid.UUID
    title: str
    status: WorkflowStatus
    specification: str
    current_step: str
    artifacts: Dict[str, Any]
    error_message: Optional[str] = None
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    owner_id: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

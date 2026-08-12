from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional
import uuid
from urllib.parse import urlparse

from pydantic import BaseModel, ConfigDict, field_validator


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
    repository_url: Optional[str] = None

    @field_validator("repository_url")
    @classmethod
    def validate_repository_url(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return value

        value = value.strip().rstrip("/")
        parsed = urlparse(value)
        path_parts = [part for part in parsed.path.split("/") if part]
        if (
            parsed.scheme != "https"
            or parsed.netloc.lower() not in {"github.com", "www.github.com"}
            or len(path_parts) != 2
            or any(part in {".", ".."} for part in path_parts)
        ):
            raise ValueError(
                "repository_url must be a secure GitHub repository URL, "
                "for example https://github.com/owner/repository"
            )
        return value


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

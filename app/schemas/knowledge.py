from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
import uuid

from pydantic import BaseModel, ConfigDict


class MemoryTier(str, Enum):
    PRIVATE = "private"
    CANDIDATE = "candidate"
    SHARED = "shared"
    EXTERNAL = "external"


class KnowledgeStatus(str, Enum):
    PROPOSED = "proposed"
    APPROVED = "approved"
    REJECTED = "rejected"
    ARCHIVED = "archived"


class KnowledgeItemCreate(BaseModel):
    title: str
    tier: MemoryTier
    category: str  # e.g., 'adr', 'coding_standard', 'playbook', 'security'
    content: str
    metadata_json: Optional[Dict[str, Any]] = None
    embedding: Optional[List[float]] = None


class KnowledgeItemResponse(BaseModel):
    id: uuid.UUID
    title: str
    tier: MemoryTier
    category: str
    status: KnowledgeStatus
    content: str
    metadata_json: Optional[Dict[str, Any]]
    approved_by: Optional[str]
    approved_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class KnowledgePromotionRequest(BaseModel):
    approved_by: str
    comments: Optional[str] = None


class KnowledgeRejectionRequest(BaseModel):
    rejected_by: str
    comments: Optional[str] = None

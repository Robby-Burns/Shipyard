from datetime import datetime
from typing import Any, Dict, List, Optional
import uuid

from enum import Enum
from pydantic import BaseModel, ConfigDict, Field


class MemoryCategory(str, Enum):
    PRIVATE = "private"
    SHARED = "shared"
    CANDIDATE = "candidate"


class MemoryRecordCreate(BaseModel):
    category: MemoryCategory
    content: str
    metadata_json: Optional[Dict[str, Any]] = None
    embedding: Optional[List[float]] = None


class MemoryRecordResponse(BaseModel):
    id: uuid.UUID
    category: MemoryCategory
    content: str
    metadata_json: Optional[Dict[str, Any]]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class MemorySearchRequest(BaseModel):
    query_text: Optional[str] = None
    category: Optional[MemoryCategory] = None
    query_embedding: Optional[List[float]] = None
    limit: int = Field(10, gt=0, le=100)

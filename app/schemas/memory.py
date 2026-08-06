from datetime import datetime
from typing import Any, Dict, List, Optional
import uuid

from pydantic import BaseModel, ConfigDict


class MemoryRecordCreate(BaseModel):
    category: str  # 'private', 'candidate', 'shared'
    content: str
    metadata_json: Optional[Dict[str, Any]] = None
    embedding: Optional[List[float]] = None


class MemoryRecordResponse(BaseModel):
    id: uuid.UUID
    category: str
    content: str
    metadata_json: Optional[Dict[str, Any]]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class MemorySearchRequest(BaseModel):
    query_text: Optional[str] = None
    category: Optional[str] = None
    query_embedding: Optional[List[float]] = None
    limit: int = 10

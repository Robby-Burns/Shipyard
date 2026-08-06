from datetime import datetime
from typing import Any, Dict, Optional
import uuid

from pydantic import BaseModel, ConfigDict


class ActivityLogCreate(BaseModel):
    event_type: str
    source: str
    request_id: Optional[str] = None
    payload: Optional[Dict[str, Any]] = None


class ActivityLogResponse(BaseModel):
    id: uuid.UUID
    event_type: str
    source: str
    request_id: Optional[str]
    payload: Optional[Dict[str, Any]]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ActivityLogFilter(BaseModel):
    event_type: Optional[str] = None
    source: Optional[str] = None
    request_id: Optional[str] = None
    limit: int = 50
    offset: int = 0

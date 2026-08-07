from datetime import datetime
from typing import Any, Dict, List, Optional
import uuid

from pydantic import BaseModel, ConfigDict


class IntakeSessionCreate(BaseModel):
    title: str


class IntakeChatInput(BaseModel):
    message: str


class IntakeSessionResponse(BaseModel):
    id: uuid.UUID
    title: str
    owner_id: Optional[str] = None
    status: str
    messages: List[Dict[str, Any]]
    specification: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

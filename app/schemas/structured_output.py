from pydantic import BaseModel, Field
from typing import Optional, List, Dict

class ReviewOutput(BaseModel):
    status: str = Field(..., description="review status: 'approved' or 'request_changes'")
    reason: Optional[str] = Field(None, description="optional reason for a change request")

class Diagram(BaseModel):
    content: str = Field(..., description="raw Mermaid diagram text")

class Adr(BaseModel):
    id: str = Field(..., description="ADR identifier, e.g. 'ADR-001'")
    body: str = Field(..., description="full ADR markdown content")

class KnowledgeCandidate(BaseModel):
    title: str
    tier: str
    category: str
    content: str

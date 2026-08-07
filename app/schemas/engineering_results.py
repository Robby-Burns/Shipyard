from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

class ADR(BaseModel):
    id: str = Field(..., description="ADR identifier, e.g., 'ADR-001'")
    title: Optional[str] = Field(None, description="Title of the ADR")
    decision: Optional[str] = Field(None, description="Decision summary of the ADR")
    rationale: Optional[str] = Field(None, description="Rationale for the ADR")

class ArchitectureData(BaseModel):
    diagram: str = Field(..., description="Mermaid diagram content")
    adrs: List[ADR] = Field(default_factory=list, description="List of ADR objects")

class ArchitectureResult(BaseModel):
    role: str = Field("architect", const=True)
    status: str = Field(..., description="Result status, e.g., 'completed'")
    architecture: ArchitectureData
    warnings: List[str] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)

class ReviewResult(BaseModel):
    role: str = Field("reviewer", const=True)
    status: str = Field(..., description="'approved' or 'request_changes'")
    summary: Optional[str] = None
    findings: List[str] = Field(default_factory=list)
    required_changes: List[str] = Field(default_factory=list)

class QAResult(BaseModel):
    role: str = Field("qa", const=True)
    status: str = Field(..., description="'passed' or 'failed'")
    coverage: Optional[float] = None
    performance: Optional[str] = None
    accessibility: Optional[str] = None
    issues: List[str] = Field(default_factory=list)

class KnowledgeCandidate(BaseModel):
    title: str
    tier: str
    category: str
    content: str

class PlatformResult(BaseModel):
    role: str = Field("platform", const=True)
    metrics: Dict[str, Any] = Field(default_factory=dict)
    recommendations: List[str] = Field(default_factory=list)
    knowledge_candidates: List[KnowledgeCandidate] = Field(default_factory=list)

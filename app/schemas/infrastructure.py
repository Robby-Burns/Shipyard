from pydantic import BaseModel
from typing import Dict, Any, List


class InfrastructureComponent(BaseModel):
    name: str
    provider: str
    adapter: str
    status: str
    health: bool
    details: Dict[str, Any]


class InfrastructureStatusResponse(BaseModel):
    status: str
    components: List[InfrastructureComponent]

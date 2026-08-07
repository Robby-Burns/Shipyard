from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class WorkflowMetrics(BaseModel):
    total_runs: int = 0
    active_count: int = 0
    completed_count: int = 0
    failed_count: int = 0
    escalated_count: int = 0
    completion_rate_pct: float = 0.0


class ToolExecutionMetrics(BaseModel):
    total_executions: int = 0
    successful_executions: int = 0
    failed_executions: int = 0
    success_rate_pct: float = 0.0
    avg_execution_time_ms: float = 0.0


class ModelUsageMetrics(BaseModel):
    total_requests: int = 0
    by_capability: Dict[str, int] = Field(default_factory=dict)


class PlatformDashboardMetrics(BaseModel):
    system_status: str = "operational"
    uptime_seconds: float = 0.0
    workflows: WorkflowMetrics = Field(default_factory=WorkflowMetrics)
    tools: ToolExecutionMetrics = Field(default_factory=ToolExecutionMetrics)
    models: ModelUsageMetrics = Field(default_factory=ModelUsageMetrics)
    recent_errors: List[Dict[str, Any]] = Field(default_factory=list)

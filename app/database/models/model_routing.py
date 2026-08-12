from datetime import datetime, timezone
import uuid
from typing import Any, Dict, List, Optional

from sqlalchemy import Boolean, DateTime, Float, Integer, JSON, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.database.session import Base


class ModelCatalogSnapshot(Base):
    """Cached provider metadata used for model selection."""

    __tablename__ = "model_catalog_snapshots"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    provider: Mapped[str] = mapped_column(String(50), index=True, nullable=False)
    model_id: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    model_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    context_length: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    max_completion_tokens: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    input_price_per_million: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    output_price_per_million: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    supported_parameters: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)
    benchmarks: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    raw_metadata: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    is_available: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    fetched_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class ModelRoutingOutcome(Base):
    """One completed or failed model attempt used for routing feedback."""

    __tablename__ = "model_routing_outcomes"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    request_id: Mapped[Optional[str]] = mapped_column(String(100), index=True, nullable=True)
    capability: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    model_id: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    prompt_tokens: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    completion_tokens: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    estimated_cost: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    latency_ms: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    success: Mapped[bool] = mapped_column(Boolean, nullable=False)
    quality_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    finish_reason: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    error_code: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    task_features: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True
    )

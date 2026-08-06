from datetime import datetime, timezone
import uuid
from typing import Any, Dict, List, Optional

try:
    from pgvector.sqlalchemy import Vector
except Exception:  # pragma: no cover
    # Fallback for non‑PostgreSQL databases (e.g., SQLite in tests).
    # We cannot use pgvector's dimension argument, so we provide a thin wrapper
    # that accepts an optional `dim` parameter but returns a JSON column. This
    # preserves the model's attribute signatures while sacrificing native vector
    # operators (cosine_distance, l2_distance, etc.) on SQLite.
    from sqlalchemy.types import JSON
    def Vector(dim=None):
        """Fallback Vector type for SQLite.

        Args:
            dim (int, optional): Ignored; present only for signature compatibility.
        Returns:
            sqlalchemy.types.JSON: Column type that stores the vector as JSON.
        """
        return JSON

from sqlalchemy import JSON, DateTime, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database.session import Base


class MemoryRecord(Base):
    __tablename__ = "memory_records"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    category: Mapped[str] = mapped_column(
        String(50), index=True, nullable=False
    )  # e.g., 'private', 'candidate', 'shared'
    content: Mapped[str] = mapped_column(Text, nullable=False)
    metadata_json: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON, nullable=True
    )
    embedding: Mapped[Optional[List[float]]] = mapped_column(
        Vector(1536), nullable=True
    )  # Standard vector length
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        index=True,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

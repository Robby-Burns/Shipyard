from datetime import datetime, timezone
import uuid
from typing import Any, Dict, List, Optional

from sqlalchemy import JSON, DateTime, String, Text, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database.session import Base
from app.schemas.knowledge import KnowledgeStatus, MemoryTier

try:
    from pgvector.sqlalchemy import Vector
except Exception:  # pragma: no cover
    from sqlalchemy.types import JSON
    def Vector(dim=None):
        return JSON


class KnowledgeItem(Base):
    __tablename__ = "knowledge_items"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    tier: Mapped[MemoryTier] = mapped_column(
        SQLEnum(MemoryTier), default=MemoryTier.CANDIDATE, index=True, nullable=False
    )
    category: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    status: Mapped[KnowledgeStatus] = mapped_column(
        SQLEnum(KnowledgeStatus), default=KnowledgeStatus.PROPOSED, index=True, nullable=False
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    metadata_json: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON, nullable=True
    )
    embedding: Mapped[Optional[List[float]]] = mapped_column(
        Vector(1536), nullable=True
    )

    # Governance & Approval audit
    approved_by: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    approved_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

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

from datetime import datetime, timezone
import uuid
from typing import Any, Dict, Optional

from sqlalchemy import JSON, DateTime, String, Text, Enum as SQLEnum, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.database.session import Base
from app.schemas.workflow import WorkflowStatus


class WorkflowRun(Base):
    __tablename__ = "workflow_runs"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, default=uuid.uuid4
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    owner_id: Mapped[Optional[str]] = mapped_column(
        String(100), index=True, nullable=True
    )
    status: Mapped[WorkflowStatus] = mapped_column(
        SQLEnum(WorkflowStatus),
        default=WorkflowStatus.CREATED,
        index=True,
        nullable=False,
    )
    specification: Mapped[str] = mapped_column(Text, nullable=False)
    current_step: Mapped[str] = mapped_column(
        String(100), default="init", nullable=False
    )

    # Store output artifacts generated across steps (e.g., build_plan, architecture_doc, review_report)
    artifacts: Mapped[Dict[str, Any]] = mapped_column(
        JSON, default=dict, nullable=False
    )

    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    approved_by: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True
    )
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
    engineering_approved_by: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True
    )

    engineering_approved_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
from datetime import datetime, timezone
import uuid
from typing import Any, Dict, Optional

from sqlalchemy import JSON, Boolean, DateTime, Integer, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.database.session import Base


class ToolExecutionLog(Base):
    __tablename__ = "tool_execution_logs"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, default=uuid.uuid4
    )
    tool_name: Mapped[str] = mapped_column(
        String(100), index=True, nullable=False
    )  # e.g., 'github', 'docker'
    action: Mapped[str] = mapped_column(String(100), nullable=False)
    payload: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON, nullable=True
    )
    response: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON, nullable=True
    )
    status_code: Mapped[int] = mapped_column(Integer, default=200)
    is_success: Mapped[bool] = mapped_column(Boolean, default=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    execution_time_ms: Mapped[float] = mapped_column(
        nullable=False, default=0.0
    )
    request_id: Mapped[Optional[str]] = mapped_column(
        String(100), index=True, nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        index=True,
    )

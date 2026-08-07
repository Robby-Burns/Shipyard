from datetime import datetime, timezone
import uuid
from typing import Any, Dict, Optional

from sqlalchemy import JSON, DateTime, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.database.session import Base


class ActivityLog(Base):
    __tablename__ = "activity_logs"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, default=uuid.uuid4
    )
    event_type: Mapped[str] = mapped_column(
        String(100), index=True, nullable=False
    )
    source: Mapped[str] = mapped_column(
        String(100), index=True, nullable=False
    )  # e.g., 'model_router', 'tool_gateway'
    request_id: Mapped[Optional[str]] = mapped_column(
        String(100), index=True, nullable=True
    )
    payload: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON, nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        index=True,
    )

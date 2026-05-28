import enum
from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, Enum, Index, String, func, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from models.base import Base


class ProcessStatus(enum.StrEnum):
    PROCESSED = "processed"
    PENDING = "pending"
    FAILED = "failed"
    IGNORED = "ignored"


class PaddleWebhookEvent(Base):
    __tablename__ = "paddle_webhook_events"
    __table_args__ = (
        Index(
            "ix_paddle_webhook_events_pending",
            "next_attempt_at",
            postgresql_where=text("process_status = 'pending'"),
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    event_id: Mapped[str] = mapped_column(String(255), unique=True)
    event_type: Mapped[str] = mapped_column(String(255))
    notification_id: Mapped[str] = mapped_column(String(255))
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB)

    # --- outbox ---
    process_status: Mapped[ProcessStatus] = mapped_column(
        Enum(
            ProcessStatus,
            name="process_status",
            native_enum=False,
            length=20,
            values_callable=lambda e: [m.value for m in e],
        ),
        default=ProcessStatus.IGNORED,
        server_default=ProcessStatus.IGNORED.value,
    )
    processed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, index=True
    )
    attempts: Mapped[int] = mapped_column(default=0, server_default="0")
    last_error: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    next_attempt_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )

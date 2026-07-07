from datetime import datetime
from enum import StrEnum
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, text
from sqlalchemy.dialects.postgresql import ENUM as PG_ENUM
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from lexflow_api.db.base import Base

notification_channel_enum = PG_ENUM(
    "in_app",
    "email",
    "teams",
    name="notification_channel",
    schema="shared",
    create_type=False,
)
notification_status_enum = PG_ENUM(
    "pending",
    "sent",
    "read",
    "failed",
    name="notification_status",
    schema="shared",
    create_type=False,
)


class NotificationChannel(StrEnum):
    IN_APP = "in_app"
    EMAIL = "email"
    TEAMS = "teams"
    SLACK = "slack"
    SMS = "sms"
    WEBHOOK = "webhook"
    PUSH = "push"


class NotificationStatus(StrEnum):
    PENDING = "pending"
    SENT = "sent"
    READ = "read"
    FAILED = "failed"
    DLQ = "dlq"


class Notification(Base):
    __tablename__ = "notifications"
    __table_args__ = {"schema": "shared"}

    id: Mapped[UUID] = mapped_column(primary_key=True, server_default=text("gen_random_uuid()"))
    user_id: Mapped[UUID] = mapped_column(ForeignKey("identity.users.id"), nullable=False)
    case_id: Mapped[UUID | None] = mapped_column(ForeignKey("cases.cases.id"))
    firm_id: Mapped[UUID] = mapped_column(ForeignKey("identity.firms.id"), nullable=False)
    channel: Mapped[str] = mapped_column(notification_channel_enum, nullable=False)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(notification_status_enum, nullable=False, server_default="pending")
    read_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    delivered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    event_type: Mapped[str | None] = mapped_column(String(100))
    correlation_id: Mapped[UUID | None] = mapped_column()
    workflow_execution_id: Mapped[UUID | None] = mapped_column()
    workflow_slug: Mapped[str | None] = mapped_column(String(100))
    priority: Mapped[str | None] = mapped_column(String(50))
    attempts: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    provider: Mapped[str | None] = mapped_column(String(50))
    action_url: Mapped[str | None] = mapped_column(String(500))
    metadata_: Mapped[dict[str, object]] = mapped_column("metadata", JSONB, nullable=False, server_default="{}")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )


class NotificationDelivery(Base):
    __tablename__ = "notification_deliveries"
    __table_args__ = {"schema": "shared"}

    id: Mapped[UUID] = mapped_column(primary_key=True, server_default=text("gen_random_uuid()"))
    notification_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("shared.notifications.id", ondelete="CASCADE")
    )
    firm_id: Mapped[UUID] = mapped_column(ForeignKey("identity.firms.id"), nullable=False)
    channel: Mapped[str] = mapped_column(String(50), nullable=False)
    provider: Mapped[str | None] = mapped_column(String(50))
    status: Mapped[str] = mapped_column(String(50), nullable=False, server_default="pending")
    attempts: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    max_attempts: Mapped[int] = mapped_column(Integer, default=4, server_default="4")
    correlation_id: Mapped[UUID | None] = mapped_column()
    workflow_execution_id: Mapped[UUID | None] = mapped_column()
    workflow_slug: Mapped[str | None] = mapped_column(String(100))
    latency_ms: Mapped[int | None] = mapped_column(Integer)
    error_message: Mapped[str | None] = mapped_column(Text)
    payload: Mapped[dict[str, object]] = mapped_column(JSONB, nullable=False, server_default="{}")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )

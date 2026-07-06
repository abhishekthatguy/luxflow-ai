from datetime import datetime
from enum import StrEnum
from uuid import UUID

from sqlalchemy import DateTime, Enum, ForeignKey, String, Text, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from lexflow_api.db.base import Base


class NotificationChannel(StrEnum):
    IN_APP = "in_app"
    EMAIL = "email"
    TEAMS = "teams"


class NotificationStatus(StrEnum):
    PENDING = "pending"
    SENT = "sent"
    READ = "read"
    FAILED = "failed"


class Notification(Base):
    __tablename__ = "notifications"
    __table_args__ = {"schema": "shared"}

    id: Mapped[UUID] = mapped_column(primary_key=True, server_default=text("gen_random_uuid()"))
    user_id: Mapped[UUID] = mapped_column(ForeignKey("identity.users.id"), nullable=False)
    case_id: Mapped[UUID | None] = mapped_column(ForeignKey("cases.cases.id"))
    firm_id: Mapped[UUID] = mapped_column(ForeignKey("identity.firms.id"), nullable=False)
    channel: Mapped[NotificationChannel] = mapped_column(
        Enum(
            NotificationChannel,
            name="notification_channel",
            schema="shared",
            values_callable=lambda x: [e.value for e in x],
        ),
        nullable=False,
    )
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[NotificationStatus] = mapped_column(
        Enum(
            NotificationStatus,
            name="notification_status",
            schema="shared",
            values_callable=lambda x: [e.value for e in x],
        ),
        nullable=False,
        server_default=NotificationStatus.PENDING.value,
    )
    read_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    metadata_: Mapped[dict[str, object]] = mapped_column("metadata", JSONB, nullable=False, server_default="{}")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )

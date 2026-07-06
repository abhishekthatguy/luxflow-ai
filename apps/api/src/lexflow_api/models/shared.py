from datetime import datetime
from enum import StrEnum
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, Integer, String, text
from sqlalchemy.dialects.postgresql import ENUM as PG_ENUM
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from lexflow_api.db.base import Base

job_type_enum = PG_ENUM(
    "ai.summary",
    "document.process",
    "workflow.execution",
    name="job_type",
    schema="shared",
    create_type=False,
)
job_status_enum = PG_ENUM(
    "queued",
    "running",
    "completed",
    "failed",
    "cancelled",
    name="job_status",
    schema="shared",
    create_type=False,
)


class JobType(StrEnum):
    AI_SUMMARY = "ai.summary"
    DOCUMENT_PROCESS = "document.process"
    WORKFLOW_EXECUTION = "workflow.execution"


class JobStatus(StrEnum):
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class OutboxEvent(Base):
    __tablename__ = "outbox_events"
    __table_args__ = {"schema": "shared"}

    id: Mapped[UUID] = mapped_column(primary_key=True, server_default=text("gen_random_uuid()"))
    firm_id: Mapped[UUID] = mapped_column(ForeignKey("identity.firms.id"), nullable=False)
    aggregate_type: Mapped[str] = mapped_column(String(100), nullable=False)
    aggregate_id: Mapped[UUID] = mapped_column(nullable=False)
    event_type: Mapped[str] = mapped_column(String(100), nullable=False)
    payload: Mapped[dict[str, object]] = mapped_column(JSONB, nullable=False, server_default="{}")
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )


class AsyncJob(Base):
    __tablename__ = "async_jobs"
    __table_args__ = {"schema": "shared"}

    id: Mapped[UUID] = mapped_column(primary_key=True, server_default=text("gen_random_uuid()"))
    firm_id: Mapped[UUID] = mapped_column(ForeignKey("identity.firms.id"))
    case_id: Mapped[UUID | None] = mapped_column(ForeignKey("cases.cases.id"), nullable=True)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("identity.users.id"))
    job_type: Mapped[str] = mapped_column(job_type_enum)
    status: Mapped[str] = mapped_column(job_status_enum, default=JobStatus.QUEUED)
    progress: Mapped[int] = mapped_column(Integer, default=0)
    resource_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    resource_id: Mapped[UUID | None] = mapped_column(nullable=True)
    result: Mapped[dict[str, object] | None] = mapped_column(JSONB, nullable=True)
    error: Mapped[dict[str, object] | None] = mapped_column(JSONB, nullable=True)
    correlation_id: Mapped[UUID] = mapped_column(server_default=text("gen_random_uuid()"))
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=text("now()"))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=text("now()"))

from datetime import datetime
from enum import StrEnum
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, text
from sqlalchemy.dialects.postgresql import ENUM as PG_ENUM
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from lexflow_api.db.base import Base

trigger_type_enum = PG_ENUM(
    "manual",
    "event",
    "schedule",
    name="trigger_type",
    schema="workflows",
    create_type=False,
)
execution_status_enum = PG_ENUM(
    "queued",
    "running",
    "completed",
    "failed",
    "cancelled",
    name="execution_status",
    schema="workflows",
    create_type=False,
)
step_status_enum = PG_ENUM(
    "pending",
    "running",
    "completed",
    "failed",
    "skipped",
    name="step_status",
    schema="workflows",
    create_type=False,
)


class TriggerType(StrEnum):
    MANUAL = "manual"
    EVENT = "event"
    SCHEDULE = "schedule"


class ExecutionStatus(StrEnum):
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class WorkflowDefinition(Base):
    __tablename__ = "workflow_definitions"
    __table_args__ = {"schema": "workflows"}

    id: Mapped[UUID] = mapped_column(primary_key=True, server_default=text("gen_random_uuid()"))
    firm_id: Mapped[UUID | None] = mapped_column(ForeignKey("identity.firms.id"), nullable=True)
    name: Mapped[str] = mapped_column(String(255))
    slug: Mapped[str] = mapped_column(String(100))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    n8n_workflow_id: Mapped[str] = mapped_column(String(100))
    trigger_type: Mapped[str] = mapped_column(trigger_type_enum, default=TriggerType.EVENT)
    is_active: Mapped[bool] = mapped_column(default=True)
    config_schema: Mapped[dict[str, object] | None] = mapped_column(JSONB, nullable=True)
    version: Mapped[int] = mapped_column(Integer, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=text("now()"))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=text("now()"))


class WorkflowExecution(Base):
    __tablename__ = "workflow_executions"
    __table_args__ = {"schema": "workflows"}

    id: Mapped[UUID] = mapped_column(primary_key=True, server_default=text("gen_random_uuid()"))
    workflow_definition_id: Mapped[UUID] = mapped_column(
        ForeignKey("workflows.workflow_definitions.id")
    )
    case_id: Mapped[UUID | None] = mapped_column(ForeignKey("cases.cases.id"), nullable=True)
    firm_id: Mapped[UUID] = mapped_column(ForeignKey("identity.firms.id"))
    triggered_by: Mapped[UUID | None] = mapped_column(ForeignKey("identity.users.id"), nullable=True)
    status: Mapped[str] = mapped_column(execution_status_enum, default=ExecutionStatus.QUEUED)
    input_payload: Mapped[dict[str, object]] = mapped_column(JSONB, default=dict)
    output_payload: Mapped[dict[str, object] | None] = mapped_column(JSONB, nullable=True)
    correlation_id: Mapped[UUID] = mapped_column()
    idempotency_key: Mapped[str | None] = mapped_column(String(255), nullable=True)
    n8n_execution_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    retry_count: Mapped[int] = mapped_column(Integer, default=0)
    max_retries: Mapped[int] = mapped_column(Integer, default=3)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=text("now()"))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=text("now()"))


class WorkflowStep(Base):
    __tablename__ = "workflow_steps"
    __table_args__ = {"schema": "workflows"}

    id: Mapped[UUID] = mapped_column(primary_key=True, server_default=text("gen_random_uuid()"))
    execution_id: Mapped[UUID] = mapped_column(
        ForeignKey("workflows.workflow_executions.id", ondelete="CASCADE")
    )
    step_name: Mapped[str] = mapped_column(String(255))
    step_order: Mapped[int] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(step_status_enum, default="pending")
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    metadata_: Mapped[dict[str, object]] = mapped_column("metadata", JSONB, default=dict)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

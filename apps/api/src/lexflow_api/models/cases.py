from datetime import datetime
from enum import StrEnum
from uuid import UUID

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import ENUM as PG_ENUM
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from lexflow_api.db.base import Base

client_type_enum = PG_ENUM(
    "individual", "organization", name="client_type", schema="cases", create_type=False
)
case_status_enum = PG_ENUM(
    "intake",
    "active",
    "on_hold",
    "closed",
    "archived",
    name="case_status",
    schema="cases",
    create_type=False,
)
priority_enum = PG_ENUM(
    "low", "normal", "high", "urgent", name="priority", schema="cases", create_type=False
)
participant_role_enum = PG_ENUM(
    "lead",
    "associate",
    "paralegal",
    "observer",
    name="participant_role",
    schema="cases",
    create_type=False,
)
task_status_enum = PG_ENUM(
    "pending",
    "in_progress",
    "completed",
    "cancelled",
    name="task_status",
    schema="cases",
    create_type=False,
)
deadline_type_enum = PG_ENUM(
    "filing",
    "discovery",
    "statute_of_limitations",
    "internal",
    "other",
    name="deadline_type",
    schema="cases",
    create_type=False,
)
deadline_status_enum = PG_ENUM(
    "upcoming",
    "met",
    "missed",
    "extended",
    name="deadline_status",
    schema="cases",
    create_type=False,
)
note_visibility_enum = PG_ENUM(
    "team", "attorneys_only", "private", name="note_visibility", schema="cases", create_type=False
)


class ClientType(StrEnum):
    INDIVIDUAL = "individual"
    ORGANIZATION = "organization"


class CaseStatus(StrEnum):
    INTAKE = "intake"
    ACTIVE = "active"
    ON_HOLD = "on_hold"
    CLOSED = "closed"
    ARCHIVED = "archived"


class Priority(StrEnum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class ParticipantRole(StrEnum):
    LEAD = "lead"
    ASSOCIATE = "associate"
    PARALEGAL = "paralegal"
    OBSERVER = "observer"


class TaskStatus(StrEnum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class DeadlineType(StrEnum):
    FILING = "filing"
    DISCOVERY = "discovery"
    STATUTE_OF_LIMITATIONS = "statute_of_limitations"
    INTERNAL = "internal"
    OTHER = "other"


class DeadlineStatus(StrEnum):
    UPCOMING = "upcoming"
    MET = "met"
    MISSED = "missed"
    EXTENDED = "extended"


class NoteVisibility(StrEnum):
    TEAM = "team"
    ATTORNEYS_ONLY = "attorneys_only"
    PRIVATE = "private"


class Client(Base):
    __tablename__ = "clients"
    __table_args__ = {"schema": "cases"}

    id: Mapped[UUID] = mapped_column(primary_key=True, server_default=text("gen_random_uuid()"))
    firm_id: Mapped[UUID] = mapped_column(ForeignKey("identity.firms.id"), nullable=False)
    type: Mapped[str] = mapped_column(client_type_enum, nullable=False, server_default="individual")
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str | None] = mapped_column(String(320))
    phone: Mapped[str | None] = mapped_column(String(50))
    metadata_: Mapped[dict[str, object]] = mapped_column(
        "metadata", JSONB, nullable=False, server_default="{}"
    )
    version: Mapped[int] = mapped_column(Integer, nullable=False, server_default="1")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class Case(Base):
    __tablename__ = "cases"
    __table_args__ = (
        UniqueConstraint("firm_id", "case_number", name="cases_firm_id_case_number_key"),
        {"schema": "cases"},
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, server_default=text("gen_random_uuid()"))
    firm_id: Mapped[UUID] = mapped_column(ForeignKey("identity.firms.id"), nullable=False)
    client_id: Mapped[UUID] = mapped_column(ForeignKey("cases.clients.id"), nullable=False)
    case_number: Mapped[str] = mapped_column(String(50), nullable=False)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    practice_area: Mapped[str | None] = mapped_column(String(100))
    status: Mapped[str] = mapped_column(case_status_enum, nullable=False, server_default="intake")
    priority: Mapped[str] = mapped_column(priority_enum, nullable=False, server_default="normal")
    lead_attorney_id: Mapped[UUID] = mapped_column(ForeignKey("identity.users.id"), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    opened_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    metadata_: Mapped[dict[str, object]] = mapped_column(
        "metadata", JSONB, nullable=False, server_default="{}"
    )
    version: Mapped[int] = mapped_column(Integer, nullable=False, server_default="1")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class CaseParticipant(Base):
    __tablename__ = "case_participants"
    __table_args__ = (
        UniqueConstraint("case_id", "user_id", name="case_participants_case_id_user_id_key"),
        {"schema": "cases"},
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, server_default=text("gen_random_uuid()"))
    case_id: Mapped[UUID] = mapped_column(
        ForeignKey("cases.cases.id", ondelete="CASCADE"), nullable=False
    )
    user_id: Mapped[UUID] = mapped_column(ForeignKey("identity.users.id"), nullable=False)
    role: Mapped[str] = mapped_column(participant_role_enum, nullable=False)
    added_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )
    added_by: Mapped[UUID] = mapped_column(ForeignKey("identity.users.id"), nullable=False)


class Task(Base):
    __tablename__ = "tasks"
    __table_args__ = {"schema": "cases"}

    id: Mapped[UUID] = mapped_column(primary_key=True, server_default=text("gen_random_uuid()"))
    case_id: Mapped[UUID] = mapped_column(
        ForeignKey("cases.cases.id", ondelete="CASCADE"), nullable=False
    )
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(task_status_enum, nullable=False, server_default="pending")
    priority: Mapped[str] = mapped_column(priority_enum, nullable=False, server_default="normal")
    assigned_to: Mapped[UUID | None] = mapped_column(ForeignKey("identity.users.id"))
    due_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_by: Mapped[UUID] = mapped_column(ForeignKey("identity.users.id"), nullable=False)
    version: Mapped[int] = mapped_column(Integer, nullable=False, server_default="1")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )


class Deadline(Base):
    __tablename__ = "deadlines"
    __table_args__ = {"schema": "cases"}

    id: Mapped[UUID] = mapped_column(primary_key=True, server_default=text("gen_random_uuid()"))
    case_id: Mapped[UUID] = mapped_column(
        ForeignKey("cases.cases.id", ondelete="CASCADE"), nullable=False
    )
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    deadline_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    type: Mapped[str] = mapped_column(deadline_type_enum, nullable=False)
    status: Mapped[str] = mapped_column(
        deadline_status_enum, nullable=False, server_default="upcoming"
    )
    reminder_sent: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")
    created_by: Mapped[UUID] = mapped_column(ForeignKey("identity.users.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )


class Hearing(Base):
    __tablename__ = "hearings"
    __table_args__ = {"schema": "cases"}

    id: Mapped[UUID] = mapped_column(primary_key=True, server_default=text("gen_random_uuid()"))
    case_id: Mapped[UUID] = mapped_column(
        ForeignKey("cases.cases.id", ondelete="CASCADE"), nullable=False
    )
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    hearing_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    location: Mapped[str | None] = mapped_column(String(500))
    court: Mapped[str | None] = mapped_column(String(255))
    judge: Mapped[str | None] = mapped_column(String(255))
    notes: Mapped[str | None] = mapped_column(Text)
    created_by: Mapped[UUID] = mapped_column(ForeignKey("identity.users.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )


class Note(Base):
    __tablename__ = "notes"
    __table_args__ = {"schema": "cases"}

    id: Mapped[UUID] = mapped_column(primary_key=True, server_default=text("gen_random_uuid()"))
    case_id: Mapped[UUID] = mapped_column(
        ForeignKey("cases.cases.id", ondelete="CASCADE"), nullable=False
    )
    author_id: Mapped[UUID] = mapped_column(ForeignKey("identity.users.id"), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    visibility: Mapped[str] = mapped_column(
        note_visibility_enum, nullable=False, server_default="team"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )


class CaseTimelineEvent(Base):
    __tablename__ = "case_timeline_events"
    __table_args__ = {"schema": "cases"}

    id: Mapped[UUID] = mapped_column(primary_key=True, server_default=text("gen_random_uuid()"))
    case_id: Mapped[UUID] = mapped_column(
        ForeignKey("cases.cases.id", ondelete="CASCADE"), nullable=False
    )
    firm_id: Mapped[UUID] = mapped_column(ForeignKey("identity.firms.id"), nullable=False)
    event_type: Mapped[str] = mapped_column(String(100), nullable=False)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    payload: Mapped[dict[str, object]] = mapped_column(JSONB, nullable=False, server_default="{}")
    actor_id: Mapped[UUID | None] = mapped_column(ForeignKey("identity.users.id"))
    occurred_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )

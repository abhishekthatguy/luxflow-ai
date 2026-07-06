from datetime import date, datetime
from decimal import Decimal
from enum import StrEnum
from uuid import UUID

from sqlalchemy import Date, DateTime, ForeignKey, Integer, Numeric, String, Text, text
from sqlalchemy.dialects.postgresql import ENUM as PG_ENUM
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from lexflow_api.db.base import Base

summary_type_enum = PG_ENUM(
    "case_overview",
    "document_summary",
    "deposition_summary",
    "contract_review",
    name="summary_type",
    schema="ai",
    create_type=False,
)
summary_status_enum = PG_ENUM(
    "generating",
    "draft",
    "approved",
    "rejected",
    "failed",
    name="summary_status",
    schema="ai",
    create_type=False,
)
llm_provider_enum = PG_ENUM(
    "openai",
    "azure_openai",
    "anthropic",
    "ollama",
    name="llm_provider",
    schema="ai",
    create_type=False,
)
prompt_status_enum = PG_ENUM(
    "success",
    "error",
    "filtered",
    name="prompt_status",
    schema="ai",
    create_type=False,
)


class SummaryType(StrEnum):
    CASE_OVERVIEW = "case_overview"
    DOCUMENT_SUMMARY = "document_summary"
    DEPOSITION_SUMMARY = "deposition_summary"
    CONTRACT_REVIEW = "contract_review"


class SummaryStatus(StrEnum):
    GENERATING = "generating"
    DRAFT = "draft"
    APPROVED = "approved"
    REJECTED = "rejected"
    FAILED = "failed"


class PromptTemplate(Base):
    __tablename__ = "prompt_templates"
    __table_args__ = {"schema": "ai"}

    id: Mapped[UUID] = mapped_column(primary_key=True, server_default=text("gen_random_uuid()"))
    name: Mapped[str] = mapped_column(String(255))
    slug: Mapped[str] = mapped_column(String(100))
    version: Mapped[int] = mapped_column(Integer, default=1)
    template: Mapped[str] = mapped_column(Text)
    llm_config: Mapped[dict[str, object]] = mapped_column("model_config", JSONB, default=dict)
    requires_approval: Mapped[bool] = mapped_column(default=True)
    is_active: Mapped[bool] = mapped_column(default=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by: Mapped[UUID | None] = mapped_column(ForeignKey("identity.users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=text("now()"))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=text("now()"))


class AISummary(Base):
    __tablename__ = "ai_summaries"
    __table_args__ = {"schema": "ai"}

    id: Mapped[UUID] = mapped_column(primary_key=True, server_default=text("gen_random_uuid()"))
    case_id: Mapped[UUID] = mapped_column(ForeignKey("cases.cases.id"))
    document_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("documents.documents.id"), nullable=True
    )
    firm_id: Mapped[UUID] = mapped_column(ForeignKey("identity.firms.id"))
    summary_type: Mapped[str] = mapped_column(summary_type_enum)
    content: Mapped[str | None] = mapped_column(Text, nullable=True)
    model: Mapped[str] = mapped_column(String(100))
    prompt_version: Mapped[str] = mapped_column(String(50))
    status: Mapped[str] = mapped_column(summary_status_enum, default=SummaryStatus.GENERATING)
    approved_by: Mapped[UUID | None] = mapped_column(ForeignKey("identity.users.id"), nullable=True)
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    rejection_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    token_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    requested_by: Mapped[UUID] = mapped_column(ForeignKey("identity.users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=text("now()"))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=text("now()"))


class PromptHistory(Base):
    __tablename__ = "prompt_history"
    __table_args__ = {"schema": "ai"}

    id: Mapped[UUID] = mapped_column(primary_key=True, server_default=text("gen_random_uuid()"))
    case_id: Mapped[UUID | None] = mapped_column(ForeignKey("cases.cases.id"), nullable=True)
    firm_id: Mapped[UUID] = mapped_column(ForeignKey("identity.firms.id"))
    user_id: Mapped[UUID] = mapped_column(ForeignKey("identity.users.id"))
    prompt_template_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("ai.prompt_templates.id"), nullable=True
    )
    rendered_prompt: Mapped[str] = mapped_column(Text)
    response: Mapped[str | None] = mapped_column(Text, nullable=True)
    model: Mapped[str] = mapped_column(String(100))
    provider: Mapped[str] = mapped_column(llm_provider_enum, default="azure_openai")
    input_tokens: Mapped[int] = mapped_column(Integer, default=0)
    output_tokens: Mapped[int] = mapped_column(Integer, default=0)
    latency_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    status: Mapped[str] = mapped_column(prompt_status_enum, default="success")
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    correlation_id: Mapped[UUID] = mapped_column()
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=text("now()"))


class LLMUsage(Base):
    __tablename__ = "llm_usage"
    __table_args__ = {"schema": "ai"}

    id: Mapped[UUID] = mapped_column(primary_key=True, server_default=text("gen_random_uuid()"))
    firm_id: Mapped[UUID] = mapped_column(ForeignKey("identity.firms.id"))
    user_id: Mapped[UUID | None] = mapped_column(ForeignKey("identity.users.id"), nullable=True)
    case_id: Mapped[UUID | None] = mapped_column(ForeignKey("cases.cases.id"), nullable=True)
    provider: Mapped[str] = mapped_column(String(50))
    model: Mapped[str] = mapped_column(String(100))
    input_tokens: Mapped[int] = mapped_column(default=0)
    output_tokens: Mapped[int] = mapped_column(default=0)
    estimated_cost_usd: Mapped[Decimal] = mapped_column(Numeric(10, 6), default=0)
    period_start: Mapped[date] = mapped_column(Date)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=text("now()"))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=text("now()"))

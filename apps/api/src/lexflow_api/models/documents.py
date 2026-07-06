from datetime import datetime
from enum import StrEnum
from uuid import UUID

from sqlalchemy import BigInteger, DateTime, ForeignKey, Integer, String, Text, text
from sqlalchemy.dialects.postgresql import ENUM as PG_ENUM
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from lexflow_api.db.base import Base

document_type_enum = PG_ENUM(
    "pleading",
    "contract",
    "evidence",
    "correspondence",
    "invoice",
    "other",
    name="document_type",
    schema="documents",
    create_type=False,
)
document_status_enum = PG_ENUM(
    "pending_upload",
    "uploaded",
    "processing",
    "ready",
    "failed",
    "archived",
    name="document_status",
    schema="documents",
    create_type=False,
)
ocr_status_enum = PG_ENUM(
    "pending",
    "processing",
    "completed",
    "failed",
    "skipped",
    name="ocr_status",
    schema="documents",
    create_type=False,
)


class DocumentType(StrEnum):
    PLEADING = "pleading"
    CONTRACT = "contract"
    EVIDENCE = "evidence"
    CORRESPONDENCE = "correspondence"
    INVOICE = "invoice"
    OTHER = "other"


class DocumentStatus(StrEnum):
    PENDING_UPLOAD = "pending_upload"
    UPLOADED = "uploaded"
    PROCESSING = "processing"
    READY = "ready"
    FAILED = "failed"
    ARCHIVED = "archived"


class OcrStatus(StrEnum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class Document(Base):
    __tablename__ = "documents"
    __table_args__ = {"schema": "documents"}

    id: Mapped[UUID] = mapped_column(primary_key=True, server_default=text("gen_random_uuid()"))
    case_id: Mapped[UUID] = mapped_column(ForeignKey("cases.cases.id"))
    firm_id: Mapped[UUID] = mapped_column(ForeignKey("identity.firms.id"))
    title: Mapped[str] = mapped_column(String(500))
    document_type: Mapped[str] = mapped_column(document_type_enum, default=DocumentType.OTHER)
    status: Mapped[str] = mapped_column(document_status_enum, default=DocumentStatus.PENDING_UPLOAD)
    current_version_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("documents.document_versions.id"), nullable=True
    )
    s3_key: Mapped[str] = mapped_column(String(1000))
    mime_type: Mapped[str] = mapped_column(String(100))
    file_size_bytes: Mapped[int] = mapped_column(BigInteger)
    checksum_sha256: Mapped[str] = mapped_column(String(64))
    ocr_status: Mapped[str] = mapped_column(ocr_status_enum, default=OcrStatus.PENDING)
    ocr_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    metadata_: Mapped[dict[str, object]] = mapped_column("metadata", JSONB, default=dict)
    uploaded_by: Mapped[UUID] = mapped_column(ForeignKey("identity.users.id"))
    version: Mapped[int] = mapped_column(Integer, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=text("now()"))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=text("now()"))
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class DocumentVersion(Base):
    __tablename__ = "document_versions"
    __table_args__ = {"schema": "documents"}

    id: Mapped[UUID] = mapped_column(primary_key=True, server_default=text("gen_random_uuid()"))
    document_id: Mapped[UUID] = mapped_column(ForeignKey("documents.documents.id", ondelete="CASCADE"))
    version_number: Mapped[int] = mapped_column(Integer)
    s3_key: Mapped[str] = mapped_column(String(1000))
    file_size_bytes: Mapped[int] = mapped_column(BigInteger)
    checksum_sha256: Mapped[str] = mapped_column(String(64))
    change_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by: Mapped[UUID] = mapped_column(ForeignKey("identity.users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=text("now()"))

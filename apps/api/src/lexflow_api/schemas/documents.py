from datetime import datetime
from uuid import UUID

from pydantic import Field

from lexflow_api.models.documents import DocumentType
from lexflow_api.schemas.common import CamelModel


class DocumentInitiate(CamelModel):
    title: str = Field(min_length=1, max_length=500)
    document_type: DocumentType = DocumentType.OTHER
    filename: str = Field(min_length=1, max_length=255)
    mime_type: str = Field(min_length=1, max_length=100)
    file_size_bytes: int = Field(gt=0, le=104_857_600)
    checksum_sha256: str = Field(min_length=64, max_length=64)


class DocumentConfirm(CamelModel):
    checksum_sha256: str = Field(min_length=64, max_length=64)


class DocumentResponse(CamelModel):
    id: UUID
    case_id: UUID
    firm_id: UUID
    title: str
    document_type: DocumentType
    status: str
    mime_type: str
    file_size_bytes: int
    checksum_sha256: str
    ocr_status: str
    ocr_text: str | None = None
    version: int
    created_at: datetime
    updated_at: datetime


class DocumentInitiateResponse(CamelModel):
    id: UUID
    status: str
    upload_url: str
    upload_expires_at: datetime
    s3_key: str


class DocumentDownloadResponse(CamelModel):
    download_url: str
    expires_at: datetime

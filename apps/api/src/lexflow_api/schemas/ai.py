from datetime import datetime
from uuid import UUID

from pydantic import Field

from lexflow_api.models.ai import SummaryType
from lexflow_api.schemas.common import CamelModel


class SummarizeRequest(CamelModel):
    summary_type: SummaryType = SummaryType.CASE_OVERVIEW
    document_id: UUID | None = None


class AISummaryResponse(CamelModel):
    id: UUID
    case_id: UUID
    document_id: UUID | None = None
    summary_type: SummaryType
    content: str | None = None
    model: str
    prompt_version: str
    status: str
    approved_by: UUID | None = None
    approved_at: datetime | None = None
    rejection_reason: str | None = None
    token_count: int | None = None
    requested_by: UUID
    created_at: datetime
    updated_at: datetime


class SummaryRejectRequest(CamelModel):
    reason: str = Field(min_length=1, max_length=2000)


class SummaryUpdateRequest(CamelModel):
    content: str = Field(min_length=1, max_length=50000)

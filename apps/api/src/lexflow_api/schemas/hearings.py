from datetime import datetime
from uuid import UUID

from pydantic import Field

from lexflow_api.schemas.common import CamelModel


class HearingCreate(CamelModel):
    title: str = Field(min_length=1, max_length=500)
    hearing_at: datetime
    location: str | None = Field(default=None, max_length=500)
    court: str | None = Field(default=None, max_length=255)
    judge: str | None = Field(default=None, max_length=255)
    notes: str | None = None


class HearingResponse(CamelModel):
    id: UUID
    case_id: UUID
    title: str
    hearing_at: datetime
    location: str | None = None
    court: str | None = None
    judge: str | None = None
    notes: str | None = None
    created_by: UUID
    created_at: datetime
    updated_at: datetime

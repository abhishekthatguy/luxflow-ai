from datetime import datetime
from uuid import UUID

from pydantic import Field

from lexflow_api.models.cases import NoteVisibility
from lexflow_api.schemas.common import CamelModel


class NoteCreate(CamelModel):
    body: str = Field(min_length=1)
    visibility: NoteVisibility = NoteVisibility.TEAM


class NoteResponse(CamelModel):
    id: UUID
    case_id: UUID
    author_id: UUID
    body: str
    visibility: NoteVisibility
    created_at: datetime
    updated_at: datetime

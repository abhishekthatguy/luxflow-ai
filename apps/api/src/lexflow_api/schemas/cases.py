from datetime import datetime
from uuid import UUID

from pydantic import Field

from lexflow_api.models.cases import CaseStatus, ParticipantRole, Priority
from lexflow_api.schemas.common import CamelModel


class CaseCreate(CamelModel):
    client_id: UUID
    case_number: str = Field(min_length=1, max_length=50)
    title: str = Field(min_length=1, max_length=500)
    practice_area: str | None = Field(default=None, max_length=100)
    status: CaseStatus = CaseStatus.INTAKE
    priority: Priority = Priority.NORMAL
    lead_attorney_id: UUID
    description: str | None = None
    metadata: dict[str, object] = Field(default_factory=dict)


class CaseUpdate(CamelModel):
    title: str | None = Field(default=None, min_length=1, max_length=500)
    practice_area: str | None = Field(default=None, max_length=100)
    status: CaseStatus | None = None
    priority: Priority | None = None
    lead_attorney_id: UUID | None = None
    description: str | None = None
    metadata: dict[str, object] | None = None
    version: int | None = None


class CaseResponse(CamelModel):
    id: UUID
    firm_id: UUID
    client_id: UUID
    case_number: str
    title: str
    practice_area: str | None = None
    status: CaseStatus
    priority: Priority
    lead_attorney_id: UUID
    description: str | None = None
    opened_at: datetime | None = None
    closed_at: datetime | None = None
    metadata: dict[str, object] = Field(default_factory=dict)
    version: int
    created_at: datetime
    updated_at: datetime


class ParticipantCreate(CamelModel):
    user_id: UUID
    role: ParticipantRole


class ParticipantResponse(CamelModel):
    id: UUID
    case_id: UUID
    user_id: UUID
    role: ParticipantRole
    added_at: datetime
    added_by: UUID

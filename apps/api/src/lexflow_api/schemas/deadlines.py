from datetime import datetime
from uuid import UUID

from pydantic import Field

from lexflow_api.models.cases import DeadlineStatus, DeadlineType
from lexflow_api.schemas.common import CamelModel


class DeadlineCreate(CamelModel):
    title: str = Field(min_length=1, max_length=500)
    deadline_at: datetime
    type: DeadlineType
    status: DeadlineStatus = DeadlineStatus.UPCOMING


class DeadlineUpdate(CamelModel):
    title: str | None = Field(default=None, min_length=1, max_length=500)
    deadline_at: datetime | None = None
    type: DeadlineType | None = None
    status: DeadlineStatus | None = None


class DeadlineResponse(CamelModel):
    id: UUID
    case_id: UUID
    title: str
    deadline_at: datetime
    type: DeadlineType
    status: DeadlineStatus
    reminder_sent: bool
    created_by: UUID
    created_at: datetime
    updated_at: datetime

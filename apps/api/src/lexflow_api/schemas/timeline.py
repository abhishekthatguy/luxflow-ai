from datetime import datetime
from uuid import UUID

from pydantic import Field

from lexflow_api.schemas.common import CamelModel


class TimelineEventResponse(CamelModel):
    id: UUID
    case_id: UUID
    firm_id: UUID
    event_type: str
    title: str
    payload: dict[str, object] = Field(default_factory=dict)
    actor_id: UUID | None = None
    occurred_at: datetime
    created_at: datetime

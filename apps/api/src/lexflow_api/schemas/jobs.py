from datetime import datetime
from uuid import UUID

from lexflow_api.schemas.common import CamelModel


class JobResponse(CamelModel):
    id: UUID
    job_type: str
    status: str
    progress: int
    case_id: UUID | None = None
    resource_type: str | None = None
    resource_id: UUID | None = None
    result: dict[str, object] | None = None
    error: dict[str, object] | None = None
    created_at: datetime
    started_at: datetime | None = None
    completed_at: datetime | None = None


class JobAcceptedResponse(CamelModel):
    job_id: UUID
    status: str
    status_url: str

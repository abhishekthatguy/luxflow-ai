from datetime import datetime
from uuid import UUID

from lexflow_api.schemas.common import CamelModel


class AuditLogResponse(CamelModel):
    id: UUID
    firm_id: UUID
    actor_id: UUID | None
    action: str
    resource_type: str
    resource_id: UUID | None
    details: dict[str, object]
    created_at: datetime

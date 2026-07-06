from datetime import datetime
from uuid import UUID

from pydantic import model_validator

from lexflow_api.schemas.common import CamelModel


class NotificationResponse(CamelModel):
    id: UUID
    user_id: UUID
    case_id: UUID | None
    firm_id: UUID
    channel: str
    title: str
    body: str
    status: str
    read_at: datetime | None
    sent_at: datetime | None
    metadata: dict[str, object]
    created_at: datetime

    @model_validator(mode="before")
    @classmethod
    def _normalize_orm(cls, data: object) -> object:
        if not hasattr(data, "id"):
            return data
        channel = data.channel.value if hasattr(data.channel, "value") else data.channel
        status = data.status.value if hasattr(data.status, "value") else data.status
        return {
            "id": data.id,
            "user_id": data.user_id,
            "case_id": data.case_id,
            "firm_id": data.firm_id,
            "channel": channel,
            "title": data.title,
            "body": data.body,
            "status": status,
            "read_at": data.read_at,
            "sent_at": data.sent_at,
            "metadata": getattr(data, "metadata_", {}),
            "created_at": data.created_at,
        }

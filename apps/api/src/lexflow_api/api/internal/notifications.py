from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel, Field

from lexflow_api.schemas.common import Envelope, envelope
from lexflow_api.services.admin_notification_service import AdminNotificationService

router = APIRouter(prefix="/internal/notifications", tags=["internal-notifications"])


class AdminNotifyRequest(BaseModel):
    subject: str = Field(min_length=1, max_length=500)
    body: str = Field(min_length=1)
    source: str = "n8n"
    metadata: dict[str, object] = Field(default_factory=dict)


def _request_id(request: Request) -> str | None:
    return getattr(request.state, "correlation_id", None)


@router.post("/admin", response_model=Envelope[dict[str, object]])
async def notify_admins(
    request: Request,
    body: AdminNotifyRequest,
) -> Envelope[dict[str, object]]:
    """Fan-out email alerts to all configured admin addresses."""
    result = await AdminNotificationService().notify(
        subject=body.subject,
        body=body.body,
        source=body.source,
        metadata=body.metadata,
    )
    return envelope(result, _request_id(request))

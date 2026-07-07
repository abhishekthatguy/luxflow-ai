from fastapi import APIRouter, Request
from pydantic import BaseModel, Field

import logging

from lexflow_api.schemas.common import Envelope, envelope
from lexflow_api.services.admin_notification_service import AdminNotificationService

logger = logging.getLogger(__name__)

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
    try:
        result = await AdminNotificationService().notify(
            subject=body.subject,
            body=body.body,
            source=body.source,
            metadata=body.metadata,
        )
    except Exception as exc:
        logger.exception("admin notification failed source=%s", body.source)
        result = {"status": "error", "message": str(exc), "source": body.source}
    return envelope(result, _request_id(request))


@router.post("/slack/test", response_model=Envelope[dict[str, object]])
async def test_slack_notification(request: Request) -> Envelope[dict[str, object]]:
    """Post a test message to Slack via n8n notification-slack-v1."""
    import httpx

    from lexflow_api.config import settings
    from lexflow_api.domain.notification_events import NotificationEventType
    from lexflow_api.services.notifications.slack_notification_service import build_slack_message
    from uuid import uuid4

    if not settings.slack_configured:
        return envelope(
            {
                "status": "skipped",
                "reason": "Set SLACK_WEBHOOK_URL or SLACK_BOT_TOKEN + SLACK_TEAM_CHANNEL_ID",
                "channelId": settings.slack_team_channel_id,
            },
            _request_id(request),
        )

    cid = uuid4()
    message = build_slack_message(
        event_type=NotificationEventType.SYSTEM_ALERT,
        title="LexFlow Slack test",
        description="Team channel integration is working. You will receive follow-up alerts here.",
        context={"status_badge": "Test", "workflow_slug": "slack-test"},
        correlation_id=cid,
    )
    n8n_url = (
        f"{settings.n8n_internal_url.rstrip('/')}/webhook/{settings.n8n_notification_slack_slug}"
    )
    body = {
        "correlationId": str(cid),
        "slackBotToken": settings.slack_bot_token.strip() or None,
        "slackChannelId": settings.slack_team_channel_id.strip() or None,
        "slackWebhookUrl": settings.slack_webhook_url.strip() or None,
        "message": message,
        "eventType": NotificationEventType.SYSTEM_ALERT.value,
        "workflowSlug": "slack-test",
    }
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(n8n_url, json=body)
        if response.status_code >= 400:
            return envelope(
                {
                    "status": "failed",
                    "correlationId": str(cid),
                    "error": response.text[:300],
                    "n8nUrl": n8n_url,
                },
                _request_id(request),
            )
        return envelope(
            {
                "status": "sent",
                "correlationId": str(cid),
                "channelId": settings.slack_team_channel_id,
                "provider": "n8n_orchestration",
            },
            _request_id(request),
        )
    except Exception as exc:
        logger.exception("slack test via n8n failed correlation=%s", cid)
        return envelope(
            {
                "status": "failed",
                "correlationId": str(cid),
                "error": str(exc)[:300],
                "n8nUrl": n8n_url,
            },
            _request_id(request),
        )

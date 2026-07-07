"""Notification delivery tasks — emit events, email, Teams orchestration."""

from __future__ import annotations

import asyncio
import logging
import time
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

import httpx

from lexflow_api.celery_app import celery_app
from lexflow_api.config import settings
from lexflow_api.db.session import async_session_factory
from lexflow_api.db.sync_session import SyncSessionLocal
from lexflow_api.domain.notification_events import NotificationEventType
from lexflow_api.models.notifications import NotificationDelivery
from lexflow_api.services.email_service import send_email_sync
from lexflow_api.services.notifications.notification_engine import NotificationEngine, NotificationEvent

logger = logging.getLogger(__name__)
_MAX_RETRIES = 4


def _parse_n8n_delivery_status(
    response: httpx.Response,
    *,
    configured: bool,
) -> tuple[str, str | None]:
    """Map n8n webhook JSON to delivery status (sent | stub | failed)."""
    if response.status_code >= 400:
        return "failed", response.text[:300]
    try:
        body = response.json()
    except Exception:
        return ("sent" if configured else "stub"), None
    if not isinstance(body, dict):
        return ("sent" if configured else "stub"), None
    n8n_status = str(body.get("status") or "")
    if n8n_status == "failed":
        return "failed", str(body.get("error") or body.get("message") or "n8n delivery failed")[:300]
    if n8n_status == "stub":
        return "stub", str(body.get("message") or "channel not configured")[:300]
    if n8n_status == "accepted":
        return "sent", None
    return ("sent" if configured else "stub"), None


def _record_delivery(
    session,
    *,
    firm_id: UUID,
    channel: str,
    provider: str,
    status: str,
    correlation_id: UUID | None,
    workflow_slug: str | None,
    workflow_execution_id: UUID | None,
    latency_ms: int | None,
    error_message: str | None,
    payload: dict[str, object],
    attempts: int,
) -> None:
    session.add(
        NotificationDelivery(
            firm_id=firm_id,
            channel=channel,
            provider=provider,
            status=status,
            attempts=attempts,
            max_attempts=_MAX_RETRIES,
            correlation_id=correlation_id,
            workflow_slug=workflow_slug,
            workflow_execution_id=workflow_execution_id,
            latency_ms=latency_ms,
            error_message=error_message,
            payload=payload,
            updated_at=datetime.now(UTC),
        )
    )


async def _emit_async(payload: dict[str, Any]) -> dict[str, Any]:
    event_type = NotificationEventType(str(payload["event_type"]))
    async with async_session_factory() as session:
        engine = NotificationEngine(session)
        result = await engine.emit(
            NotificationEvent(
                event_type=event_type,
                firm_id=UUID(str(payload["firm_id"])),
                title=str(payload["title"]),
                description=str(payload["description"]),
                case_id=UUID(str(payload["case_id"])) if payload.get("case_id") else None,
                correlation_id=UUID(str(payload["correlation_id"])) if payload.get("correlation_id") else None,
                workflow_slug=str(payload["workflow_slug"]) if payload.get("workflow_slug") else None,
                workflow_execution_id=(
                    UUID(str(payload["workflow_execution_id"]))
                    if payload.get("workflow_execution_id")
                    else None
                ),
                priority=str(payload["priority"]) if payload.get("priority") else None,
                status_badge=str(payload.get("status_badge") or "Update"),
                context=dict(payload.get("context") or {}),
                actor_id=UUID(str(payload["actor_id"])) if payload.get("actor_id") else None,
                recipient_user_ids={
                    UUID(str(x)) for x in payload.get("recipient_user_ids") or []
                }
                or None,
            )
        )
        await session.commit()
        return {
            "correlationId": str(result.correlation_id),
            "inApp": result.in_app_count,
            "emailQueued": result.email_queued,
            "teamsQueued": result.teams_queued,
            "slackQueued": result.slack_queued,
        }


@celery_app.task(name="lexflow_api.tasks.notification_tasks.emit_notification_event")
def emit_notification_event(payload: dict[str, Any]) -> dict[str, Any]:
    try:
        return asyncio.run(_emit_async(payload))
    except Exception:
        logger.exception("emit_notification_event failed event_type=%s", payload.get("event_type"))
        raise


@celery_app.task(
    bind=True,
    name="lexflow_api.tasks.notification_tasks.deliver_email_notification",
    max_retries=3,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_backoff_max=120,
)
def deliver_email_notification(self, payload: dict[str, object]) -> dict[str, object]:
    intended_to = str(payload["to"])
    if not settings.is_deliverable_notification_email(intended_to):
        logger.info("EMAIL_SKIP undeliverable_demo_address to=%s", intended_to)
        return {"status": "skipped", "to": intended_to, "reason": "demo_address"}

    to, subject_prefix, redirected = settings.resolve_notification_email(intended_to)
    subject = subject_prefix + str(payload["subject"])
    html_body = str(payload.get("html_body") or "")
    plain_body = str(payload.get("plain_body") or subject)
    firm_id = UUID(str(payload["firm_id"]))
    correlation_id = UUID(str(payload["correlation_id"])) if payload.get("correlation_id") else None
    attempt = self.request.retries + 1

    result = send_email_sync(to=to, subject=subject, body=plain_body, html_body=html_body or None)
    session = SyncSessionLocal()
    try:
        status = str(result.get("status", "failed"))
        if status == "failed" and attempt < _MAX_RETRIES:
            session.commit()
            raise RuntimeError(str(result.get("error", "email failed")))

        final_status = "dlq" if status == "failed" else status
        _record_delivery(
            session,
            firm_id=firm_id,
            channel="email",
            provider=str(result.get("provider", "smtp")),
            status=final_status,
            correlation_id=correlation_id,
            workflow_slug=str(payload.get("workflow_slug")) if payload.get("workflow_slug") else None,
            workflow_execution_id=(
                UUID(str(payload["workflow_execution_id"]))
                if payload.get("workflow_execution_id")
                else None
            ),
            latency_ms=int(result.get("latency_ms") or 0),
            error_message=str(result.get("error")) if result.get("error") else None,
            payload={
                "to": to,
                "intendedTo": intended_to,
                "redirected": redirected,
                "subject": subject,
                "eventType": payload.get("event_type"),
            },
            attempts=attempt,
        )
        session.commit()
        return {"status": final_status, **result}
    finally:
        session.close()


@celery_app.task(
    bind=True,
    name="lexflow_api.tasks.notification_tasks.deliver_teams_notification",
    max_retries=3,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_backoff_max=120,
)
def deliver_teams_notification(self, payload: dict[str, object]) -> dict[str, object]:
    firm_id = UUID(str(payload["firm_id"]))
    correlation_id = UUID(str(payload["correlation_id"])) if payload.get("correlation_id") else None
    card = payload.get("card") or {}
    attempt = self.request.retries + 1
    started = time.perf_counter()

    webhook_url = settings.teams_webhook_url.strip()
    n8n_url = f"{settings.n8n_internal_url.rstrip('/')}/webhook/{settings.n8n_notification_teams_slug}"
    body = {
        "correlationId": str(correlation_id) if correlation_id else None,
        "teamsWebhookUrl": webhook_url or None,
        "card": card,
        "eventType": payload.get("event_type"),
        "workflowSlug": payload.get("workflow_slug"),
    }

    status = "stub"
    error: str | None = None
    try:
        with httpx.Client(timeout=30.0) as client:
            response = client.post(n8n_url, json=body)
            status, error = _parse_n8n_delivery_status(
                response,
                configured=bool(webhook_url),
            )
    except Exception as exc:
        status = "failed"
        error = str(exc)[:300]
        if attempt < _MAX_RETRIES:
            raise
    if status == "failed" and attempt < _MAX_RETRIES:
        raise RuntimeError(error or "teams delivery failed")

    session = SyncSessionLocal()
    try:
        final_status = "dlq" if status == "failed" else status
        _record_delivery(
            session,
            firm_id=firm_id,
            channel="teams",
            provider="n8n_orchestration",
            status=final_status,
            correlation_id=correlation_id,
            workflow_slug=str(payload.get("workflow_slug")) if payload.get("workflow_slug") else None,
            workflow_execution_id=None,
            latency_ms=int((time.perf_counter() - started) * 1000),
            error_message=error,
            payload={"eventType": payload.get("event_type"), "hasWebhook": bool(webhook_url)},
            attempts=attempt,
        )
        session.commit()
        return {"status": final_status, "error": error}
    finally:
        session.close()


@celery_app.task(
    bind=True,
    name="lexflow_api.tasks.notification_tasks.deliver_slack_notification",
    max_retries=3,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_backoff_max=120,
)
def deliver_slack_notification(self, payload: dict[str, object]) -> dict[str, object]:
    firm_id = UUID(str(payload["firm_id"]))
    correlation_id = UUID(str(payload["correlation_id"])) if payload.get("correlation_id") else None
    message = dict(payload.get("message") or {})
    attempt = self.request.retries + 1
    started = time.perf_counter()

    bot_token = settings.slack_bot_token.strip()
    channel_id = settings.slack_team_channel_id.strip()
    webhook_url = settings.slack_webhook_url.strip()
    configured = settings.slack_configured
    n8n_url = f"{settings.n8n_internal_url.rstrip('/')}/webhook/{settings.n8n_notification_slack_slug}"
    body = {
        "correlationId": str(correlation_id) if correlation_id else None,
        "slackBotToken": bot_token or None,
        "slackChannelId": channel_id or None,
        "slackWebhookUrl": webhook_url or None,
        "message": message,
        "eventType": payload.get("event_type"),
        "workflowSlug": payload.get("workflow_slug"),
    }

    status = "stub"
    error: str | None = None
    try:
        with httpx.Client(timeout=30.0) as client:
            response = client.post(n8n_url, json=body)
            status, error = _parse_n8n_delivery_status(
                response,
                configured=configured,
            )
    except Exception as exc:
        status = "failed"
        error = str(exc)[:300]
        if attempt < _MAX_RETRIES:
            raise
    if status == "failed" and attempt < _MAX_RETRIES:
        raise RuntimeError(error or "slack delivery failed")

    session = SyncSessionLocal()
    try:
        final_status = "dlq" if status == "failed" else status
        _record_delivery(
            session,
            firm_id=firm_id,
            channel="slack",
            provider="n8n_orchestration",
            status=final_status,
            correlation_id=correlation_id,
            workflow_slug=str(payload.get("workflow_slug")) if payload.get("workflow_slug") else None,
            workflow_execution_id=(
                UUID(str(payload["workflow_execution_id"]))
                if payload.get("workflow_execution_id")
                else None
            ),
            latency_ms=int((time.perf_counter() - started) * 1000),
            error_message=error,
            payload={
                "eventType": payload.get("event_type"),
                "channelId": channel_id or None,
                "hasBot": bool(bot_token and channel_id),
                "hasWebhook": bool(webhook_url),
            },
            attempts=attempt,
        )
        session.commit()
        logger.info(
            "SLACK_NOTIFICATION status=%s channel=%s event=%s",
            final_status,
            channel_id or "webhook",
            payload.get("event_type"),
        )
        return {"status": final_status, "error": error}
    finally:
        session.close()


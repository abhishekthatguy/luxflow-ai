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
    to = str(payload["to"])
    subject = str(payload["subject"])
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
            payload={"to": to, "subject": subject, "eventType": payload.get("event_type")},
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
            if response.status_code >= 400:
                status = "failed"
                error = response.text[:300]
            else:
                status = "sent" if webhook_url else "stub"
    except Exception as exc:
        status = "failed"
        error = str(exc)[:300]
        if attempt < _MAX_RETRIES:
            raise

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


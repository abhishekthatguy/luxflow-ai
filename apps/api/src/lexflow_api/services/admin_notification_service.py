"""Admin notification fan-out via NotificationEngine."""

from __future__ import annotations

import logging
from typing import Any
from uuid import UUID

from sqlalchemy import select

from lexflow_api.config import settings
from lexflow_api.db.session import async_session_factory
from lexflow_api.domain.notification_events import NotificationEventType
from lexflow_api.models.identity import Firm
from lexflow_api.services.notifications.notification_engine import NotificationEngine, NotificationEvent

logger = logging.getLogger(__name__)


def _event_type_for_source(source: str) -> NotificationEventType:
    slug = source.lower()
    if "daily-partner" in slug or "partner-report" in slug:
        return NotificationEventType.DAILY_SUMMARY
    if "approval-escalation" in slug or "approval" in slug:
        return NotificationEventType.APPROVAL_REQUIRED
    if "ops-health" in slug or "health-monitor" in slug:
        return NotificationEventType.SYSTEM_ALERT
    return NotificationEventType.WORKFLOW_COMPLETED


class AdminNotificationService:
    async def notify(
        self,
        *,
        subject: str,
        body: str,
        source: str = "n8n",
        metadata: dict[str, object] | None = None,
        firm_id: UUID | None = None,
    ) -> dict[str, Any]:
        meta = dict(metadata or {})
        meta["source"] = source
        meta["email_subject"] = subject
        meta["report_summary"] = body
        meta["workflow_name"] = str(meta.get("workflow") or source)
        event_type = _event_type_for_source(source)

        async with async_session_factory() as session:
            if firm_id is None:
                firm = await session.scalar(select(Firm).limit(1))
                if firm is None:
                    return {"status": "skipped", "reason": "no firm"}
                firm_id = firm.id

            engine = NotificationEngine(session)
            result = await engine.emit(
                NotificationEvent(
                    event_type=event_type,
                    firm_id=firm_id,
                    title=subject,
                    description=body,
                    status_badge="Report" if event_type == NotificationEventType.DAILY_SUMMARY else "Alert",
                    context={
                        **meta,
                        "report_summary": body,
                        "error_message": body if "fail" in subject.lower() else None,
                    },
                    channels=frozenset({"email", "teams", "in_app"}),
                )
            )
            await session.commit()
            return {
                "status": "queued",
                "source": source,
                "eventType": event_type.value,
                "correlationId": str(result.correlation_id),
                "inApp": result.in_app_count,
                "emailQueued": result.email_queued,
                "teamsQueued": result.teams_queued,
                "slackQueued": result.slack_queued,
                "adminFallbackEmails": settings.admin_emails,
            }

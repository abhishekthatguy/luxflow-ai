"""Admin notification fan-out via NotificationEngine."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy import select

from lexflow_api.config import settings
from lexflow_api.db.session import async_session_factory
from lexflow_api.domain.notification_events import NotificationEventType
from lexflow_api.models.identity import Firm
from lexflow_api.services.notifications.notification_engine import NotificationEngine, NotificationEvent


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

        async with async_session_factory() as session:
            if firm_id is None:
                firm = await session.scalar(select(Firm).limit(1))
                if firm is None:
                    return {"status": "skipped", "reason": "no firm"}
                firm_id = firm.id

            engine = NotificationEngine(session)
            result = await engine.emit(
                NotificationEvent(
                    event_type=NotificationEventType.SYSTEM_ALERT,
                    firm_id=firm_id,
                    title=subject,
                    description=body,
                    status_badge="Alert",
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
                "correlationId": str(result.correlation_id),
                "inApp": result.in_app_count,
                "emailQueued": result.email_queued,
                "teamsQueued": result.teams_queued,
                "adminFallbackEmails": settings.admin_emails,
            }

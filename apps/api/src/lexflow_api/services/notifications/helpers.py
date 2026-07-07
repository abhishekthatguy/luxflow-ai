"""Convenience helpers to emit notifications from domain services."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from lexflow_api.domain.notification_events import NotificationEventType
from lexflow_api.services.notifications.notification_engine import NotificationEngine, NotificationEvent


async def emit_case_notification(
    session: AsyncSession,
    *,
    event_type: NotificationEventType,
    firm_id: UUID,
    case_id: UUID,
    title: str,
    description: str,
    status_badge: str = "Update",
    workflow_slug: str | None = None,
    workflow_execution_id: UUID | None = None,
    actor_id: UUID | None = None,
    recipient_user_ids: set[UUID] | None = None,
    context: dict[str, Any] | None = None,
):
    engine = NotificationEngine(session)
    return await engine.emit(
        NotificationEvent(
            event_type=event_type,
            firm_id=firm_id,
            case_id=case_id,
            title=title,
            description=description,
            status_badge=status_badge,
            workflow_slug=workflow_slug,
            workflow_execution_id=workflow_execution_id,
            actor_id=actor_id,
            recipient_user_ids=recipient_user_ids,
            context=context or {},
        )
    )


def queue_notification_event(payload: dict[str, Any]) -> None:
    from lexflow_api.tasks.notification_tasks import emit_notification_event

    emit_notification_event.delay(payload)

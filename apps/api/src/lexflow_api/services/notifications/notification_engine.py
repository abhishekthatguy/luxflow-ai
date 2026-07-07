"""Enterprise notification engine — all business rules live here."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from lexflow_api.domain.notification_events import NotificationEventType
from lexflow_api.models.notifications import NotificationChannel, NotificationStatus
from lexflow_api.services.audit import write_audit_log
from lexflow_api.services.notifications.context_builder import build_case_context, status_color_for
from lexflow_api.services.notifications.email_template_service import render_email, render_plain_summary
from lexflow_api.services.notifications.recipient_resolver import NotificationRecipient, RecipientResolver
from lexflow_api.services.notifications.teams_notification_service import build_teams_message_card
from lexflow_api.services.notification_service import NotificationService

logger = logging.getLogger(__name__)

# RBAC routing — which roles receive each event type
EVENT_ROLE_MAP: dict[NotificationEventType, frozenset[str]] = {
    NotificationEventType.CASE_CREATED: frozenset({"Attorney", "Associate", "ManagingPartner", "Paralegal"}),
    NotificationEventType.CASE_ASSIGNED: frozenset({"Attorney", "Associate"}),
    NotificationEventType.DOCUMENT_UPLOADED: frozenset({"Attorney", "Associate", "Paralegal"}),
    NotificationEventType.OCR_COMPLETED: frozenset({"Attorney", "Associate", "Paralegal"}),
    NotificationEventType.AI_SUMMARY_READY: frozenset({"Attorney", "Associate"}),
    NotificationEventType.AI_SUMMARY_APPROVED: frozenset({"ManagingPartner", "Attorney"}),
    NotificationEventType.WORKFLOW_STARTED: frozenset({"Attorney", "Paralegal"}),
    NotificationEventType.WORKFLOW_COMPLETED: frozenset({"Attorney", "ManagingPartner"}),
    NotificationEventType.WORKFLOW_FAILED: frozenset({"ManagingPartner", "SystemAdministrator", "Attorney"}),
    NotificationEventType.APPROVAL_REQUIRED: frozenset({"Attorney", "ManagingPartner"}),
    NotificationEventType.DAILY_SUMMARY: frozenset({"ManagingPartner"}),
    NotificationEventType.SYSTEM_ALERT: frozenset({"SystemAdministrator", "ManagingPartner"}),
}


@dataclass
class NotificationEvent:
    event_type: NotificationEventType
    firm_id: UUID
    title: str
    description: str
    case_id: UUID | None = None
    correlation_id: UUID | None = None
    workflow_slug: str | None = None
    workflow_execution_id: UUID | None = None
    priority: str | None = None
    status_badge: str = "Update"
    roles: frozenset[str] | None = None
    recipient_user_ids: set[UUID] | None = None
    context: dict[str, Any] = field(default_factory=dict)
    channels: frozenset[str] = frozenset({"in_app", "email", "teams"})
    actor_id: UUID | None = None


@dataclass
class NotificationDispatchResult:
    correlation_id: UUID
    in_app_count: int
    email_queued: int
    teams_queued: int


class NotificationEngine:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._notifications = NotificationService(session)
        self._resolver = RecipientResolver(session)

    async def emit(self, event: NotificationEvent) -> NotificationDispatchResult:
        correlation_id = event.correlation_id or uuid4()
        case_ctx = await build_case_context(
            self._session,
            firm_id=event.firm_id,
            case_id=event.case_id,
            extra=event.context,
        )
        case_ctx["status_badge"] = event.status_badge
        case_ctx["status_color"] = status_color_for(event.status_badge)
        case_ctx["workflow_name"] = event.context.get("workflow_name") or event.workflow_slug
        case_ctx["workflow_slug"] = event.workflow_slug
        case_ctx["workflow_execution_id"] = (
            str(event.workflow_execution_id) if event.workflow_execution_id else None
        )
        case_ctx["correlation_id"] = str(correlation_id)
        case_ctx["headline"] = event.title

        recipients = await self._resolve_recipients(event)
        subject, html_body = render_email(event.event_type, case_ctx)
        plain_body = render_plain_summary({**case_ctx, "headline": event.title})

        in_app_count = 0
        email_queued = 0

        for recipient in recipients:
            if "in_app" in event.channels and recipient.user_id:
                meta = {
                    **event.context,
                    "eventType": event.event_type.value,
                    "correlationId": str(correlation_id),
                    "workflowSlug": event.workflow_slug,
                    "priority": event.priority or case_ctx.get("priority"),
                    "actionUrl": case_ctx.get("case_url"),
                }
                await self._notifications.create_rich_in_app(
                    user_id=recipient.user_id,
                    firm_id=event.firm_id,
                    title=event.title,
                    body=event.description,
                    description=event.description,
                    case_id=event.case_id,
                    event_type=event.event_type.value,
                    correlation_id=correlation_id,
                    workflow_slug=event.workflow_slug,
                    workflow_execution_id=event.workflow_execution_id,
                    priority=event.priority or str(case_ctx.get("priority") or "normal"),
                    action_url=str(case_ctx.get("case_url") or ""),
                    metadata=meta,
                )
                in_app_count += 1

            if "email" in event.channels:
                from lexflow_api.tasks.notification_tasks import deliver_email_notification

                deliver_email_notification.delay(
                    {
                        "to": recipient.email,
                        "subject": subject,
                        "html_body": html_body,
                        "plain_body": plain_body,
                        "firm_id": str(event.firm_id),
                        "correlation_id": str(correlation_id),
                        "event_type": event.event_type.value,
                        "workflow_slug": event.workflow_slug,
                        "workflow_execution_id": (
                            str(event.workflow_execution_id) if event.workflow_execution_id else None
                        ),
                        "user_id": str(recipient.user_id) if recipient.user_id else None,
                        "case_id": str(event.case_id) if event.case_id else None,
                    }
                )
                email_queued += 1

        teams_queued = 0
        if "teams" in event.channels:
            teams_card = build_teams_message_card(
                event_type=event.event_type,
                title=event.title,
                description=event.description,
                context=case_ctx,
                correlation_id=correlation_id,
            )
            from lexflow_api.tasks.notification_tasks import deliver_teams_notification

            deliver_teams_notification.delay(
                {
                    "card": teams_card,
                    "firm_id": str(event.firm_id),
                    "correlation_id": str(correlation_id),
                    "event_type": event.event_type.value,
                    "workflow_slug": event.workflow_slug,
                }
            )
            teams_queued = 1

        await write_audit_log(
            self._session,
            firm_id=event.firm_id,
            actor_id=event.actor_id,
            action="notification.emitted",
            resource_type="notification",
            resource_id=correlation_id,
            details={
                "eventType": event.event_type.value,
                "correlationId": str(correlation_id),
                "inApp": in_app_count,
                "emailQueued": email_queued,
                "teamsQueued": teams_queued,
                "caseId": str(event.case_id) if event.case_id else None,
                "workflowSlug": event.workflow_slug,
            },
        )

        logger.info(
            "notification_emitted event_type=%s correlation_id=%s in_app=%s email=%s teams=%s",
            event.event_type.value,
            correlation_id,
            in_app_count,
            email_queued,
            teams_queued,
            extra={
                "correlation_id": str(correlation_id),
                "workflow_slug": event.workflow_slug,
                "event_type": event.event_type.value,
            },
        )

        return NotificationDispatchResult(
            correlation_id=correlation_id,
            in_app_count=in_app_count,
            email_queued=email_queued,
            teams_queued=teams_queued,
        )

    async def _resolve_recipients(self, event: NotificationEvent) -> list[NotificationRecipient]:
        if event.recipient_user_ids:
            return await self._resolver.resolve_case_participants(
                firm_id=event.firm_id,
                user_ids=event.recipient_user_ids,
            )
        roles = event.roles or EVENT_ROLE_MAP.get(event.event_type, frozenset({"Attorney"}))
        return await self._resolver.resolve_by_roles(firm_id=event.firm_id, roles=set(roles))

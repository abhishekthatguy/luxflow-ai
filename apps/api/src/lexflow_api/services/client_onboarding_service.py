"""Client onboarding notifications — welcome email + staff alerts (WF-04)."""

from __future__ import annotations

import logging
from uuid import UUID

from urllib.parse import quote

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from lexflow_api.config import settings
from lexflow_api.domain.notification_events import NotificationEventType
from lexflow_api.exceptions import NotFoundError, ValidationAppError
from lexflow_api.models.cases import Client
from lexflow_api.models.workflows import WorkflowExecution
from lexflow_api.services.notifications.email_template_service import render_email, render_plain_summary
from lexflow_api.services.notifications.notification_engine import NotificationEngine, NotificationEvent
from lexflow_api.services.password_reset_service import PasswordResetService

logger = logging.getLogger(__name__)


class ClientOnboardingService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_client_for_execution(self, execution: WorkflowExecution) -> Client:
        payload = execution.input_payload or {}
        client_id_raw = payload.get("clientId")
        if not client_id_raw:
            raise ValidationAppError("Workflow execution missing clientId in input payload.")
        client_id = UUID(str(client_id_raw))
        client = await self._session.scalar(
            select(Client).where(
                Client.id == client_id,
                Client.firm_id == execution.firm_id,
                Client.deleted_at.is_(None),
            )
        )
        if client is None:
            raise NotFoundError("Client not found for workflow execution.")
        return client

    def _client_context(self, client: Client) -> dict[str, object]:
        base = settings.notification_web_base_url.rstrip("/")
        query = f"name={quote(client.name)}"
        if client.email:
            query += f"&email={quote(client.email.strip())}"
        return {
            "client_name": client.name,
            "client_email": client.email or "—",
            "client_type": client.type,
            "client_url": f"{base}/clients/{client.id}",
            "portal_url": f"{base}/portal?{query}",
            "workflow_slug": "client-created-v1",
            "headline": f"Welcome, {client.name}",
            "status_badge": "Welcome",
        }

    async def send_welcome_email(
        self,
        execution: WorkflowExecution,
    ) -> dict[str, object]:
        client = await self.get_client_for_execution(execution)
        if not client.email or not client.email.strip():
            return {
                "skipped": True,
                "reason": "Client has no email address.",
                "clientId": str(client.id),
            }

        ctx = self._client_context(client)
        invite = await PasswordResetService(self._session).send_portal_invite_for_client(
            client,
            send_email=False,
        )
        if invite.get("setupUrl"):
            ctx["setup_url"] = invite["setupUrl"]

        subject, html_body = render_email(NotificationEventType.CLIENT_WELCOME, ctx)
        plain_body = render_plain_summary(ctx)

        from lexflow_api.tasks.notification_tasks import deliver_email_notification

        deliver_email_notification.delay(
            {
                "to": client.email.strip(),
                "subject": subject,
                "html_body": html_body,
                "plain_body": plain_body,
                "firm_id": str(execution.firm_id),
                "correlation_id": str(execution.correlation_id or execution.id),
                "event_type": NotificationEventType.CLIENT_WELCOME.value,
                "workflow_slug": "client-created-v1",
                "workflow_execution_id": str(execution.id),
                "user_id": None,
                "case_id": None,
            }
        )
        logger.info(
            "client_welcome_email_queued client_id=%s to=%s execution_id=%s",
            client.id,
            client.email,
            execution.id,
        )
        return {
            "skipped": False,
            "clientId": str(client.id),
            "to": client.email.strip(),
            "emailQueued": 1,
            "portalInvite": invite,
        }

    async def notify_intake_team(
        self,
        execution: WorkflowExecution,
        *,
        actor_id: UUID | None = None,
    ) -> dict[str, object]:
        client = await self.get_client_for_execution(execution)
        ctx = self._client_context(client)
        engine = NotificationEngine(self._session)
        result = await engine.emit(
            NotificationEvent(
                event_type=NotificationEventType.CLIENT_CREATED,
                firm_id=execution.firm_id,
                title=f"New client: {client.name}",
                description=(
                    f"Client {client.name} ({client.email or 'no email'}) was added. "
                    "Assign intake and review CRM sync."
                ),
                status_badge="New Client",
                workflow_slug="client-created-v1",
                workflow_execution_id=execution.id,
                actor_id=actor_id,
                channels=frozenset({"email", "in_app"}),
                include_admin_emails=True,
                context=ctx,
            )
        )
        return {
            "clientId": str(client.id),
            "emailQueued": result.email_queued,
            "inAppCount": result.in_app_count,
            "adminFallbackEmails": settings.admin_emails,
        }

    async def record_crm_sync(self, execution: WorkflowExecution) -> dict[str, object]:
        client = await self.get_client_for_execution(execution)
        return {
            "clientId": str(client.id),
            "crmStatus": "acknowledged",
            "message": "CRM sync stub — client record available in LexFlow.",
        }

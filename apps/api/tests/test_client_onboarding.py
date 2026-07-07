"""Tests for client onboarding email service (WF-04)."""

from unittest.mock import patch
from uuid import uuid4

import pytest

from lexflow_api.domain.notification_events import NotificationEventType
from lexflow_api.services.client_onboarding_service import ClientOnboardingService
from lexflow_api.services.notifications.notification_engine import NotificationEvent


@pytest.mark.asyncio
async def test_welcome_email_queues_for_client_email() -> None:
    from lexflow_api.models.cases import Client
    from lexflow_api.models.workflows import WorkflowExecution

    client = Client(
        id=uuid4(),
        firm_id=uuid4(),
        name="Gitlime",
        type="individual",
        email="kashyapabhi688@gmail.com",
    )
    execution = WorkflowExecution(
        id=uuid4(),
        firm_id=client.firm_id,
        workflow_definition_id=uuid4(),
        status="queued",
        input_payload={"clientId": str(client.id)},
    )

    class FakeSession:
        async def scalar(self, _stmt):
            return client

    service = ClientOnboardingService(FakeSession())  # type: ignore[arg-type]

    with patch.object(service, "get_client_for_execution", return_value=client):
        with patch(
            "lexflow_api.services.client_onboarding_service.PasswordResetService"
        ) as mock_reset_cls:
            async def _fake_invite(*_a, **_k):
                return {
                    "setupUrl": "http://localhost:3000/portal/reset-password?token=test",
                    "skipped": False,
                }

            mock_reset_cls.return_value.send_portal_invite_for_client = _fake_invite
            with patch("lexflow_api.tasks.notification_tasks.deliver_email_notification") as mock_deliver:
                mock_deliver.delay = lambda payload: None
                result = await service.send_welcome_email(execution)

    assert result["skipped"] is False
    assert result["to"] == "kashyapabhi688@gmail.com"
    assert result["emailQueued"] == 1


def test_client_created_event_includes_admin_emails_flag() -> None:
    event = NotificationEvent(
        event_type=NotificationEventType.CLIENT_CREATED,
        firm_id=uuid4(),
        title="New client",
        description="Test",
        include_admin_emails=True,
    )
    assert event.include_admin_emails is True


@pytest.mark.asyncio
async def test_welcome_skipped_without_email() -> None:
    from lexflow_api.models.cases import Client
    from lexflow_api.models.workflows import WorkflowExecution

    client = Client(
        id=uuid4(),
        firm_id=uuid4(),
        name="No Email Co",
        type="organization",
        email=None,
    )
    execution = WorkflowExecution(
        id=uuid4(),
        firm_id=client.firm_id,
        workflow_definition_id=uuid4(),
        status="queued",
        input_payload={"clientId": str(client.id)},
    )
    service = ClientOnboardingService(None)  # type: ignore[arg-type]

    with patch.object(service, "get_client_for_execution", return_value=client):
        result = await service.send_welcome_email(execution)

    assert result["skipped"] is True

"""Tests for notification template rendering and Teams payload."""

from uuid import uuid4

from lexflow_api.domain.notification_events import NotificationEventType
from lexflow_api.services.notifications.email_template_service import render_email, render_plain_summary
from lexflow_api.services.notifications.slack_notification_service import build_slack_message
from lexflow_api.services.notifications.teams_notification_service import build_teams_message_card


def test_render_case_created_email_contains_case_title() -> None:
    ctx = {
        "case_title": "Motor Vehicle Accident Claim",
        "client_name": "John Doe",
        "attorney_name": "Jane Attorney",
        "status_badge": "Created",
        "status_color": "#107C10",
        "practice_area": "litigation",
        "priority": "normal",
        "case_url": "http://localhost:3000/cases/abc/overview",
        "correlation_id": str(uuid4()),
    }
    subject, html = render_email(NotificationEventType.CASE_CREATED, ctx)
    assert "Motor Vehicle" in subject or "Motor Vehicle" in html
    assert "John Doe" in html
    assert "LexFlow AI" in html
    assert "Open Case" in html


def test_teams_message_card_has_actions() -> None:
    cid = uuid4()
    card = build_teams_message_card(
        event_type=NotificationEventType.DOCUMENT_UPLOADED,
        title="Document uploaded",
        description="Police Report.pdf uploaded",
        context={
            "case_title": "MVA Claim",
            "client_name": "John Doe",
            "status_badge": "Processing",
            "case_url": "http://localhost:3000/cases/x/overview",
        },
        correlation_id=cid,
    )
    assert card["@type"] == "MessageCard"
    actions = card["potentialAction"]
    assert len(actions) == 2
    assert actions[0]["name"] == "Open Case"


def test_plain_summary_fallback() -> None:
    text = render_plain_summary({"case_title": "Test Case", "status_badge": "Completed"})
    assert "Test Case" in text
    assert "Completed" in text


def test_slack_message_has_blocks_and_actions() -> None:
    cid = uuid4()
    msg = build_slack_message(
        event_type=NotificationEventType.CLIENT_CREATED,
        title="New client: Gitlime",
        description="Gitlime was added to LexFlow and is ready for intake.",
        context={
            "client_name": "Gitlime",
            "client_email": "kashyapabhi688@gmail.com",
            "client_url": "http://localhost:3000/clients/abc",
            "workflow_slug": "client-created-v1",
            "status_badge": "New Client",
        },
        correlation_id=cid,
    )
    attachments = msg["attachments"]
    assert attachments
    blocks = attachments[0]["blocks"]
    assert any(b.get("type") == "actions" for b in blocks)
    assert "Gitlime" in str(msg)
    assert "client.created" not in str(blocks)
    assert "What to do next" in str(blocks)


def test_slack_case_created_human_readable() -> None:
    cid = uuid4()
    msg = build_slack_message(
        event_type=NotificationEventType.CASE_CREATED,
        title="New case opened",
        description="",
        context={
            "case_title": "Smith v. Jones",
            "case_number": "2026-00026",
            "client_name": "John Smith",
            "attorney_name": "Jane Attorney",
            "case_url": "http://localhost:3000/cases/x/overview",
            "status_badge": "Created",
        },
        correlation_id=cid,
    )
    attachments = msg["attachments"]
    blocks_blob = str(attachments[0]["blocks"])
    assert "Smith v. Jones" in blocks_blob
    assert "2026-00026" in blocks_blob
    assert "case.created" not in blocks_blob
    assert "What to do next" in blocks_blob


def test_demo_emails_not_deliverable() -> None:
    from lexflow_api.config import settings

    assert settings.is_deliverable_notification_email("partner@example.com") is False
    assert settings.is_deliverable_notification_email("admin@example.com") is False
    assert settings.is_deliverable_notification_email("clawtbot@gmail.com") is True


"""Slack team channel notifications — Block Kit payloads for LexFlow follow-ups."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from lexflow_api.config import settings
from lexflow_api.domain.notification_events import NotificationEventType


def build_slack_message(
    *,
    event_type: NotificationEventType,
    title: str,
    description: str,
    context: dict[str, Any],
    correlation_id: UUID,
) -> dict[str, object]:
    """Build Slack incoming-webhook / chat.postMessage payload."""
    base = settings.notification_web_base_url.rstrip("/")
    case_url = str(context.get("case_url") or context.get("client_url") or f"{base}/clients")
    dashboard_url = f"{base}/operations"
    workflow = str(context.get("workflow_slug") or context.get("workflow_name") or event_type.value)

    fields = [
        {"type": "mrkdwn", "text": f"*Event*\n{event_type.value}"},
        {"type": "mrkdwn", "text": f"*Status*\n{context.get('status_badge') or 'Update'}"},
    ]
    if context.get("client_name"):
        fields.append({"type": "mrkdwn", "text": f"*Client*\n{context['client_name']}"})
    if context.get("client_email"):
        fields.append({"type": "mrkdwn", "text": f"*Email*\n{context['client_email']}"})
    if context.get("case_title"):
        fields.append({"type": "mrkdwn", "text": f"*Case*\n{context['case_title']}"})
    fields.append({"type": "mrkdwn", "text": f"*Workflow*\n{workflow}"})

    blocks: list[dict[str, object]] = [
        {
            "type": "header",
            "text": {"type": "plain_text", "text": title[:150], "emoji": True},
        },
        {
            "type": "section",
            "text": {"type": "mrkdwn", "text": description[:3000]},
        },
        {"type": "section", "fields": fields[:10]},
        {
            "type": "context",
            "elements": [
                {
                    "type": "mrkdwn",
                    "text": f"LexFlow AI · correlation `{correlation_id}`",
                }
            ],
        },
        {
            "type": "actions",
            "elements": [
                {
                    "type": "button",
                    "text": {"type": "plain_text", "text": "Open in LexFlow", "emoji": True},
                    "url": case_url,
                    "action_id": "open_lexflow",
                },
                {
                    "type": "button",
                    "text": {"type": "plain_text", "text": "Operations", "emoji": True},
                    "url": dashboard_url,
                    "action_id": "open_ops",
                },
            ],
        },
    ]

    return {
        "text": f"{title} — {description[:200]}",
        "blocks": blocks,
        "metadata": {
            "correlationId": str(correlation_id),
            "eventType": event_type.value,
            "workflowSlug": context.get("workflow_slug"),
        },
    }

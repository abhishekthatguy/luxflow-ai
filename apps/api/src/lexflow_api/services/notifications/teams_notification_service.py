"""Microsoft Teams Adaptive Card payload builder — no HTTP here (n8n orchestrates delivery)."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from lexflow_api.config import settings
from lexflow_api.domain.notification_events import NotificationEventType


def build_teams_message_card(
    *,
    event_type: NotificationEventType,
    title: str,
    description: str,
    context: dict[str, Any],
    correlation_id: UUID,
) -> dict[str, object]:
    """MessageCard format compatible with Teams Incoming Webhook."""
    case_url = context.get("case_url") or settings.notification_web_base_url
    dashboard_url = f"{settings.notification_web_base_url.rstrip('/')}/operations"

    facts = [
        {"name": "Case", "value": str(context.get("case_title") or "—")},
        {"name": "Client", "value": str(context.get("client_name") or "—")},
        {"name": "Workflow", "value": str(context.get("workflow_name") or event_type.value)},
        {"name": "Status", "value": str(context.get("status_badge") or "Update")},
        {"name": "Priority", "value": str(context.get("priority") or "Normal")},
        {"name": "Attorney", "value": str(context.get("attorney_name") or "—")},
    ]

    theme = _theme_color(context.get("status_badge"))

    return {
        "@type": "MessageCard",
        "@context": "https://schema.org/extensions",
        "summary": title,
        "themeColor": theme,
        "title": title,
        "text": description,
        "sections": [
            {
                "activityTitle": "LexFlow AI Workflow Engine",
                "facts": facts,
                "markdown": True,
            }
        ],
        "potentialAction": [
            {
                "@type": "OpenUri",
                "name": "Open Case",
                "targets": [{"os": "default", "uri": case_url}],
            },
            {
                "@type": "OpenUri",
                "name": "Open Dashboard",
                "targets": [{"os": "default", "uri": dashboard_url}],
            },
        ],
        "metadata": {
            "correlationId": str(correlation_id),
            "eventType": event_type.value,
            "workflowSlug": context.get("workflow_slug"),
            "workflowExecutionId": context.get("workflow_execution_id"),
        },
    }


def _theme_color(status: object) -> str:
    label = str(status or "").lower()
    if "fail" in label or "critical" in label:
        return "D13438"
    if "approv" in label or "complete" in label:
        return "107C10"
    if "pending" in label or "required" in label:
        return "FF8C00"
    return "0078D4"

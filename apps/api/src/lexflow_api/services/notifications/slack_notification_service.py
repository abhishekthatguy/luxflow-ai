"""Slack team channel notifications — human-readable Block Kit payloads."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from lexflow_api.config import settings
from lexflow_api.domain.notification_events import NotificationEventType

# Per-event copy: category label, emoji, and suggested next step for the team.
_EVENT_COPY: dict[NotificationEventType, dict[str, str]] = {
    NotificationEventType.CLIENT_CREATED: {
        "emoji": "👋",
        "category": "Client onboarding",
        "action": "Review the client profile and assign someone to handle intake.",
    },
    NotificationEventType.CASE_CREATED: {
        "emoji": "📂",
        "category": "New case",
        "action": "Open the case, upload documents, and kick off the intake workflow.",
    },
    NotificationEventType.CASE_ASSIGNED: {
        "emoji": "👤",
        "category": "Case assignment",
        "action": "Review the matter details and confirm your availability.",
    },
    NotificationEventType.DOCUMENT_UPLOADED: {
        "emoji": "📄",
        "category": "Document upload",
        "action": "OCR and indexing will run automatically — check back shortly.",
    },
    NotificationEventType.OCR_COMPLETED: {
        "emoji": "🔍",
        "category": "Document processed",
        "action": "Review extracted text and trigger an AI summary if needed.",
    },
    NotificationEventType.AI_SUMMARY_READY: {
        "emoji": "✨",
        "category": "AI summary ready",
        "action": "Review the draft summary and approve or request changes.",
    },
    NotificationEventType.AI_SUMMARY_APPROVED: {
        "emoji": "✅",
        "category": "AI summary approved",
        "action": "The approved summary is now available on the case record.",
    },
    NotificationEventType.WORKFLOW_STARTED: {
        "emoji": "▶️",
        "category": "Workflow started",
        "action": "Monitor progress from the case timeline or operations dashboard.",
    },
    NotificationEventType.WORKFLOW_COMPLETED: {
        "emoji": "🏁",
        "category": "Workflow completed",
        "action": "No action needed unless follow-up tasks were created.",
    },
    NotificationEventType.WORKFLOW_FAILED: {
        "emoji": "🚨",
        "category": "Workflow error",
        "action": "Open operations, inspect the failed step, and retry or escalate.",
    },
    NotificationEventType.APPROVAL_REQUIRED: {
        "emoji": "⏳",
        "category": "Approval pending",
        "action": "An item has been waiting over 24 hours — please review and approve.",
    },
    NotificationEventType.DAILY_SUMMARY: {
        "emoji": "📊",
        "category": "Daily digest",
        "action": "Review firm-wide metrics and follow up on flagged items.",
    },
    NotificationEventType.SYSTEM_ALERT: {
        "emoji": "⚠️",
        "category": "System alert",
        "action": "Check the operations dashboard and resolve any failing dependencies.",
    },
}


def build_slack_message(
    *,
    event_type: NotificationEventType,
    title: str,
    description: str,
    context: dict[str, Any],
    correlation_id: UUID,
) -> dict[str, object]:
    """Build Slack chat.postMessage payload with readable Block Kit layout."""
    copy = _EVENT_COPY.get(event_type, {"emoji": "📣", "category": "Update", "action": ""})
    emoji = copy["emoji"]
    category = copy["category"]
    next_step = copy["action"]

    base = settings.notification_web_base_url.rstrip("/")
    case_url = str(context.get("case_url") or context.get("client_url") or f"{base}/clients")
    dashboard_url = f"{base}/operations"

    headline = _clean_headline(title, emoji=emoji)
    summary = _human_summary(description, context=context, event_type=event_type)
    status_badge = str(context.get("status_badge") or "Update")
    theme_color = _theme_color(status_badge)

    detail_fields = _detail_fields(context=context, status_badge=status_badge, event_type=event_type)

    blocks: list[dict[str, object]] = [
        {
            "type": "header",
            "text": {"type": "plain_text", "text": headline[:150], "emoji": True},
        },
        {
            "type": "section",
            "text": {"type": "mrkdwn", "text": summary[:3000]},
        },
    ]

    if detail_fields:
        blocks.append({"type": "divider"})
        blocks.append({"type": "section", "fields": detail_fields[:10]})

    if next_step and event_type != NotificationEventType.WORKFLOW_COMPLETED:
        blocks.append(
            {
                "type": "section",
                "text": {"type": "mrkdwn", "text": f"*What to do next*\n{next_step}"},
            }
        )

    timestamp = str(context.get("timestamp") or datetime.now(UTC).strftime("%d %b %Y, %H:%M UTC"))
    ref = str(correlation_id).split("-")[0]
    blocks.extend(
        [
            {"type": "divider"},
            {
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": f"LexFlow AI · {category} · {timestamp} · ref `{ref}`",
                    }
                ],
            },
            {
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": "View in LexFlow", "emoji": True},
                        "url": case_url,
                        "action_id": "open_lexflow",
                        "style": "primary",
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
    )

    fallback = f"{headline} — {summary[:200]}"

    return {
        "text": fallback,
        "attachments": [{"color": theme_color, "blocks": blocks}],
        "metadata": {
            "correlationId": str(correlation_id),
            "eventType": event_type.value,
            "workflowSlug": context.get("workflow_slug"),
        },
    }


def _clean_headline(title: str, *, emoji: str) -> str:
    """Strip email-style prefixes and duplicate emoji from titles."""
    cleaned = title.strip()
    for prefix in ("[LexFlow] ", "[LexFlow]", "LexFlow: ", "LexFlow — "):
        if cleaned.startswith(prefix):
            cleaned = cleaned[len(prefix) :].strip()
    if cleaned.startswith(emoji):
        return cleaned
    return f"{emoji}  {cleaned}"


def _human_summary(
    description: str,
    *,
    context: dict[str, Any],
    event_type: NotificationEventType,
) -> str:
    """Prefer a plain-language summary; fall back to structured context."""
    body = (description or "").strip()
    if body and not _looks_technical(body):
        return body

    parts: list[str] = []
    case_title = context.get("case_title")
    case_number = context.get("case_number")
    client_name = context.get("client_name")

    if event_type == NotificationEventType.CLIENT_CREATED and client_name:
        parts.append(f"*{client_name}* has been added to LexFlow and is ready for intake.")
    elif event_type == NotificationEventType.CASE_CREATED and case_title:
        ref = f" ({case_number})" if case_number else ""
        parts.append(f"A new matter *{case_title}*{ref} was opened and assigned to the team.")
    elif event_type == NotificationEventType.AI_SUMMARY_APPROVED and case_title:
        parts.append(f"The AI summary for *{case_title}* was reviewed and approved.")
    elif event_type == NotificationEventType.WORKFLOW_FAILED:
        workflow = _friendly_workflow_name(context.get("workflow_slug") or context.get("workflow_name"))
        err = context.get("error_message") or body
        if workflow and case_title:
            parts.append(f"The *{workflow}* workflow failed on case *{case_title}*.")
        elif workflow:
            parts.append(f"The *{workflow}* workflow encountered an error.")
        if err and err != parts[-1] if parts else err:
            parts.append(str(err)[:500])
    elif event_type == NotificationEventType.SYSTEM_ALERT:
        parts.append(body or "A platform health check detected an issue that needs attention.")
    elif event_type == NotificationEventType.APPROVAL_REQUIRED:
        parts.append(body or "One or more items are waiting for attorney or partner approval.")
    elif event_type == NotificationEventType.DAILY_SUMMARY:
        report = context.get("report_summary") or body
        parts.append(str(report)[:800] if report else "Your daily firm digest is ready.")
    elif case_title:
        parts.append(f"Update on case *{case_title}*.")
        if body:
            parts.append(body)
    elif body:
        parts.append(body)
    else:
        parts.append("There is a new update in LexFlow that may need your attention.")

    return "\n".join(parts)


def _detail_fields(
    *,
    context: dict[str, Any],
    status_badge: str,
    event_type: NotificationEventType,
) -> list[dict[str, str]]:
    """Two-column detail grid — only show fields that add value."""
    fields: list[dict[str, str]] = []

    case_number = context.get("case_number")
    case_title = context.get("case_title")
    if case_number or case_title:
        case_line = case_title or "—"
        if case_number:
            case_line = f"{case_number} · {case_line}"
        fields.append({"type": "mrkdwn", "text": f"*Case*\n{case_line}"})

    if context.get("client_name"):
        fields.append({"type": "mrkdwn", "text": f"*Client*\n{context['client_name']}"})

    if context.get("attorney_name"):
        fields.append({"type": "mrkdwn", "text": f"*Lead attorney*\n{context['attorney_name']}"})

    if context.get("practice_area"):
        fields.append(
            {
                "type": "mrkdwn",
                "text": f"*Practice area*\n{str(context['practice_area']).replace('_', ' ').title()}",
            }
        )

    if context.get("priority"):
        fields.append(
            {
                "type": "mrkdwn",
                "text": f"*Priority*\n{str(context['priority']).title()}",
            }
        )

    workflow = _friendly_workflow_name(context.get("workflow_slug") or context.get("workflow_name"))
    if workflow and event_type in {
        NotificationEventType.WORKFLOW_FAILED,
        NotificationEventType.WORKFLOW_COMPLETED,
        NotificationEventType.WORKFLOW_STARTED,
    }:
        fields.append({"type": "mrkdwn", "text": f"*Automation*\n{workflow}"})

    if status_badge and status_badge not in {"Update", "Report"}:
        fields.append({"type": "mrkdwn", "text": f"*Status*\n{status_badge}"})

    return fields


def _friendly_workflow_name(slug: object) -> str | None:
    if not slug:
        return None
    name = str(slug).replace("-v1", "").replace("-v2", "").replace("-v3", "")
    return name.replace("-", " ").replace("_", " ").title()


def _looks_technical(text: str) -> bool:
    lowered = text.lower()
    markers = (
        "notificationengine",
        "celery",
        "wf-14",
        "n8n",
        "→",
        "failed probes:",
        "correlation",
    )
    return any(m in lowered for m in markers)


def _theme_color(status_badge: str) -> str:
    label = status_badge.lower()
    if "fail" in label or "critical" in label or "alert" in label:
        return "#D13438"
    if "approv" in label or "complete" in label:
        return "#107C10"
    if "pending" in label or "required" in label:
        return "#FF8C00"
    return "#0078D4"

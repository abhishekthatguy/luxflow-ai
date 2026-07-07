"""Workflow group definitions — used by build_workflows.py and documentation."""

from __future__ import annotations

SERIAL_PREFIX = "WF"

GROUPS: dict[str, dict[str, str]] = {
    "business": {
        "label": "Business",
        "folder": "business",
        "serial_range": "WF-01 – WF-06",
        "description": (
            "Core legal automation — case lifecycle, document pipeline, and AI approval flows. "
            "Triggered by domain events from FastAPI (case created, document uploaded, etc.)."
        ),
        "activate": "Yes — webhook workflows active in all environments",
        "n8n_tag": "business",
    },
    "notifications": {
        "label": "Notifications",
        "folder": "notifications",
        "serial_range": "WF-07",
        "description": (
            "Time-based reminders and escalations for pending attorney approvals and SLA breaches."
        ),
        "activate": "Yes — scheduled hourly",
        "n8n_tag": "notifications",
    },
    "reports": {
        "label": "Reports",
        "folder": "reports",
        "serial_range": "WF-08",
        "description": (
            "Scheduled operational digests for managing partners — pending work, failures, errors."
        ),
        "activate": "Yes — scheduled daily",
        "n8n_tag": "reports",
    },
    "infra": {
        "label": "Infrastructure",
        "folder": "infra",
        "serial_range": "WF-09",
        "description": (
            "Platform health monitoring — Redis, RabbitMQ, Celery, API. Creates incidents and "
            "alerts admins on failure."
        ),
        "activate": "Yes — scheduled every 5 minutes",
        "n8n_tag": "infra",
    },
    "test": {
        "label": "Test",
        "folder": "test",
        "serial_range": "WF-10",
        "description": (
            "CI and local smoke workflows. Manual trigger only — never wired to production traffic."
        ),
        "activate": "Manual only — do not enable for scheduled/webhook production traffic",
        "n8n_tag": "test",
    },
}

# Import order for n8n folder scanning (stable)
IMPORT_FOLDERS = [g["folder"] for g in GROUPS.values()]


def display_name(serial: int, short_name: str) -> str:
    """Canonical n8n workflow title: WF-01 · Case Intake Automation."""
    return f"{SERIAL_PREFIX}-{serial:02d} · {short_name}"

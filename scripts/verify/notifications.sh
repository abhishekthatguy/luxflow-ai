#!/usr/bin/env bash
# Notification engine smoke verification
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT/apps/api"

echo "==> Unit tests: notification engine"
python3 -m venv .venv 2>/dev/null || true
# shellcheck disable=SC1091
. .venv/bin/activate
pip install -q -e ".[dev]" 2>/dev/null
pytest -q tests/test_notification_engine.py

echo "==> Template render smoke"
python3 - <<'PY'
from lexflow_api.domain.notification_events import NotificationEventType
from lexflow_api.services.notifications.email_template_service import render_email

subject, html = render_email(
    NotificationEventType.WORKFLOW_COMPLETED,
    {
        "case_title": "Motor Vehicle Accident Claim",
        "client_name": "John Doe",
        "attorney_name": "Jane Attorney",
        "status_badge": "Completed",
        "status_color": "#107C10",
        "workflow_name": "Document Upload Pipeline",
        "current_stage": "AI Summary Generated",
        "timestamp": "09:42 UTC",
        "case_url": "http://localhost:3000/cases/demo/overview",
        "recent_activity": ["Upload completed", "OCR completed", "AI Summary completed"],
    },
)
assert "LexFlow AI" in html
assert "Open Case" in html
print("OK  HTML template rendered")
print(f"OK  Subject: {subject[:60]}...")
PY

echo "PASS notification verification"

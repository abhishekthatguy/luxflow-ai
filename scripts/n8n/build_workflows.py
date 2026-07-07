#!/usr/bin/env python3
"""Generate enterprise n8n workflow JSON files from catalog."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "n8n" / "workflows"

sys_path = Path(__file__).resolve().parent
if str(sys_path) not in __import__("sys").path:
    __import__("sys").path.insert(0, str(sys_path))
from workflow_groups import GROUPS, display_name  # noqa: E402
from enterprise_nodes import (  # noqa: E402
    build_document_upload_enterprise,
    build_notification_slack_workflow,
    build_notification_teams_workflow,
    build_scheduled_runner_workflow,
    build_session_heartbeat_workflow,
    build_session_init_workflow,
    build_standard_webhook_workflow,
    build_test_slack_notification_workflow,
    signed_callback_nodes,
    API_BASE,
)


# One-line purpose for each workflow (shown in index docs and n8n meta).
WORKFLOW_SUMMARIES: dict[str, str] = {
    "case-intake-v1": "New case created → validate, assign attorney, create tasks, notify Teams.",
    "document-upload-v1": "Document OCR done → request AI summary and create attorney approval task.",
    "ai-summary-approved-v1": "Attorney approves AI draft → notify partner, archive summary, audit.",
    "client-created-v1": "New client added → CRM sync, welcome email, assign intake team.",
    "case-closed-v1": "Case closed → archive documents, export PDF, email client, move to cold storage.",
    "ai-failure-recovery-v1": "AI job failed → retry 3×, then create human review and alert attorney.",
    "approval-escalation-v1": "Hourly SLA check → remind attorney; escalate to partner after 24h.",
    "daily-partner-report-v1": "Daily 8am digest → pending cases, failed AI jobs, workflow errors to partners.",
    "ops-health-monitor-v1": "Every 5 min → probe Redis, RabbitMQ, Celery, API; alert ops on failure.",
    "workflow-session-init-v1": "Run once — create orchestrator session token in Redis (WF-11).",
    "workflow-session-heartbeat-v1": "Every 5 min — refresh session; re-trigger WF-11 if expired.",
    "notification-teams-v1": "POST Adaptive Card payload to Microsoft Teams Incoming Webhook.",
    "notification-slack-v1": "POST Block Kit payload to Slack via Bot API or Incoming Webhook.",
    "test-slack-notification-v1": "Manual Slack smoke — switch test_mode in Pick Test Case node.",
    "smoke-callback-v1": "Manual CI smoke → verify n8n can reach FastAPI internal health endpoint.",
}


def _code_node(node_id: str, name: str, code: str, x: int) -> dict:
    return {
        "parameters": {"jsCode": code},
        "id": node_id,
        "name": name,
        "type": "n8n-nodes-base.code",
        "typeVersion": 2,
        "position": [x, 300],
    }


def _webhook_node(slug: str, x: int = 240) -> dict:
    return {
        "parameters": {
            "httpMethod": "POST",
            "path": slug,
            "responseMode": "onReceived",
            "options": {},
        },
        "id": "webhook",
        "name": "Webhook",
        "type": "n8n-nodes-base.webhook",
        "typeVersion": 2,
        "position": [x, 300],
        "webhookId": slug,
    }


def _schedule_node(cron: str, x: int = 240) -> dict:
    return {
        "parameters": {"rule": {"interval": [{"field": "cronExpression", "expression": cron}]}},
        "id": "schedule",
        "name": "Schedule",
        "type": "n8n-nodes-base.scheduleTrigger",
        "typeVersion": 1.2,
        "position": [x, 300],
    }


def _manual_node(x: int = 240, *, notes: str = "") -> dict:
    node: dict = {
        "parameters": {},
        "id": "manual",
        "name": "Manual Trigger",
        "type": "n8n-nodes-base.manualTrigger",
        "typeVersion": 1,
        "position": [x, 300],
    }
    if notes:
        node["notes"] = notes
    return node


def _http_callback_node(slug: str, x: int) -> dict:
    return {
        "parameters": {
            "method": "POST",
            "url": f"{API_BASE}/internal/webhooks/n8n/{slug}",
            "sendHeaders": True,
            "headerParameters": {
                "parameters": [
                    {"name": "X-LexFlow-Signature", "value": "={{ $json.callbackSignature }}"},
                ]
            },
            "sendBody": True,
            "specifyBody": "json",
            "jsonBody": "={{ $json.callbackBody }}",
        },
        "id": "callback",
        "name": "Callback API",
        "type": "n8n-nodes-base.httpRequest",
        "typeVersion": 4.2,
        "position": [x, 300],
    }


def _admin_notify_node(step_id: str, label: str, workflow_name: str, x: int) -> dict:
    subject = f"[LexFlow] {workflow_name} — {label}"
    return {
        "parameters": {
            "method": "POST",
            "url": "http://api:8000/internal/notifications/admin",
            "sendBody": True,
            "specifyBody": "json",
            "jsonBody": (
                '={"subject": '
                + json.dumps(subject)
                + ', "body": '
                + json.dumps(f"Workflow step completed: {label}")
                + ', "source": "n8n", "metadata": {"workflow": '
                + json.dumps(workflow_name)
                + ', "step": '
                + json.dumps(label)
                + ', "executionId": "{{ $execution.id }}"}}'
            ),
        },
        "id": step_id,
        "name": label,
        "type": "n8n-nodes-base.httpRequest",
        "typeVersion": 4.2,
        "position": [x, 300],
    }


def _chain_nodes(
    trigger: dict,
    steps: list[tuple[str, str]],
    *,
    slug: str = "",
    workflow_name: str = "",
    admin_notify_steps: set[str] | None = None,
    with_callback: bool = False,
    enterprise: bool = False,
) -> dict:
    if enterprise and slug:
        return build_standard_webhook_workflow(
            slug,
            trigger,
            steps,
            workflow_name=workflow_name,
            admin_notify_steps=admin_notify_steps,
            with_callback=with_callback,
        )

    notify_steps = admin_notify_steps or set()
    nodes = [trigger]
    x = 460
    last = trigger["name"]
    connections: dict = {}

    for step_id, label in steps:
        x += 220
        if label in notify_steps:
            nodes.append(_admin_notify_node(step_id, label, workflow_name, x))
        else:
            code = (
                f"const prev = $json.body ?? $json;\n"
                f"return [{{ json: {{ ...prev, step: '{label}', ok: true }} }}];"
            )
            nodes.append(_code_node(step_id, label, code, x))
        connections[last] = {"main": [[{"node": label, "type": "main", "index": 0}]]}
        last = label

    if with_callback and slug:
        cb_nodes, cb_conn, prep_name = signed_callback_nodes(slug, x + 220)
        nodes.extend(cb_nodes)
        connections[last] = {"main": [[{"node": prep_name, "type": "main", "index": 0}]]}
        connections.update(cb_conn)

    return {"nodes": nodes, "connections": connections}


def _write(path: Path, wf: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(wf, indent=2) + "\n")
    print(f"OK  {path.relative_to(ROOT)}")


CATALOG = [
    {
        "file": "business/case-intake-v1.json",
        "name": "Case Intake Automation",
        "slug": "case-intake-v1",
        "group": "business",
        "trigger": "webhook",
        "tags": ["case", "notifications", "business"],
        "meta": {
            "purpose": "Automate case intake — validate request, assign attorney, create tasks, notify Teams, audit.",
            "domain_event": "CaseCreated",
            "fastapi_trigger": "Outbox relay or POST /api/v1/cases/{id}/workflows/trigger",
            "trigger": "POST /webhook/case-intake-v1 (Case Created)",
            "input": {"caseId": "uuid", "firmId": "uuid", "clientId": "uuid", "executionId": "uuid"},
            "output": {"status": "completed", "assignedAttorney": "uuid"},
            "retries": 3,
            "failure": "Dead-letter queue + admin notification",
            "owner": "platform-team",
            "version": 1,
            "category": "case-management",
        },
        "steps": [
            ("validate", "Validate JWT"),
            ("case", "Get Case Details"),
            ("assign", "Assign Attorney"),
            ("task", "Create Task"),
            ("teams", "Notify Teams"),
            ("audit", "Audit"),
        ],
        "callback": True,
    },
    {
        "file": "business/document-upload-v1.json",
        "name": "Document Upload Pipeline",
        "slug": "document-upload-v1",
        "group": "business",
        "trigger": "webhook",
        "tags": ["documents", "ai", "business"],
        "meta": {
            "purpose": "Flagship E2E flow — OCR complete → AI summary → attorney notification → approval task.",
            "domain_event": "DocumentUploaded",
            "fastapi_trigger": "Celery workflow_tasks.trigger_document_upload_workflow after OCR",
            "trigger": "POST /webhook/document-upload-v1 (Document Uploaded)",
            "input": {"documentId": "uuid", "caseId": "uuid", "executionId": "uuid", "firmId": "uuid"},
            "output": {"status": "completed", "approvalTaskCreated": True},
            "retries": 3,
            "failure": "Mark execution failed; notify attorney + admin",
            "owner": "document-team",
            "version": 1,
            "category": "document-processing",
        },
        "steps": [
            ("ocr", "Wait for OCR"),
            ("ai", "Request AI Summary"),
            ("notify", "Notify Attorney"),
            ("approval", "Create Approval Task"),
        ],
        "callback": True,
        "enterprise_graph": "document-upload",
    },
    {
        "file": "business/ai-summary-approved-v1.json",
        "name": "AI Summary Approved",
        "slug": "ai-summary-approved-v1",
        "group": "business",
        "trigger": "webhook",
        "tags": ["ai", "case", "business"],
        "meta": {
            "purpose": "Post-approval — update case status, notify managing partner, archive summary, audit.",
            "domain_event": "SummaryApproved",
            "fastapi_trigger": "ai_service.approve_summary() → outbox event",
            "trigger": "POST /webhook/ai-summary-approved-v1",
            "input": {"summaryId": "uuid", "caseId": "uuid", "approvedBy": "uuid"},
            "output": {"status": "archived", "partnerNotified": True},
            "retries": 2,
            "failure": "Retry then escalate to partner",
            "owner": "ai-team",
            "version": 1,
            "category": "ai-approval",
        },
        "steps": [
            ("update", "Update Case"),
            ("partner", "Notify Managing Partner"),
            ("archive", "Archive Summary"),
            ("audit", "Audit"),
        ],
        "callback": True,
    },
    {
        "file": "business/client-created-v1.json",
        "name": "New Client Onboarding",
        "slug": "client-created-v1",
        "group": "business",
        "trigger": "webhook",
        "tags": ["case", "notifications", "business"],
        "meta": {
            "purpose": "CRM sync, welcome email, intake team assignment when a new client is created.",
            "domain_event": "ClientCreated",
            "fastapi_trigger": "clients API POST /api/v1/clients → outbox",
            "trigger": "POST /webhook/client-created-v1",
            "input": {"clientId": "uuid", "email": "string", "firmId": "uuid"},
            "output": {"crmSynced": True, "intakeAssigned": True},
            "retries": 3,
            "failure": "Manual intake queue",
            "owner": "client-success",
            "version": 1,
            "category": "case-management",
        },
        "steps": [
            ("crm", "CRM Sync"),
            ("welcome", "Welcome Email"),
            ("intake", "Assign Intake Team"),
            ("audit", "Audit"),
        ],
    },
    {
        "file": "business/case-closed-v1.json",
        "name": "Case Closed",
        "slug": "case-closed-v1",
        "group": "business",
        "trigger": "webhook",
        "tags": ["case", "documents", "business"],
        "meta": {
            "purpose": "Archive documents, export PDF, email client, move S3, audit when case closes.",
            "domain_event": "CaseStatusChanged(closed)",
            "fastapi_trigger": "cases API PATCH status=closed → outbox",
            "trigger": "POST /webhook/case-closed-v1",
            "input": {"caseId": "uuid", "firmId": "uuid"},
            "output": {"archived": True, "clientEmailed": True},
            "retries": 2,
            "failure": "Manual archive queue",
            "owner": "case-management",
            "version": 1,
            "category": "case-management",
        },
        "steps": [
            ("archive", "Archive Docs"),
            ("pdf", "Export PDF"),
            ("email", "Email Client"),
            ("s3", "Move S3"),
            ("audit", "Audit"),
        ],
    },
    {
        "file": "business/ai-failure-recovery-v1.json",
        "name": "AI Failure Recovery",
        "slug": "ai-failure-recovery-v1",
        "group": "business",
        "trigger": "webhook",
        "tags": ["ai", "operations", "business"],
        "meta": {
            "purpose": "Retry failed AI jobs 3× then create human review task and notify attorney.",
            "domain_event": "AIJobFailed",
            "fastapi_trigger": "ai_tasks failure handler → workflow execution",
            "trigger": "POST /webhook/ai-failure-recovery-v1",
            "input": {"jobId": "uuid", "caseId": "uuid", "documentId": "uuid"},
            "output": {"recovered": "boolean", "humanReview": "boolean"},
            "retries": 3,
            "failure": "Human review task + admin notification",
            "owner": "ai-team",
            "version": 1,
            "category": "ai-approval",
        },
        "steps": [
            ("r1", "Retry 1"),
            ("r2", "Retry 2"),
            ("r3", "Retry 3"),
            ("review", "Create Human Review"),
            ("notify", "Notify Attorney"),
        ],
        "admin_notify_steps": ["Notify Attorney"],
    },
    {
        "file": "notifications/approval-escalation-v1.json",
        "name": "Approval Escalation",
        "slug": "approval-escalation-v1",
        "group": "notifications",
        "trigger": "schedule",
        "cron": "0 * * * *",
        "tags": ["notifications", "case"],
        "meta": {
            "purpose": "Hourly SLA check — approvals pending >24h get reminder, then partner escalation.",
            "domain_event": None,
            "fastapi_trigger": "n8n schedule only (no FastAPI trigger)",
            "trigger": "Cron every hour",
            "input": {},
            "output": {"escalatedCount": "number", "remindersSent": "number"},
            "retries": 1,
            "failure": "Log + infra health-monitor alert",
            "owner": "operations-team",
            "version": 1,
            "category": "notifications",
        },
        "steps": [
            ("pending", "Pending Approval"),
            ("old", "Older than 24h"),
            ("remind", "Reminder"),
            ("still", "Still Pending"),
            ("escalate", "Escalate to Partner"),
        ],
        "admin_notify_steps": ["Reminder", "Escalate to Partner"],
    },
    {
        "file": "reports/daily-partner-report-v1.json",
        "name": "Daily Partner Report",
        "slug": "daily-partner-report-v1",
        "group": "reports",
        "trigger": "schedule",
        "cron": "0 8 * * *",
        "tags": ["reports", "operations"],
        "meta": {
            "purpose": "Morning digest — pending cases, failed AI jobs, workflow errors to partners.",
            "domain_event": None,
            "fastapi_trigger": "n8n schedule only",
            "trigger": "Cron daily 8:00 AM UTC",
            "input": {},
            "output": {"reportSent": True, "recipientCount": "number"},
            "retries": 1,
            "failure": "Retry once; admin alert",
            "owner": "operations-team",
            "version": 1,
            "category": "reports",
        },
        "steps": [
            ("pending", "Pending Cases"),
            ("ai", "Failed AI Jobs"),
            ("wf", "Workflow Errors"),
            ("email", "Email Partner"),
            ("teams", "Teams Notification"),
        ],
        "admin_notify_steps": ["Email Partner", "Teams Notification"],
    },
    {
        "file": "infra/health-monitor-v1.json",
        "name": "Operations Health Monitor",
        "slug": "ops-health-monitor-v1",
        "group": "infra",
        "trigger": "schedule",
        "cron": "*/5 * * * *",
        "tags": ["operations", "health", "infra"],
        "meta": {
            "purpose": "Every 5 min — probe Redis, RabbitMQ, Celery, API; create incident + alert admins.",
            "domain_event": None,
            "fastapi_trigger": "n8n schedule only",
            "trigger": "Cron every 5 minutes",
            "input": {},
            "output": {"healthy": True, "incidents": []},
            "retries": 0,
            "failure": "Self-alert via admin notification",
            "owner": "platform-team",
            "version": 1,
            "category": "infra",
        },
        "steps": [
            ("check", "Health Check"),
            ("redis", "Redis"),
            ("rabbit", "RabbitMQ"),
            ("celery", "Celery"),
            ("api", "API"),
            ("incident", "Create Incident"),
            ("notify", "Notify Ops"),
        ],
        "admin_notify_steps": ["Create Incident", "Notify Ops"],
    },
    {
        "file": "test/smoke-callback-v1.json",
        "name": "Platform Smoke Callback",
        "slug": "smoke-callback-v1",
        "group": "test",
        "trigger": "manual",
        "tags": ["platform", "health", "test"],
        "meta": {
            "purpose": "CI/local smoke — verifies n8n can reach FastAPI internal smoke endpoint.",
            "domain_event": None,
            "fastapi_trigger": "Manual / scripts/verify/n8n-callback.sh",
            "trigger": "Manual (CI / verify-n8n-callback)",
            "input": {},
            "output": {"status": "ok"},
            "retries": 0,
            "failure": "Fail CI gate",
            "owner": "platform-team",
            "version": 1,
            "category": "test",
        },
        "steps": [],
        "custom": "smoke",
    },
    {
        "file": "infra/workflow-session-init-v1.json",
        "name": "Workflow Session Initialize",
        "slug": "workflow-session-init-v1",
        "group": "infra",
        "trigger": "webhook",
        "tags": ["infra", "security", "session"],
        "meta": {
            "purpose": "Create orchestrator session in Redis — run once on deploy or when heartbeat detects expiry.",
            "domain_event": None,
            "fastapi_trigger": "Manual / POST /webhook/workflow-session-init-v1",
            "trigger": "Manual or webhook (also triggered by WF-12 on session expiry)",
            "input": {},
            "output": {"sessionToken": "string", "expiresAt": "iso8601"},
            "retries": 0,
            "failure": "Business workflows blocked until session initialized",
            "owner": "platform-team",
            "version": 1,
            "category": "infra",
        },
        "custom": "session-init",
    },
    {
        "file": "infra/workflow-session-heartbeat-v1.json",
        "name": "Workflow Session Heartbeat",
        "slug": "workflow-session-heartbeat-v1",
        "group": "infra",
        "trigger": "schedule",
        "cron": "*/5 * * * *",
        "tags": ["infra", "security", "session"],
        "meta": {
            "purpose": "Every 5 min — verify/refresh orchestrator session; re-run WF-11 if expired.",
            "domain_event": None,
            "fastapi_trigger": "n8n schedule only",
            "trigger": "Cron every 5 minutes",
            "input": {},
            "output": {"sessionValid": True, "requiresInitialize": False},
            "retries": 0,
            "failure": "Triggers WF-11 Initialize via webhook",
            "owner": "platform-team",
            "version": 1,
            "category": "infra",
        },
        "custom": "session-heartbeat",
    },
    {
        "file": "notifications/notification-teams-v1.json",
        "name": "Teams Notification Delivery",
        "slug": "notification-teams-v1",
        "group": "notifications",
        "trigger": "webhook",
        "tags": ["notifications", "teams"],
        "meta": {
            "purpose": "Deliver pre-built Adaptive Card to Microsoft Teams Incoming Webhook.",
            "domain_event": "NotificationTeamsRequested",
            "fastapi_trigger": "NotificationEngine Celery deliver_teams_notification",
            "trigger": "POST /webhook/notification-teams-v1",
            "input": {"card": "object", "teamsWebhookUrl": "string", "correlationId": "string"},
            "output": {"status": "accepted"},
            "retries": 3,
            "failure": "Retry with backoff; DLQ after max attempts",
            "owner": "platform-team",
            "version": 1,
            "category": "notifications",
        },
        "custom": "notification-teams",
    },
    {
        "file": "notifications/notification-slack-v1.json",
        "name": "Slack Notification Delivery",
        "slug": "notification-slack-v1",
        "group": "notifications",
        "trigger": "webhook",
        "tags": ["notifications", "slack"],
        "meta": {
            "purpose": "Deliver pre-built Block Kit message to Slack team channel.",
            "domain_event": "NotificationSlackRequested",
            "fastapi_trigger": "NotificationEngine Celery deliver_slack_notification",
            "trigger": "POST /webhook/notification-slack-v1",
            "input": {
                "message": "object",
                "slackBotToken": "string",
                "slackChannelId": "string",
                "slackWebhookUrl": "string",
                "correlationId": "string",
            },
            "output": {"status": "accepted"},
            "retries": 3,
            "failure": "Retry with backoff; DLQ after max attempts",
            "owner": "platform-team",
            "version": 1,
            "category": "notifications",
        },
        "custom": "notification-slack",
    },
    {
        "file": "test/test-slack-notification-v1.json",
        "name": "Slack Notification Smoke Test",
        "slug": "test-slack-notification-v1",
        "group": "test",
        "trigger": "manual",
        "tags": ["notifications", "slack", "test"],
        "meta": {
            "purpose": "Manual Slack smoke — test notification-slack-v1 from n8n editor with dummy payloads.",
            "domain_event": None,
            "fastapi_trigger": "Manual only — n8n editor Execute Workflow",
            "trigger": "Manual (n8n editor — do NOT activate)",
            "input": {"test_mode": "basic_text | client_created | case_created | workflow_failed | stub_no_credentials | via_fastapi"},
            "output": {"pass": True, "test_mode": "string", "actual": "accepted|stub|sent"},
            "retries": 0,
            "failure": "Inspect Report Result node — check SLACK_* env on n8n container",
            "owner": "platform-team",
            "version": 1,
            "category": "test",
        },
        "custom": "test-slack",
    },
]


for _idx, _item in enumerate(CATALOG, start=1):
    _item["serial"] = _idx
    _item.setdefault("summary", WORKFLOW_SUMMARIES.get(_item["slug"], _item["meta"]["purpose"]))


def _build_smoke(display: str, meta: dict) -> dict:
    return {
        "name": display,
        "nodes": [
            _manual_node(240),
            {
                "parameters": {
                    "method": "POST",
                    "url": "http://api:8000/internal/platform/smoke",
                    "sendBody": True,
                    "specifyBody": "json",
                    "jsonBody": '={"source": "n8n", "correlationId": "{{ $execution.id }}"}',
                },
                "id": "http",
                "name": "Call FastAPI Smoke",
                "type": "n8n-nodes-base.httpRequest",
                "typeVersion": 4.2,
                "position": [480, 300],
            },
        ],
        "connections": {"Manual Trigger": {"main": [[{"node": "Call FastAPI Smoke", "type": "main", "index": 0}]]}},
        "active": False,
        "settings": {"executionOrder": "v1"},
        "tags": [{"name": "wf-10"}],
        "meta": meta,
    }


def _prepare_catalog_item(item: dict) -> dict:
    group = item.get("group", "business")
    serial = int(item["serial"])
    short_name = str(item["name"])
    item["display_name"] = display_name(serial, short_name)
    item["meta"] = {
        **item.get("meta", {}),
        "group": group,
        "serial": serial,
        "summary": item.get("summary", ""),
    }
    tags = [f"wf-{serial:02d}"]
    item["tags"] = tags
    return item


def main() -> None:
    prepared = [_prepare_catalog_item(dict(item)) for item in CATALOG]
    for item in prepared:
        path = OUT / item["file"]
        title = item["display_name"]
        if item.get("custom") == "smoke":
            wf = _build_smoke(title, item["meta"])
        elif item.get("custom") == "test-slack":
            built = build_test_slack_notification_workflow(
                _manual_node(
                    notes=(
                        "Manual only — edit test_mode in Pick Test Case. "
                        "Do NOT activate. See test/slack-notification.test-cases.md"
                    ),
                ),
            )
            wf = {
                "name": title,
                **built,
                "active": False,
                "settings": {"executionOrder": "v1"},
                "tags": [{"name": t} for t in item["tags"]],
                "meta": item["meta"],
            }
        elif item.get("custom") == "session-init":
            built = build_session_init_workflow(_webhook_node(item["slug"]), _manual_node())
            wf = {
                "name": title,
                **built,
                "active": True,
                "settings": {"executionOrder": "v1"},
                "tags": [{"name": t} for t in item["tags"]],
                "meta": item["meta"],
            }
        elif item.get("custom") == "session-heartbeat":
            built = build_session_heartbeat_workflow(_schedule_node(item["cron"]))
            wf = {
                "name": title,
                **built,
                "active": True,
                "settings": {"executionOrder": "v1"},
                "tags": [{"name": t} for t in item["tags"]],
                "meta": item["meta"],
            }
        elif item.get("custom") == "notification-teams":
            built = build_notification_teams_workflow(_webhook_node(item["slug"]))
            wf = {
                "name": title,
                **built,
                "active": True,
                "settings": {"executionOrder": "v1"},
                "tags": [{"name": t} for t in item["tags"]],
                "meta": item["meta"],
            }
        elif item.get("custom") == "notification-slack":
            built = build_notification_slack_workflow(_webhook_node(item["slug"]))
            wf = {
                "name": title,
                **built,
                "active": True,
                "settings": {"executionOrder": "v1"},
                "tags": [{"name": t} for t in item["tags"]],
                "meta": item["meta"],
            }
        elif item["trigger"] == "webhook":
            if item.get("enterprise_graph") == "document-upload":
                built = build_document_upload_enterprise(
                    item["slug"],
                    _webhook_node(item["slug"]),
                )
            else:
                built = _chain_nodes(
                    _webhook_node(item["slug"]),
                    item["steps"],
                    slug=item["slug"],
                    workflow_name=title,
                    admin_notify_steps=set(item.get("admin_notify_steps", [])),
                    with_callback=item.get("callback", False),
                    enterprise=True,
                )
            wf = {
                "name": title,
                **built,
                "active": True,
                "settings": {"executionOrder": "v1"},
                "tags": [{"name": t} for t in item["tags"]],
                "meta": item["meta"],
            }
        elif item["trigger"] == "schedule":
            notify_on_failure = item["slug"] == "ops-health-monitor-v1"
            built = build_scheduled_runner_workflow(
                item["slug"],
                _schedule_node(item["cron"]),
                notify_on_failure=notify_on_failure,
            )
            wf = {
                "name": title,
                **built,
                "active": True,
                "settings": {"executionOrder": "v1"},
                "tags": [{"name": t} for t in item["tags"]],
                "meta": item["meta"],
            }
        else:
            continue
        _write(path, wf)

    catalog_out = prepared
    (OUT / "catalog.json").write_text(json.dumps(catalog_out, indent=2) + "\n")
    (OUT / "groups.json").write_text(json.dumps(GROUPS, indent=2) + "\n")
    data_out = ROOT / "apps" / "api" / "scripts" / "data" / "workflow_catalog.json"
    data_out.parent.mkdir(parents=True, exist_ok=True)
    data_out.write_text(json.dumps(catalog_out, indent=2) + "\n")
    print(f"OK  n8n/workflows/catalog.json ({len(catalog_out)} workflows)")
    print(f"OK  n8n/workflows/groups.json")
    print(f"OK  apps/api/scripts/data/workflow_catalog.json")

    import subprocess

    subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "n8n" / "generate_workflow_docs.py")],
        check=True,
        cwd=str(ROOT / "scripts" / "n8n"),
    )


if __name__ == "__main__":
    main()

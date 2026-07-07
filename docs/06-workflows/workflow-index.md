# Workflow Index — Quick Reference

Canonical naming: **`WF-NN · Short Title`** (e.g. `WF-02 · Document Upload Pipeline`).
Webhook slugs (`document-upload-v1`) are stable API identifiers — do not change.

| # | n8n name | Folder | Slug | Trigger | One-liner |
|---|----------|--------|------|---------|-----------|
| 1 | WF-01 · Case Intake Automation | `business/` | `case-intake-v1` | webhook | New case created → validate, assign attorney, create tasks, notify Teams. |
| 2 | WF-02 · Document Upload Pipeline | `business/` | `document-upload-v1` | webhook | Document OCR done → request AI summary and create attorney approval task. |
| 3 | WF-03 · AI Summary Approved | `business/` | `ai-summary-approved-v1` | webhook | Attorney approves AI draft → notify partner, archive summary, audit. |
| 4 | WF-04 · New Client Onboarding | `business/` | `client-created-v1` | webhook | New client added → CRM sync, welcome email, assign intake team. |
| 5 | WF-05 · Case Closed | `business/` | `case-closed-v1` | webhook | Case closed → archive documents, export PDF, email client, move to cold storage. |
| 6 | WF-06 · AI Failure Recovery | `business/` | `ai-failure-recovery-v1` | webhook | AI job failed → retry 3×, then create human review and alert attorney. |
| 7 | WF-07 · Approval Escalation | `notifications/` | `approval-escalation-v1` | schedule | Hourly SLA check → remind attorney; escalate to partner after 24h. |
| 8 | WF-08 · Daily Partner Report | `reports/` | `daily-partner-report-v1` | schedule | Daily 8am digest → pending cases, failed AI jobs, workflow errors to partners. |
| 9 | WF-09 · Operations Health Monitor | `infra/` | `ops-health-monitor-v1` | schedule | Every 5 min → probe Redis, RabbitMQ, Celery, API; alert ops on failure. |
| 10 | WF-10 · Platform Smoke Callback | `test/` | `smoke-callback-v1` | manual | Manual CI smoke → verify n8n can reach FastAPI internal health endpoint. |

## Folder groups

| Folder | Serials | Role |
|--------|---------|------|
| `business/` | WF-01 – WF-06 | Core legal automation — case lifecycle, document pipeline, and AI approval flows. |
| `notifications/` | WF-07 | Time-based reminders and escalations for pending attorney approvals and SLA breaches. |
| `reports/` | WF-08 | Scheduled operational digests for managing partners — pending work, failures, errors. |
| `infra/` | WF-09 | Platform health monitoring — Redis, RabbitMQ, Celery, API. |
| `test/` | WF-10 | CI and local smoke workflows. |

## n8n UI tips

- **Sort by name** — workflows appear in execution order (WF-01 … WF-10).
- **Filter by tag** — use `business`, `notifications`, `reports`, `infra`, or `test`.
- **Repo folders** mirror groups under `n8n/workflows/{folder}/`.

Regenerate: `make n8n-build` · Apply to n8n: `make n8n-import` · DB seed: `make seed-workflows`


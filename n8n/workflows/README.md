# n8n Workflow Repository

Auto-generated index. Source of truth: `scripts/n8n/build_workflows.py` → `catalog.json`.

## Folder groups

### `business/` — Business

Core legal automation — case lifecycle, document pipeline, and AI approval flows. Triggered by domain events from FastAPI (case created, document uploaded, etc.).

- **WF-01 · Case Intake Automation** — `case-intake-v1.json` (webhook/schedule)
  - New case created → validate, assign attorney, create tasks, notify Teams.
- **WF-02 · Document Upload Pipeline** — `document-upload-v1.json` (webhook/schedule)
  - Document OCR done → request AI summary and create attorney approval task.
- **WF-03 · AI Summary Approved** — `ai-summary-approved-v1.json` (webhook/schedule)
  - Attorney approves AI draft → notify partner, archive summary, audit.
- **WF-04 · New Client Onboarding** — `client-created-v1.json` (webhook/schedule)
  - New client added → CRM sync, welcome email, assign intake team.
- **WF-05 · Case Closed** — `case-closed-v1.json` (webhook/schedule)
  - Case closed → archive documents, export PDF, email client, move to cold storage.
- **WF-06 · AI Failure Recovery** — `ai-failure-recovery-v1.json` (webhook/schedule)
  - AI job failed → retry 3×, then create human review and alert attorney.

### `notifications/` — Notifications

Time-based reminders and escalations for pending attorney approvals and SLA breaches.

- **WF-07 · Approval Escalation** — `approval-escalation-v1.json` (webhook/schedule)
  - Hourly SLA check → remind attorney; escalate to partner after 24h.

### `reports/` — Reports

Scheduled operational digests for managing partners — pending work, failures, errors.

- **WF-08 · Daily Partner Report** — `daily-partner-report-v1.json` (webhook/schedule)
  - Daily 8am digest → pending cases, failed AI jobs, workflow errors to partners.

### `infra/` — Infrastructure

Platform health monitoring — Redis, RabbitMQ, Celery, API. Creates incidents and alerts admins on failure.

- **WF-09 · Operations Health Monitor** — `ops-health-monitor-v1.json` (webhook/schedule)
  - Every 5 min → probe Redis, RabbitMQ, Celery, API; alert ops on failure.

### `test/` — Test

CI and local smoke workflows. Manual trigger only — never wired to production traffic.

- **WF-10 · Platform Smoke Callback** — `smoke-callback-v1.json` (manual)
  - Manual CI smoke → verify n8n can reach FastAPI internal health endpoint.

## Commands

```bash
python3 scripts/n8n/build_workflows.py  # JSON + docs
make n8n-import                         # purge + import to n8n
make seed-workflows                     # PostgreSQL definitions
```

See [workflow-index.md](./workflow-index.md) for the one-line reference table.

See [docs/06-workflows/workflow-groups.md](../../docs/06-workflows/workflow-groups.md).


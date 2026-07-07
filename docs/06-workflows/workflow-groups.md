# Workflow Groups

**LexFlow AI** — n8n workflow organization by function

Workflows are grouped into five folders under `n8n/workflows/`. Each group has a distinct operational role, activation policy, and owner.

---

## Group index

| Group | Folder | Workflows | Activation |
|-------|--------|-----------|------------|
| **Business** | `business/` | 6 | Yes — webhook workflows active in all environments |
| **Notifications** | `notifications/` | 1 | Yes — scheduled hourly |
| **Reports** | `reports/` | 1 | Yes — scheduled daily |
| **Infrastructure** | `infra/` | 1 | Yes — scheduled every 5 minutes |
| **Test** | `test/` | 1 | Manual only — do not enable for scheduled/webhook production traffic |

---

## Business (`business/`)

Core legal automation — case lifecycle, document pipeline, and AI approval flows. Triggered by domain events from FastAPI (case created, document uploaded, etc.).

**Activation:** Yes — webhook workflows active in all environments

| Workflow | Slug | Trigger |
|----------|------|---------|
| Case Intake Automation | `case-intake-v1` | webhook |
| Document Upload Pipeline | `document-upload-v1` | webhook |
| AI Summary Approved | `ai-summary-approved-v1` | webhook |
| New Client Onboarding | `client-created-v1` | webhook |
| Case Closed | `case-closed-v1` | webhook |
| AI Failure Recovery | `ai-failure-recovery-v1` | webhook |

### What each workflow does

- **`case-intake-v1`** — Automate case intake — validate request, assign attorney, create tasks, notify Teams, audit.
- **`document-upload-v1`** — Flagship E2E flow — OCR complete → AI summary → attorney notification → approval task.
- **`ai-summary-approved-v1`** — Post-approval — update case status, notify managing partner, archive summary, audit.
- **`client-created-v1`** — CRM sync, welcome email, intake team assignment when a new client is created.
- **`case-closed-v1`** — Archive documents, export PDF, email client, move S3, audit when case closes.
- **`ai-failure-recovery-v1`** — Retry failed AI jobs 3× then create human review task and notify attorney.

---

## Notifications (`notifications/`)

Time-based reminders and escalations for pending attorney approvals and SLA breaches.

**Activation:** Yes — scheduled hourly

| Workflow | Slug | Trigger |
|----------|------|---------|
| Approval Escalation | `approval-escalation-v1` | schedule `0 * * * *` |

### What each workflow does

- **`approval-escalation-v1`** — Hourly SLA check — approvals pending >24h get reminder, then partner escalation.

---

## Reports (`reports/`)

Scheduled operational digests for managing partners — pending work, failures, errors.

**Activation:** Yes — scheduled daily

| Workflow | Slug | Trigger |
|----------|------|---------|
| Daily Partner Report | `daily-partner-report-v1` | schedule `0 8 * * *` |

### What each workflow does

- **`daily-partner-report-v1`** — Morning digest — pending cases, failed AI jobs, workflow errors to partners.

---

## Infrastructure (`infra/`)

Platform health monitoring — Redis, RabbitMQ, Celery, API. Creates incidents and alerts admins on failure.

**Activation:** Yes — scheduled every 5 minutes

| Workflow | Slug | Trigger |
|----------|------|---------|
| Operations Health Monitor | `ops-health-monitor-v1` | schedule `*/5 * * * *` |

### What each workflow does

- **`ops-health-monitor-v1`** — Every 5 min — probe Redis, RabbitMQ, Celery, API; create incident + alert admins.

---

## Test (`test/`)

CI and local smoke workflows. Manual trigger only — never wired to production traffic.

**Activation:** Manual only — do not enable for scheduled/webhook production traffic

| Workflow | Slug | Trigger |
|----------|------|---------|
| Platform Smoke Callback | `smoke-callback-v1` | manual |

### What each workflow does

- **`smoke-callback-v1`** — CI/local smoke — verifies n8n can reach FastAPI internal smoke endpoint.

---

## Related docs

- [Workflow technical reference](./workflow-technical-reference.md) — webhooks, payloads, callbacks
- [n8n/workflows/README.md](../../n8n/workflows/README.md) — repo folder guide
- [Workflow catalog UI](http://localhost:3000/workflows) — live status in LexFlow


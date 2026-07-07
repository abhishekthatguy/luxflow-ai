# Workflow Technical Reference

**LexFlow AI** — auto-generated from `n8n/workflows/catalog.json`

> Regenerate: `python3 scripts/n8n/build_workflows.py`

## Architecture

```
Domain Event → FastAPI (auth, audit) → workflow_executions row → Celery
    → POST n8n webhook (HMAC) → n8n steps → POST /internal/n8n/callback
```

Scheduled workflows run inside n8n on cron — no FastAPI trigger required.

## Environment URLs

| Context | n8n base | API internal |
|---------|----------|--------------|
| Local Docker | `http://n8n:5678` | `http://api:8000` |
| Local host (editor) | `http://localhost:5679` | `http://localhost:8000` |

## Authentication

| Direction | Mechanism |
|-----------|-----------|
| FastAPI → n8n webhook | `X-LexFlow-Signature` HMAC-SHA256 (`N8N_WEBHOOK_SECRET`) |
| n8n → FastAPI callback | Same HMAC on callback body |
| n8n → admin notify | Internal network only (no auth in local dev) |

## Workflow definitions (PostgreSQL)

Table: `workflows.workflow_definitions`. Seed: `make seed-workflows`.

---

## Business

### `case-intake-v1` — WF-01 · Case Intake Automation

| Field | Value |
|-------|-------|
| **Serial** | WF-01 |
| **Group** | `business` |
| **Owner** | platform-team |
| **Version** | v1 |
| **Trigger type** | `webhook` |
| **Retries** | 3 |
| **Repo path** | `n8n/workflows/business/case-intake-v1.json` |

#### Summary

New case created → validate, assign attorney, create tasks, notify Teams.

#### Purpose

Automate case intake — validate request, assign attorney, create tasks, notify Teams, audit.

#### Domain event

`CaseCreated`

#### FastAPI trigger

Outbox relay or POST /api/v1/cases/{id}/workflows/trigger

#### Webhook

- **Local:** `POST http://localhost:5679/webhook/case-intake-v1`
- **Docker internal:** `POST http://n8n:5678/webhook/case-intake-v1`

#### Callback

`POST http://api:8000/internal/n8n/callback` — HMAC-signed completion payload.

#### Input payload

```json
{
  "caseId": "uuid",
  "firmId": "uuid",
  "clientId": "uuid",
  "executionId": "uuid"
}
```

#### Output payload

```json
{
  "status": "completed",
  "assignedAttorney": "uuid"
}
```

#### Steps

1. **Validate JWT** (`validate`)
2. **Get Case Details** (`case`)
3. **Assign Attorney** (`assign`)
4. **Create Task** (`task`)
5. **Notify Teams** (`teams`)
6. **Audit** (`audit`)

#### Failure handling

Dead-letter queue + admin notification

#### Tags

`wf-01`

---

### `document-upload-v1` — WF-02 · Document Upload Pipeline

| Field | Value |
|-------|-------|
| **Serial** | WF-02 |
| **Group** | `business` |
| **Owner** | document-team |
| **Version** | v1 |
| **Trigger type** | `webhook` |
| **Retries** | 3 |
| **Repo path** | `n8n/workflows/business/document-upload-v1.json` |

#### Summary

Document OCR done → request AI summary and create attorney approval task.

#### Purpose

Flagship E2E flow — OCR complete → AI summary → attorney notification → approval task.

#### Domain event

`DocumentUploaded`

#### FastAPI trigger

Celery workflow_tasks.trigger_document_upload_workflow after OCR

#### Webhook

- **Local:** `POST http://localhost:5679/webhook/document-upload-v1`
- **Docker internal:** `POST http://n8n:5678/webhook/document-upload-v1`

#### Callback

`POST http://api:8000/internal/n8n/callback` — HMAC-signed completion payload.

#### Input payload

```json
{
  "documentId": "uuid",
  "caseId": "uuid",
  "executionId": "uuid",
  "firmId": "uuid"
}
```

#### Output payload

```json
{
  "status": "completed",
  "approvalTaskCreated": true
}
```

#### Steps

1. **Wait for OCR** (`ocr`)
2. **Request AI Summary** (`ai`)
3. **Notify Attorney** (`notify`)
4. **Create Approval Task** (`approval`)

#### Failure handling

Mark execution failed; notify attorney + admin

#### Tags

`wf-02`

---

### `ai-summary-approved-v1` — WF-03 · AI Summary Approved

| Field | Value |
|-------|-------|
| **Serial** | WF-03 |
| **Group** | `business` |
| **Owner** | ai-team |
| **Version** | v1 |
| **Trigger type** | `webhook` |
| **Retries** | 2 |
| **Repo path** | `n8n/workflows/business/ai-summary-approved-v1.json` |

#### Summary

Attorney approves AI draft → notify partner, archive summary, audit.

#### Purpose

Post-approval — update case status, notify managing partner, archive summary, audit.

#### Domain event

`SummaryApproved`

#### FastAPI trigger

ai_service.approve_summary() → outbox event

#### Webhook

- **Local:** `POST http://localhost:5679/webhook/ai-summary-approved-v1`
- **Docker internal:** `POST http://n8n:5678/webhook/ai-summary-approved-v1`

#### Callback

`POST http://api:8000/internal/n8n/callback` — HMAC-signed completion payload.

#### Input payload

```json
{
  "summaryId": "uuid",
  "caseId": "uuid",
  "approvedBy": "uuid"
}
```

#### Output payload

```json
{
  "status": "archived",
  "partnerNotified": true
}
```

#### Steps

1. **Update Case** (`update`)
2. **Notify Managing Partner** (`partner`)
3. **Archive Summary** (`archive`)
4. **Audit** (`audit`)

#### Failure handling

Retry then escalate to partner

#### Tags

`wf-03`

---

### `client-created-v1` — WF-04 · New Client Onboarding

| Field | Value |
|-------|-------|
| **Serial** | WF-04 |
| **Group** | `business` |
| **Owner** | client-success |
| **Version** | v1 |
| **Trigger type** | `webhook` |
| **Retries** | 3 |
| **Repo path** | `n8n/workflows/business/client-created-v1.json` |

#### Summary

New client added → CRM sync, welcome email, assign intake team.

#### Purpose

CRM sync, welcome email, intake team assignment when a new client is created.

#### Domain event

`ClientCreated`

#### FastAPI trigger

clients API POST /api/v1/clients → outbox

#### Webhook

- **Local:** `POST http://localhost:5679/webhook/client-created-v1`
- **Docker internal:** `POST http://n8n:5678/webhook/client-created-v1`

#### Input payload

```json
{
  "clientId": "uuid",
  "email": "string",
  "firmId": "uuid"
}
```

#### Output payload

```json
{
  "crmSynced": true,
  "intakeAssigned": true
}
```

#### Steps

1. **CRM Sync** (`crm`)
2. **Welcome Email** (`welcome`)
3. **Assign Intake Team** (`intake`)
4. **Audit** (`audit`)

#### Failure handling

Manual intake queue

#### Tags

`wf-04`

---

### `case-closed-v1` — WF-05 · Case Closed

| Field | Value |
|-------|-------|
| **Serial** | WF-05 |
| **Group** | `business` |
| **Owner** | case-management |
| **Version** | v1 |
| **Trigger type** | `webhook` |
| **Retries** | 2 |
| **Repo path** | `n8n/workflows/business/case-closed-v1.json` |

#### Summary

Case closed → archive documents, export PDF, email client, move to cold storage.

#### Purpose

Archive documents, export PDF, email client, move S3, audit when case closes.

#### Domain event

`CaseStatusChanged(closed)`

#### FastAPI trigger

cases API PATCH status=closed → outbox

#### Webhook

- **Local:** `POST http://localhost:5679/webhook/case-closed-v1`
- **Docker internal:** `POST http://n8n:5678/webhook/case-closed-v1`

#### Input payload

```json
{
  "caseId": "uuid",
  "firmId": "uuid"
}
```

#### Output payload

```json
{
  "archived": true,
  "clientEmailed": true
}
```

#### Steps

1. **Archive Docs** (`archive`)
2. **Export PDF** (`pdf`)
3. **Email Client** (`email`)
4. **Move S3** (`s3`)
5. **Audit** (`audit`)

#### Failure handling

Manual archive queue

#### Tags

`wf-05`

---

### `ai-failure-recovery-v1` — WF-06 · AI Failure Recovery

| Field | Value |
|-------|-------|
| **Serial** | WF-06 |
| **Group** | `business` |
| **Owner** | ai-team |
| **Version** | v1 |
| **Trigger type** | `webhook` |
| **Retries** | 3 |
| **Repo path** | `n8n/workflows/business/ai-failure-recovery-v1.json` |

#### Summary

AI job failed → retry 3×, then create human review and alert attorney.

#### Purpose

Retry failed AI jobs 3× then create human review task and notify attorney.

#### Domain event

`AIJobFailed`

#### FastAPI trigger

ai_tasks failure handler → workflow execution

#### Webhook

- **Local:** `POST http://localhost:5679/webhook/ai-failure-recovery-v1`
- **Docker internal:** `POST http://n8n:5678/webhook/ai-failure-recovery-v1`

#### Admin notifications

These steps call `POST http://api:8000/internal/notifications/admin`:

- Notify Attorney

#### Input payload

```json
{
  "jobId": "uuid",
  "caseId": "uuid",
  "documentId": "uuid"
}
```

#### Output payload

```json
{
  "recovered": "boolean",
  "humanReview": "boolean"
}
```

#### Steps

1. **Retry 1** (`r1`)
2. **Retry 2** (`r2`)
3. **Retry 3** (`r3`)
4. **Create Human Review** (`review`)
5. **Notify Attorney** (`notify`)

#### Failure handling

Human review task + admin notification

#### Tags

`wf-06`

---

## Notifications

### `approval-escalation-v1` — WF-07 · Approval Escalation

| Field | Value |
|-------|-------|
| **Serial** | WF-07 |
| **Group** | `notifications` |
| **Owner** | operations-team |
| **Version** | v1 |
| **Trigger type** | `schedule` |
| **Retries** | 1 |
| **Repo path** | `n8n/workflows/notifications/approval-escalation-v1.json` |

#### Summary

Hourly SLA check → remind attorney; escalate to partner after 24h.

#### Purpose

Hourly SLA check — approvals pending >24h get reminder, then partner escalation.

#### FastAPI trigger

n8n schedule only (no FastAPI trigger)

#### Schedule

Cron: `0 * * * *`

#### Admin notifications

These steps call `POST http://api:8000/internal/notifications/admin`:

- Reminder
- Escalate to Partner

#### Input payload

```json
{}
```

#### Output payload

```json
{
  "escalatedCount": "number",
  "remindersSent": "number"
}
```

#### Steps

1. **Pending Approval** (`pending`)
2. **Older than 24h** (`old`)
3. **Reminder** (`remind`)
4. **Still Pending** (`still`)
5. **Escalate to Partner** (`escalate`)

#### Failure handling

Log + infra health-monitor alert

#### Tags

`wf-07`

---

### `notification-teams-v1` — WF-13 · Teams Notification Delivery

| Field | Value |
|-------|-------|
| **Serial** | WF-13 |
| **Group** | `notifications` |
| **Owner** | platform-team |
| **Version** | v1 |
| **Trigger type** | `webhook` |
| **Retries** | 3 |
| **Repo path** | `n8n/workflows/notifications/notification-teams-v1.json` |

#### Summary

POST Adaptive Card payload to Microsoft Teams Incoming Webhook.

#### Purpose

Deliver pre-built Adaptive Card to Microsoft Teams Incoming Webhook.

#### Domain event

`NotificationTeamsRequested`

#### FastAPI trigger

NotificationEngine Celery deliver_teams_notification

#### Webhook

- **Local:** `POST http://localhost:5679/webhook/notification-teams-v1`
- **Docker internal:** `POST http://n8n:5678/webhook/notification-teams-v1`

#### Input payload

```json
{
  "card": "object",
  "teamsWebhookUrl": "string",
  "correlationId": "string"
}
```

#### Output payload

```json
{
  "status": "accepted"
}
```

#### Steps

_No steps (manual trigger only)._

#### Failure handling

Retry with backoff; DLQ after max attempts

#### Tags

`wf-13`

---

### `notification-slack-v1` — WF-14 · Slack Notification Delivery

| Field | Value |
|-------|-------|
| **Serial** | WF-14 |
| **Group** | `notifications` |
| **Owner** | platform-team |
| **Version** | v1 |
| **Trigger type** | `webhook` |
| **Retries** | 3 |
| **Repo path** | `n8n/workflows/notifications/notification-slack-v1.json` |

#### Summary

POST Block Kit payload to Slack via Bot API or Incoming Webhook.

#### Purpose

Deliver pre-built Block Kit message to Slack team channel.

#### Domain event

`NotificationSlackRequested`

#### FastAPI trigger

NotificationEngine Celery deliver_slack_notification

#### Webhook

- **Local:** `POST http://localhost:5679/webhook/notification-slack-v1`
- **Docker internal:** `POST http://n8n:5678/webhook/notification-slack-v1`

#### Input payload

```json
{
  "message": "object",
  "slackBotToken": "string",
  "slackChannelId": "string",
  "slackWebhookUrl": "string",
  "correlationId": "string"
}
```

#### Output payload

```json
{
  "status": "accepted"
}
```

#### Steps

_No steps (manual trigger only)._

#### Failure handling

Retry with backoff; DLQ after max attempts

#### Tags

`wf-14`

---

## Reports

### `daily-partner-report-v1` — WF-08 · Daily Partner Report

| Field | Value |
|-------|-------|
| **Serial** | WF-08 |
| **Group** | `reports` |
| **Owner** | operations-team |
| **Version** | v1 |
| **Trigger type** | `schedule` |
| **Retries** | 1 |
| **Repo path** | `n8n/workflows/reports/daily-partner-report-v1.json` |

#### Summary

Daily 8am digest → pending cases, failed AI jobs, workflow errors to partners.

#### Purpose

Morning digest — pending cases, failed AI jobs, workflow errors to partners.

#### FastAPI trigger

n8n schedule only

#### Schedule

Cron: `0 8 * * *`

#### Admin notifications

These steps call `POST http://api:8000/internal/notifications/admin`:

- Email Partner
- Teams Notification

#### Input payload

```json
{}
```

#### Output payload

```json
{
  "reportSent": true,
  "recipientCount": "number"
}
```

#### Steps

1. **Pending Cases** (`pending`)
2. **Failed AI Jobs** (`ai`)
3. **Workflow Errors** (`wf`)
4. **Email Partner** (`email`)
5. **Teams Notification** (`teams`)

#### Failure handling

Retry once; admin alert

#### Tags

`wf-08`

---

## Infrastructure

### `ops-health-monitor-v1` — WF-09 · Operations Health Monitor

| Field | Value |
|-------|-------|
| **Serial** | WF-09 |
| **Group** | `infra` |
| **Owner** | platform-team |
| **Version** | v1 |
| **Trigger type** | `schedule` |
| **Retries** | 0 |
| **Repo path** | `n8n/workflows/infra/health-monitor-v1.json` |

#### Summary

Every 5 min → probe Redis, RabbitMQ, Celery, API; alert ops on failure.

#### Purpose

Every 5 min — probe Redis, RabbitMQ, Celery, API; create incident + alert admins.

#### FastAPI trigger

n8n schedule only

#### Schedule

Cron: `*/5 * * * *`

#### Admin notifications

These steps call `POST http://api:8000/internal/notifications/admin`:

- Create Incident
- Notify Ops

#### Input payload

```json
{}
```

#### Output payload

```json
{
  "healthy": true,
  "incidents": []
}
```

#### Steps

1. **Health Check** (`check`)
2. **Redis** (`redis`)
3. **RabbitMQ** (`rabbit`)
4. **Celery** (`celery`)
5. **API** (`api`)
6. **Create Incident** (`incident`)
7. **Notify Ops** (`notify`)

#### Failure handling

Self-alert via admin notification

#### Tags

`wf-09`

---

### `workflow-session-init-v1` — WF-11 · Workflow Session Initialize

| Field | Value |
|-------|-------|
| **Serial** | WF-11 |
| **Group** | `infra` |
| **Owner** | platform-team |
| **Version** | v1 |
| **Trigger type** | `webhook` |
| **Retries** | 0 |
| **Repo path** | `n8n/workflows/infra/workflow-session-init-v1.json` |

#### Summary

Run once — create orchestrator session token in Redis (WF-11).

#### Purpose

Create orchestrator session in Redis — run once on deploy or when heartbeat detects expiry.

#### FastAPI trigger

Manual / POST /webhook/workflow-session-init-v1

#### Webhook

- **Local:** `POST http://localhost:5679/webhook/workflow-session-init-v1`
- **Docker internal:** `POST http://n8n:5678/webhook/workflow-session-init-v1`

#### Input payload

```json
{}
```

#### Output payload

```json
{
  "sessionToken": "string",
  "expiresAt": "iso8601"
}
```

#### Steps

_No steps (manual trigger only)._

#### Failure handling

Business workflows blocked until session initialized

#### Tags

`wf-11`

---

### `workflow-session-heartbeat-v1` — WF-12 · Workflow Session Heartbeat

| Field | Value |
|-------|-------|
| **Serial** | WF-12 |
| **Group** | `infra` |
| **Owner** | platform-team |
| **Version** | v1 |
| **Trigger type** | `schedule` |
| **Retries** | 0 |
| **Repo path** | `n8n/workflows/infra/workflow-session-heartbeat-v1.json` |

#### Summary

Every 5 min — refresh session; re-trigger WF-11 if expired.

#### Purpose

Every 5 min — verify/refresh orchestrator session; re-run WF-11 if expired.

#### FastAPI trigger

n8n schedule only

#### Schedule

Cron: `*/5 * * * *`

#### Input payload

```json
{}
```

#### Output payload

```json
{
  "sessionValid": true,
  "requiresInitialize": false
}
```

#### Steps

_No steps (manual trigger only)._

#### Failure handling

Triggers WF-11 Initialize via webhook

#### Tags

`wf-12`

---

## Test

### `smoke-callback-v1` — WF-10 · Platform Smoke Callback

| Field | Value |
|-------|-------|
| **Serial** | WF-10 |
| **Group** | `test` |
| **Owner** | platform-team |
| **Version** | v1 |
| **Trigger type** | `manual` |
| **Retries** | 0 |
| **Repo path** | `n8n/workflows/test/smoke-callback-v1.json` |

#### Summary

Manual CI smoke → verify n8n can reach FastAPI internal health endpoint.

#### Purpose

CI/local smoke — verifies n8n can reach FastAPI internal smoke endpoint.

#### FastAPI trigger

Manual / scripts/verify/n8n-callback.sh

#### Trigger

Manual — run from n8n UI or CI (`verify-n8n-callback`). Never activate for live webhooks.

#### Input payload

```json
{}
```

#### Output payload

```json
{
  "status": "ok"
}
```

#### Steps

_No steps (manual trigger only)._

#### Failure handling

Fail CI gate

#### Tags

`wf-10`

---

### `test-slack-notification-v1` — WF-15 · Slack Notification Smoke Test

| Field | Value |
|-------|-------|
| **Serial** | WF-15 |
| **Group** | `test` |
| **Owner** | platform-team |
| **Version** | v1 |
| **Trigger type** | `manual` |
| **Retries** | 0 |
| **Repo path** | `n8n/workflows/test/test-slack-notification-v1.json` |

#### Summary

Manual Slack smoke — switch test_mode in Pick Test Case node.

#### Purpose

Manual Slack smoke — test notification-slack-v1 from n8n editor with dummy payloads.

#### FastAPI trigger

Manual only — n8n editor Execute Workflow

#### Trigger

Manual — run from n8n UI or CI (`verify-n8n-callback`). Never activate for live webhooks.

#### Input payload

```json
{
  "test_mode": "basic_text | client_created | case_created | workflow_failed | stub_no_credentials | via_fastapi"
}
```

#### Output payload

```json
{
  "pass": true,
  "test_mode": "string",
  "actual": "accepted|stub|sent"
}
```

#### Steps

_No steps (manual trigger only)._

#### Failure handling

Inspect Report Result node — check SLACK_* env on n8n container

#### Tags

`wf-15`

---


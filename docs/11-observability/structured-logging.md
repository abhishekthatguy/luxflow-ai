# Structured Logging

**LexFlow AI** — JSON Log Format, PII Redaction & Correlation  
**Version:** 1.0  
**Status:** Draft — Pre-Implementation  
**Last Updated:** 2026-07-06

---

## Purpose

Define the **canonical structured logging contract** for all LexFlow AI containers. Every service emits JSON logs to stdout, collected by Fluent Bit and routed to CloudWatch Logs (90-day hot) and S3 (7-year compliance archive). Logs must be queryable, tenant-aware, trace-linked, and **free of attorney-client privileged content**.

This document specifies the log schema, field catalog, `correlationId` lifecycle, PII redaction rules, log levels, and query patterns. Implementation lives in `services/shared/logging/` and per-container middleware — this doc is the contract.

Cross-cutting platform patterns: [../03-architecture/cross-cutting-concerns.md](../03-architecture/cross-cutting-concerns.md).

---

## Scope

| In Scope | Out of Scope |
|----------|--------------|
| JSON log schema and required fields | Python `structlog` processor implementation |
| `correlationId` generation and propagation | Fluent Bit sidecar Terraform configuration |
| PII and privileged content redaction rules | CloudWatch Logs Insights saved query JSON |
| Log levels and usage guidelines | Audit log schema (see [../05-database/audit-schema.md](../05-database/audit-schema.md)) |
| Per-service log field extensions | SIEM integration |

---

## Responsibilities

| Role | Responsibility |
|------|----------------|
| **Platform Engineer** | Maintain shared logging processor and redaction rule set |
| **Backend Engineer** | Emit logs via shared processor; add domain-specific context fields |
| **Frontend Engineer** | Browser console logs in dev only; production logs via API server |
| **DevOps / SRE** | Configure Fluent Bit routing, retention, S3 subscription filters |
| **Security Team** | Review redaction rules quarterly; approve new sensitive field additions |
| **Compliance Officer** | Validate 7-year archive meets firm retention requirements |

---

## Architecture

### Log Pipeline

```mermaid
flowchart LR
    subgraph Containers["ECS Tasks"]
        APP["Application<br/>structlog → stdout"]
        FB["Fluent Bit Sidecar<br/>parse + enrich"]
    end

    subgraph Routing["Log Routing"]
        CW["CloudWatch Logs<br/>/lexflow/{env}/{service}"]
        FILTER["Subscription Filter<br/>ERROR + audit events"]
        S3["S3 Compliance Bucket<br/>SSE-KMS, 7-year lifecycle"]
    end

    subgraph Query["Analysis"]
        INSIGHTS["CloudWatch Insights<br/>operational queries"]
        ATHENA["Athena<br/>historical compliance queries"]
    end

    APP --> FB --> CW
    CW --> FILTER --> S3
    CW --> INSIGHTS
    S3 --> ATHENA
```

### Correlation ID Lifecycle

```mermaid
sequenceDiagram
    participant FE as Frontend
    participant ALB as ALB
    participant MW as CorrelationIdMiddleware
    participant API as Route Handler
    participant RMQ as RabbitMQ
    participant WRK as Worker
    participant N8N as n8n

    FE->>ALB: Request<br/>X-Correlation-Id: (optional)
    ALB->>MW: Forward headers
    alt Header absent or invalid UUID
        MW->>MW: Generate new correlationId
    else Valid UUID present
        MW->>MW: Accept client correlationId
    end
    MW->>API: Bind correlationId to request context
    Note over API: All logs include correlationId
    API->>RMQ: Publish message<br/>headers: X-Correlation-Id
    RMQ->>WRK: Deliver with headers
    Note over WRK: Extract correlationId from AMQP headers
    WRK->>N8N: Webhook payload.correlationId
    N8N->>API: Callback X-Correlation-Id
    Note over API: Same correlationId across full flow
```

### Log Context Binding

```mermaid
flowchart TB
    REQ["Inbound Request"] --> MW["CorrelationIdMiddleware"]
    MW --> CTX["Request Context"]
    
    subgraph CTX["Bound Context — Auto-Injected"]
        CID["correlationId"]
        UID["userId"]
        FID["firmId"]
        TID["traceId / spanId"]
        RID["requestId"]
    end

    CTX --> PROC["Logging Processor"]
    PROC --> REDACT["PII Redaction Filter"]
    REDACT --> EMIT["JSON to stdout"]
```

---

## Log Schema

### Base Schema (All Services)

Every log line is a single JSON object on one line (NDJSON). No multi-line stack traces without structured wrapping.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `timestamp` | string (ISO 8601 UTC) | Yes | `2026-07-06T08:00:00.123Z` |
| `level` | string | Yes | `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL` |
| `service` | string | Yes | Container name: `web`, `api`, `worker`, `n8n`, `outbox-publisher` |
| `environment` | string | Yes | `local`, `dev`, `staging`, `production` |
| `message` | string | Yes | Human-readable event description |
| `correlationId` | string (UUID v4) | Yes | Business correlation identifier |
| `requestId` | string (UUID v4) | HTTP only | Per-request identifier (may differ from correlationId) |
| `traceId` | string (32 hex) | When traced | W3C trace ID from active span |
| `spanId` | string (16 hex) | When traced | W3C span ID from active span |
| `userId` | string (UUID) | When authenticated | Acting user |
| `firmId` | string (UUID) | When known | Tenant identifier |
| `caseId` | string (UUID) | When applicable | Matter context |
| `duration_ms` | number | When timed | Operation duration in milliseconds |
| `error` | object | On failure | Structured error (see below) |

### HTTP Request Extension

| Field | Type | Description |
|-------|------|-------------|
| `http.method` | string | `GET`, `POST`, `PATCH`, `DELETE` |
| `http.path` | string | Route template: `/api/v1/cases/{caseId}/workflows/trigger` |
| `http.status` | number | Response status code |
| `http.client_ip` | string | Client IP (ALB X-Forwarded-For, truncated) |
| `http.user_agent` | string | Truncated to 256 chars |
| `http.request_size_bytes` | number | Request body size |
| `http.response_size_bytes` | number | Response body size |

### Worker Task Extension

| Field | Type | Description |
|-------|------|-------------|
| `task.name` | string | Celery task name: `workers.tasks.process_document` |
| `task.id` | string | Celery task UUID |
| `queue.name` | string | Source queue: `ai.inference`, `workflow.trigger` |
| `event.type` | string | Domain event type: `document.uploaded` |
| `event.id` | string | Domain event UUID |
| `retry.count` | number | Current retry attempt (0 = first) |

### Workflow Extension

| Field | Type | Description |
|-------|------|-------------|
| `workflow.slug` | string | Workflow identifier: `intake-document-review` |
| `workflow.executionId` | string | `workflow_executions.id` |
| `workflow.stepId` | string | Current n8n step identifier |
| `workflow.status` | string | `triggered`, `running`, `completed`, `failed` |

### AI Extension

| Field | Type | Description |
|-------|------|-------------|
| `ai.provider` | string | `openai`, `azure_openai`, `anthropic` |
| `ai.model` | string | Model identifier: `gpt-4o` |
| `ai.summaryType` | string | `case_summary`, `document_extract` |
| `ai.input_tokens` | number | Input token count |
| `ai.output_tokens` | number | Output token count |
| `ai.latency_ms` | number | Provider round-trip time |
| `ai.jobId` | string | Async AI job identifier |

### Error Object

| Field | Type | Description |
|-------|------|-------------|
| `error.type` | string | Exception class: `WorkflowTriggerError` |
| `error.message` | string | Sanitized error message (no PII) |
| `error.code` | string | Application error code: `WORKFLOW_NOT_FOUND` |
| `error.stack` | string | Stack trace (ERROR+ only; truncated to 4 KB) |
| `error.retryable` | boolean | Whether the operation is transient |

---

## Example Log Lines

### API — Successful Workflow Trigger

```json
{
  "timestamp": "2026-07-06T08:00:00.123Z",
  "level": "INFO",
  "service": "api",
  "environment": "production",
  "message": "Workflow triggered",
  "correlationId": "550e8400-e29b-41d4-a716-446655440000",
  "requestId": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
  "traceId": "4bf92f3577b34da6a3ce929d0e0e4736",
  "spanId": "00f067aa0ba902b7",
  "userId": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "firmId": "f1f2f3f4-f5f6-7890-abcd-ef1234567890",
  "caseId": "c1c2c3c4-c5c6-7890-abcd-ef1234567890",
  "duration_ms": 45,
  "http": {
    "method": "POST",
    "path": "/api/v1/cases/{caseId}/workflows/trigger",
    "status": 202,
    "client_ip": "203.0.113.42",
    "response_size_bytes": 128
  },
  "workflow": {
    "slug": "intake-document-review",
    "executionId": "e1e2e3e4-e5e6-7890-abcd-ef1234567890",
    "status": "triggered"
  }
}
```

### Worker — Document Processing Failure

```json
{
  "timestamp": "2026-07-06T08:01:15.456Z",
  "level": "ERROR",
  "service": "worker",
  "environment": "production",
  "message": "Document processing failed — retrying",
  "correlationId": "550e8400-e29b-41d4-a716-446655440000",
  "traceId": "4bf92f3577b34da6a3ce929d0e0e4736",
  "spanId": "a1b2c3d4e5f67890",
  "firmId": "f1f2f3f4-f5f6-7890-abcd-ef1234567890",
  "caseId": "c1c2c3c4-c5c6-7890-abcd-ef1234567890",
  "task": {
    "name": "workers.tasks.process_document",
    "id": "t1t2t3t4-t5t6-7890-abcd-ef1234567890"
  },
  "queue": {
    "name": "document.processing"
  },
  "retry": {
    "count": 2
  },
  "error": {
    "type": "S3AccessError",
    "message": "Failed to read object from S3",
    "code": "S3_READ_FAILED",
    "retryable": true
  }
}
```

### n8n — Step Completion (Log-Only Span)

```json
{
  "timestamp": "2026-07-06T08:02:30.789Z",
  "level": "INFO",
  "service": "n8n",
  "environment": "production",
  "message": "Workflow step completed",
  "correlationId": "550e8400-e29b-41d4-a716-446655440000",
  "workflow": {
    "slug": "intake-document-review",
    "executionId": "e1e2e3e4-e5e6-7890-abcd-ef1234567890",
    "stepId": "send-notification",
    "status": "completed"
  },
  "duration_ms": 1200
}
```

---

## Correlation ID

### Definition

`correlationId` is a **business-level correlation identifier** that ties together all logs, traces, and support tickets for a single user-initiated operation or workflow execution. It is distinct from `traceId` (W3C distributed trace) and `requestId` (single HTTP request).

| Identifier | Scope | Generated By | Format |
|------------|-------|--------------|--------|
| `correlationId` | End-to-end business operation | API `CorrelationIdMiddleware` | UUID v4 |
| `traceId` | Distributed trace | OpenTelemetry SDK | 32 hex chars |
| `requestId` | Single HTTP request | API middleware | UUID v4 |

### Generation Rules

1. **Edge generation** — If `X-Correlation-Id` header is absent, middleware generates a new UUID v4.
2. **Client-provided** — If present and valid UUID v4, accept as-is. Malformed values → generate new (log WARNING).
3. **Never reuse** — A new user action always gets a new `correlationId`. Retries within the same operation keep the same ID.
4. **Propagate everywhere** — HTTP responses include `X-Correlation-Id`. AMQP messages carry it in headers. n8n payloads include `correlationId`. Callbacks return it.

### Propagation Matrix

| Hop | Mechanism | Header / Field |
|-----|-----------|----------------|
| Frontend → API | HTTP header | `X-Correlation-Id` |
| API → Response | HTTP header | `X-Correlation-Id` |
| API → RabbitMQ | AMQP header | `X-Correlation-Id` |
| Worker → n8n | JSON payload | `correlationId` |
| n8n → API callback | HTTP header | `X-Correlation-Id` |
| All logs | Auto-injected | `correlationId` field |
| All spans | OTel attribute | `correlationId` |

### Support Query Pattern

```
fields @timestamp, level, service, message, http.status, error.message
| filter correlationId = '550e8400-e29b-41d4-a716-446655440000'
| sort @timestamp asc
```

---

## PII Redaction

### Redaction Policy

LexFlow handles **Restricted — Privileged** and **Restricted — PII** data. The logging processor applies redaction **before** log emission. Redaction is fail-safe: when in doubt, redact.

```mermaid
flowchart TB
    LOG["Log Event Dict"] --> PROC["Structlog Processor Chain"]
    PROC --> FIELD["Field-Level Redaction"]
    FIELD --> PATTERN["Pattern-Based Redaction"]
    PATTERN --> NESTED["Nested Object Walk"]
    NESTED --> EMIT["Safe JSON Output"]

    subgraph Rules["Redaction Rules"]
        R1["Known sensitive keys → [REDACTED]"]
        R2["Regex patterns → [REDACTED]"]
        R3["Max string length → truncate"]
        R4["Document content → ID only"]
    end

    FIELD --> Rules
```

### Always Redacted (Field Names)

| Field Pattern | Replacement | Rationale |
|---------------|-------------|-----------|
| `password`, `passwd`, `secret` | `[REDACTED]` | Credentials |
| `token`, `access_token`, `refresh_token`, `api_key` | `[REDACTED]` | Authentication secrets |
| `authorization` (header value) | `[REDACTED]` | Bearer tokens |
| `ssn`, `social_security` | `[REDACTED]` | Government identifier |
| `credit_card`, `card_number` | `[REDACTED]` | Financial PII |
| `prompt`, `completion`, `llm_response` | `[REDACTED]` | Privileged AI content |
| `document_content`, `document_body` | `[REDACTED]` | Attorney-client privileged text |
| `email_body`, `note_content` | `[REDACTED]` | Client communications |

### Pattern-Based Redaction (Regex)

| Pattern | Replacement | Example |
|---------|-------------|---------|
| SSN `\d{3}-\d{2}-\d{4}` | `[REDACTED:SSN]` | `123-45-6789` |
| Credit card `\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}` | `[REDACTED:CC]` | `4111-1111-1111-1111` |
| Email (in non-identifier context) | `[REDACTED:EMAIL]` | `client@lawfirm.com` |
| Bearer token `Bearer\s+\S+` | `Bearer [REDACTED]` | `Bearer eyJhbG...` |
| AWS key `AKIA[0-9A-Z]{16}` | `[REDACTED:AWS_KEY]` | `AKIAIOSFODNN7EXAMPLE` |

### Safe to Log (Identifiers Only)

| Data Type | Log As | Never Log |
|-----------|--------|-----------|
| Document | `documentId`, `documentType`, `size_bytes`, `page_count` | File content, extracted text |
| Case / Matter | `caseId`, `caseNumber`, `practiceArea` | Case notes, strategy memos |
| Client | `clientId`, `firmId` | Client name, address, SSN |
| AI inference | `ai.provider`, `ai.model`, `ai.input_tokens`, `ai.output_tokens`, `ai.jobId` | Prompt text, model response |
| User | `userId`, `role` | Email, display name (use ID only) |
| n8n payload | `workflow.slug`, `executionId`, `stepId` | Full payload body (log field names only) |

### Redaction Verification

| Check | Frequency | Owner |
|-------|-----------|-------|
| Unit tests for redaction processor | Every PR touching logging | Backend Engineer |
| Staging log audit (manual sample) | Monthly | Security Team |
| Production log scan for PII patterns | Weekly (automated) | SRE |
| Redaction rule review | Quarterly | Security + Compliance |

---

## Log Levels

| Level | Usage | Production Enabled | Example |
|-------|-------|-------------------|---------|
| `DEBUG` | Verbose internal state, cache hits/misses | No | `Cache miss for perms:{firmId}:{userId}` |
| `INFO` | Normal operations, request completion, workflow steps | Yes | `Workflow triggered`, `Document uploaded` |
| `WARNING` | Recoverable issues, degraded mode, approaching limits | Yes | `Retry attempt 2/5`, `Rate limit 80% consumed` |
| `ERROR` | Failures requiring attention, unhandled exceptions | Yes | `S3 read failed`, `LLM provider timeout` |
| `CRITICAL` | System-level failures, data store unreachable | Yes | `PostgreSQL connection pool exhausted` |

### Level Selection Guidelines

- **INFO** for every successful mutating operation (create, update, trigger).
- **WARNING** when an automatic retry or fallback path activates.
- **ERROR** when an operation fails and will retry or route to DLQ.
- **CRITICAL** when the service cannot perform its core function.
- Never log at INFO or below for authentication failures — use WARNING (feeds security dashboard).

---

## Per-Service Conventions

| Service | Log Group | Additional Fields | Notes |
|---------|-----------|-------------------|-------|
| `web` | `/lexflow/{env}/web` | `page.route`, `client.navigation` | Server-side only; no browser PII logging |
| `api` | `/lexflow/{env}/api` | `http.*`, domain context | All routes; audit events duplicated to audit log |
| `worker` | `/lexflow/{env}/worker` | `task.*`, `queue.*`, `event.*` | Include `retry.count` on every retry |
| `n8n` | `/lexflow/{env}/n8n` | `workflow.*` | JSON stdout; no execution data payloads |
| `outbox-publisher` | `/lexflow/{env}/outbox` | `outbox.pending_count`, `outbox.published_count` | Log every publish cycle |

---

## CloudWatch Log Groups

| Environment | Log Group Prefix | Retention | Archive |
|-------------|-----------------|-----------|---------|
| Production | `/lexflow/production/` | 90 days | S3 `lexflow-logs-archive-prod` |
| Staging | `/lexflow/staging/` | 30 days | None |
| Dev | `/lexflow/dev/` | 14 days | None |
| Local | stdout | N/A | None |

Provisioning details: [../09-deployment/](../09-deployment/) and [../deployment-architecture.md](../deployment-architecture.md).

---

## Query Patterns

### Error Rate by Service (Last Hour)

```
fields @timestamp, service, level, message
| filter level = 'ERROR'
| stats count() as errors by service
| sort errors desc
```

### Workflow Failures for a Firm

```
fields @timestamp, correlationId, workflow.slug, error.message
| filter firmId = 'f1f2f3f4-f5f6-7890-abcd-ef1234567890'
  and workflow.status = 'failed'
| sort @timestamp desc
| limit 50
```

### Slow API Requests (p99 Diagnostic)

```
fields @timestamp, http.path, duration_ms, correlationId
| filter service = 'api' and duration_ms > 1000
| sort duration_ms desc
| limit 20
```

---

## Best Practices

1. **Structured only** — No plain-text `print()` or unstructured log lines in production code.
2. **Log events, not streams** — One JSON object per logical event; no continuation lines.
3. **Bind context early** — Set `correlationId`, `firmId`, `userId` at middleware; downstream code inherits.
4. **Log IDs, not content** — `documentId=abc-123`, never document text.
5. **Include duration** — Every outbound call and handler logs `duration_ms`.
6. **Error logs carry `error.code`** — Enables metric grouping and alert rules.
7. **Do not log health check traffic** — Exclude `/health` and `/ready` from request logging.

---

## Tradeoffs

| Decision | Benefit | Cost |
|----------|---------|------|
| NDJSON to stdout | Container-native, no agent dependency in app | Requires Fluent Bit sidecar for routing |
| Field-name redaction vs content scanning | Fast, predictable | May miss PII in unexpected field names — mitigated by regex pass |
| `correlationId` separate from `traceId` | Support-friendly queries without trace tooling | Two IDs to propagate |
| 90-day CloudWatch hot retention | Fast operational queries | Older logs require Athena on S3 archive |
| Truncated stack traces (4 KB) | Prevents log flooding | Deep stack frames may be lost |

---

## References

| Document | Description |
|----------|-------------|
| [README.md](./README.md) | Observability folder index |
| [distributed-tracing.md](./distributed-tracing.md) | Trace-linked logging, `traceId` / `spanId` |
| [../03-architecture/cross-cutting-concerns.md](../03-architecture/cross-cutting-concerns.md) | CorrelationIdMiddleware, logging processor ownership |
| [../05-database/audit-schema.md](../05-database/audit-schema.md) | Immutable audit log (separate from application logs) |
| [../08-security/incident-response.md](../08-security/incident-response.md) | Log preservation during security incidents |
| [../compliance-data-governance.md](../compliance-data-governance.md) | Data classification driving redaction rules |
| [../14-playbooks/incident-triage.md](../14-playbooks/incident-triage.md) | CorrelationId-based incident investigation (planned) |

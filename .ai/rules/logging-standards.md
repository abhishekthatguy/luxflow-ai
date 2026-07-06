# Logging Standards — LexFlow AI

**Applies to:** API, workers, outbox publisher, n8n (correlation only)  
**Docs:** `docs/11-observability/structured-logging.md`

---

## Purpose

Canonical structured logging contract. All containers emit **JSON to stdout**. Logs must be queryable, correlation-linked, tenant-aware, and **free of attorney-client privileged content**.

---

## Log Format

Every log line is a single JSON object:

```json
{
  "timestamp": "2026-07-06T12:00:00.000Z",
  "level": "info",
  "service": "api",
  "environment": "production",
  "correlationId": "550e8400-e29b-41d4-a716-446655440000",
  "traceId": "abc123",
  "spanId": "def456",
  "event": "case_created",
  "message": "Case created successfully",
  "firmId": "uuid",
  "userId": "uuid",
  "caseId": "uuid",
  "durationMs": 45
}
```

---

## Required Fields

| Field | Required | Description |
|-------|----------|-------------|
| `timestamp` | Yes | ISO 8601 UTC |
| `level` | Yes | `debug`, `info`, `warning`, `error`, `critical` |
| `service` | Yes | `api`, `worker`, `web`, `outbox`, `n8n` |
| `environment` | Yes | `local`, `dev`, `staging`, `production` |
| `correlationId` | Yes | UUID — end-to-end request tracking |
| `event` | Yes | snake_case machine-readable event name |
| `message` | Yes | Human-readable summary (no PII) |

---

## Correlation ID Lifecycle

| Step | Behavior |
|------|----------|
| Client sends `X-Correlation-Id` | Use if valid UUID |
| Absent or invalid | Generate new UUID in middleware |
| Publish to RabbitMQ | Include in AMQP headers |
| Worker consumes | Extract and bind to log context |
| n8n webhook | Include `correlationId` in JSON payload |
| n8n callback | Return `X-Correlation-Id` header |

**Rule:** Same `correlationId` across entire flow — frontend → API → queue → worker → n8n → callback.

---

## Log Levels

| Level | When |
|-------|------|
| `debug` | Dev/local only — verbose internals |
| `info` | Normal operations — request completed, job started |
| `warning` | Expected failures — 404 matter wall, validation, retry |
| `error` | Unexpected failures — unhandled exception, upstream failure |
| `critical` | Service degradation — DB unreachable, auth system down |

| Do | Don't |
|----|-------|
| Log `info` on successful mutations (without content) | Log `debug` in production by default |
| Log `warning` for matter wall denies | Log `error` for expected 404 |
| Log `error` once at boundary | Log same exception at every layer |

---

## PII & Privileged Content Redaction

**Never log:**

| Category | Examples |
|----------|----------|
| Document content | Full text, excerpts |
| Client PII | SSN, DOB, home address |
| Auth secrets | JWT, API keys, passwords |
| LLM prompts/responses | Full prompt body (use redacted hash/reference) |
| Privileged communications | Attorney notes content |

| Do | Don't |
|----|-------|
| Log `documentId`, `caseId` UUIDs | Log document filenames with client names |
| Log `prompt_version` slug | Log rendered prompt text |
| Use redaction processor | `logger.info(f"Summary: {summary_text}")` |

**Ref:** `docs/11-observability/structured-logging.md` — redaction rule set

---

## Event Naming

| Pattern | Examples |
|---------|----------|
| `{noun}_{past_tense}` | `case_created`, `document_uploaded` |
| `request_{outcome}` | `request_completed`, `request_failed` |
| `job_{state}` | `job_started`, `job_failed` |
| `denied_{reason}` | `denied_matter_wall`, `denied_rbac` |

---

## Per-Service Extensions

| Service | Additional Fields |
|---------|-------------------|
| `api` | `method`, `path`, `status`, `durationMs` |
| `worker` | `taskName`, `jobId`, `queueName`, `retryCount` |
| `outbox` | `eventType`, `outboxId` |
| `n8n` | `workflowSlug`, `executionId` |

---

## Good vs Bad Logging

```python
# BAD
logger.info(f"User {user.email} uploaded {file_content[:500]}")

# GOOD
logger.info(
    "document_uploaded",
    user_id=str(user.id),
    case_id=str(case_id),
    document_id=str(doc.id),
    size_bytes=file.size,
    correlation_id=correlation_id,
)
```

```python
# BAD — duplicate logging at every layer
except CaseNotFound:
    logger.error("not found")  # in domain
    logger.error("not found")  # in application
    logger.error("not found")  # in handler

# GOOD — log once at API exception handler
# domain raises; handler maps to 404 + single warning log
```

---

## Audit Log vs Application Log

| Type | Store | Purpose |
|------|-------|---------|
| Application log | CloudWatch → S3 | Operations, debugging |
| Audit log | PostgreSQL `audit.audit_logs` | Compliance, immutable |

| Do | Don't |
|----|-------|
| Write audit entries for mutations and auth denies | Duplicate full audit payload in app logs |
| Reference `auditLogId` in app log if needed | Use app logs as compliance record |

---

## Frontend Logging

| Environment | Policy |
|-------------|--------|
| Local/dev | `console.debug` allowed |
| Production | No client-side privileged data logging |
| Production errors | Report to API error endpoint with `correlationId` only |

---

## Logging Checklist

- [ ] JSON format to stdout
- [ ] `correlationId` on every line
- [ ] No PII or document content
- [ ] Appropriate log level
- [ ] `event` field is machine-readable
- [ ] Matter wall denies logged (not silent)
- [ ] Uses shared logging processor from `services/shared/`

---

## References

- [docs/11-observability/structured-logging.md](../../docs/11-observability/structured-logging.md)
- [docs/05-database/audit-schema.md](../../docs/05-database/audit-schema.md)
- [observability-standards.md](./observability-standards.md)
- [security-rules.md](./security-rules.md)

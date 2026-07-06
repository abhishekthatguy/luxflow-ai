# Error Handling — LexFlow AI

**Applies to:** API, domain, application, workers, frontend error display  
**Docs:** `docs/04-api/error-handling.md`

---

## Purpose

Unified error handling across layers. Public API uses **RFC 7807 Problem Details**. Internal errors are logged with correlation IDs — never expose stack traces to clients.

---

## Layer Responsibilities

| Layer | Responsibility |
|-------|----------------|
| Domain | Raise typed domain exceptions (`CaseNotFound`, `InvalidCaseTransition`) |
| Application | Catch infra failures; map to domain errors where appropriate |
| API (FastAPI) | Global exception handler → RFC 7807 |
| Workers | Retry transient; dead-letter persistent; log with `correlationId` |
| Frontend | Parse `type` URI; show `ApiErrorPanel`; retry per guidance |

---

## RFC 7807 (Public API)

Content-Type: `application/problem+json`

```json
{
  "type": "https://lexflow.ai/errors/case-not-found",
  "title": "Case Not Found",
  "status": 404,
  "detail": "The requested case could not be found.",
  "instance": "/api/v1/cases/550e8400-e29b-41d4-a716-446655440000",
  "meta": {
    "requestId": "uuid",
    "timestamp": "2026-07-06T12:00:00Z"
  }
}
```

### Validation Errors (422)

Include field-level `errors[]`:

```json
{
  "type": "https://lexflow.ai/errors/validation-failed",
  "title": "Validation Failed",
  "status": 422,
  "errors": [
    { "field": "practiceArea", "message": "Must be a valid practice area." }
  ],
  "meta": { "requestId": "uuid" }
}
```

---

## HTTP Status Mapping

| Status | When | Example `type` suffix |
|--------|------|------------------------|
| 400 | Malformed JSON, bad query | `malformed-request` |
| 401 | Missing/expired JWT | `unauthorized` |
| 403 | RBAC denial (non-case) | `forbidden` |
| 404 | Not found; **unauthorized case GET** | `case-not-found` |
| 409 | Idempotency conflict; ETag mismatch | `idempotency-conflict` |
| 422 | Pydantic validation | `validation-failed` |
| 429 | Rate limited | `rate-limit-exceeded` |
| 500 | Unhandled | `internal-error` |
| 502 | Upstream (n8n callback timeout) | `upstream-error` |
| 503 | Dependency unavailable | `service-unavailable` |

### Matter Wall Special Case (ADR-007)

| Scenario | Status | Body |
|----------|--------|------|
| Non-participant GET case | **404** | Same shape as truly missing case |
| Non-participant POST (mutation) | **403** | `forbidden` — action denied |
| RBAC failure (no permission at all) | **403** | `forbidden` |

```python
# GOOD — intentional 404 for enumeration protection
if not authz.can_read_case(actor, case_id):
    raise CaseNotFound(case_id)  # maps to 404, not 403
```

---

## Domain Exceptions

| Do | Don't |
|----|-------|
| Raise specific domain exceptions | Raise `HTTPException` in domain |
| Include minimal context (ids, codes) | Include PII in exception messages |
| Map to registered `type` URIs in handler | Invent ad hoc error strings per handler |

```python
# domain/exceptions.py
class DomainError(Exception):
    code: str

class CaseNotFound(DomainError):
    code = "case-not-found"

class InvalidCaseTransition(DomainError):
    code = "invalid-case-transition"
```

---

## Idempotency Errors (409)

```json
{
  "type": "https://lexflow.ai/errors/idempotency-conflict",
  "title": "Idempotency Conflict",
  "status": 409,
  "detail": "Idempotency key reused with different payload."
}
```

| Do | Don't |
|----|-------|
| Return cached response on same key + same body hash | Silently overwrite on key reuse |
| Store idempotency records 24h | Infinite idempotency store growth |

---

## Worker Error Handling

| Error Type | Action |
|------------|--------|
| Transient (network, timeout) | Retry with exponential backoff |
| Domain validation | No retry — mark job `failed` |
| LLM rate limit | Retry with `Retry-After` |
| Unhandled | Dead-letter + alert P2 |

```python
# GOOD — worker marks job failed with reason
try:
    await handler.execute(cmd)
except DomainError as e:
    await job_repo.mark_failed(job_id, error_code=e.code)
    # no retry
except TransientError:
    raise self.retry(countdown=2 ** self.request.retries)
```

---

## n8n Callback Errors

| Callback `status` | FastAPI Action |
|-------------------|----------------|
| `success` | Interpret raw response; update execution |
| `failed` | Mark execution failed; audit; optional notification |
| Invalid HMAC | 401 — do not process |
| Unknown `executionId` | 404 |

---

## Frontend Error Display

```typescript
// GOOD — parse RFC 7807 type
function ApiErrorPanel({ error }: { error: ProblemDetails }) {
  if (error.status === 404 && error.type.endsWith("/case-not-found")) {
    return <EmptyState title="Case not found" />;  // no "access denied" wording
  }
  return <Alert variant="destructive">{error.title}</Alert>;
}
```

| Do | Don't |
|----|-------|
| Map known `type` URIs to UX | Display raw `detail` with internal info |
| Offer retry on 429/503 with backoff | Infinite retry loops |
| Clear React Query cache on auth 401 | Leave stale privileged data |

---

## Logging on Error

Every error response must have matching structured log:

```json
{
  "level": "warning",
  "event": "request_failed",
  "correlationId": "uuid",
  "errorType": "case-not-found",
  "status": 404,
  "path": "/api/v1/cases/{id}",
  "userId": "uuid"
}
```

| Do | Don't |
|----|-------|
| Log `correlationId` + `errorType` | Log stack trace at WARNING for expected 404 |
| Log matter wall denies at INFO/WARNING | Log case content in error path |

---

## Error Handling Checklist

- [ ] Domain exceptions — no HTTP in domain layer
- [ ] Global handler maps all exceptions to RFC 7807
- [ ] 404 for unauthorized case GET
- [ ] Field errors on 422
- [ ] `requestId` in all error bodies
- [ ] No stack traces or secrets in client responses
- [ ] Frontend handles known error types
- [ ] Worker retry policy defined per error class

---

## References

- [docs/04-api/error-handling.md](../../docs/04-api/error-handling.md)
- [docs/13-decisions/007-matter-walls-404-deny.md](../../docs/13-decisions/007-matter-walls-404-deny.md)
- [api-standards.md](./api-standards.md)
- [logging-standards.md](./logging-standards.md)
- [security-rules.md](./security-rules.md)

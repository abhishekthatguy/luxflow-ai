# LexFlow AI — End-to-End System Walkthrough

**Scenario:** Paralegal uploads a policy document; AI summary is generated, approved, workflow fires, notification delivered, audit log written.

**Scope:** Full request path from browser to persistence and back.

---

## Master Flow Diagram

```
Browser (Chrome)
    ↓ HTTPS
Next.js 14 (App Router) — localhost:3000
    ↓ fetch() + Bearer JWT
FastAPI — localhost:8000
    ↓
CorrelationIdMiddleware → JSON logging (PII redacted)
    ↓
JWT Validation (HS256) → CurrentUser { id, firmId, roles }
    ↓
RBAC + Matter Wall check
    ↓
DocumentService.confirm_upload()
    ↓
┌─────────────────────────────────────────────────────────────┐
│ PostgreSQL (single transaction)                              │
│  • documents.documents (status → uploaded)                   │
│  • documents.document_versions                               │
│  • shared.outbox_events (DocumentUploaded)                   │
│  • cases.timeline_events                                     │
│  • audit.audit_logs                                          │
│  • shared.notifications (in-app)                             │
└─────────────────────────────────────────────────────────────┘
    ↓
virus_scan_stub() — local; ClamAV in prod
    ↓
MinIO HEAD + confirm checksum
    ↓
Celery apply_async → RabbitMQ broker
    ↓
Celery Worker — process_document_ocr
    ↓
MinIO GET object → pypdf extract → PostgreSQL UPDATE ocr_text
    ↓
Outbox relay task → HTTP POST n8n webhook
    ↓
n8n workflow → optional callback POST /api/internal/n8n/{slug}
    ↓
NotificationService → shared.notifications
    ↓
Browser polls GET /documents/{id} → ocrStatus: complete
    ↓
POST /cases/{id}/ai/summarize → 202
    ↓
Celery generate_case_summary → ai.ai_summaries (pending_review)
    ↓
POST /ai/summaries/{id}/approve
    ↓
audit.audit_logs (ai.summary.approved)
    ↓
GET /audit/logs (Managing Partner)
```

---

## Step-by-Step Reference

### Step 1 — User Opens Browser

| Aspect | Detail |
|--------|--------|
| **Purpose** | Authenticated SPA shell loads dashboard |
| **Data** | `localStorage.lexflow_access_token` |
| **Security** | Token short-lived (15 min access); refresh token rotation |
| **Logging** | None until first API call |
| **Failure** | Expired token → 401 → redirect `/login` |
| **Retry** | Client calls `POST /auth/refresh` once |
| **Observability** | Browser DevTools Network tab |

---

### Step 2 — Next.js Frontend

| Aspect | Detail |
|--------|--------|
| **Purpose** | Render React UI; client-side routing to `/cases/{id}/documents` |
| **Data** | Case ID from URL; form: title, filename, mimeType, fileSizeBytes, checksumSha256 |
| **Security** | CSP headers in production; no secrets in client bundle |
| **Logging** | Client errors to console only (no PII in prod) |
| **Failure** | API unreachable → user-facing error via `formatApiError` |
| **Retry** | User-initiated re-upload |
| **Observability** | Next.js server logs in SSR paths; static pages pre-rendered |

---

### Step 3 — FastAPI Gateway

| Aspect | Detail |
|--------|--------|
| **Purpose** | HTTP API, validation, auth, service orchestration |
| **Data** | Pydantic models → service layer DTOs |
| **Security** | CORS allowlist; Problem+JSON errors (no stack traces in prod) |
| **Logging** | `request_completed` JSON with correlationId, method, path, statusCode, durationMs |
| **Failure** | Unhandled → 500 Problem detail; AppError → mapped status |
| **Retry** | Idempotency keys (planned) for mutating POSTs |
| **Observability** | OpenTelemetry spans → Tempo; `/health` for ALB |

---

### Step 4 — JWT Validation

| Aspect | Detail |
|--------|--------|
| **Purpose** | Authenticate user; extract firm + roles |
| **Data** | Claims: `sub`, `firm_id`, `roles`, `email`, `exp` |
| **Security** | HS256 locally; RS256 + Entra ID in production |
| **Logging** | Failed auth → 401, no token payload logged |
| **Failure** | Expired → 401; invalid signature → 401 |
| **Retry** | Client refresh flow |
| **Observability** | Auth failure rate metric (CloudWatch in prod) |

---

### Step 5 — RBAC

| Aspect | Detail |
|--------|--------|
| **Purpose** | Role-based feature access |
| **Data** | Roles: Attorney, Paralegal, ManagingPartner, SystemAdministrator |
| **Security** | Least privilege; audit read = firm-wide roles only |
| **Logging** | 403 Forbidden logged with userId, path |
| **Failure** | Missing role → 403 |
| **Retry** | N/A — authorization failure is final |
| **Observability** | 403 rate alarm |

---

### Step 6 — Matter Wall

| Aspect | Detail |
|--------|--------|
| **Purpose** | Case-scoped data isolation (ethical walls) |
| **Data** | `cases.case_participants` membership check |
| **Security** | **404 deny** — unauthorized users cannot infer case existence (ADR-007) |
| **Logging** | Access denied logged internally; response is 404 |
| **Failure** | Non-participant → 404 Not Found |
| **Retry** | N/A |
| **Observability** | Penetration test: zero cross-matter leakage |

---

### Step 7 — Case Service (Create Case Path)

| Aspect | Detail |
|--------|--------|
| **Purpose** | Create matter aggregate |
| **Data** | `cases.cases`, participant, timeline |
| **Security** | firm_id from JWT, never from request body |
| **Logging** | Audit: `case.created` |
| **Failure** | Validation → 422; conflict → 409 |
| **Retry** | Client retry with Idempotency-Key |
| **Observability** | Case creation counter |

---

### Step 8 — Document Initiate (Storage Service)

| Aspect | Detail |
|--------|--------|
| **Purpose** | Register metadata; return presigned PUT URL |
| **Data** | `documents.documents` status `pending_upload`, s3_key, checksum |
| **Security** | Presigned URL TTL 15 min; scoped to single object key |
| **Logging** | Audit: `document.upload.initiated` |
| **Failure** | Matter wall → 404; invalid checksum format → 422 |
| **Retry** | New initiate if presign expires |
| **Observability** | Upload initiate latency |

---

### Step 9 — Browser → MinIO (Direct PUT)

| Aspect | Detail |
|--------|--------|
| **Purpose** | Upload binary without API proxy |
| **Data** | Raw file bytes in S3 object |
| **Security** | TLS; bucket policy denies public read |
| **Logging** | MinIO access logs (S3 server access logging in prod) |
| **Failure** | Network drop → client retries PUT |
| **Retry** | Multipart upload for large files (prod) |
| **Observability** | S3 4xx/5xx metrics |

---

### Step 10 — Document Confirm

| Aspect | Detail |
|--------|--------|
| **Purpose** | Verify upload integrity; trigger processing |
| **Data** | Version row; status `uploaded`; outbox event |
| **Security** | SHA-256 match; HEAD size match; virus scan |
| **Logging** | Audit + timeline + notification |
| **Failure** | Checksum mismatch → 409; virus fail → 409 |
| **Retry** | Re-upload if confirm fails |
| **Observability** | Confirm success rate |

---

### Step 11 — RabbitMQ

| Aspect | Detail |
|--------|--------|
| **Purpose** | Durable task queue between API and workers |
| **Data** | Celery message: task name, args, correlation metadata |
| **Security** | Private VPC; TLS + credentials in prod (Amazon MQ) |
| **Logging** | Broker logs; queue depth metrics |
| **Failure** | Broker down → API returns 503 or queues locally (fail closed preferred) |
| **Retry** | Celery acks late; requeue on worker crash |
| **Observability** | Alarm: queue depth > threshold |

---

### Step 12 — Celery Worker

| Aspect | Detail |
|--------|--------|
| **Purpose** | Async OCR, AI, outbox relay, workflow trigger |
| **Data** | Reads/writes PostgreSQL; reads MinIO |
| **Security** | Same DB credentials as API; no public ingress |
| **Logging** | JSON logs with correlationId propagation |
| **Failure** | Task exception → retry 3x → dead letter |
| **Retry** | Exponential backoff: 60s, 120s, 240s |
| **Observability** | Worker CPU, task duration, failure rate |

---

### Step 13 — OCR Processing

| Aspect | Detail |
|--------|--------|
| **Purpose** | Extract searchable text from PDF |
| **Data** | `documents.documents.ocr_text`, `ocr_status` |
| **Security** | Text stays in firm-scoped DB |
| **Logging** | Task start/complete with documentId |
| **Failure** | Corrupt PDF → ocr_status `failed`; case still usable |
| **Retry** | Manual re-process endpoint (admin) |
| **Observability** | OCR success rate by mime type |

---

### Step 14 — AI Service

| Aspect | Detail |
|--------|--------|
| **Purpose** | Generate case summary draft |
| **Data** | `ai.ai_summaries`, `async_jobs` |
| **Security** | Case-scoped context only; PII redaction before LLM (prod) |
| **Logging** | Token counts; no raw document text in logs |
| **Failure** | LLM timeout → job `failed`; user notified |
| **Retry** | 2 retries with backoff; circuit breaker on provider |
| **Observability** | LLM latency p95, error rate, cost per firm |

---

### Step 15 — Workflow Service

| Aspect | Detail |
|--------|--------|
| **Purpose** | Trigger n8n orchestration |
| **Data** | `workflows.workflow_executions`, steps |
| **Security** | HMAC webhook secret; n8n on private network |
| **Logging** | Execution correlationId |
| **Failure** | n8n down → outbox retries; execution `failed` |
| **Retry** | Outbox: 5 attempts then `failed` + alert |
| **Observability** | Workflow completion rate |

---

### Step 16 — n8n

| Aspect | Detail |
|--------|--------|
| **Purpose** | Notifications, external HTTP, scheduling |
| **Data** | Workflow JSON; no direct DB |
| **Security** | No PostgreSQL nodes; callback HMAC verified |
| **Logging** | n8n execution logs |
| **Failure** | Node error → workflow error output branch |
| **Retry** | Per-node retry config (3x default) |
| **Observability** | Execution dashboard |

---

### Step 17 — Notifications

| Aspect | Detail |
|--------|--------|
| **Purpose** | Alert users of document ready, approvals needed |
| **Data** | `shared.notifications` channel `in_app` |
| **Security** | user_id scoped; firm_id denormalized |
| **Logging** | Delivery status |
| **Failure** | Email fail → status `failed`; in-app still sent |
| **Retry** | Worker poll pending notifications |
| **Observability** | Unread count; delivery latency |

---

### Step 18 — Audit Log Written

| Aspect | Detail |
|--------|--------|
| **Purpose** | Immutable compliance record |
| **Data** | `audit.audit_logs`: actor, action, resource, details JSONB |
| **Security** | Append-only; no UPDATE/DELETE in application code |
| **Logging** | Audit write is itself not re-audited (DB triggers optional) |
| **Failure** | Audit write failure rolls back transaction — mutation fails |
| **Retry** | Transaction retry on serialization conflict |
| **Observability** | Audit volume; export jobs for compliance |

---

### Step 19 — Response to Browser

| Aspect | Detail |
|--------|--------|
| **Purpose** | Envelope JSON `{ data, meta }` with requestId |
| **Data** | CamelCase serialized DTOs |
| **Security** | No internal IDs leaked in errors |
| **Logging** | correlationId echoed in `X-Correlation-ID` header |
| **Failure** | Problem+JSON body |
| **Retry** | Client-side |
| **Observability** | End-to-end trace completes |

---

## Data Store Summary

| Store | What It Holds (This Flow) |
|-------|---------------------------|
| **PostgreSQL** | Cases, documents, versions, OCR text, AI summaries, jobs, outbox, notifications, audit |
| **MinIO/S3** | PDF binary at versioned key |
| **Redis** | Celery results, rate limit counters, session cache (future) |
| **RabbitMQ** | Celery task messages |

---

## Related Docs

- [Demo Script](./DEMO_SCRIPT.md)
- [Failure Scenarios](../interview/FAILURE_SCENARIOS.md)
- [Architecture Walkthrough](../interview/ARCHITECTURE_WALKTHROUGH.md)

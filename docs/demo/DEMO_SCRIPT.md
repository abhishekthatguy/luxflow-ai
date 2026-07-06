# LexFlow AI — 20-Minute Live Demo Script

**Audience:** CTO, Principal Engineer, Legal Operations  
**Presenter role:** Senior Solutions Architect  
**Environment:** Local stack (`make dev && make migrate && make seed && make seed-sprint4 && make seed-sprint5`)  
**Duration:** 20 minutes (+ 5 min Q&A buffer)

---

## Story Arc

> *A national insurer refers a coverage dispute. The firm opens a matter, ingests policy documents, generates an AI case summary for attorney review, triggers notification workflows, and the managing partner verifies the full audit trail — all without email attachments or silent AI outputs.*

---

## Pre-Demo Checklist (5 min before)

| Check | Command / URL |
|-------|----------------|
| Stack healthy | `docker compose ps` — all services `healthy` |
| Migrations | `make migrate` |
| Seed data | `make seed && make seed-sprint4 && make seed-sprint5` |
| API health | `curl http://localhost:8000/health` |
| Web | `http://localhost:3000` |
| Grafana (traces) | `http://localhost:3001` |
| RabbitMQ UI | `http://localhost:15672` (guest/guest) |
| MinIO console | `http://localhost:9001` |

**Credentials**

| Role | Email | Password |
|------|-------|----------|
| Attorney | `jane@example.com` | `password123` |
| Paralegal | `alex@example.com` | `password123` |
| Managing Partner | `partner@example.com` | `password123` |

**Browser tabs to pre-open:** Landing (`/`), DevTools Network (preserve log), Grafana Tempo, RabbitMQ Queues.

---

## Act 1 — Opening & Context (2:00)

### Screen
`http://localhost:3000` — marketing landing page

### Actions
1. Scroll hero → Capabilities → Security sections (30 sec)
2. Click **Sign in to platform**

### Talking Points
- "LexFlow is **enterprise legal automation** — not a chatbot bolted onto email."
- "Every AI output requires **human-in-the-loop approval** before client visibility."
- "Architecture separates **decisions (FastAPI)** from **orchestration (n8n)** and **async work (Celery)**."

### Screenshot Placeholder
`![Landing hero](./screenshots/01-landing-hero.png)`

**Timing:** 0:00 – 2:00

---

## Act 2 — Attorney Opens the Matter (3:00)

### Screen
`/login` → `/cases` → `/cases/new`

### Actions
1. Sign in as **Jane** (Attorney)
2. Navigate **Cases** → **New case**
3. Create matter:
   - **Client:** Acme Corporation (seed) — *narrate as "National Insurance Carrier"*
   - **Case number:** `INS-2026-0042`
   - **Title:** `Meridian Mutual — Coverage Denial Dispute`
   - **Lead attorney:** Jane (self)
4. Land on `/cases/{id}/overview`

### API Called
```http
POST /api/v1/auth/login
POST /api/v1/cases
Authorization: Bearer {accessToken}
```

### What Happens Under the Hood

| Component | Action |
|-----------|--------|
| **Next.js** | Client-side form → `apiFetch` with JWT in `Authorization` |
| **FastAPI** | JWT validated → `CurrentUser` with roles + `firm_id` |
| **RBAC** | Attorney role permitted to create cases |
| **CaseService** | Inserts `cases.cases`, participant row, timeline event |
| **PostgreSQL** | `cases.cases`, `cases.case_participants`, `cases.timeline_events` |
| **Audit** | `audit.audit_logs` — `case.created` |
| **Redis** | Not used on this path |

### Logs Created
```json
{"message":"request_completed","correlationId":"…","method":"POST","path":"/api/v1/cases","statusCode":201,"durationMs":45}
```

### Interview Talking Points
- Matter is the **aggregate root** — documents, AI, workflows attach here.
- **Multi-tenant isolation** via `firm_id` on every row.
- **Optimistic concurrency** via `version` column on PATCH (mention if asked).

### Screenshot Placeholder
`![New case form](./screenshots/02-new-case.png)`

**Timing:** 2:00 – 5:00

---

## Act 3 — Paralegal Uploads Policy Documents (5:00)

### Screen
`/cases/{id}/documents`

### Actions
1. *(Optional)* Sign out → sign in as **Alex** (Paralegal), navigate to same case
2. Click **Upload document**
3. Select file: `policy-declaration.pdf` (or bundled `tests/e2e/fixtures/sample-document.txt` renamed)
4. Wait for upload → confirm → show status change to `uploaded` → `processing` → `ready`
5. Open **Network tab** — highlight presigned PUT (direct to MinIO, not through API)

### API Sequence
```http
POST /api/v1/cases/{caseId}/documents     → 201 presignedUrl + documentId
PUT  {presignedUrl}                        → 200 (browser → MinIO directly)
POST /api/v1/documents/{documentId}/confirm → 200
GET  /api/v1/documents/{documentId}        → poll ocrStatus
```

### What Happens Under the Hood

| Step | Component | Detail |
|------|-----------|--------|
| Initiate | **FastAPI** | Validates matter wall, SHA-256, file size; creates `documents.documents` status `pending_upload` |
| Presign | **S3/MinIO** | `generate_presigned_put` — binary never streams through API |
| Confirm | **FastAPI** | HEAD object in MinIO, **virus scan stub** (`scan_object_stub`), version row, outbox event |
| Queue | **RabbitMQ** | Celery task `process_document_ocr` published to broker |
| Worker | **Celery** | `document_tasks.py` — pypdf OCR, updates `ocr_text`, `ocr_status` |
| Storage | **MinIO** | Object at `firms/{firmId}/cases/{caseId}/documents/{uuid}/v1/{filename}` |
| **PostgreSQL** | `documents.documents`, `documents.document_versions`, `shared.outbox_events` |
| **Redis** | Celery result backend (task status) |

### Celery Task
`lexflow_api.tasks.document_tasks.process_document_ocr`

### RabbitMQ
Exchange/queue: Celery default broker — message body = task name + document ID + correlation context.

### n8n
Outbox relay publishes `DocumentUploaded` → n8n webhook (`document-upload-notify-v1.json`) — *mention; may run async*.

### Grafana / Tempo
Show trace span: `POST /documents` → `celery.process_document_ocr` (if OTel wired in demo env).

### Logs Created
- API: `request_completed` with `correlationId`
- Worker: `virus_scan_stub` with `s3Key`, `engine: stub`
- Audit: `document.upload.confirmed` with `caseId` in details

### Interview Talking Points
- **Presigned upload** = scalability + security (no API memory pressure for 500 MB files).
- Virus scan: **stub locally**, ClamAV in production (RFC-004 deferral).
- **Transactional outbox** — event and DB commit are atomic.

### Screenshot Placeholders
- `![Document upload UI](./screenshots/03-document-upload.png)`
- `![Network presigned PUT](./screenshots/04-presigned-put.png)`
- `![MinIO object browser](./screenshots/05-minio-object.png)`

**Timing:** 5:00 – 10:00

---

## Act 4 — AI Case Summary (Async + HITL) (4:00)

### Screen
`/cases/{id}/ai`

### Actions
1. Sign in as **Jane** (Attorney)
2. Click **Generate summary** (case overview type)
3. Show **202 Accepted** + job ID in Network tab
4. Poll until summary appears with status `pending_review`
5. Read draft summary — emphasize it is **not client-ready**
6. Click **Approve**
7. Status → `approved`

### API Sequence
```http
POST /api/v1/cases/{caseId}/ai/summarize   → 202 { jobId }
GET  /api/v1/jobs/{jobId}                  → poll status
GET  /api/v1/cases/{caseId}/ai/summaries   → list
POST /api/v1/ai/summaries/{id}/approve     → 200
```

### What Happens Under the Hood

| Component | Action |
|-----------|--------|
| **FastAPI** | Creates `async_jobs` row, enqueues Celery |
| **Celery** | `ai_tasks.generate_case_summary` — loads case + OCR text |
| **LLM** | Local: `LlmStubProvider`; Prod: Azure OpenAI (ADR-008) |
| **PostgreSQL** | `ai.ai_summaries` status `pending_review` → `approved` |
| **Audit** | `ai.summary.approved` |
| **Redis** | Job progress cache |

### Interview Talking Points
- **202 + async job** — API stays under 500 ms p95; long work in worker pool.
- **HITL gate** — configurable per summary type; aligns with bar rules.
- **No auto-send** — explicit non-goal in product docs.

### Screenshot Placeholders
- `![AI summary pending review](./screenshots/06-ai-pending.png)`
- `![Approved summary](./screenshots/07-ai-approved.png)`

**Timing:** 10:00 – 14:00

---

## Act 5 — Workflow, Notifications, n8n (3:00)

### Screen
`/cases/{id}/workflows` + notification bell (header)

### Actions
1. Click **Trigger workflow** (document notification or seeded workflow def)
2. Show execution status `running` → `completed`
3. Click **notification bell** — show in-app notification from document upload
4. *(Optional)* RabbitMQ UI — show queue depth returning to 0
5. *(Optional)* n8n UI — show workflow execution log

### API Sequence
```http
POST /api/v1/workflows/trigger              → 202
GET  /api/v1/workflows                      → list executions
GET  /api/v1/notifications/unread-count
GET  /api/v1/notifications
```

### What Happens Under the Hood

| Component | Action |
|-----------|--------|
| **WorkflowService** | Creates execution record, enqueues Celery relay |
| **Celery** | POST to n8n internal webhook with HMAC secret |
| **n8n** | Runs nodes (HTTP, email stub, Teams stub) — **no PostgreSQL nodes** |
| **n8n callback** | `POST /api/internal/n8n/{slug}` — updates step status |
| **PostgreSQL** | `workflows.workflow_executions`, `shared.notifications` |
| **Redis** | Rate limit keys (not on this path) |

### Interview Talking Points
- **ADR-002:** n8n orchestrates; FastAPI decides.
- n8n is **private network only** — security scan must fail on public exposure.
- Notifications: in-app now; SES + Teams in Phase 2.

### Screenshot Placeholders
- `![Workflow execution](./screenshots/08-workflow.png)`
- `![Notification bell](./screenshots/09-notifications.png)`

**Timing:** 14:00 – 17:00

---

## Act 6 — Managing Partner Audit Review (2:00)

### Screen
`/audit` (Managing Partner only)

### Actions
1. Sign out → sign in as **partner@example.com**
2. Navigate **Audit** in sidebar
3. Filter mentally for today's actions: case created, document confirmed, summary approved
4. Point to `actor_id`, `action`, `resource_type`, `details.caseId`

### API
```http
GET /api/v1/audit/logs?pageSize=50
Authorization: Bearer {partnerToken}
```

### What Happens Under the Hood
- **RBAC:** `FIRM_WIDE_ACCESS_ROLES` — ManagingPartner, SystemAdministrator only
- **PostgreSQL:** `audit.audit_logs` — append-only, indexed by `firm_id + created_at`
- Attorney (Jane) gets **403** on same endpoint — demo briefly if time

### Interview Talking Points
- **Immutable audit** — compliance officer can reconstruct who did what, when.
- 7-year retention default; legal hold overrides deletion.
- Matter walls + audit = defensible access control story.

### Screenshot Placeholder
`![Audit log viewer](./screenshots/10-audit-log.png)`

**Timing:** 17:00 – 19:00

---

## Act 7 — Observability & Production Scale (1:00)

### Screen
Grafana (`localhost:3001`) + `docker compose logs api --tail 20`

### Actions
1. Show JSON log line with `correlationId`, redacted PII
2. Show Tempo trace (if available) linking API → worker
3. Verbal bridge to production topology

### Talking Points — Production Scalability

| Tier | Scale approach |
|------|----------------|
| **Web (Next.js)** | ECS Fargate horizontal pods behind ALB |
| **API (FastAPI)** | Stateless replicas; connection pool to RDS |
| **Workers** | Auto-scale on RabbitMQ queue depth |
| **PostgreSQL** | RDS Multi-AZ; read replicas for reporting |
| **Redis** | ElastiCache cluster — cache + rate limit + Celery backend |
| **S3** | Unlimited; lifecycle policies for archived matters |
| **n8n** | Dedicated ECS service; no autoscale to zero |

- Target: **1,000 concurrent users**, **50k workflow executions/month**
- **99.9% SLA** — RPO 15 min, RTO 4 hr
- **CloudFront + WAF** at edge; JWT + RBAC + matter walls in app layer

### Screenshot Placeholder
`![Grafana trace](./screenshots/11-grafana-trace.png)`

**Timing:** 19:00 – 20:00

---

## Closing Statement (30 sec)

> "What you saw is one insurance coverage matter — from intake to audited AI output — with every boundary we'd deploy in production: presigned storage, async workers, human approval, private orchestration, and immutable audit. LexFlow augments attorneys; it never replaces their judgment."

---

## Fallback Plans

| Failure | Recovery |
|---------|----------|
| OCR slow | Show job polling UI; narrate worker processing |
| n8n unreachable | Show outbox row in DB; explain retry |
| AI stub empty | Show `pending_review` row; approve pre-seeded summary |
| Partner login fails | Run `make seed-sprint5` |

---

## Related Docs

- [E2E Flow](./E2E_FLOW.md)
- [Executive Presentation](./EXECUTIVE_PRESENTATION.md)
- [Architecture Walkthrough](../interview/ARCHITECTURE_WALKTHROUGH.md)

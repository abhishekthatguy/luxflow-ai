# LexFlow AI — Data Flow Architecture

**Purpose:** Sync vs async request paths for AI assistants implementing features.  
**Authoritative source:** `docs/03-architecture/data-flow.md`  
**Canonical pipeline:** `Frontend → FastAPI → Queue → Worker → n8n → External`

---

## Path Selection Rules

| Path | When | Response | Authority |
|------|------|----------|-----------|
| **Synchronous** | Reads, light writes (< 200ms), auth, config | 200/201 JSON | FastAPI + PostgreSQL/Redis |
| **Asynchronous** | Workflows, AI, OCR, bulk, external orchestration | 202 + jobId + statusUrl | FastAPI initiates; Worker executes |
| **Callback** | n8n completion, external webhooks | Internal HMAC endpoint | FastAPI persists final state |
| **Real-time push** | Job done, notifications | SSE / poll / WebSocket | FastAPI → Frontend |

**Decision tree:**
```
Request → Authenticated? → No → 401
       → Authorized (RBAC + matter wall)? → No → 403 or 404 (ADR-007)
       → Read or light write? → Sync path → 200/201
       → Workflow/AI/OCR/bulk? → Async path → 202
```

---

## Dual-Path Overview

```mermaid
flowchart TB
    subgraph Client["Client Tier"]
        FE["Next.js Frontend"]
    end

    subgraph SyncPath["Synchronous Path"]
        API_S["FastAPI"]
        PG_S[("PostgreSQL")]
        REDIS["Redis Cache"]
    end

    subgraph AsyncPath["Asynchronous Path"]
        API_A["FastAPI"]
        OUTBOX["Outbox Table"]
        RMQ["RabbitMQ"]
        WORKER["Celery Worker"]
        N8N["n8n — Private"]
        EXT["External APIs"]
    end

    FE -->|"GET, light PATCH"| API_S
    API_S --> PG_S & REDIS
    API_S -->|"200/201"| FE

    FE -->|"POST trigger, AI, upload complete"| API_A
    API_A --> OUTBOX & RMQ
    API_A -->|"202 Accepted"| FE
    RMQ --> WORKER
    WORKER --> N8N & PG_S & EXT
    N8N -->|"HMAC callback"| API_A
    API_A -->|"SSE / poll"| FE
```

---

## Isolation Rules (Non-Negotiable)

| Rule | Enforcement |
|------|-------------|
| Frontend never calls n8n, RabbitMQ, workers | No credentials in browser; network isolation |
| Frontend never calls LLM providers | No API keys client-side |
| All mutations audited | Audit middleware + domain handlers |
| Async jobs return correlation ID | `X-Correlation-Id` propagated end-to-end |
| n8n never writes PostgreSQL | No DB credentials in n8n; architecture review |

---

## Sync Path — Case Detail Read

```mermaid
sequenceDiagram
    actor User
    participant FE as Next.js
    participant API as FastAPI
    participant RBAC as Auth + Matter Wall
    participant Redis as Redis
    participant PG as PostgreSQL

    User->>FE: Open case detail
    FE->>API: GET /api/v1/cases/{id}<br/>Bearer JWT + X-Correlation-Id
    API->>RBAC: Validate JWT + matter wall
    alt Matter wall deny
        RBAC-->>FE: 404 Not Found (ADR-007)
    end
    API->>Redis: GET case:{id} (TTL 60s)
    API->>PG: Load case + participants + timeline
    API-->>FE: 200 { data: CaseDetail }
```

**Characteristics:** Immediate response, cache-friendly, matter wall before data load.

---

## Sync Path — Lightweight Write (Task Complete)

```mermaid
sequenceDiagram
    actor User
    participant FE as Next.js
    participant API as FastAPI
    participant UC as CompleteTaskCommand
    participant PG as PostgreSQL
    participant Audit as AuditWriter

    User->>FE: Mark task complete
    FE->>API: PATCH /api/v1/tasks/{id}<br/>If-Match: version
    API->>UC: Execute synchronously
    UC->>PG: Update task + timeline event
    UC->>Audit: task.completed
    alt Version conflict
        UC-->>FE: 409 Conflict
    end
    UC-->>FE: 200 { data: Task }
```

**Sync write criteria:** Single aggregate mutation, < 200ms, no external API calls.

---

## Async Path — Workflow Trigger (Canonical)

```mermaid
sequenceDiagram
    actor User
    participant FE as Next.js
    participant API as FastAPI
    participant PG as PostgreSQL
    participant RMQ as RabbitMQ
    participant Worker as Celery
    participant N8N as n8n
    participant MS365 as Microsoft 365
    participant SSE as SSE

    User->>FE: Trigger intake workflow
    FE->>API: POST /cases/{id}/workflows/trigger<br/>Idempotency-Key
    API->>PG: BEGIN — insert execution + outbox
    API->>PG: COMMIT
    API->>RMQ: Enqueue workflow.trigger
    API-->>FE: 202 { jobId, statusUrl, correlationId }
    FE->>SSE: Subscribe /jobs/{jobId}/events

    Worker->>RMQ: Consume task
    Worker->>N8N: POST /webhook/intake (HMAC)
    Worker->>PG: status = running
    N8N->>MS365: SharePoint + email
    N8N->>API: POST /internal/webhooks/n8n (HMAC)
    API->>PG: status = completed + audit
    API->>SSE: job.completed
    SSE-->>FE: Update timeline
```

**Key points:**
- FastAPI authorizes BEFORE enqueue
- Transaction includes outbox event (ADR-006)
- n8n only executes external I/O
- Final state persisted by FastAPI callback handler

---

## Async Path — AI Document Summary

```mermaid
sequenceDiagram
    actor User
    participant FE as Next.js
    participant API as FastAPI
    participant RMQ as RabbitMQ
    participant Worker as Celery
    participant S3 as S3
    participant LLM as Azure OpenAI
    participant PG as PostgreSQL

    User->>FE: Request AI summary
    FE->>API: POST /documents/{id}/summarize
    API->>API: Auth + matter wall + doc ready
    API->>PG: Create ai_summary (generating)
    API->>RMQ: Enqueue ai.summarize
    API-->>FE: 202 { jobId }

    Worker->>S3: Fetch document text
    Worker->>Worker: Safety pipeline (PII redaction)
    Worker->>LLM: Generate summary
    Worker->>PG: Update ai_summary (draft) + prompt_history + llm_usage
    Worker->>PG: Audit + timeline event

    FE->>API: GET /ai/summaries/{id}
    API-->>FE: 200 { status: draft, content }
    Note over User,PG: HITL — attorney approves before team visibility
```

**Never:** LLM call in API handler. Always worker path (ADR-004).

---

## Document Upload Flow

```mermaid
flowchart LR
    FE[Frontend] -->|1 POST /uploads/init| API[FastAPI]
    API -->|2 Create doc status=uploading| PG[(PostgreSQL)]
    API -->|3 Presigned PUT URL| FE
    FE -->|4 PUT binary| S3[(S3)]
    FE -->|5 POST /uploads/complete| API
    API -->|6 Verify checksum| S3
    API -->|7 status=processing| PG
    API -->|8 Enqueue document.process| RMQ[RabbitMQ]
    RMQ --> WRK[Worker]
    WRK -->|OCR, metadata| PG
    WRK -->|DocumentProcessed| RMQ
```

**Rule:** Binary never transits API containers — presigned S3 only.

---

## Real-Time Update Patterns

| Pattern | Use Case | Endpoint |
|---------|----------|----------|
| **SSE** (preferred) | Job status, notifications | `GET /api/v1/jobs/{id}/events` |
| **Polling** (fallback) | Restrictive proxies | `GET /api/v1/jobs/{id}` every 3s + backoff |
| **WebSocket** (Phase 2) | Bidirectional collaboration | FastAPI WS endpoint |

```mermaid
sequenceDiagram
    participant FE as Frontend
    participant API as FastAPI
    participant Redis as Redis Pub/Sub

    FE->>API: SSE connect
    API->>Redis: SUBSCRIBE job:{jobId}
    Note over API: Worker completes
    API->>Redis: PUBLISH job:{jobId}
    Redis-->>API: Message
    API-->>FE: event: completed
```

---

## Data Classification by Flow

| Flow | Classification | Encryption | Retention |
|------|----------------|------------|-----------|
| Case metadata (sync) | Confidential | TLS + RDS at rest | Case lifecycle |
| Document binary (S3) | Privileged | SSE-KMS | 7+ years post-close |
| AI prompt/response | Work product | TLS + optional field encryption | 3 years |
| Queue payload | Confidential | AMQP TLS; no PII in headers | 7 day TTL |
| n8n callback | Confidential | HMAC + TLS | Persisted in workflow_executions |
| Audit entries | Compliance | Append-only immutable | 7 years minimum |

---

## Implementation Checklist for AI Assistants

### Adding a sync endpoint
- [ ] JWT + RBAC + matter wall middleware
- [ ] Single aggregate mutation or read
- [ ] Audit log on mutation
- [ ] Optimistic concurrency if updating (`If-Match`)
- [ ] Response envelope per `docs/04-api/rest-standards.md`

### Adding an async endpoint
- [ ] Return 202 with `jobId`, `statusUrl`, `correlationId`
- [ ] Persist job record + outbox in same transaction
- [ ] Enqueue Celery task with idempotency check
- [ ] Worker: idempotent handler, matter wall re-check
- [ ] SSE or poll endpoint for status
- [ ] Audit on completion/failure

### Adding n8n integration
- [ ] FastAPI decides IF to trigger (auth + business rules)
- [ ] Worker invokes n8n webhook with HMAC
- [ ] n8n callbacks to `/internal/webhooks/n8n`
- [ ] FastAPI persists final state — n8n does not write DB

---

## Best Practices

1. Default to async for anything > 500ms expected
2. Propagate `X-Correlation-Id` Frontend → Worker → n8n → callback
3. `Idempotency-Key` on all async triggers
4. Matter wall check at submission AND worker execution
5. Persist AI/workflow results before notifying frontend
6. Presigned S3 for all file uploads

---

## References

| Document | Topic |
|----------|-------|
| `docs/03-architecture/data-flow.md` | Full specification |
| `docs/03-architecture/event-driven-design.md` | Outbox + RabbitMQ |
| `docs/04-api/endpoints-ai.md` | AI 202 pattern |
| `docs/06-workflows/webhook-contracts.md` | n8n payloads |
| `memory/INVARIANTS.md` | Non-negotiable rules |
| `architecture/DECISIONS.md` | ADR-004, ADR-006 |

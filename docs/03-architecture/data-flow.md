# Data Flow Architecture

**LexFlow AI** — Synchronous & Asynchronous Paths  
**Version:** 1.0  
**Status:** Draft — Pre-Implementation  
**Last Updated:** 2026-07-06

---

## Purpose

This document describes **how data moves through LexFlow AI** — distinguishing synchronous paths (immediate user feedback) from asynchronous paths (automation, AI, workflows). It defines the canonical pipeline:

```
Frontend → FastAPI → Queue → Worker → n8n → External
```

All paths enforce authentication and authorization at FastAPI before any domain handler executes.

---

## Scope

| In Scope | Out of Scope |
|----------|--------------|
| Sync read/write request flows | Database query optimization |
| Async job lifecycle (202 → completion) | n8n workflow node graphs |
| Real-time update delivery (SSE/WebSocket) | Frontend state management internals |
| Document upload flow (presigned S3) | CDN cache invalidation rules |
| AI inference async pipeline | LLM prompt templates |

---

## Responsibilities

| Path Type | When Used | Response Pattern | Authority |
|-----------|-----------|------------------|-----------|
| **Synchronous** | Reads, lightweight writes, auth, config | 200/201 immediate JSON | FastAPI + PostgreSQL/Redis |
| **Asynchronous** | Workflows, AI, OCR, bulk ops, notifications | 202 + job polling/SSE | FastAPI initiates; Worker executes |
| **Callback** | n8n completion, external webhooks | Internal HMAC endpoint | FastAPI persists final state |
| **Real-time push** | Job completion, notifications | SSE/WebSocket/polling | FastAPI → Frontend |

### Path Ownership Rules

| Rule | Enforcement |
|------|-------------|
| Frontend never calls n8n, RabbitMQ, or workers | Network + no credentials in browser |
| Frontend never calls LLM providers | No API keys client-side |
| All mutations audited | Audit middleware + domain handlers |
| Async jobs return correlation ID | Middleware generates if absent |
| n8n never writes to PostgreSQL | Architecture + no DB credentials in n8n |

---

## Architecture

### Dual-Path Overview

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

    FE -->|"GET, light POST"| API_S
    API_S --> PG_S
    API_S --> REDIS
    API_S -->|"JSON response"| FE

    FE -->|"POST trigger, AI, bulk"| API_A
    API_A --> OUTBOX
    API_A --> RMQ
    API_A -->|"202 Accepted"| FE
    RMQ --> WORKER
    WORKER --> N8N
    WORKER --> PG_S
    N8N --> EXT
    N8N -->|"HMAC callback"| API_A
    API_A -->|"SSE / poll"| FE
```

### Path Selection Decision Tree

```mermaid
flowchart TD
    START["Incoming API Request"] --> AUTH{"Authenticated<br/>& Authorized?"}
    AUTH -->|No| REJECT["401 / 403"]
    AUTH -->|Yes| TYPE{"Operation Type?"}

    TYPE -->|Read / Query| SYNC["Synchronous Path"]
    TYPE -->|Light write<br/>< 200ms expected| SYNC
    TYPE -->|Workflow trigger| ASYNC["Asynchronous Path"]
    TYPE -->|AI inference| ASYNC
    TYPE -->|Document processing| ASYNC
    TYPE -->|Bulk operation| ASYNC
    TYPE -->|External orchestration| ASYNC

    SYNC --> CACHE{"Cache hit?"}
    CACHE -->|Yes| RETURN_C["200 + cached data"]
    CACHE -->|No| DB["PostgreSQL query"]
    DB --> RETURN_S["200 / 201 response"]

    ASYNC --> PERSIST["Persist intent + outbox"]
    PERSIST --> ENQUEUE["Publish to RabbitMQ"]
    ENQUEUE --> RETURN_A["202 + jobId + correlationId"]
```

---

## Flow Diagrams

### Synchronous Path — Case Detail Read

```mermaid
sequenceDiagram
    actor User
    participant FE as Next.js
    participant API as FastAPI
    participant Auth as Auth Middleware
    participant RBAC as PermissionResolver
    participant Redis as Redis
    participant PG as PostgreSQL

    User->>FE: Open case detail page
    FE->>API: GET /api/v1/cases/{id}<br/>Authorization: Bearer JWT<br/>X-Correlation-Id: uuid

    API->>Auth: Validate JWT
    Auth->>RBAC: Check matter wall + RBAC
    alt Not authorized
        RBAC-->>FE: 404 Not Found
    end

    API->>Redis: GET permissions:{userId}
    alt Cache miss
        API->>PG: Load case + participants + timeline
        API->>Redis: SET case:{id} TTL 60s
    else Cache hit
        API->>PG: Load case (partial cache)
    end

    API-->>FE: 200 { data: CaseDetail }
    FE-->>User: Render case view
```

### Synchronous Path — Lightweight Write

```mermaid
sequenceDiagram
    actor Paralegal
    participant FE as Next.js
    participant API as FastAPI
    participant UC as CompleteTaskCommand
    participant PG as PostgreSQL
    participant Audit as AuditWriter

    Paralegal->>FE: Mark task complete
    FE->>API: PATCH /api/v1/tasks/{id}<br/>If-Match: version

    API->>UC: Execute (sync — no queue)
    UC->>PG: Update task, increment version
    UC->>PG: Append timeline event
    UC->>Audit: task.completed

    alt Version conflict
        UC-->>FE: 409 Conflict
    end

    UC-->>FE: 200 { data: Task }
    FE-->>Paralegal: UI updated
```

### Asynchronous Path — Workflow Trigger (Canonical)

```mermaid
sequenceDiagram
    actor Attorney
    participant FE as Next.js
    participant API as FastAPI
    participant PG as PostgreSQL
    participant RMQ as RabbitMQ
    participant Worker as Celery Worker
    participant N8N as n8n
    participant MS365 as Microsoft 365
    participant SSE as SSE Channel

    Attorney->>FE: Trigger "New Client Intake" workflow
    FE->>API: POST /api/v1/cases/{id}/workflows/trigger<br/>Idempotency-Key: uuid

    API->>PG: BEGIN TRANSACTION
    API->>PG: Insert workflow_execution (queued)
    API->>PG: Insert outbox_event (WorkflowTriggered)
    API->>PG: COMMIT
    API->>RMQ: Enqueue workflow.trigger task
    API-->>FE: 202 { jobId, statusUrl, correlationId }

    FE->>SSE: Subscribe /api/v1/jobs/{jobId}/events

    Worker->>RMQ: Consume workflow.trigger
    Worker->>PG: Idempotent — load execution
    Worker->>N8N: POST /webhook/intake (HMAC signed)
    Worker->>PG: status = running

    N8N->>MS365: Create SharePoint folder
    N8N->>MS365: Send welcome email
    N8N->>API: POST /internal/webhooks/n8n (HMAC)

    API->>PG: status = completed, output_payload
    API->>PG: Timeline event, audit log
    API->>SSE: Push job.completed
    SSE-->>FE: Event received
    FE-->>Attorney: Timeline updated
```

### Asynchronous Path — AI Document Summary

```mermaid
sequenceDiagram
    actor Attorney
    participant FE as Next.js
    participant API as FastAPI
    participant RMQ as RabbitMQ
    participant Worker as Celery Worker
    participant S3 as S3
    participant LLM as LLM Provider
    participant PG as PostgreSQL

    Attorney->>FE: Request AI summary
    FE->>API: POST /api/v1/documents/{id}/summarize

    API->>API: Authorize, validate document ready
    API->>PG: Create ai_summary (generating)
    API->>RMQ: Enqueue ai.summarize
    API-->>FE: 202 { jobId }

    Worker->>S3: Fetch document text
    Worker->>LLM: Generate summary (provider abstraction)
    Worker->>PG: Update ai_summary (draft)
    Worker->>PG: Log prompt_history, llm_usage
    Worker->>PG: Audit + timeline event

    Note over FE,PG: Attorney reviews draft — human-in-the-loop
    FE->>API: GET /api/v1/ai/summaries/{id}
    API-->>FE: 200 { status: draft, content: "..." }
```

### Document Upload Data Flow

```mermaid
flowchart LR
    FE["Frontend"] -->|"1. POST /uploads/init"| API["FastAPI"]
    API -->|"2. Create document record<br/>status=uploading"| PG[("PostgreSQL")]
    API -->|"3. Presigned PUT URL"| FE
    FE -->|"4. PUT binary"| S3[("S3")]
    FE -->|"5. POST /uploads/complete"| API
    API -->|"6. Verify checksum"| S3
    API -->|"7. status=processing"| PG
    API -->|"8. Enqueue document.process"| RMQ["RabbitMQ"]
    RMQ --> WRK["Worker"]
    WRK -->|"OCR, metadata"| PG
    WRK -->|"DocumentProcessed event"| RMQ
```

---

## Real-Time Update Patterns

| Pattern | Use Case | Implementation |
|---------|----------|----------------|
| **SSE** | Job status, notifications | `GET /api/v1/jobs/{id}/events` — preferred |
| **WebSocket** | Bidirectional case collaboration (Phase 2) | FastAPI WebSocket endpoint |
| **Polling** | Fallback for restrictive proxies | `GET /api/v1/jobs/{id}` every 3s with backoff |

```mermaid
sequenceDiagram
    participant FE as Frontend
    participant API as FastAPI
    participant Redis as Redis Pub/Sub

    FE->>API: SSE connect (job events)
    API->>Redis: SUBSCRIBE job:{jobId}

    Note over API: Worker completes job
    API->>Redis: PUBLISH job:{jobId} completed
    Redis-->>API: Message
    API-->>FE: event: completed
    FE->>API: Close SSE, refresh case timeline
```

---

## Data Flow Classification

| Flow | Classification | Encryption | Retention |
|------|----------------|------------|-----------|
| Case metadata (sync) | Confidential | TLS in transit, RDS at rest | Per case lifecycle |
| Document binary (S3) | Privileged | SSE-KMS | 7+ years post-close |
| AI prompt/response (async) | Work product | TLS + optional field encryption | 3 years (prompt_history) |
| Workflow payload (queue) | Confidential | TLS (AMQP), no PII in headers | Transient — 7 day TTL |
| n8n callback payload | Confidential | HMAC + TLS | Persisted in workflow_executions |
| Audit entries | Compliance | Append-only, immutable | 7 years minimum |

---

## Best Practices

1. **Default to async for anything > 500ms** — Protect API latency percentiles and user experience.
2. **Return 202 with status URL** — Never block HTTP on LLM or external API calls.
3. **Propagate correlation ID end-to-end** — Frontend generates or accepts `X-Correlation-Id`; workers and n8n include it.
4. **Idempotency-Key on all async triggers** — Prevents duplicate workflow executions from double-clicks.
5. **Presigned S3 uploads** — Binary data never transits API containers.
6. **Human-in-the-loop gate before external send** — AI drafts stay internal until attorney approval.
7. **Matter wall check before every data flow** — Even async workers verify case access for triggered_by user.

---

## Tradeoffs

| Decision | Benefit | Cost |
|----------|---------|------|
| 202 + polling/SSE vs WebSocket everywhere | Simpler infra, proxy-friendly | Slight delay vs push-native WS |
| Outbox + direct enqueue | Faster worker pickup for urgent tasks | Dual publish path — must stay consistent |
| Sync path for light writes | Immediate UI feedback | Risk of scope creep — monitor p95 latency |
| n8n in async path only | Clean security boundary | Additional hop vs direct Graph API from worker |
| S3 presigned upload | Scales to large files | Client must handle upload retry |

---

## Future Improvements

| Phase | Enhancement |
|-------|-------------|
| Phase 2 | WebSocket for collaborative case editing |
| Phase 2 | GraphQL subscriptions for real-time dashboards |
| Phase 3 | Change Data Capture (CDC) for analytics pipeline |
| Phase 3 | Priority lanes — urgent deadline workflows preempt bulk jobs |
| Phase 4 | Event-driven read model projection for sub-100ms search |

---

## References

| Document | Description |
|----------|-------------|
| [README.md](./README.md) | Architecture folder index |
| [system-context.md](./system-context.md) | C4 Level 1 |
| [container-architecture.md](./container-architecture.md) | C4 Level 2 |
| [component-architecture.md](./component-architecture.md) | C4 Level 3 |
| [event-driven-design.md](./event-driven-design.md) | Outbox and RabbitMQ detail |
| [cross-cutting-concerns.md](./cross-cutting-concerns.md) | Idempotency, tracing |
| [../api-architecture.md](../api-architecture.md) | REST conventions, 202 pattern |
| [../ai-architecture.md](../ai-architecture.md) | AI async pipeline |
| [../workflow-orchestration.md](../workflow-orchestration.md) | n8n webhook contracts |
| [../13-decisions/004-async-ai-processing.md](../13-decisions/004-async-ai-processing.md) | Async AI decision |

# Architecture Deep Dive — 45-Minute Discussion Guide

**LexFlow AI** — Staff-Level System Design Topics  
**Version:** 1.0  
**Status:** Draft — Pre-Implementation  
**Last Updated:** 2026-07-06

---

## Purpose

This document supports a **45-minute architecture deep dive** — the whiteboard session after the [15-minute elevator pitch](./system-design-overview.md). Each section is a self-contained topic with diagrams, talking points, likely interviewer probes, and cross-references to canonical docs.

**Recommended flow:** Sections 1 → 2 → 3 → 5 → 4 → 6 → 7 → 8 (domain first, then events, then AI, then ops).

---

## Scope

| In Scope | Out of Scope |
|----------|--------------|
| C4 Level 3 component design | Source code walkthrough |
| Domain-driven design boundaries | UI component hierarchy |
| Event-driven integration patterns | Terraform module internals |
| n8n bridge contracts | Individual n8n workflow JSON |
| RAG and AI safety architecture | Model fine-tuning |
| Observability and DR at architecture level | Runbook step-by-step commands |

---

## Table of Contents

1. [Domain Model & Bounded Contexts](#1-domain-model--bounded-contexts)
2. [Hexagonal Architecture & FastAPI Components](#2-hexagonal-architecture--fastapi-components)
3. [Event-Driven Design & Outbox](#3-event-driven-design--outbox)
4. [AI Pipeline — Async, RAG, Human-in-the-Loop](#4-ai-pipeline--async-rag-human-in-the-loop)
5. [Workflow Orchestration & n8n Boundary](#5-workflow-orchestration--n8n-boundary)
6. [Data Architecture — PostgreSQL, S3, pgvector](#6-data-architecture--postgresql-s3-pgvector)
7. [API, AuthZ & Matter Walls](#7-api-authz--matter-walls)
8. [Observability, Deployment & Disaster Recovery](#8-observability-deployment--disaster-recovery)

---

## 1. Domain Model & Bounded Contexts

### Talking Points

- **Case (Matter)** is the aggregate root — documents, workflows, AI outputs, and audit entries attach to cases.
- Eight bounded contexts with **schema-separated PostgreSQL** — no cross-context table writes.
- **Matter walls** are a domain policy enforced by Identity & Access, applied at query time in every context.
- Integration between contexts is **event-first**; synchronous calls only for read-only query interfaces.

### Context Map

```mermaid
flowchart TB
    subgraph Core["Core Domain"]
        CASE["Case Management ★<br/>Aggregate: Case"]
    end

    subgraph Supporting["Supporting Contexts"]
        ID["Identity & Access"]
        DOC["Document Management"]
        WF["Workflow Orchestration"]
        AI["AI & Knowledge"]
    end

    subgraph Generic["Generic Subdomains"]
        CLIENT["Client Management"]
        NOTIFY["Notifications"]
        AUDIT["Audit & Compliance"]
    end

    CASE -->|Customer-Supplier| CLIENT
    CASE -->|Customer-Supplier| DOC
    DOC -->|Published events| AI
    CASE -->|Conformance| WF
    ID -->|ACL enforcement| CASE
    CASE -->|Events| NOTIFY
    CASE -->|Events| AUDIT

    style CASE fill:#d4edda,stroke:#155724
```

### Key Domain Events

| Event | Publisher | Typical Consumers |
|-------|-----------|-------------------|
| `CaseCreated` | Case Management | Workflow, Notifications, Audit |
| `DocumentUploaded` | Document Management | OCR worker, Workflow |
| `DocumentProcessed` | Document Management | AI embeddings, Workflow |
| `WorkflowTriggered` | Workflow Orchestration | Celery → n8n bridge |
| `SummaryGenerated` | AI & Knowledge | Notifications, Approvals |
| `ApprovalRequested` | Audit & Compliance | Notifications |

Full catalog: [02-domain/domain-events.md](../02-domain/domain-events.md).

### Interviewer Probes

| Probe | Strong Answer |
|-------|---------------|
| "Why not one big schema?" | Schema separation enforces bounded context ownership; events prevent tight coupling |
| "Who owns the client record?" | Client Management — Case references `client_id` read-only |
| "How do ethical walls work in the domain?" | `MatterWallPolicy` in Identity; Case stores participant list; every query filters |

**Go deeper:** [02-domain/case-aggregate.md](../02-domain/case-aggregate.md), [domain-model.md](../domain-model.md).

---

## 2. Hexagonal Architecture & FastAPI Components

### Talking Points

- FastAPI `apps/api` is a **thin HTTP adapter** — all logic in `services/{context}/`.
- **Workers import the same use cases** as API routes — no duplicated business rules.
- **Domain layer never imports infrastructure** — repository interfaces live in domain.
- Middleware stack order matters: CORS → CorrelationId → RateLimit → Auth → Audit.

### C4 Level 3 — Component Diagram

```mermaid
C4Component
    title FastAPI — Internal Components

    Container_Boundary(api, "FastAPI API Service") {
        Component(mw, "Middleware", "Auth, rate limit, audit, correlation")
        Component(router, "API Router v1", "REST by resource")
        Component(internal, "Internal Webhooks", "n8n HMAC callbacks")

        Component(identity, "Identity Module", "RBAC, sessions")
        Component(cases, "Case Management", "Cases, tasks, walls")
        Component(docs, "Document Management", "Upload, OCR triggers")
        Component(workflow, "Workflow Orchestration", "n8n bridge")
        Component(ai, "AI & Knowledge", "LLM, prompts, RAG")
        Component(audit, "Audit & Compliance", "Immutable log")
        Component(shared, "Shared Kernel", "Outbox, DB, tracing")
    }

    ContainerDb(pg, "PostgreSQL", "RDS")
    ContainerQueue(rmq, "RabbitMQ", "Amazon MQ")

    Rel(router, mw, "Through")
    Rel(router, cases, "Delegates")
    Rel(router, ai, "Delegates")
    Rel(internal, workflow, "Callbacks")
    Rel(cases, shared, "Uses")
    Rel(shared, pg, "SQLAlchemy")
    Rel(shared, rmq, "Publish")
```

### Hexagonal Layers per Context

```mermaid
flowchart TB
    subgraph Driving["Driving Adapters"]
        HTTP["FastAPI Routes"]
        CELERY["Celery Tasks"]
        WH["n8n Webhooks"]
    end

    subgraph Application["Application Layer"]
        CMD["Commands / Queries"]
        UC["Use Cases"]
    end

    subgraph Domain["Domain Layer"]
        ENT["Entities & Aggregates"]
        EVT["Domain Events"]
        REPO["Repository Interfaces"]
    end

    subgraph Driven["Driven Adapters"]
        SQL["SQLAlchemy Repos"]
        S3["S3 Adapter"]
        N8N["n8n Bridge"]
        LLM["LLM Adapters"]
    end

    HTTP & CELERY & WH --> UC
    UC --> ENT & REPO & EVT
    REPO -.-> SQL & S3
    UC --> N8N & LLM
```

### Worker Task → Use Case Mapping

| Celery Task | Queue | Use Case |
|-------------|-------|----------|
| `document.process` | `document.process.normal` | `ProcessDocumentCommand` |
| `workflow.trigger` | `workflow.trigger.normal` | `TriggerWorkflowCommand` |
| `ai.summarize` | `ai.inference.normal` | `GenerateSummaryCommand` |
| `ai.embed` | `ai.embed.low` | `CreateEmbeddingsCommand` |
| `outbox.publish` | `system.outbox.high` | `PublishPendingEvents` |

**Go deeper:** [03-architecture/component-architecture.md](../03-architecture/component-architecture.md), [folder-structure.md](../folder-structure.md).

---

## 3. Event-Driven Design & Outbox

### Talking Points

- **Dual-write problem:** Cannot write to PostgreSQL AND publish to RabbitMQ in one atomic operation without the outbox.
- **Outbox pattern:** Domain change + `outbox_events` INSERT in **single transaction**; publisher polls and marks published.
- **At-least-once delivery** with **idempotent consumers** — use `idempotency_key` on handlers.
- **DLQ after max retries** — alert on any DLQ message count > 0.

### Event Pipeline

```mermaid
flowchart TB
    subgraph Produce["Production — Same Transaction"]
        CMD["Command Handler"]
        AGG["Aggregate Persist"]
        OB["outbox_events INSERT"]
        CMD --> AGG --> OB
    end

    subgraph Publish["Outbox Publisher — Celery beat 1s"]
        POLL["Poll pending"]
        RMQ_PUB["Publish to RabbitMQ"]
        MARK["Mark published_at"]
        POLL --> RMQ_PUB --> MARK
    end

    subgraph Broker["RabbitMQ Topic Exchange"]
        EX["lexflow.events"]
        Q1["case.events"]
        Q2["document.events"]
        Q3["workflow.events"]
        Q4["ai.events"]
        DLQ["*.dlq"]
    end

    subgraph Consume["Idempotent Handlers"]
        H1["Workflow Handler"]
        H2["AI Handler"]
        H3["Notification Handler"]
    end

    OB --> POLL
    RMQ_PUB --> EX
    EX --> Q1 & Q2 & Q3 & Q4
    Q3 --> H1
    Q4 --> H2
    Q1 --> H3
    Q1 & Q2 & Q3 & Q4 -.->|max retries| DLQ
```

### Saga-Lite — Workflow + Document Coordination

```mermaid
sequenceDiagram
    participant API as FastAPI
    participant PG as PostgreSQL
    participant RMQ as RabbitMQ
    participant DocW as Document Worker
    participant WfW as Workflow Worker
    participant N8N as n8n

    API->>PG: Upload doc + CaseUpdated + outbox
    API-->>API: 201 Created

    RMQ->>DocW: DocumentUploaded
    DocW->>PG: OCR complete → DocumentProcessed

    RMQ->>WfW: DocumentProcessed
    WfW->>PG: Create WorkflowExecution
    WfW->>N8N: Signed webhook trigger
    N8N-->>WfW: Callback via /internal/webhooks
    WfW->>PG: Complete + notify
```

**No distributed 2PC** — each step is idempotent; compensation is manual via admin replay from DLQ.

### Interviewer Probes

| Probe | Strong Answer |
|-------|---------------|
| "Why RabbitMQ not Kafka?" | 50K workflows/month; topic routing + DLQ + priority queues; team familiarity; Amazon MQ managed HA |
| "Why not SQS?" | Need routing keys, DLQ semantics, priority — RabbitMQ fits orchestration fan-out |
| "Exactly-once?" | We target at-least-once + idempotency; exactly-once end-to-end is impractical at our scale |
| "Ordering?" | Per-aggregate ordering via partition key in Phase 2; global ordering not required |

**Go deeper:** [03-architecture/event-driven-design.md](../03-architecture/event-driven-design.md), [ADR-006](../13-decisions/006-transactional-outbox.md), [06-workflows/retry-dlq.md](../06-workflows/retry-dlq.md).

---

## 4. AI Pipeline — Async, RAG, Human-in-the-Loop

### Talking Points

- **All LLM calls via Celery** — API returns 202 immediately ([ADR-004](../13-decisions/004-async-ai-processing.md)).
- **RAG is case-scoped** — every vector query filters `case_id` + matter wall check before retrieval.
- **Hybrid search** — pgvector semantic + PostgreSQL full-text + Reciprocal Rank Fusion (RRF).
- **Human-in-the-loop** — AI output status = `draft` until attorney `approved`; never auto-sent to clients.
- **Prompt registry** — Jinja2 templates versioned in DB; all invocations logged in `prompt_history`.

### End-to-End AI Flow

```mermaid
flowchart TB
    subgraph Request["User Request — Sync Boundary"]
        USER["Attorney requests summary"]
        API["FastAPI — validate + enqueue"]
        RESP["202 + jobId"]
    end

    subgraph Worker["Async Worker Path"]
        LOAD["Load document + case scope"]
        RAG["RAG retrieve — case-filtered chunks"]
        PROMPT["Prompt template + context"]
        LLM["LLM Provider API"]
        STORE["Store draft summary"]
        AUDIT["Audit + prompt_history"]
        NOTIFY["Notify attorney"]
    end

    subgraph Review["Human-in-the-Loop"]
        REVIEW["Attorney reviews draft"]
        APPROVE["Approve / Reject / Edit"]
        CLIENT["Client delivery — only if approved"]
    end

    USER --> API --> RESP
    API -.->|enqueue| LOAD
    LOAD --> RAG --> PROMPT --> LLM --> STORE --> AUDIT --> NOTIFY
    NOTIFY --> REVIEW --> APPROVE --> CLIENT
```

### RAG Pipeline

```mermaid
flowchart LR
    subgraph Ingest["Async Ingestion"]
        OCR["OCR text"]
        CHUNK["Chunk 512 tokens / 64 overlap"]
        EMB["text-embedding-3-small"]
        VEC[("document_embeddings<br/>pgvector HNSW")]
    end

    subgraph Retrieve["Inference-Time Retrieval"]
        AUTHZ["Matter wall check"]
        QEMB["Query embedding"]
        VS["Vector search WHERE case_id = ?"]
        FT["Full-text WHERE case_id = ?"]
        RRF["RRF merge top-K"]
    end

    OCR --> CHUNK --> EMB --> VEC
    AUTHZ --> QEMB --> VS
    AUTHZ --> FT
    VS & FT --> RRF
```

### AI Safety Controls

| Control | Implementation |
|---------|----------------|
| Case scope | `case_id` filter on every retrieval query |
| PII redaction | Pre-LLM redaction pipeline; no PII in logs |
| Prompt injection defense | System prompt hardening; no user content in system role |
| Output validation | Schema validation; citation requirement for research |
| Usage metering | Per-firm, per-case token tracking — [07-ai/usage-metering.md](../07-ai/usage-metering.md) |
| Provider DPAs | Azure OpenAI preferred for firm data residency |

**Go deeper:** [07-ai/rag-architecture.md](../07-ai/rag-architecture.md), [07-ai/safety-guardrails.md](../07-ai/safety-guardrails.md), [07-ai/human-in-the-loop.md](../07-ai/human-in-the-loop.md).

---

## 5. Workflow Orchestration & n8n Boundary

### Talking Points

- n8n is a **private HTTP orchestration engine** — invisible to end users.
- **FastAPI decides** whether a workflow may run (authZ, case state, firm config).
- **Workers invoke n8n** via HMAC-signed webhooks on internal ALB.
- **n8n callbacks** hit `/internal/webhooks` — HMAC verified, excluded from public OpenAPI.
- **Git is source of truth** for workflow JSON — sandbox → production promotion via CI.

### n8n Boundary Diagram

```mermaid
flowchart TB
    subgraph Users["Human Actors"]
        U["Attorney / Paralegal"]
    end

    subgraph LexFlow["LexFlow — Business Logic Owner"]
        API["FastAPI<br/>Authorization · State · Audit"]
        WRK["Celery Worker<br/>Trigger + Callback handler"]
        PG[("PostgreSQL<br/>workflow_executions")]
    end

    subgraph N8NZone["Zone 3 — Orchestration Only"]
        N8N["n8n<br/>HTTP transforms · retries · M365 calls"]
    end

    subgraph External["External Systems"]
        MS365["Microsoft 365"]
        COURT["Court APIs"]
        BILL["Billing"]
    end

    U -->|"HTTPS"| API
    API -->|"Persist execution"| PG
    API -->|"Enqueue trigger"| WRK
    WRK -->|"HMAC POST /webhook/{id}"| N8N
    N8N --> MS365 & COURT & BILL
    N8N -->|"HMAC callback"| API
    API --> PG

    N8N -.->|"✗ NO direct DB"| X["PostgreSQL blocked"]
    U -.->|"✗ NO direct access"| N8N
```

### What n8n MAY Do vs MUST NOT Do

| n8n MAY | n8n MUST NOT |
|---------|--------------|
| Call Microsoft Graph (email, SharePoint) | Write to PostgreSQL |
| Transform payloads between HTTP steps | Enforce matter walls or RBAC |
| Retry failed external API calls | Store attorney-client privileged data long-term |
| Callback to FastAPI with execution results | Be reachable from public internet |

### Workflow Promotion Pipeline

```mermaid
flowchart LR
    DEV["Engineer edits<br/>n8n/workflows/*.json"]
    PR["PR + smoke tests"]
    SANDBOX["Import to sandbox n8n"]
    MANUAL["Manual trigger validation"]
    PROD["Promote to production n8n"]
    ACTIVE["Activate workflow"]

    DEV --> PR --> SANDBOX --> MANUAL --> PROD --> ACTIVE
```

**Go deeper:** [06-workflows/orchestration-model.md](../06-workflows/orchestration-model.md), [06-workflows/n8n-integration.md](../06-workflows/n8n-integration.md), [ADR-002](../13-decisions/002-n8n-orchestration-only.md).

---

## 6. Data Architecture — PostgreSQL, S3, pgvector

### Talking Points

- **Single PostgreSQL** with schema-per-bounded-context ([ADR-003](../13-decisions/003-postgresql-single-database.md)).
- **Documents:** metadata in PostgreSQL; binaries in S3; presigned multipart upload bypasses API for large files (500 MB max).
- **Embeddings:** pgvector HNSW index in `documents.document_embeddings` — case_id denormalized for fast scoped search.
- **Audit:** append-only `audit.audit_logs` — separate DB role, no DELETE permission for app user.
- **Partitioning:** `audit_logs` and `prompt_history` partitioned monthly at scale.

### Schema Overview

```mermaid
erDiagram
    CASES_CASES ||--o{ DOCUMENTS_DOCUMENTS : contains
    CASES_CASES ||--o{ WORKFLOWS_EXECUTIONS : triggers
    CASES_CASES ||--o{ AI_SUMMARIES : generates
    DOCUMENTS_DOCUMENTS ||--o{ DOCUMENTS_VERSIONS : versions
    DOCUMENTS_DOCUMENTS ||--o{ DOCUMENT_EMBEDDINGS : embeds
    IDENTITY_USERS ||--o{ CASES_PARTICIPANTS : assigned
    AUDIT_AUDIT_LOGS }o--|| CASES_CASES : references

    CASES_CASES {
        uuid id PK
        uuid client_id FK
        string status
        string practice_area
    }

    DOCUMENT_EMBEDDINGS {
        uuid id PK
        uuid case_id FK
        vector embedding
        text chunk_text
    }
```

### Document Upload Path

```mermaid
sequenceDiagram
    actor User
    participant API as FastAPI
    participant S3 as S3
    participant PG as PostgreSQL
    participant Worker as Celery

    User->>API: POST /uploads/initiate
    API->>API: Matter wall + virus scan policy check
    API->>S3: Generate presigned multipart URL
    API-->>User: presigned URLs + uploadId

    User->>S3: Direct upload (bypasses API)
    User->>API: POST /uploads/complete
    API->>PG: Document metadata + outbox event
    API-->>User: 201

    Worker->>S3: Fetch object
    Worker->>PG: OCR + DocumentProcessed event
```

**Go deeper:** [05-database/schema-overview.md](../05-database/schema-overview.md), [05-database/indexing-strategy.md](../05-database/indexing-strategy.md), [database-architecture.md](../database-architecture.md).

---

## 7. API, AuthZ & Matter Walls

### Talking Points

- **JWT access tokens** — 15-minute TTL; refresh tokens httpOnly, rotated on use.
- **RBAC** — 10 predefined roles (Attorney, Paralegal, Admin, Client Portal, etc.).
- **Matter walls (ABAC)** — case participant list + ethical wall rules; enforced server-side on every endpoint.
- **404 on deny** — unauthorized users cannot enumerate case existence.
- **Future:** Microsoft Entra ID OIDC federation (Phase 3).

### Authorization Flow

```mermaid
flowchart TB
    REQ["Incoming Request + JWT"]
    AUTHN["Authenticate — validate JWT"]
    RBAC["RBAC — role permits action?"]
    WALL["Matter Wall — user on case?"]
    QUERY["Execute query WITH case filter"]
    RESP["200 / 404"]

    REQ --> AUTHN
    AUTHN -->|invalid| E401["401 Unauthorized"]
    AUTHN --> RBAC
    RBAC -->|deny| E404A["404 Not Found"]
    RBAC --> WALL
    WALL -->|deny| E404B["404 Not Found"]
    WALL --> QUERY --> RESP
```

### Permission Cache

| Layer | TTL | Invalidation |
|-------|-----|--------------|
| Redis permission cache | 5 min | `RoleAssigned`, `ParticipantAdded` events |
| Matter wall evaluation | Per request | Cannot cache across cases without case_id key |

**Go deeper:** [04-api/authorization-rbac.md](../04-api/authorization-rbac.md), [08-security/matter-walls.md](../08-security/matter-walls.md), [ADR-005](../13-decisions/005-jwt-authentication.md).

---

## 8. Observability, Deployment & Disaster Recovery

### Talking Points

- **Correlation IDs** propagate from API → worker → n8n callback → audit log.
- **Structured JSON logging** — zero PII; automatic secret redaction.
- **Distributed tracing** — OpenTelemetry / X-Ray; 10% sampling at scale.
- **ECS Fargate** on AWS — separate services for web, api, worker, n8n.
- **DR:** RPO ≤ 15 min, RTO ≤ 4 hr — quarterly drills.

### Observability Stack

```mermaid
flowchart LR
    subgraph Apps["Application Tier"]
        API["FastAPI"]
        WRK["Workers"]
        N8N["n8n"]
    end

    subgraph Signals["Telemetry"]
        LOG["CloudWatch Logs<br/>JSON structured"]
        TRACE["X-Ray / OTel<br/>correlation_id"]
        METRIC["CloudWatch Metrics<br/>p95, queue depth, DLQ"]
    end

    subgraph Alert["Alerting"]
        CW["CloudWatch Alarms"]
        PD["PagerDuty"]
        RUN["Runbooks — 11-observability/"]
    end

    API & WRK & N8N --> LOG & TRACE & METRIC
    METRIC --> CW --> PD
    PD --> RUN
```

### Critical Alert Thresholds

| Metric | Warning | Critical |
|--------|---------|----------|
| API p95 latency | > 500ms | > 1s |
| RabbitMQ queue depth | > 5,000 | > 20,000 |
| DLQ messages | > 0 | > 10 |
| n8n callback failures | > 5/hr | > 20/hr |

### HA & DR Summary

```mermaid
flowchart TB
    subgraph AZ["Multi-AZ — Automatic"]
        ALB["ALB health checks"]
        RDS["RDS Multi-AZ failover ~60-120s"]
        MQ["Amazon MQ active/standby"]
    end

    subgraph Region["Cross-Region — Manual DR"]
        CRR["S3 CRR to us-west-2"]
        SNAP["RDS cross-region snapshots"]
        DNS["Route 53 failover"]
        RUNBOOK["DR runbook — RTO 4hr"]
    end

    ALB & RDS & MQ --> AZ
    CRR & SNAP & DNS --> RUNBOOK
```

**Go deeper:** [11-observability/README.md](../11-observability/README.md), [09-deployment/aws-topology.md](../09-deployment/aws-topology.md), [09-deployment/disaster-recovery.md](../09-deployment/disaster-recovery.md).

---

## Deep Dive Checklist — Did You Cover?

| Topic | Covered? | Doc Reference |
|-------|----------|---------------|
| Bounded contexts & case aggregate | ☐ | [02-domain/](../02-domain/README.md) |
| Outbox + idempotency | ☐ | [ADR-006](../13-decisions/006-transactional-outbox.md) |
| n8n boundary | ☐ | [ADR-002](../13-decisions/002-n8n-orchestration-only.md) |
| Async AI + HITL | ☐ | [ADR-004](../13-decisions/004-async-ai-processing.md) |
| Case-scoped RAG | ☐ | [07-ai/rag-architecture.md](../07-ai/rag-architecture.md) |
| Matter walls + 404 | ☐ | [08-security/matter-walls.md](../08-security/matter-walls.md) |
| NFR targets | ☐ | [03-architecture/nfr-requirements.md](../03-architecture/nfr-requirements.md) |
| DR RPO/RTO | ☐ | [09-deployment/disaster-recovery.md](../09-deployment/disaster-recovery.md) |

---

## References

| Document | Path |
|----------|------|
| Interview index | [README.md](./README.md) |
| 15-minute pitch | [system-design-overview.md](./system-design-overview.md) |
| Tradeoffs | [tradeoffs-discussion.md](./tradeoffs-discussion.md) |
| Scaling scenarios | [scaling-questions.md](./scaling-questions.md) |
| Security Q&A | [security-questions.md](./security-questions.md) |
| C4 component architecture | [../03-architecture/component-architecture.md](../03-architecture/component-architecture.md) |
| Integration patterns | [../03-architecture/integration-patterns.md](../03-architecture/integration-patterns.md) |
| Cross-cutting concerns | [../03-architecture/cross-cutting-concerns.md](../03-architecture/cross-cutting-concerns.md) |

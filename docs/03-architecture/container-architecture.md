# Container Architecture — C4 Level 2

**LexFlow AI** — Enterprise AI Automation Platform for Law Firms  
**Version:** 1.0  
**Status:** Draft — Pre-Implementation  
**Last Updated:** 2026-07-06

---

## Purpose

This document describes LexFlow AI at **C4 Level 2 (Containers)** — the deployable runtime units, data stores, messaging infrastructure, and network zones that compose the platform. It bridges system context (Level 1) and FastAPI module design (Level 3).

---

## Scope

| In Scope | Out of Scope |
|----------|--------------|
| ECS Fargate services and their responsibilities | FastAPI route handlers and use cases |
| Data stores (PostgreSQL, Redis, S3, RabbitMQ) | Table-level schema (see database-architecture) |
| Network zones (public edge, private VPC) | Terraform module variables |
| Container-to-container communication patterns | Frontend component tree |
| n8n placement and access restrictions | n8n workflow node configuration |

---

## Responsibilities

### Container Responsibility Matrix

| Container | Primary Responsibilities | Does NOT |
|-----------|-------------------------|----------|
| **Next.js Frontend** | UI rendering, client state, token refresh UX, SSE/WebSocket client | Business rules, direct n8n/queue access, secrets |
| **FastAPI API** | AuthZ, validation, domain commands/queries, outbox writes, internal webhooks | Long-running AI inference in request path |
| **Celery Workers** | Async task execution, outbox publishing, n8n invocation, AI jobs | HTTP API surface for users |
| **n8n Orchestrator** | External HTTP orchestration, retries, payload transforms | Business logic, PostgreSQL writes, public exposure |
| **PostgreSQL** | System of record, outbox, audit, workflow state | Cache, message broker |
| **Redis** | Cache, rate limits, Celery result backend, distributed locks | Authoritative domain state |
| **RabbitMQ** | Durable async messaging, DLQ routing | Business logic execution |
| **S3** | Document binaries, export artifacts, log archives | Structured relational queries |

---

## Architecture

### C4 Container Diagram

```mermaid
C4Container
    title Container Diagram — LexFlow AI

    Person(user, "Firm User", "Attorney, paralegal, admin, client")

    System_Boundary(lexflow, "LexFlow AI") {
        Container(web, "Next.js Frontend", "TypeScript, React 18, App Router", "Delivers UI, BFF proxy, real-time client")
        Container(api, "FastAPI API", "Python 3.12, FastAPI", "REST API, auth, domain logic, internal webhooks")
        Container(worker, "Celery Workers", "Python, Celery", "Async processing, outbox publisher, n8n bridge")
        Container(n8n, "n8n Orchestrator", "n8n", "Private HTTP orchestration to external systems")
        ContainerDb(pg, "PostgreSQL + pgvector", "RDS Multi-AZ", "Domain data, audit, outbox, embeddings")
        ContainerDb(redis, "Redis", "ElastiCache Cluster", "Cache, rate limits, Celery adjunct")
        ContainerQueue(rmq, "RabbitMQ", "Amazon MQ", "Domain event queues, task routing")
        ContainerDb(s3, "S3", "AWS S3 SSE-KMS", "Documents, artifacts, compliance archives")
    }

    System_Ext(ms365, "Microsoft 365", "Graph API")
    System_Ext(llm, "LLM Providers", "OpenAI, Azure OpenAI, Claude")
    System_Ext(ext, "External APIs", "Court, billing, DMS")

    Rel(user, web, "Uses", "HTTPS")
    Rel(web, api, "API calls", "HTTPS / JSON")
    Rel(api, pg, "Reads/writes", "SQL/TLS")
    Rel(api, redis, "Cache, rate limit", "TLS")
    Rel(api, rmq, "Enqueue tasks", "AMQP/TLS")
    Rel(api, s3, "Presigned URLs", "HTTPS")
    Rel(rmq, worker, "Consumes", "AMQP/TLS")
    Rel(worker, pg, "Reads/writes", "SQL/TLS")
    Rel(worker, s3, "Read/write objects", "HTTPS")
    Rel(worker, n8n, "Signed webhook trigger", "HTTP — VPC internal")
    Rel(worker, llm, "AI inference", "HTTPS")
    Rel(n8n, ms365, "Orchestrate", "Graph API")
    Rel(n8n, ext, "Orchestrate", "HTTPS")
    Rel(n8n, api, "Callback", "HMAC-signed HTTP")
```

### Deployment Topology

```mermaid
flowchart TB
    subgraph Internet["Public Internet"]
        USER["Users"]
    end

    subgraph Edge["Edge Layer"]
        R53["Route 53"]
        CF["CloudFront + WAF"]
        ALB["Application Load Balancer"]
    end

    subgraph VPC["AWS VPC — Private Subnets (Multi-AZ)"]
        subgraph Compute["ECS Fargate Cluster"]
            WEB["web-service<br/>Next.js<br/>min 2 tasks"]
            API["api-service<br/>FastAPI<br/>min 2 tasks"]
            WRK["worker-service<br/>Celery<br/>scale on queue depth"]
            N8N["n8n-service<br/>internal ALB only<br/>min 1 task"]
        end

        subgraph Data["Data Layer"]
            PG[("PostgreSQL + pgvector<br/>RDS Multi-AZ")]
            REDIS[("Redis<br/>ElastiCache Cluster")]
            RMQ["RabbitMQ<br/>Amazon MQ Active/Standby"]
            S3[("S3<br/>SSE-KMS")]
        end

        subgraph Internal["Internal Only"]
            IALB["Internal ALB<br/>n8n ingress"]
        end
    end

    subgraph Observability["Observability"]
        CW["CloudWatch"]
        XRAY["X-Ray / OpenTelemetry"]
        SM["Secrets Manager"]
    end

    USER --> R53 --> CF --> ALB
    ALB --> WEB
    ALB --> API
    API --> PG
    API --> REDIS
    API --> RMQ
    API --> S3
    RMQ --> WRK
    WRK --> PG
    WRK --> S3
    WRK --> IALB --> N8N
    WRK --> LLM_EXT["LLM APIs"]
    N8N --> EXT["External APIs"]
    N8N --> API

    API --> CW
    WRK --> CW
    WEB --> CW
```

---

## Flow Diagrams

### Request Routing — Public Path

```mermaid
sequenceDiagram
    actor User
    participant CF as CloudFront
    participant ALB as ALB
    participant Web as Next.js
    participant API as FastAPI
    participant PG as PostgreSQL
    participant Redis as Redis

    User->>CF: HTTPS request
    CF->>ALB: Forward (static or dynamic)
    ALB->>Web: SSR / static assets
    Web->>API: REST API (Bearer JWT)
    API->>Redis: Permission cache lookup
    alt Cache miss
        API->>PG: Load permissions
        API->>Redis: Cache result (TTL 5m)
    end
    API->>PG: Domain query/command
    API-->>Web: JSON response
    Web-->>User: Rendered UI
```

### Async Job Routing — Private Path

```mermaid
sequenceDiagram
    participant API as FastAPI
    participant PG as PostgreSQL
    participant RMQ as RabbitMQ
    participant Worker as Celery Worker
    participant N8N as n8n (private)
    participant Ext as External API

    API->>PG: Transaction — domain change + outbox event
    API->>RMQ: Optional direct task enqueue
    API-->>API: Return 202 + correlationId

    Worker->>RMQ: Consume message
    Worker->>PG: Idempotent handler — domain logic
    Worker->>N8N: POST signed webhook (VPC internal)
    N8N->>Ext: HTTP orchestration
    Ext-->>N8N: Response
    N8N->>API: HMAC callback — internal route
    API->>PG: Persist result, audit, notify
```

### Network Security Zones

```mermaid
flowchart LR
    subgraph Zone0["Zone 0 — Internet"]
        U["Users"]
    end

    subgraph Zone1["Zone 1 — DMZ"]
        WAF["WAF"]
        ALB_P["Public ALB"]
    end

    subgraph Zone2["Zone 2 — Application"]
        WEB["Next.js"]
        API["FastAPI"]
        WRK["Workers"]
    end

    subgraph Zone3["Zone 3 — Orchestration"]
        IALB["Internal ALB"]
        N8N["n8n"]
    end

    subgraph Zone4["Zone 4 — Data"]
        PG["PostgreSQL"]
        REDIS["Redis"]
        RMQ["RabbitMQ"]
        S3["S3"]
    end

    U --> WAF --> ALB_P
    ALB_P --> WEB
    ALB_P --> API
    API --> Zone4
    WRK --> Zone4
    WRK --> IALB --> N8N
    N8N -.->|"No public ingress"| X["✗ Internet"]

    style Zone3 fill:#ffd
    style Zone4 fill:#ddf
```

---

## Container Specifications

| Container | Runtime | Scaling Trigger | Min Tasks | Health Check |
|-----------|---------|-----------------|-----------|--------------|
| Next.js | Node 20, ECS Fargate | CPU > 70%, request count | 2 | `GET /api/health` |
| FastAPI | Python 3.12, ECS Fargate | CPU > 70%, p95 latency | 2 | `GET /api/v1/health` |
| Celery Workers | Python 3.12, ECS Fargate | RabbitMQ queue depth | 2 | Celery inspect ping |
| n8n | n8n official image | Manual (Phase 3: HA) | 1 | `GET /healthz` via internal ALB |

### Data Store Specifications

| Store | Instance Class (initial) | HA Mode | Encryption |
|-------|-------------------------|---------|------------|
| PostgreSQL | db.r6g.xlarge | Multi-AZ synchronous | RDS KMS at rest, TLS in transit |
| Redis | cache.r6g.large × 2 shards | Cluster mode, 2 replicas/shard | ElastiCache encryption |
| RabbitMQ | mq.m5.large | Active/standby | TLS, auth via Secrets Manager |
| S3 | Standard + IA lifecycle | Cross-region replication | SSE-KMS |

---

## Communication Contracts

| From | To | Protocol | Auth |
|------|-----|----------|------|
| Browser | Next.js / FastAPI | HTTPS, TLS 1.2+ | JWT Bearer |
| Next.js | FastAPI | HTTPS (server-side) | Service token or user JWT forward |
| FastAPI | PostgreSQL | SQL over TLS | IAM auth via Secrets Manager creds |
| FastAPI | RabbitMQ | AMQP over TLS | Broker credentials |
| Worker | n8n | HTTP (VPC private) | HMAC-signed payload + shared secret |
| n8n | FastAPI | HTTP (internal route) | HMAC signature verification |
| Worker | LLM providers | HTTPS | API keys from Secrets Manager |

---

## Best Practices

1. **Stateless containers** — All durable state in PostgreSQL, S3, or RabbitMQ; containers are horizontally replaceable.
2. **n8n behind internal ALB only** — Security groups deny all public ingress to n8n tasks.
3. **Separate ECS services per container type** — Independent scaling policies for API vs workers vs web.
4. **PgBouncer between API/workers and RDS** — Connection pooling in transaction mode; max 100 connections per API task.
5. **Secrets never in container images** — AWS Secrets Manager injected at task startup.
6. **Version-controlled n8n workflows** — Git is source of truth; sandbox promotion via CI/CD.

---

## Tradeoffs

| Decision | Benefit | Cost |
|----------|---------|------|
| ECS Fargate over EKS | Lower operational overhead for modular monolith | Less granular orchestration than Kubernetes |
| Single PostgreSQL (schema-separated) | ACID transactions across bounded contexts | Vertical scaling ceiling — read replicas for relief |
| Amazon MQ (RabbitMQ) over SQS | Topic routing, DLQ, priority queues native | Higher cost than SQS; broker is managed SPOF (active/standby) |
| n8n single instance (Phase 1) | Simpler ops, sufficient for 50K workflows/month | Brief pause on task restart — workflows retry |
| Redis for cache + Celery adjunct | Unified infra component | Redis outage affects rate limits, not domain data |

---

## Future Improvements

| Phase | Enhancement |
|-------|-------------|
| Phase 2 | Dedicated worker pools per queue domain (document, AI, workflow) |
| Phase 3 | n8n HA — 2+ tasks behind internal ALB with sticky execution IDs |
| Phase 3 | RDS read replica routing for dashboards and search |
| Phase 4 | Extract AI bounded context to independent ECS service if GPU/isolation needed |
| Phase 4 | Multi-region active-passive with automated DNS failover |

---

## References

| Document | Description |
|----------|-------------|
| [README.md](./README.md) | Architecture folder index |
| [system-context.md](./system-context.md) | C4 Level 1 |
| [component-architecture.md](./component-architecture.md) | C4 Level 3 — FastAPI modules |
| [data-flow.md](./data-flow.md) | Sync and async behavioral flows |
| [../deployment-architecture.md](../deployment-architecture.md) | Terraform, CI/CD, ECS details |
| [../database-architecture.md](../database-architecture.md) | Schema and data store design |
| [../workflow-orchestration.md](../workflow-orchestration.md) | n8n contracts and promotion |
| [../disaster-recovery.md](../disaster-recovery.md) | HA and failover procedures |
| [../13-decisions/001-modular-monolith.md](../13-decisions/001-modular-monolith.md) | Modular monolith decision |
| [../13-decisions/003-postgresql-single-database.md](../13-decisions/003-postgresql-single-database.md) | Single database decision |

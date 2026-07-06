# LexFlow AI — Technology Stack Reference

**Purpose:** Quick technology lookup for AI assistants writing code or docs.  
**Authoritative source:** `docs/development-standards.md`, `docs/03-architecture/container-architecture.md`

---

## Stack Overview

```
┌─────────────────────────────────────────────────────────────┐
│  PRESENTATION    Next.js 14+ · React 18 · TypeScript        │
│                  Tailwind CSS · ShadCN UI                   │
│                  Zustand · TanStack React Query             │
├─────────────────────────────────────────────────────────────┤
│  API             Python 3.12+ · FastAPI · Pydantic v2       │
│                  SQLAlchemy 2.0 · Alembic                   │
├─────────────────────────────────────────────────────────────┤
│  ASYNC           Celery · RabbitMQ (Amazon MQ)              │
│                  Redis 7+ (cache, rate limit, Celery adj.)  │
├─────────────────────────────────────────────────────────────┤
│  ORCHESTRATION   n8n (private VPC — NOT public)             │
├─────────────────────────────────────────────────────────────┤
│  DATA            PostgreSQL 16+ · pgvector                  │
│                  Amazon S3 (SSE-KMS)                        │
├─────────────────────────────────────────────────────────────┤
│  AI              Azure OpenAI (prod) · OpenAI (fallback)    │
│                  Anthropic Claude (contract review)         │
│                  Ollama (local dev only)                    │
├─────────────────────────────────────────────────────────────┤
│  INFRA           AWS ECS Fargate · RDS · ElastiCache        │
│                  Route 53 · CloudFront · WAF · ALB            │
│                  Secrets Manager · CloudWatch · X-Ray       │
│                  Terraform · Docker · GitHub Actions      │
├─────────────────────────────────────────────────────────────┤
│  TESTING         pytest · Vitest · Playwright · k6          │
│                  Testcontainers (integration)               │
├─────────────────────────────────────────────────────────────┤
│  LINTING         ruff · mypy · ESLint · Prettier            │
└─────────────────────────────────────────────────────────────┘
```

---

## Frontend

| Component | Technology | Notes |
|-----------|------------|-------|
| Framework | Next.js 14+ App Router | Server Components default |
| Language | TypeScript (strict) | |
| UI library | React 18+ | Functional components only |
| Styling | Tailwind CSS | |
| Components | ShadCN UI | `apps/web/src/components/ui/` |
| Client state | Zustand | UI/ephemeral only |
| Server state | TanStack React Query | API data, caching |
| Real-time | SSE (Phase 1), WebSocket (Phase 2) | Job status, notifications |
| Auth UX | Token refresh via FastAPI | BFF pattern for SSR |
| Testing | Vitest (unit), Playwright (E2E) | |
| Lint/format | ESLint, Prettier | |

**Frontend MUST NOT:** contain business rules, call n8n/RabbitMQ/workers, store secrets, call LLM APIs.

Docs: `docs/12-ui/`, `docs/12-ui/state-management.md`, `docs/12-ui/design-system.md`

---

## Backend (FastAPI)

| Component | Technology | Notes |
|-----------|------------|-------|
| Runtime | Python 3.12+ | Locked minimum |
| Framework | FastAPI | OpenAPI 3.1 auto-gen |
| Validation | Pydantic v2 | Request/response models |
| ORM | SQLAlchemy 2.0 | Async sessions |
| Migrations | Alembic | Per-schema versions |
| Architecture | DDD + Clean/Hexagonal | `domain ← application ← infrastructure` |
| API version | `/api/v1` | URL path versioning |
| Errors | RFC 7807 Problem Details | `docs/04-api/error-handling.md` |
| Auth | JWT RS256 + refresh rotation | ADR-005 |
| Testing | pytest, pytest-asyncio | |
| Lint/format | ruff format, ruff check, mypy strict | Line length 100 |

**Module layout per bounded context:**
```
services/{context}/
├── domain/           # Pure Python — no framework imports
├── application/      # Use cases / commands / queries
└── infrastructure/   # SQLAlchemy repos, S3, HTTP clients
```

**FastAPI route handlers:** thin — delegate to application use cases.

Docs: `docs/development-standards.md`, `docs/04-api/rest-standards.md`, `docs/03-architecture/component-architecture.md`

---

## Workers (Celery)

| Component | Technology | Notes |
|-----------|------------|-------|
| Task runner | Celery | |
| Broker | RabbitMQ (Amazon MQ) | Durable queues, DLQ |
| Result backend | Redis | Non-authoritative |
| Beat | Celery Beat | Outbox publisher (1s poll) |

**Worker responsibilities:**
- Outbox event publishing
- AI inference (LLM calls)
- Document processing (OCR, embeddings)
- n8n webhook invocation
- Notification delivery

**Workers MUST NOT:** expose HTTP API to users.

Queue naming: `{domain}.{action}.{priority}` — e.g., `ai.summarize.normal`, `workflow.trigger.high`

Docs: `docs/03-architecture/event-driven-design.md`, `docs/06-workflows/retry-dlq.md`

---

## n8n (Orchestration Only)

| Allowed | Prohibited |
|---------|------------|
| HTTP/API calls to external systems | Business logic / legal rules |
| Payload transforms for integrations | PostgreSQL nodes / direct DB writes |
| Retry with backoff | Authorization decisions |
| Callback to FastAPI internal webhooks | Public internet exposure |
| Simple routing on HTTP status | Code nodes with domain logic |

**Network:** Private subnet, internal ALB only, no WAF route.

Docs: `docs/06-workflows/n8n-integration.md`, `docs/06-workflows/orchestration-model.md`, ADR-002

---

## Data Stores

### PostgreSQL 16+ (RDS Multi-AZ)

| Schema | Owner Context | Key Tables |
|--------|---------------|------------|
| `identity` | Identity & Access | firms, users, roles, permissions, refresh_tokens |
| `cases` | Case Management + Client | cases, clients, tasks, deadlines, participants |
| `documents` | Document Management | documents, document_versions, document_embeddings |
| `workflows` | Workflow Orchestration | workflow_definitions, workflow_executions, workflow_steps |
| `ai` | AI & Knowledge | ai_summaries, prompt_templates, prompt_history, llm_usage |
| `audit` | Audit & Compliance | audit_logs, approvals |
| `shared` | Cross-cutting | outbox_events, idempotency_keys, notifications |

**Extensions:** pgvector (embeddings), full-text search.

Docs: `docs/05-database/schema-overview.md`, ADR-003

### Redis 7+ (ElastiCache)

- Permission cache
- Rate limiting
- Celery result backend
- Distributed locks
- SSE pub/sub (`job:{jobId}`)

### S3 (SSE-KMS)

- Document binaries (presigned upload)
- Export artifacts
- Compliance archives
- Versioned, lifecycle policies

---

## AI / LLM

| Provider | Environment | Role |
|----------|-------------|------|
| Azure OpenAI | Production | Primary — completions, embeddings, chat |
| OpenAI API | Staging / failover | Secondary when Azure unavailable |
| Anthropic Claude | Production | Contract review (128K context) |
| Ollama | Local dev | Never in production |

**Provider selection:** Runtime from `ai.prompt_templates.model_config` — not hardcoded in workers.

**All AI async:** API returns 202; worker calls LLM; result persisted before notify.

Docs: `docs/07-ai/llm-providers.md`, ADR-004, ADR-008

---

## External Integrations

| System | Pattern | Path |
|--------|---------|------|
| Microsoft 365 | Graph API via n8n + FastAPI adapters | `docs/03-architecture/integration-patterns.md` |
| Azure OpenAI | Direct from Celery worker | `docs/07-ai/llm-providers.md` |
| Court e-filing | n8n orchestration | `docs/06-workflows/workflow-catalog.md` |
| Billing/ERP | Event-driven export | `docs/03-architecture/integration-patterns.md` |
| Entra ID (Phase 3) | OIDC federated login | ADR-005 |

---

## Infrastructure (AWS)

| Service | Purpose |
|---------|---------|
| ECS Fargate | web, api, worker, n8n containers |
| RDS PostgreSQL | Multi-AZ, encrypted |
| ElastiCache Redis | Cluster mode |
| Amazon MQ | RabbitMQ active/standby |
| S3 | Documents, artifacts |
| ALB | HTTPS termination, path routing |
| CloudFront + WAF | CDN, DDoS protection |
| Route 53 | DNS, health checks |
| Secrets Manager | JWT keys, API keys, DB credentials |
| CloudWatch + X-Ray | Logs, metrics, tracing |

**IaC:** Terraform — `infra/terraform/`  
**Region:** us-east-1 primary, us-west-2 DR standby

Docs: `docs/09-deployment/aws-topology.md`, `docs/09-deployment/terraform.md`

---

## CI/CD

| Stage | Tool |
|-------|------|
| Lint/test | GitHub Actions |
| Container build | Docker |
| Deploy | ECS rolling update |
| Migrations | Alembic (zero-downtime strategy) |
| n8n promotion | dev → staging → prod (manual gate) |

Docs: `docs/09-deployment/cicd-pipeline.md`, `docs/06-workflows/promotion-pipeline.md`

---

## Version Policy

Use **latest stable major** unless locked (Python 3.12+, PostgreSQL 16+). Pin in dependency files when implementation begins.

---

## Anti-Patterns (Stack Level)

| Don't | Do Instead |
|-------|------------|
| Sync LLM in FastAPI handler | Enqueue Celery task, return 202 |
| PostgreSQL node in n8n | FastAPI persists; n8n calls HTTP APIs only |
| Business logic in Next.js | Call FastAPI API |
| Cross-schema FK in migrations | UUID reference + app validation |
| Secrets in repo or n8n JSON | AWS Secrets Manager |
| Public n8n URL | Private subnet + internal ALB |

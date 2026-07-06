# Repository & Folder Structure

**LexFlow AI** — Monorepo Layout  
**Version:** 1.0  
**Status:** Draft — Pre-Implementation  
**Last Updated:** 2026-07-06

---

## 1. Overview

LexFlow AI uses a **monorepo** structure to co-locate frontend, backend, workers, automation definitions, shared packages, and infrastructure. This enables atomic changes across layers, unified CI/CD, and consistent versioning.

The layout follows conventions used by enterprise teams (Microsoft, Stripe, AWS internal repos): clear separation of deployable apps, shared libraries, infrastructure-as-code, and documentation.

---

## 2. Top-Level Structure

```
lexflow-ai/
├── apps/                    # Deployable applications
├── services/                # Backend domain modules (Python packages)
├── workers/                 # Celery worker entrypoints & task definitions
├── n8n/                     # n8n workflow JSON (version-controlled)
├── packages/                # Shared libraries (TS + Python)
├── infra/                   # Terraform, Docker, CI/CD
├── docs/                    # Architecture & product documentation
├── scripts/                 # Dev tooling, seed data, migration helpers
├── tests/                   # Cross-cutting integration & E2E tests
├── .github/                 # GitHub Actions workflows
├── docker-compose.yml       # Local development stack
├── Makefile                 # Common dev commands
├── README.md                # Project entry point
└── LICENSE
```

---

## 3. Applications (`apps/`)

Deployable units that map to ECS services.

```
apps/
├── web/                          # Next.js frontend
│   ├── src/
│   │   ├── app/                  # App Router pages & layouts
│   │   │   ├── (auth)/           # Login, password reset
│   │   │   ├── (dashboard)/      # Authenticated shell
│   │   │   │   ├── cases/
│   │   │   │   ├── clients/
│   │   │   │   ├── documents/
│   │   │   │   ├── workflows/
│   │   │   │   ├── approvals/
│   │   │   │   ├── admin/
│   │   │   │   └── settings/
│   │   │   └── api/              # Next.js route handlers (BFF only — thin)
│   │   ├── components/
│   │   │   ├── ui/               # ShadCN primitives
│   │   │   ├── cases/
│   │   │   ├── documents/
│   │   │   └── shared/
│   │   ├── hooks/
│   │   ├── lib/
│   │   │   ├── api-client.ts     # Typed FastAPI client
│   │   │   ├── auth.ts
│   │   │   └── query-keys.ts
│   │   ├── stores/               # Zustand stores
│   │   └── types/
│   ├── public/
│   ├── Dockerfile
│   ├── next.config.ts
│   ├── tailwind.config.ts
│   ├── tsconfig.json
│   └── package.json
│
└── api/                          # FastAPI application (API gateway + modules)
    ├── src/
    │   ├── main.py               # Application factory
    │   ├── config.py             # Settings (pydantic-settings)
    │   ├── dependencies.py       # FastAPI DI
    │   ├── middleware/
    │   │   ├── auth.py
    │   │   ├── correlation_id.py
    │   │   ├── rate_limit.py
    │   │   └── audit.py
    │   ├── api/
    │   │   └── v1/
    │   │       ├── router.py
    │   │       ├── cases.py
    │   │       ├── clients.py
    │   │       ├── documents.py
    │   │       ├── workflows.py
    │   │       ├── ai.py
    │   │       ├── approvals.py
    │   │       ├── notifications.py
    │   │       ├── admin.py
    │   │       └── internal/     # n8n callbacks — NOT in public OpenAPI
    │   │           └── webhooks.py
    │   └── core/
    │       ├── exceptions.py
    │       └── pagination.py
    ├── alembic/                  # Database migrations
    │   ├── versions/
    │   └── env.py
    ├── tests/
    ├── Dockerfile
    ├── pyproject.toml
    └── README.md
```

---

## 4. Domain Services (`services/`)

Python packages implementing bounded contexts. Imported by `apps/api` and `workers/`. Each follows hexagonal architecture:

```
services/
├── {context}/
│   ├── domain/           # Entities, value objects, domain events, repository interfaces
│   ├── application/      # Use cases (commands/queries), DTOs
│   ├── infrastructure/   # SQLAlchemy repos, S3 adapters, external API clients
│   └── tests/
```

```
services/
├── identity/                     # Users, roles, permissions, sessions
│   ├── domain/
│   ├── application/
│   └── infrastructure/
│
├── case_management/              # Cases, timeline, matter walls
│   ├── domain/
│   │   ├── entities/
│   │   │   ├── case.py
│   │   │   ├── hearing.py
│   │   │   └── deadline.py
│   │   ├── events/
│   │   └── repositories/
│   ├── application/
│   │   ├── commands/
│   │   └── queries/
│   └── infrastructure/
│
├── client_management/            # Clients, contacts, engagement letters
│
├── document_management/          # Upload, versioning, OCR pipeline triggers
│
├── workflow_orchestration/       # Workflow definitions, execution state, n8n bridge
│
├── ai_knowledge/                 # LLM providers, prompts, embeddings, RAG
│
├── notifications/                # Email, in-app, Teams dispatch
│
├── audit_compliance/             # Audit log writer, compliance exports
│
└── shared/                       # Cross-cutting Python utilities
    ├── events/                   # Event bus, outbox publisher
    ├── database/                 # Session factory, base models
    ├── security/                 # Crypto, HMAC, PII utilities
    └── tracing/                  # OpenTelemetry helpers
```

---

## 5. Workers (`workers/`)

```
workers/
├── celery/
│   ├── app.py                    # Celery application factory
│   ├── config.py                 # Queue routing, retry policies
│   ├── tasks/
│   │   ├── document_tasks.py
│   │   ├── workflow_tasks.py
│   │   ├── ai_tasks.py
│   │   ├── notification_tasks.py
│   │   └── maintenance_tasks.py
│   ├── Dockerfile
│   └── README.md
```

Workers import use cases from `services/` — they never duplicate business logic.

---

## 6. n8n Workflows (`n8n/`)

```
n8n/
├── workflows/
│   ├── intake/                   # Case intake automation
│   │   └── new-client-intake.json
│   ├── documents/                # SharePoint sync, OCR callbacks
│   ├── notifications/          # Email, Teams alerts
│   ├── integrations/             # Microsoft Graph, court e-filing
│   └── _templates/               # Starter workflow templates
├── credentials/                  # .gitkeep only — NEVER commit secrets
├── README.md                     # Import/promotion procedures
└── docker-compose.n8n.yml        # Local n8n instance
```

**Naming convention:** `{domain}-{action}-v{major}.json`  
Example: `intake-new-client-v1.json`

---

## 7. Shared Packages (`packages/`)

```
packages/
├── ui/                           # Shared React component library
│   ├── src/
│   │   ├── components/
│   │   └── index.ts
│   ├── package.json
│   └── tsconfig.json
│
├── shared/                       # Shared TypeScript types & constants
│   ├── src/
│   │   ├── types/                # Mirrors OpenAPI-generated types
│   │   ├── constants/
│   │   └── validators/
│   └── package.json
│
└── sdk/                          # Generated + hand-written API client
    ├── src/
    │   └── client.ts
    └── package.json
```

OpenAPI spec is generated from FastAPI and used to codegen TypeScript types into `packages/shared/` and `packages/sdk/`.

---

## 8. Infrastructure (`infra/`)

```
infra/
├── terraform/
│   ├── modules/
│   │   ├── vpc/
│   │   ├── ecs/
│   │   ├── rds/
│   │   ├── elasticache/
│   │   ├── amazon_mq/
│   │   ├── s3/
│   │   ├── alb/
│   │   ├── cloudfront/
│   │   ├── secrets/
│   │   └── monitoring/
│   ├── environments/
│   │   ├── dev/
│   │   ├── staging/
│   │   └── production/
│   └── README.md
│
├── docker/
│   ├── docker-compose.dev.yml
│   ├── docker-compose.test.yml
│   └── nginx/                    # Local reverse proxy mimicking ALB
│
└── github-actions/               # Reusable workflow templates (referenced from .github/)
```

---

## 9. Documentation (`docs/`)

See [README.md](./README.md) for the full documentation index.

```
docs/
├── README.md                     # Documentation index
├── product-overview.md
├── high-level-architecture.md
├── domain-model.md
├── database-architecture.md
├── api-architecture.md
├── authentication-authorization.md
├── security-architecture.md
├── workflow-orchestration.md
├── ai-architecture.md
├── event-driven-architecture.md
├── integration-architecture.md
├── deployment-architecture.md
├── observability.md
├── disaster-recovery.md
├── compliance-data-governance.md
├── testing-strategy.md
├── development-standards.md
├── folder-structure.md           # This document
└── adr/                          # Architecture Decision Records
    ├── README.md
    ├── 001-modular-monolith.md
    ├── 002-n8n-orchestration-only.md
    └── ...
```

---

## 10. Scripts & Tests

```
scripts/
├── seed/                         # Dev/staging seed data
├── openapi/                      # Generate TS client from OpenAPI
├── db/                           # Migration helpers, backup scripts
└── n8n/                          # Import/export workflow scripts

tests/
├── integration/                  # API integration tests (Testcontainers)
├── e2e/                          # Playwright browser tests
└── load/                         # k6 load test scenarios
```

---

## 11. Local Development Stack

`docker-compose.yml` at repo root orchestrates:

| Service | Port | Purpose |
|---------|------|---------|
| web | 3000 | Next.js dev server |
| api | 8000 | FastAPI |
| postgres | 5432 | PostgreSQL + pgvector |
| redis | 6379 | Cache + Celery backend |
| rabbitmq | 5672 / 15672 | Message broker + management UI |
| n8n | 5678 | Orchestration (internal network only) |
| worker | — | Celery worker |
| minio | 9000 | S3-compatible local storage |

---

## 12. Naming Conventions

| Artifact | Convention | Example |
|----------|------------|---------|
| Python modules | `snake_case` | `case_management/` |
| Python classes | `PascalCase` | `CaseRepository` |
| API routes | `kebab-case` | `/api/v1/case-deadlines` |
| Database tables | `snake_case`, plural | `audit_logs` |
| Events | `PascalCase` past tense | `CaseCreated` |
| n8n workflows | `kebab-case-vN` | `intake-new-client-v1` |
| Terraform resources | `{env}-{service}-{resource}` | `prod-api-alb` |
| Environment vars | `SCREAMING_SNAKE` | `DATABASE_URL` |

---

## 13. Related Documents

- [high-level-architecture.md](./high-level-architecture.md)
- [development-standards.md](./development-standards.md)
- [deployment-architecture.md](./deployment-architecture.md)

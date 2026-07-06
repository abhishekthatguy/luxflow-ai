# Folder Structure — LexFlow AI

**Applies to:** All new files, modules, and documentation  
**Docs:** `docs/folder-structure.md`

---

## Purpose

Tell AI assistants **where files belong** in the monorepo. Placing code correctly is a security and architecture requirement, not style preference.

---

## Top-Level Layout

```
lexflow-ai/
├── apps/           # Deployable applications (web, api)
├── services/       # Backend bounded contexts (Python packages)
├── workers/        # Celery entrypoints and tasks
├── n8n/            # Workflow JSON (version-controlled)
├── packages/       # Shared TS/Python libraries
├── infra/          # Terraform, Docker, CI templates
├── docs/           # Human architecture documentation
├── scripts/        # Dev tooling, codegen, seeds
├── tests/          # Cross-cutting integration & E2E
├── .ai/            # AI assistant rules, prompts, context
├── .github/        # GitHub Actions
└── docker-compose.yml
```

---

## Decision Tree: Where Does This Go?

```
New code?
├── User-facing UI          → apps/web/src/
├── HTTP route/DTO          → apps/api/src/api/v1/
├── Business rule           → services/{context}/domain/ or application/
├── DB adapter              → services/{context}/infrastructure/
├── Background job          → workers/celery/tasks/ (calls services/)
├── External HTTP sequence  → n8n/workflows/
├── Shared TS types         → packages/shared/
├── API client              → packages/sdk/
├── Architecture doc        → docs/{numbered-section}/
├── AI assistant rule       → .ai/rules/
└── LLM prompt template     → DB registry (seed in scripts/); NOT n8n
```

---

## `apps/web/` (Next.js)

```
apps/web/src/
├── app/                    # App Router — pages, layouts, route groups
│   ├── (auth)/             # Login, password reset
│   ├── (dashboard)/        # Authenticated shell
│   │   ├── cases/
│   │   ├── documents/
│   │   └── ...
│   └── api/                # BFF only — thin proxies, no domain logic
├── components/
│   ├── ui/                 # ShadCN primitives (generated — avoid edits)
│   ├── cases/              # Feature components
│   └── shared/
├── hooks/                  # React Query hooks, custom hooks
├── lib/                    # api-client, auth, query-keys
├── stores/                 # Zustand (UI state only)
└── types/                  # Frontend-only types (prefer packages/shared)
```

| Put Here | Never Put Here |
|----------|----------------|
| Presentation components | Authorization logic |
| React Query hooks | Direct PostgreSQL access |
| Zustand UI state | LLM prompt templates |
| BFF cookie/session helpers | Case business validation |

---

## `apps/api/` (FastAPI)

```
apps/api/src/
├── main.py                 # App factory
├── config.py               # Pydantic Settings
├── dependencies.py         # DI wiring
├── middleware/             # auth, correlation_id, rate_limit, audit
├── api/v1/                 # Public REST routers
│   ├── cases.py
│   ├── documents.py
│   └── internal/           # n8n webhooks — NOT in public OpenAPI
│       └── webhooks.py
└── core/                   # exceptions, pagination helpers
```

**Rule:** Route files translate HTTP ↔ application DTOs. No SQL, no domain invariants in routers.

---

## `services/{context}/` (Bounded Contexts)

```
services/case_management/
├── domain/
│   ├── entities/
│   ├── events/
│   ├── repositories/       # Ports (interfaces)
│   └── services/           # Domain services (pure logic)
├── application/
│   ├── commands/
│   ├── queries/
│   └── dtos/
├── infrastructure/
│   ├── repositories/       # SQLAlchemy implementations
│   └── adapters/
└── tests/
```

### Context List

| Directory | Context |
|-----------|---------|
| `identity/` | Users, roles, sessions |
| `case_management/` | Cases, participants, matter walls |
| `client_management/` | Clients, contacts |
| `document_management/` | Documents, versions, OCR |
| `workflow_orchestration/` | Executions, n8n bridge |
| `ai_knowledge/` | LLM, prompts, RAG, metering |
| `notifications/` | Email, in-app, Teams |
| `audit_compliance/` | Audit log, approvals |
| `shared/` | Outbox, DB session, tracing, crypto |

---

## `workers/celery/`

```
workers/celery/
├── app.py
├── config.py
└── tasks/
    ├── document_tasks.py
    ├── workflow_tasks.py
    ├── ai_tasks.py
    └── notification_tasks.py
```

Tasks **import use cases** from `services/`. Never duplicate business logic.

---

## `n8n/`

```
n8n/
├── workflows/
│   ├── intake/
│   ├── documents/
│   ├── notifications/
│   ├── integrations/
│   └── _templates/
├── credentials/            # .gitkeep ONLY — never commit secrets
└── README.md
```

---

## `packages/`

| Package | Contents |
|---------|----------|
| `packages/shared/` | Generated + hand-written TS types from OpenAPI |
| `packages/sdk/` | Typed API client (`API_VERSION` constant) |
| `packages/ui/` | Shared React components (if extracted) |

---

## `tests/` (Cross-Cutting)

| Directory | Contents |
|-----------|----------|
| `tests/integration/` | API tests with Testcontainers |
| `tests/e2e/` | Playwright specs |
| `tests/load/` | k6 scenarios |

Unit tests live **next to code**: `services/{context}/tests/`, `apps/web/**/*.test.tsx`.

---

## `.ai/` (AI Assistant Layer)

```
.ai/
├── rules/                  # This directory — coding standards for AI
├── prompts/                # Reusable assistant task prompts
├── context/                # Curated snippets for common tasks
└── README.md
```

See [context-engineering-standards.md](./context-engineering-standards.md).

---

## Do / Don't

| Do | Don't |
|----|-------|
| Add new bounded context as `services/{name}/` | Create `lib/` or `utils/` dumping ground |
| Colocate unit tests with module | Put all tests only in root `tests/` |
| Put migrations in `apps/api/alembic/` | Run manual DDL in production |
| Version n8n JSON in `n8n/workflows/` | Store workflows only in n8n UI |
| Put ADRs in `docs/13-decisions/` | Add new ADRs to legacy `docs/adr/` |

---

## References

- [docs/folder-structure.md](../../docs/folder-structure.md)
- [backend-standards.md](./backend-standards.md)
- [workflow-standards.md](./workflow-standards.md)
- [context-engineering-standards.md](./context-engineering-standards.md)

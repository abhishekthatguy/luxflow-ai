# LexFlow AI — Engineering Handbook

**Version:** 1.0 · **Status:** Draft — Pre-Implementation · **Last Updated:** 2026-07-06

---

## Purpose

This is the **complete engineering reference** for LexFlow AI. It consolidates stack choices, architecture principles, coding standards, quality gates, and operational practices so any engineer can contribute effectively without tribal knowledge.

For deep technical design, see `docs/`. For AI-assisted workflows, see `.ai/tasks/`.

---

## Scope

| In Scope | Out of Scope |
|----------|--------------|
| Technology stack and versions | Firm-specific legal ethics policies |
| Repository layout and naming | Vendor contract negotiations |
| Coding standards (Python, TypeScript) | Individual sprint planning |
| Testing pyramid and CI gates | Penetration test raw findings |
| Security and compliance engineering | Product roadmap prioritization |
| Deployment and observability overview | HR and hiring processes |

---

## 1. Product Context

LexFlow AI is an **enterprise AI automation platform for law firms**. It eliminates repetitive manual work for lawyers, paralegals, and operations teams without replacing legal judgment.

| Metric | Target |
|--------|--------|
| Concurrent users | 1,000+ |
| Workflow executions | 50,000+ / month |
| Documents | Millions |
| Availability | 99.9% |
| RPO / RTO | ≤ 15 min / ≤ 4 hours |

**Primary personas:** Associate Attorney, Paralegal, Legal Assistant, Firm Administrator, Client (portal).

See: `docs/01-product/`

---

## 2. Technology Stack

| Layer | Technology | Version Policy |
|-------|-----------|----------------|
| Frontend | Next.js, React, TypeScript | Latest stable major |
| UI | Tailwind CSS, ShadCN UI | Latest stable |
| State | Zustand, React Query (TanStack) | Latest stable |
| Backend | Python 3.12+, FastAPI, Pydantic v2 | Python 3.12+ locked |
| ORM | SQLAlchemy 2.0, Alembic | Latest stable |
| Queue | Celery, RabbitMQ | Latest stable |
| Database | PostgreSQL 16+, pgvector | PostgreSQL 16+ |
| Cache | Redis 7+ | Latest stable |
| AI | Azure OpenAI (primary), provider adapters | Latest stable SDK |
| Orchestration | n8n (private) | Orchestration only |
| Testing | pytest, Vitest, Playwright, k6 | Latest stable |
| Linting | ruff, mypy, ESLint, Prettier | Latest stable |
| Infrastructure | Terraform, Docker, GitHub Actions | Latest stable |
| Observability | OpenTelemetry, CloudWatch, structured JSON logs | — |

---

## 3. Architecture Overview

```
Frontend (Next.js) → FastAPI → Queue (RabbitMQ) → Workers (Celery) → n8n → External Services
                         ↕                              ↕
                    PostgreSQL + pgvector            Redis + S3
```

### Bounded Contexts

| Context | Package | Owns |
|---------|---------|------|
| Identity | `services/identity/` | Users, roles, sessions |
| Case Management | `services/case_management/` | Cases, deadlines, matter walls |
| Client Management | `services/client_management/` | Clients, contacts |
| Document Management | `services/document_management/` | Upload, versioning, OCR |
| Workflow Orchestration | `services/workflow_orchestration/` | n8n bridge, executions |
| AI Knowledge | `services/ai_knowledge/` | LLM, prompts, RAG |
| Notifications | `services/notifications/` | Email, in-app, Teams |
| Audit & Compliance | `services/audit_compliance/` | Audit logs, exports |

### Layer Architecture (Backend)

```
services/{context}/
├── domain/           # Entities, events, repository interfaces — pure Python
├── application/      # Use cases (commands/queries) — depends on domain
└── infrastructure/   # SQLAlchemy, S3, HTTP — implements domain interfaces
```

**Dependency rule:** domain ← application ← infrastructure. Never reverse.

See: `docs/03-architecture/`, `docs/02-domain/`

---

## 4. Repository Layout

```
lexflow-ai/
├── apps/           # Deployable: web (Next.js), api (FastAPI)
├── services/       # Bounded context Python packages
├── workers/        # Celery tasks
├── n8n/            # Workflow JSON (version-controlled)
├── packages/       # Shared TS: ui, shared, sdk
├── infra/          # Terraform, Docker, CI/CD
├── docs/           # Architecture documentation (146 docs)
├── tests/          # Cross-cutting integration & E2E
├── scripts/        # Dev tooling, seeds, OpenAPI codegen
├── .ai/            # AI prompts, handbook, rules, memory
├── .github/        # GitHub Actions, PR/issue templates
└── docker-compose.yml
```

See: `docs/folder-structure.md`

---

## 5. Platform Invariants

These are **non-negotiable** across all engineering work:

| # | Invariant | Enforcement |
|---|-----------|-------------|
| 1 | Business logic in FastAPI only | Code review; ADR-002 for n8n |
| 2 | n8n is private orchestration | Network isolation; no public webhooks |
| 3 | Async AI processing | 202 Accepted pattern; Celery workers |
| 4 | Human-in-the-loop for legal AI outputs | Approval workflow before client delivery |
| 5 | Matter walls on every case-scoped path | Integration tests on every PR |
| 6 | 404 (not 403) on unauthorized case GET | ADR-007; anti-enumeration |
| 7 | Immutable audit logs | Append-only `audit.audit_logs` |
| 8 | Transactional outbox for events | ADR-006; no direct message publish |
| 9 | No secrets in code or commits | TruffleHog CI gate |
| 10 | No real client data in non-prod | Factories and anonymization only |

---

## 6. Coding Standards

### Python (Backend)

| Tool | Purpose |
|------|---------|
| ruff format | Code formatting (Black-compatible) |
| ruff check | Linting + import sorting |
| mypy | Strict type checking |
| Line length | 100 characters |

- Route handlers are thin — delegate to application use cases
- Pydantic models for request/response
- One router file per resource group
- Internal webhooks excluded from public OpenAPI

### TypeScript (Frontend)

| Tool | Purpose |
|------|---------|
| Prettier | Formatting |
| ESLint | Linting (strict) |
| TypeScript | Strict mode |

- Server Components by default
- Client Components only when interactivity required
- BFF routes are thin proxies to FastAPI
- Typed API client from `packages/sdk/`

### Naming Conventions

| Artifact | Convention | Example |
|----------|------------|---------|
| Python modules | snake_case | `case_management/` |
| Python classes | PascalCase | `CreateCaseCommand` |
| API routes | kebab-case | `/api/v1/case-deadlines` |
| DB tables | snake_case, plural | `case_deadlines` |
| Events | PascalCase past tense | `CaseCreated` |
| n8n workflows | kebab-case-vN | `deadline-reminder-v1` |
| Git branches | type/description | `feat/case-deadline-api` |

See: `docs/development-standards.md`

---

## 7. Branching & Git Workflow

**Trunk-based development** with short-lived feature branches:

| Rule | Detail |
|------|--------|
| Branch from | `main` (protected) |
| Branch naming | `{type}/{short-description}` |
| Types | `feat`, `fix`, `chore`, `docs`, `refactor`, `test` |
| Max lifetime | 3 days (prefer ≤ 1 day) |
| Merge method | Squash merge |
| PR required | Yes — minimum 1 approval |
| CI required | All checks pass |

---

## 8. Testing Strategy

### Testing Pyramid

| Layer | Tool | When | Duration | Coverage |
|-------|------|------|----------|----------|
| Unit (backend) | pytest | Every PR | < 10s | 90% domain + application |
| Unit (frontend) | Vitest | Every PR | < 30s | Critical components |
| Integration | pytest + Testcontainers | Every PR | < 5 min | All API endpoints |
| E2E | Playwright | Post-deploy staging | < 15 min | ~10 critical journeys |
| Load | k6 | Pre-release | On demand | 1K users, 50K workflows/mo |
| Security | pytest + Trivy | Every PR | < 2 min | All auth paths |

### PR Merge Blockers

1. All unit and integration tests pass
2. **Matter wall test suite passes**
3. No CRITICAL/HIGH container vulnerabilities (Trivy)
4. Domain + application coverage does not decrease
5. No secrets in diff

See: `docs/10-testing/`

---

## 9. Security Engineering

| Area | Standard |
|------|----------|
| Authentication | JWT + refresh tokens (ADR-005) |
| Authorization | RBAC + matter walls (ABAC) |
| Encryption | TLS 1.3 in transit; AES-256 at rest |
| Secrets | AWS Secrets Manager — never in code |
| AI safety | PII redaction; prompt injection defense; HITL |
| Compliance | ABA, GDPR, CCPA, SOC 2 mapping |
| Incident response | P1–P4 severity; breach lifecycle |

See: `docs/08-security/`

---

## 10. API Design

- Resource-oriented REST under `/api/v1/`
- Uniform `{ data, meta }` response envelope
- RFC 7807 error format
- Pagination, filtering, sorting conventions
- Idempotency keys for mutating operations
- Async AI endpoints return 202 with job ID

See: `docs/04-api/`

---

## 11. Database

- Single PostgreSQL 16+ with 7 schemas (ADR-003)
- UUID primary keys; `TIMESTAMPTZ` timestamps
- Alembic migrations — always reversible
- Zero-downtime: additive changes first
- pgvector for document embeddings

See: `docs/05-database/`

---

## 12. Workflows (n8n)

- n8n orchestrates external HTTP calls only
- Triggered by FastAPI or internal scheduler
- HMAC-signed callbacks to internal webhooks
- Workflow JSON version-controlled in `n8n/workflows/`
- Promotion: dev → staging → production

See: `docs/06-workflows/`, `docs/14-playbooks/add-workflow.md`

---

## 13. AI Integration

- Azure OpenAI as production default (ADR-008)
- Provider adapter pattern for multi-LLM
- All processing async via Celery workers (ADR-004)
- Versioned prompt registry
- RAG with hybrid search (pgvector + full-text)
- Attorney approval for legal outputs (HITL)

See: `docs/07-ai/`

---

## 14. Deployment & Operations

| Environment | Purpose | Deploy Trigger |
|-------------|---------|----------------|
| Local | Developer workstation | docker-compose |
| Dev | Integration testing | Auto on main merge |
| Staging | Pre-production validation | Auto on main merge |
| Production | Live firm usage | Manual gate |

- ECS on AWS; Terraform for infrastructure
- Zero-downtime rolling deploys
- Structured JSON logging with PII redaction
- OpenTelemetry distributed tracing
- P1–P4 alerting with runbooks

See: `docs/09-deployment/`, `docs/11-observability/`, `docs/14-playbooks/`

---

## 15. Documentation Standards

Every `docs/` document includes: Purpose, Scope, Responsibilities, Architecture (with Mermaid), Best Practices, Tradeoffs, Future Improvements, References.

ADRs are immutable once accepted — supersede with new ADR number.

See: `docs/README.md`, `docs/13-decisions/`

---

## 16. AI-Assisted Development

Use `.ai/tasks/` prompt templates for common engineering tasks:

| Task | Template |
|------|----------|
| New API endpoint | `create-api.md` |
| New UI page | `create-ui.md` |
| Database migration | `create-database-table.md` |
| n8n workflow | `create-workflow.md` |
| Code review | `review-code.md` |
| Security review | `review-security.md` |
| Unit tests | `generate-unit-tests.md` |
| Integration tests | `generate-integration-tests.md` |
| E2E tests | `generate-playwright-tests.md` |
| Documentation | `generate-documentation.md` |

Load context from `.ai/memory/`, `.ai/rules/`, and `docs/` in that priority order.

---

## 17. Onboarding Path

| Week | Focus | Documents |
|------|-------|-----------|
| Day 1 | Setup + product context | `14-playbooks/local-dev-setup.md`, `01-product/vision.md` |
| Day 2–3 | Architecture + domain | `03-architecture/system-context.md`, `02-domain/` |
| Day 4–5 | First contribution | Pick small ticket; follow development-lifecycle.md |
| Week 2 | Deep dive on role area | Backend: `04-api/`, `05-database/` · Frontend: `12-ui/` |
| Week 3 | Security + testing | `08-security/`, `10-testing/` |
| Week 4 | Operate | `14-playbooks/`, `11-observability/` |

See: `docs/14-playbooks/onboarding.md`

---

## References

| Document | Path |
|----------|------|
| Documentation index | `docs/README.md` |
| Development standards | `docs/development-standards.md` |
| Folder structure | `docs/folder-structure.md` |
| ADR index | `docs/13-decisions/README.md` |
| Development lifecycle | `.ai/handbook/development-lifecycle.md` |
| Definition of Ready | `.ai/handbook/definition-of-ready.md` |
| Definition of Done | `.ai/handbook/definition-of-done.md` |
| AI task prompts | `.ai/tasks/README.md` |

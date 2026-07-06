# Development Standards

**LexFlow AI** — Engineering Conventions & Process  
**Version:** 1.0  
**Status:** Draft — Pre-Implementation  
**Last Updated:** 2026-07-06

---

## 1. Overview

This document defines coding standards, branching strategy, PR process, and development workflow for LexFlow AI. All engineers follow these conventions to ensure consistency, quality, and maintainability.

---

## 2. Technology Stack Reference

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
| AI | OpenAI SDK, Anthropic SDK | Latest stable |
| Testing | pytest, Vitest, Playwright | Latest stable |
| Linting | ruff, mypy, ESLint, Prettier | Latest stable |
| Infrastructure | Terraform, Docker, GitHub Actions | Latest stable |

---

## 3. Branching Strategy

**Trunk-based development** with short-lived feature branches:

```
main (protected)
  ├── feat/case-intake-api
  ├── feat/document-upload-ui
  ├── fix/matter-wall-bypass
  └── chore/upgrade-dependencies
```

| Rule | Detail |
|------|--------|
| Branch from | `main` |
| Branch naming | `{type}/{short-description}` — types: `feat`, `fix`, `chore`, `docs`, `refactor`, `test` |
| Max branch lifetime | 3 days (prefer ≤ 1 day) |
| Merge method | Squash merge |
| PR required | Yes — minimum 1 approval |
| CI required | All checks pass before merge |

---

## 3.1 RFC Gate — Design Before Code

**Every major feature requires an Accepted RFC** before implementation begins. See [`docs/18-rfc/README.md`](./18-rfc/README.md).

| Stage | Requirement |
|-------|-------------|
| Sprint planning | Epic has **Accepted** RFC (or documented exemption) |
| Branch `feat/` | PR links `RFC-NNN` in description |
| Code review | Behavior matches accepted RFC; deviations noted in RFC |

RFC covers *what to build*; ADR covers *irreversible architecture*. Both may be required for the same epic.

**Platform Readiness** (Sprint 1 exit) must pass before auth or business logic — see [`docs/14-playbooks/platform-readiness-gate.md`](./14-playbooks/platform-readiness-gate.md).

---

## 4. Pull Request Process

### 4.1 PR Checklist

Every PR must satisfy:

- [ ] Description explains **why** (not just what)
- [ ] Tests added/updated for changed behavior
- [ ] Matter wall tests pass (if touching authorization)
- [ ] No secrets in code or commits
- [ ] Database migration included (if schema change) with downgrade
- [ ] API changes reflected in OpenAPI spec
- [ ] Documentation updated (if architectural change)
- [ ] ADR created (if significant architectural decision)
- [ ] RFC linked (if implementing a major feature — `docs/18-rfc/`)

### 4.2 PR Size Guidelines

| Size | Lines Changed | Review Time |
|------|--------------|-------------|
| Small (preferred) | < 200 | Same day |
| Medium | 200–500 | 1–2 days |
| Large (avoid) | > 500 | Split if possible |

### 4.3 Review Standards

Reviewers check for:
1. Correctness — does it work?
2. Security — matter walls, input validation, no secrets
3. Architecture — business logic in FastAPI, not n8n or frontend
4. Tests — meaningful coverage, not trivial assertions
5. Performance — no N+1 queries, appropriate indexes

---

## 5. Python Backend Standards

### 5.1 Architecture Layers

```
services/{context}/
├── domain/           # Pure Python — no framework imports
├── application/      # Use cases — depends on domain interfaces
├── infrastructure/   # SQLAlchemy, S3, HTTP clients — implements domain interfaces
```

**Dependency rule:** domain ← application ← infrastructure. Never reverse.

### 5.2 Code Style

| Tool | Configuration |
|------|--------------|
| Formatter | ruff format (Black-compatible) |
| Linter | ruff check |
| Type checker | mypy (strict mode) |
| Import sorting | ruff (isort rules) |
| Line length | 100 characters |

### 5.3 Naming Conventions

| Artifact | Convention | Example |
|----------|------------|---------|
| Modules | snake_case | `case_management/` |
| Classes | PascalCase | `CreateCaseCommand` |
| Functions | snake_case | `create_case()` |
| Constants | SCREAMING_SNAKE | `MAX_UPLOAD_SIZE` |
| Private | Leading underscore | `_validate_input()` |
| Type aliases | PascalCase | `CaseId = UUID` |

### 5.4 FastAPI Conventions

- Route handlers are thin — delegate to application use cases
- Pydantic models for request/response (never return ORM models directly)
- Dependency injection for database sessions, current user, authorization
- One router file per resource group
- Internal webhooks in separate router not included in public OpenAPI

---

## 6. TypeScript Frontend Standards

### 6.1 Code Style

| Tool | Configuration |
|------|--------------|
| Formatter | Prettier |
| Linter | ESLint (strict) |
| Type checker | TypeScript strict mode |

### 6.2 Component Conventions

- Functional components only
- Server Components by default (Next.js App Router)
- Client Components only when interactivity required (`"use client"`)
- ShadCN UI primitives — do not modify generated ShadCN files directly
- API calls via React Query hooks — never raw fetch in components
- Zustand for UI state only (modals, sidebar, filters) — not server data

### 6.3 File Naming

| Type | Convention | Example |
|------|------------|---------|
| Components | PascalCase | `CaseTimeline.tsx` |
| Hooks | camelCase with `use` prefix | `useCaseDetail.ts` |
| Utilities | camelCase | `formatDate.ts` |
| Types | PascalCase | `Case.ts` |
| Pages | lowercase (App Router) | `cases/[id]/page.tsx` |

---

## 7. Database Standards

- All schema changes via Alembic migrations — never manual DDL in production
- Migrations must include both `upgrade()` and `downgrade()`
- Use `CREATE INDEX CONCURRENTLY` for indexes on large tables
- UUID primary keys everywhere
- Foreign keys with explicit `ON DELETE` behavior documented
- No raw SQL in application code (except migrations and complex reporting queries reviewed by two engineers)

---

## 8. Git Conventions

### 8.1 Commit Messages

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
feat(cases): add case intake API endpoint
fix(auth): prevent matter wall bypass on document download
docs(architecture): add AI architecture document
chore(deps): upgrade FastAPI to 0.115
test(workflows): add integration test for n8n callback
```

### 8.2 Commit Rules

- Atomic commits — one logical change per commit
- No WIP commits on main
- No force push to main
- Squash merge preserves clean history

---

## 9. Environment Variables

- All config via environment variables (12-factor app)
- `.env.example` documents all variables with descriptions — no values
- Secrets via AWS Secrets Manager in deployed environments
- Pydantic Settings (backend) and validated env module (frontend)
- Never commit `.env` files

---

## 10. Documentation Standards

- Architecture changes require doc update in same PR
- Significant decisions require ADR in `docs/adr/`
- API changes auto-update OpenAPI spec
- README in each deployable app and service module
- Inline code comments only for non-obvious business logic

---

## 11. Local Development Setup

```bash
# Prerequisites: Docker, Node 20+, Python 3.12+, Make

git clone {repo}
cd lexflow-ai
cp .env.example .env          # Fill in local values
make setup                     # Install deps, run migrations, seed data
make dev                       # Start all services via docker compose
make test                      # Run unit + integration tests
make lint                      # Run all linters
```

---

## 12. Related Documents

- [folder-structure.md](./folder-structure.md)
- [testing-strategy.md](./testing-strategy.md)
- [api-architecture.md](./api-architecture.md)
- [deployment-architecture.md](./deployment-architecture.md)
- [adr/README.md](./adr/README.md)

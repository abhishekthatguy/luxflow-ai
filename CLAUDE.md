# LexFlow AI — Claude Code Instructions

You are working on **LexFlow AI**, an enterprise AI automation platform for US law firms.

---

## Mandatory Context (Read First)

@.ai/memory/PROJECT.md
@.ai/memory/INVARIANTS.md

For any implementation task, also load the relevant task prompt from `.ai/tasks/`.

---

## What This Project Is

LexFlow AI eliminates repetitive manual work for lawyers, paralegals, and operations teams. It does **not** replace legal judgment.

**Central domain:** Case (legal matter) with matter walls, documents, workflows, AI summaries, and immutable audit logs.

**Stack:** Next.js · FastAPI · PostgreSQL + pgvector · RabbitMQ · Celery · n8n (private) · Redis · S3 · AWS ECS

---

## Non-Negotiable Architecture Rules

1. **FastAPI owns all business logic** — `services/{bounded_context}/` with hexagonal architecture
2. **n8n is orchestration only** — private VPC, no business rules, no PostgreSQL nodes, no public access
3. **Frontend → FastAPI only** — never n8n, never RabbitMQ
4. **All AI is async** — API returns 202, Celery worker calls LLM (ADR-004)
5. **Matter walls** — case access requires participant membership; deny with **404**
6. **Human-in-the-loop** — AI legal outputs need attorney approval before team visibility
7. **Transactional outbox** — events published in same DB transaction as domain change
8. **Immutable audit logs** — append-only, every mutating API call logged

---

## Where Things Live

| What | Where |
|------|-------|
| AI context (load first) | `.ai/` |
| Full documentation | `docs/` (15 numbered folders) |
| API routes (thin) | `apps/api/src/api/v1/` |
| Business logic | `services/{context}/application/` |
| Domain entities | `services/{context}/domain/` |
| Repositories | `services/{context}/infrastructure/` |
| Celery tasks | `workers/celery/tasks/` |
| n8n workflows | `n8n/workflows/{domain}/` |
| Frontend pages | `apps/web/src/app/(dashboard)/` |
| Migrations | `apps/api/alembic/versions/` |

---

## Task Playbooks

Copy and fill variables from `.ai/tasks/`:

| Task | Playbook |
|------|----------|
| New REST endpoint | `.ai/tasks/create-api.md` |
| New UI page | `.ai/tasks/create-ui.md` |
| New DB table | `.ai/tasks/create-database-table.md` |
| New n8n workflow | `.ai/tasks/create-workflow.md` |
| Review PR | `.ai/tasks/review-code.md` |
| Security audit | `.ai/tasks/review-security.md` |
| Unit tests | `.ai/tasks/generate-unit-tests.md` |
| Integration tests | `.ai/tasks/generate-integration-tests.md` |
| Playwright E2E | `.ai/tasks/generate-playwright-tests.md` |
| Documentation | `.ai/tasks/generate-documentation.md` |

---

## Standards

All standards in `.ai/rules/` — see `.ai/rules/README.md` for index.

Key files:
- `backend-standards.md` — DDD, FastAPI, SQLAlchemy
- `frontend-standards.md` — Next.js App Router, React Query, Zustand
- `api-standards.md` — REST envelope, RFC 7807, `/api/v1`
- `security-rules.md` — auth, matter walls, secrets
- `workflow-standards.md` — n8n boundaries
- `testing-standards.md` — pyramid, matter wall gate
- `code-review-checklist.md` — PR review

---

## Patterns & Examples

Structural templates (no copy-paste code — follow the pattern):
- `.ai/patterns/` — api-endpoint, use-case, domain-entity, repository, event-handler, celery-task, n8n-workflow, react-page, react-query-hook, alembic-migration

Annotated flows:
- `.ai/examples/` — create case, document upload, AI async, workflow trigger, matter wall, audit log

---

## Agent Modes

Adopt the appropriate persona from `.ai/agents/`:
- Backend → `backend-engineer.md`
- Frontend → `frontend-engineer.md`
- n8n → `workflow-engineer.md`
- LLM/RAG → `ai-ml-engineer.md`
- Security → `security-reviewer.md`
- PR review → `code-reviewer.md`
- Architecture → `tech-lead.md`

---

## Documentation Authority

| Layer | Path | When to Use |
|-------|------|-------------|
| Compressed AI context | `.ai/` | Session start, quick reference |
| Full enterprise docs | `docs/` | Deep design, onboarding, compliance |
| ADRs | `docs/13-decisions/` | Architectural decisions |

**Conflict resolution:** `docs/` > `.ai/` > your assumptions

---

## Git Conventions

- **Branches:** `feat/`, `fix/`, `chore/`, `docs/`, `test/`, `refactor/` + kebab-case
- **Commits:** Conventional Commits — `feat(cases): add intake endpoint`
- **PRs:** Use `.github/pull_request_template.md`
- **Merge:** Squash to `main`; CI must pass; matter wall tests required

---

## Before Submitting Work

Check [`.ai/handbook/definition-of-done.md`](.ai/handbook/definition-of-done.md):

- [ ] Matches bounded context and folder structure
- [ ] Matter wall authorization enforced (backend)
- [ ] Audit log written for mutating operations
- [ ] Tests added (unit + integration where applicable)
- [ ] No secrets in code
- [ ] No business logic in n8n or frontend
- [ ] OpenAPI updated if API changed
- [ ] Migration included if schema changed

---

## Full Index

- `.ai/README.md` — AI context master index
- `docs/README.md` — documentation master index
- `AGENTS.md` — shared agent instructions (Cursor, Copilot, Claude)

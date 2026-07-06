# LexFlow AI — Agent Instructions

**Enterprise AI Automation Platform for Law Firms**

This file is the entry point for **Cursor**, **Claude Code**, **GitHub Copilot**, and other AI coding assistants.

---

## Before You Write Anything

1. Read [`.ai/memory/PROJECT.md`](.ai/memory/PROJECT.md) — product, stack, constraints
2. Read [`.ai/memory/INVARIANTS.md`](.ai/memory/INVARIANTS.md) — **non-negotiable rules**
3. Load task-specific context from [`.ai/README.md`](.ai/README.md)

**Authoritative documentation:** [`docs/README.md`](docs/README.md) (146 documents). When `.ai/` and `docs/` conflict, **`docs/` wins**.

---

## Platform Invariants (Never Violate)

| # | Rule |
|---|------|
| 1 | **Business logic in FastAPI** (`services/`) — never in n8n or frontend |
| 2 | **n8n is private** — orchestration only; no public access; no PostgreSQL nodes |
| 3 | **Frontend never calls n8n** — all traffic via FastAPI |
| 4 | **Async AI only** — LLM calls via RabbitMQ → Celery; API returns `202 Accepted` |
| 5 | **Human-in-the-loop** — legal AI outputs require attorney approval before team visibility |
| 6 | **Matter walls** — unauthorized case access returns **404** (not 403) |
| 7 | **Immutable audit** — append-only audit logs for all mutating operations |
| 8 | **Transactional outbox** — domain events published atomically with DB writes |
| 9 | **Case-scoped RAG** — vector search always filters by `case_id` |
| 10 | **No secrets in code** — AWS Secrets Manager only |

Full detail: [`.ai/memory/INVARIANTS.md`](.ai/memory/INVARIANTS.md)

---

## Architecture Pipeline

```
Frontend (Next.js) → FastAPI → RabbitMQ → Celery Workers → n8n (private) → External APIs
                         ↕                                    ↕
                  PostgreSQL + pgvector                   Redis + S3
```

---

## Context Loading by Task

| Task | Load |
|------|------|
| **Any task** | `.ai/memory/PROJECT.md` + `.ai/memory/INVARIANTS.md` |
| Create API | `.ai/tasks/create-api.md` + `.ai/patterns/api-endpoint-pattern.md` + `.ai/rules/backend-standards.md` |
| Create UI | `.ai/tasks/create-ui.md` + `.ai/patterns/react-page-pattern.md` + `.ai/rules/frontend-standards.md` |
| Database table | `.ai/tasks/create-database-table.md` + `.ai/patterns/alembic-migration-pattern.md` + `docs/05-database/` |
| n8n workflow | `.ai/tasks/create-workflow.md` + `.ai/patterns/n8n-workflow-pattern.md` + `.ai/rules/workflow-standards.md` |
| Code review | `.ai/tasks/review-code.md` + `.ai/rules/code-review-checklist.md` |
| Security review | `.ai/tasks/review-security.md` + `.ai/rules/security-rules.md` |
| Unit tests | `.ai/tasks/generate-unit-tests.md` + `.ai/rules/testing-standards.md` |
| Integration tests | `.ai/tasks/generate-integration-tests.md` — **matter wall tests mandatory** |
| E2E tests | `.ai/tasks/generate-playwright-tests.md` |
| Documentation | `.ai/tasks/generate-documentation.md` |
| Architecture change | `.ai/handbook/adr-process.md` + `docs/13-decisions/` |

---

## Agent Personas

| Persona | File | Use When |
|---------|------|----------|
| Backend Engineer | [`.ai/agents/backend-engineer.md`](.ai/agents/backend-engineer.md) | FastAPI, domain, workers, DB |
| Frontend Engineer | [`.ai/agents/frontend-engineer.md`](.ai/agents/frontend-engineer.md) | Next.js, React Query, UI |
| Workflow Engineer | [`.ai/agents/workflow-engineer.md`](.ai/agents/workflow-engineer.md) | n8n JSON, webhooks |
| AI/ML Engineer | [`.ai/agents/ai-ml-engineer.md`](.ai/agents/ai-ml-engineer.md) | LLM, RAG, prompts |
| Security Reviewer | [`.ai/agents/security-reviewer.md`](.ai/agents/security-reviewer.md) | Auth, matter walls, threats |
| Code Reviewer | [`.ai/agents/code-reviewer.md`](.ai/agents/code-reviewer.md) | PR review |
| DevOps Engineer | [`.ai/agents/devops-engineer.md`](.ai/agents/devops-engineer.md) | AWS, Terraform, CI/CD |
| Tech Lead | [`.ai/agents/tech-lead.md`](.ai/agents/tech-lead.md) | ADRs, tradeoffs, design |

---

## Standards Quick Reference

| Topic | Rule File |
|-------|-----------|
| All code | [`.ai/rules/coding-standards.md`](.ai/rules/coding-standards.md) |
| Backend | [`.ai/rules/backend-standards.md`](.ai/rules/backend-standards.md) |
| Frontend | [`.ai/rules/frontend-standards.md`](.ai/rules/frontend-standards.md) |
| API | [`.ai/rules/api-standards.md`](.ai/rules/api-standards.md) |
| Workflows | [`.ai/rules/workflow-standards.md`](.ai/rules/workflow-standards.md) |
| Security | [`.ai/rules/security-rules.md`](.ai/rules/security-rules.md) |
| Testing | [`.ai/rules/testing-standards.md`](.ai/rules/testing-standards.md) |
| Git / PR | [`.ai/rules/git-workflow.md`](.ai/rules/git-workflow.md) |
| Naming | [`.ai/rules/naming-conventions.md`](.ai/rules/naming-conventions.md) |
| Folder layout | [`.ai/rules/folder-structure.md`](.ai/rules/folder-structure.md) |

Full index: [`.ai/rules/README.md`](.ai/rules/README.md)

---

## Engineering Handbook

| Document | Purpose |
|----------|---------|
| [Engineering Handbook](.ai/handbook/engineering-handbook.md) | Complete engineering reference |
| [Development Lifecycle](.ai/handbook/development-lifecycle.md) | Idea → production |
| [Definition of Ready](.ai/handbook/definition-of-ready.md) | Ticket readiness |
| [Definition of Done](.ai/handbook/definition-of-done.md) | PR merge criteria |
| [ADR Process](.ai/handbook/adr-process.md) | Architecture decisions |

---

## Domain Language

Use terms from [`.ai/memory/GLOSSARY.md`](.ai/memory/GLOSSARY.md):

- **Case** (not Ticket, Issue, Project) — central aggregate
- **Matter Wall** — case-level access restriction
- **Client** — individual or organization receiving legal services
- **Workflow** — automated sequence (n8n orchestrates, FastAPI decides)
- **Summary** — AI-generated text requiring attorney review

---

## Do Not

- Put business logic in n8n Code nodes or frontend components
- Call n8n from the browser
- Make synchronous LLM calls in API request handlers
- Return 403 for unauthorized case access (use 404)
- Commit secrets, `.env` files, or credentials
- Skip matter wall authorization tests
- Contradict ADRs without proposing a new one

---

## Repository Map

```
lexflow-ai/
├── .ai/           ← AI context (this is your primary knowledge base)
├── docs/          ← Full enterprise documentation (01-product … 15-interview)
├── apps/          ← web (Next.js), api (FastAPI) — when implemented
├── services/      ← Bounded context Python packages
├── workers/       ← Celery tasks
├── n8n/workflows/ ← Version-controlled workflow JSON
├── packages/      ← Shared TS libraries
└── infra/         ← Terraform, Docker, CI/CD
```

---

## Maintenance

When architecture or domain changes:

1. Update `docs/` (authoritative)
2. Update `.ai/memory/` and `.ai/architecture/`
3. Update `.ai/rules/` if standards change
4. Add ADR to `docs/13-decisions/` and `.ai/architecture/DECISIONS.md`

See [`.ai/rules/context-engineering-standards.md`](.ai/rules/context-engineering-standards.md)

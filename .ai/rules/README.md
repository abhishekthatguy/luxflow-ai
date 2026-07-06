# LexFlow AI — AI Assistant Rules Index

**Version:** 1.0 · **Status:** Active · **Last Updated:** 2026-07-06

This directory is the **authoritative instruction layer** for AI coding assistants (Cursor, Copilot, Claude, etc.) working in the LexFlow AI monorepo. Rules here are **actionable constraints** — not documentation. For deep architecture context, follow links to `docs/`.

---

## When to Use These Rules

| Situation | Action |
|-----------|--------|
| Starting any task in this repo | Read this index; load rules for touched layers |
| Writing backend code | `backend-standards.md`, `api-standards.md`, `security-rules.md` |
| Writing frontend code | `frontend-standards.md`, `api-standards.md`, `security-rules.md` |
| Adding n8n workflows | `workflow-standards.md` only — no business logic in n8n |
| Adding AI prompts/templates | `prompt-engineering-standards.md`, `security-rules.md` |
| Editing `.ai/` itself | `context-engineering-standards.md` |
| Opening a PR | `code-review-checklist.md`, `git-workflow.md`, `testing-standards.md` |

---

## Platform Invariants (Non-Negotiable)

These apply to **every** rule file and override convenience shortcuts:

1. **Case-centric domain** — Cases are the central aggregate; matter walls enforce access
2. **Business logic in FastAPI** — Never in n8n, frontend, or workers duplicating domain rules
3. **n8n is private orchestration only** — No PostgreSQL, no authorization, no domain rules
4. **Async AI** — All LLM calls via queue/worker; human-in-the-loop for legal outputs
5. **Immutable audit** — Append-only audit logs for significant actions
6. **Event-driven** — Transactional outbox → RabbitMQ → Celery workers
7. **404 on matter wall deny (GET)** — Per ADR-007; never 403 for unauthorized case reads

**Binding decisions:** `docs/13-decisions/`

---

## Rule Files

### Core Engineering

| File | Scope | Primary Docs |
|------|-------|--------------|
| [coding-standards.md](./coding-standards.md) | Cross-stack conventions, tooling, PR hygiene | `docs/development-standards.md` |
| [design-principles.md](./design-principles.md) | DDD, hexagonal, modular monolith, event-driven | `docs/03-architecture/`, `docs/13-decisions/` |
| [naming-conventions.md](./naming-conventions.md) | Python, TypeScript, API, DB, events, n8n | `docs/folder-structure.md` |
| [folder-structure.md](./folder-structure.md) | Monorepo layout, where code belongs | `docs/folder-structure.md` |

### Layer-Specific

| File | Scope | Primary Docs |
|------|-------|--------------|
| [backend-standards.md](./backend-standards.md) | FastAPI, DDD, hexagonal, `services/` | `docs/03-architecture/component-architecture.md` |
| [frontend-standards.md](./frontend-standards.md) | Next.js, React Query, Zustand, ShadCN | `docs/12-ui/` |
| [workflow-standards.md](./workflow-standards.md) | n8n orchestration only | `docs/06-workflows/`, ADR-002 |
| [api-standards.md](./api-standards.md) | REST, RFC 7807, versioning | `docs/04-api/` |

### Quality & Operations

| File | Scope | Primary Docs |
|------|-------|--------------|
| [testing-standards.md](./testing-standards.md) | Pyramid, matter wall tests, CI gates | `docs/10-testing/` |
| [error-handling.md](./error-handling.md) | API, domain, worker error patterns | `docs/04-api/error-handling.md` |
| [logging-standards.md](./logging-standards.md) | JSON logs, PII redaction, correlation | `docs/11-observability/structured-logging.md` |
| [observability-standards.md](./observability-standards.md) | Traces, metrics, alerts, runbooks | `docs/11-observability/` |
| [security-rules.md](./security-rules.md) | Matter walls, secrets, auth, compliance | `docs/08-security/` |

### Process & AI Layer

| File | Scope | Primary Docs |
|------|-------|--------------|
| [git-workflow.md](./git-workflow.md) | Trunk-based dev, PR process | `docs/development-standards.md` |
| [commit-message-standards.md](./commit-message-standards.md) | Conventional Commits | `docs/development-standards.md` |
| [branch-naming.md](./branch-naming.md) | Branch types and naming | `docs/development-standards.md` |
| [code-review-checklist.md](./code-review-checklist.md) | Reviewer and author checklists | `docs/10-testing/`, `docs/08-security/` |
| [prompt-engineering-standards.md](./prompt-engineering-standards.md) | LLM prompts, templates, HITL | `docs/07-ai/prompt-management.md` |
| [context-engineering-standards.md](./context-engineering-standards.md) | Maintaining `.ai/` layer | This directory |

---

## Rule Precedence

When rules conflict, apply this order:

1. **Security rules** (`security-rules.md`) — always win
2. **ADRs** (`docs/13-decisions/`) — binding architectural decisions
3. **Layer-specific rules** (backend, frontend, workflow, API)
4. **General coding standards**
5. **Assistant convenience** — never overrides 1–4

If a user request contradicts security or ADR rules, **stop and explain** before implementing.

---

## Quick Load Matrix for AI Assistants

| Task Type | Minimum Rules to Load |
|-----------|----------------------|
| New API endpoint | `api-standards.md`, `backend-standards.md`, `security-rules.md`, `testing-standards.md` |
| Case/document feature | Above + `error-handling.md`, matter wall sections |
| UI page/component | `frontend-standards.md`, `api-standards.md`, `security-rules.md` |
| n8n workflow JSON | `workflow-standards.md` only |
| AI prompt/template | `prompt-engineering-standards.md`, `security-rules.md` |
| Database migration | `backend-standards.md`, `naming-conventions.md` |
| Observability change | `logging-standards.md`, `observability-standards.md` |

---

## Maintenance

- Update rules in the **same PR** as the behavioral change they encode
- Significant architectural shifts require ADR in `docs/13-decisions/` **and** rule file updates
- See [context-engineering-standards.md](./context-engineering-standards.md) for `.ai/` layer governance

---

## References

- [docs/README.md](../../docs/README.md) — Full documentation index
- [docs/development-standards.md](../../docs/development-standards.md) — Human engineering standards
- [docs/13-decisions/README.md](../../docs/13-decisions/README.md) — Architecture Decision Records

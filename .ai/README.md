# LexFlow AI — AI Context Index

**Purpose:** Master index for AI assistants (Cursor, Claude, GitHub Copilot, Codex) working on LexFlow AI.  
**Status:** Pre-implementation — documentation phase complete.  
**Source of truth:** `docs/` (146 documents across 15 numbered folders).  
**Last updated:** 2026-07-06

---

## What This Folder Is

`.ai/` is **context engineering** for AI tools — compressed, actionable knowledge derived from `docs/`. It is NOT application code. When implementing features, always verify against the full document in `docs/` if details are ambiguous.

```
.ai/
├── README.md              ← You are here
├── agents/                ← Role personas (backend, frontend, security, …)
├── patterns/              ← Structural templates + pseudocode outlines
├── examples/              ← Annotated end-to-end flows (no runnable code)
├── rules/                 ← Enforceable standards (backend, frontend, security, …)
├── tasks/                 ← Task playbooks (create-api, create-ui, review-code, …)
├── memory/                ← Stable project knowledge (load first)
│   ├── PROJECT.md         ← Product + stack + invariants (single entry point)
│   ├── STACK.md           ← Technology reference
│   ├── INVARIANTS.md      ← Non-negotiable rules — never violate
│   ├── GLOSSARY.md        ← Domain terms (from docs/02-domain/ubiquitous-language.md)
│   ├── DOMAIN.md          ← Bounded contexts + aggregates
│   └── DOC-INDEX.md       ← Map to docs/01–15 folders
├── architecture/          ← Architecture summaries
│   ├── OVERVIEW.md        ← C4 + deployment topology
│   ├── DATA-FLOW.md       ← Sync/async paths
│   ├── BOUNDED-CONTEXTS.md← Context map + integration
│   └── DECISIONS.md       ← ADR 001–008 summary
├── handbook/              ← DoR, DoD, lifecycle, ADR process
└── templates/             ← Issue and PR templates
```

---

## How AI Assistants Should Use This

### 1. Session Start (Always)

Read in order:
1. `memory/PROJECT.md` — what LexFlow is, who it's for, core constraints
2. `memory/INVARIANTS.md` — rules that must never be broken
3. Task-specific file from `memory/` or `architecture/`

### 2. Pick a Persona + Pattern

| Task type | Persona | Pattern | Rules |
|-----------|---------|---------|-------|
| API / backend | `agents/backend-engineer.md` | `patterns/api-endpoint-pattern.md` | `rules/backend-standards.md` |
| Use case / domain | `agents/backend-engineer.md` | `patterns/use-case-pattern.md` | `rules/design-principles.md` |
| Frontend page | `agents/frontend-engineer.md` | `patterns/react-page-pattern.md` | `rules/frontend-standards.md` |
| React Query hook | `agents/frontend-engineer.md` | `patterns/react-query-hook-pattern.md` | `rules/frontend-standards.md` |
| Database migration | `agents/backend-engineer.md` | `patterns/alembic-migration-pattern.md` | `rules/backend-standards.md` |
| n8n workflow | `agents/workflow-engineer.md` | `patterns/n8n-workflow-pattern.md` | `rules/workflow-standards.md` |
| AI / LLM | `agents/ai-ml-engineer.md` | `patterns/celery-task-pattern.md` | `rules/prompt-engineering-standards.md` |
| Event handler | `agents/backend-engineer.md` | `patterns/event-handler-pattern.md` | `rules/backend-standards.md` |
| Security review | `agents/security-reviewer.md` | — | `rules/security-rules.md` |
| PR review | `agents/code-reviewer.md` | — | `rules/code-review-checklist.md` |
| Architecture decision | `agents/tech-lead.md` | — | `handbook/adr-process.md` |
| Infrastructure | `agents/devops-engineer.md` | — | `docs/09-deployment/` |

**Examples:** See `examples/` for annotated flows (create case, document upload, AI async, workflow trigger, matter wall, audit).

### 3. Before Writing Code (Deep Reads)

| Task type | Read first |
|-----------|------------|
| API / backend | `memory/DOMAIN.md`, `architecture/DATA-FLOW.md`, `docs/04-api/` |
| Frontend | `memory/STACK.md`, `docs/12-ui/`, `memory/INVARIANTS.md` |
| Database | `memory/DOMAIN.md`, `docs/05-database/schema-overview.md` |
| n8n workflow | `memory/INVARIANTS.md` (n8n rules), `docs/06-workflows/` |
| AI / LLM | `architecture/DECISIONS.md` (ADR-004, ADR-008), `docs/07-ai/` |
| Security / auth | `memory/INVARIANTS.md`, `docs/08-security/matter-walls.md` |
| Infrastructure | `architecture/OVERVIEW.md`, `docs/09-deployment/` |

### 4. Before Architectural Changes

- Check `architecture/DECISIONS.md` — do not contradict accepted ADRs without proposing a new ADR
- Check `memory/INVARIANTS.md` — platform invariants are non-negotiable
- Update `.ai/` context files when ADRs or invariants change

### 5. Terminology

Use `memory/GLOSSARY.md` for naming. Code uses `Case` (not `Matter`, `Ticket`, `Project`). UI may display "Matter" per firm preference.

### 6. Deep Dives

`.ai/` compresses; `docs/` is authoritative. Cross-references use paths like `docs/04-api/endpoints-cases.md`. When `.ai/` and `docs/` conflict, **docs/ wins** — flag the discrepancy.

---

## Tool-Specific Guidance

### Cursor

- Add `.ai/` to project rules or `@`-mention files at session start
- For large tasks: `@.ai/memory/PROJECT.md` + `@.ai/memory/INVARIANTS.md`
- Use `memory/DOC-INDEX.md` to find the right `docs/` file

### Claude / Chat

- Paste `memory/PROJECT.md` + relevant architecture file as system context
- Reference ADR numbers when discussing tradeoffs

### GitHub Copilot

- Copilot reads open files and repo context; keep `INVARIANTS.md` or `PROJECT.md` open when coding
- Inline comments should use glossary terms

---

## Platform Invariants (Quick Reference)

Full detail: `memory/INVARIANTS.md`

1. **Case-centric** — Case is the central aggregate; matter walls enforce access
2. **Business logic in FastAPI** — never in n8n or frontend
3. **n8n is private** — orchestration only; not publicly accessible
4. **Async AI** — all LLM via queue/worker; HITL for legal outputs
5. **Immutable audit** — append-only audit logs
6. **Event-driven** — transactional outbox → RabbitMQ → Celery

---

## Canonical Pipeline

```
Frontend (Next.js) → FastAPI → Queue (RabbitMQ) → Workers (Celery) → n8n → External
                         ↕                              ↕
                    PostgreSQL + pgvector            Redis + S3
```

---

## Scale Targets

| Metric | Target |
|--------|--------|
| Concurrent users | 1,000+ |
| Workflow executions | 50,000+ / month |
| Availability | 99.9% |
| RPO / RTO | ≤ 15 min / ≤ 4 hours |

---

## Related Entry Points

| Path | Purpose |
|------|---------|
| `docs/README.md` | Full documentation index |
| `README.md` | Repository entry point |
| `docs/14-playbooks/onboarding.md` | New engineer reading path |
| `docs/13-decisions/` | Full ADR text |
| `docs/development-standards.md` | Coding conventions |

---

## Maintenance

When updating LexFlow architecture or domain model:

1. Update authoritative doc in `docs/`
2. Update corresponding `.ai/` file(s)
3. If new ADR: add to `architecture/DECISIONS.md` and `docs/13-decisions/`
4. If new domain term: add to `memory/GLOSSARY.md` and `docs/02-domain/ubiquitous-language.md`

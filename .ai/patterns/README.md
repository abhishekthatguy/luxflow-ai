# LexFlow AI — Implementation Patterns

**Purpose:** Reusable structural templates and pseudocode outlines for consistent implementation.  
**Not included:** Runnable application code — use these as scaffolds only.

---

## How to Use

1. Identify the artifact type (endpoint, use case, migration, etc.).
2. Open the matching pattern file.
3. Read **Mandatory Reads** and **Invariants** before writing code.
4. Follow **Structure Template** for file placement per `docs/folder-structure.md`.
5. Complete the pattern **Checklist** before PR.

---

## Pattern Index

| Pattern | File | Layer |
|---------|------|-------|
| REST endpoint | [api-endpoint-pattern.md](./api-endpoint-pattern.md) | `apps/api/` |
| Use case (command/query) | [use-case-pattern.md](./use-case-pattern.md) | `services/*/application/` |
| Domain entity / aggregate | [domain-entity-pattern.md](./domain-entity-pattern.md) | `services/*/domain/` |
| Repository | [repository-pattern.md](./repository-pattern.md) | domain interface + infra impl |
| Event handler (consumer) | [event-handler-pattern.md](./event-handler-pattern.md) | `workers/celery/` |
| Outbox emission | [outbox-event-pattern.md](./outbox-event-pattern.md) | command + `shared/` |
| Celery task | [celery-task-pattern.md](./celery-task-pattern.md) | `workers/celery/tasks/` |
| n8n workflow | [n8n-workflow-pattern.md](./n8n-workflow-pattern.md) | `n8n/workflows/` |
| React page | [react-page-pattern.md](./react-page-pattern.md) | `apps/web/src/app/` |
| React Query hook | [react-query-hook-pattern.md](./react-query-hook-pattern.md) | `apps/web/src/hooks/` |
| Alembic migration | [alembic-migration-pattern.md](./alembic-migration-pattern.md) | `apps/api/alembic/` |

---

## Layer Dependency (All Backend Patterns)

```
domain ← application ← infrastructure
         ↑
    apps/api (adapter)
    workers (adapter)
```

---

## Global References

| Resource | Path |
|----------|------|
| Dev standards | `docs/development-standards.md` |
| Component arch | `docs/03-architecture/component-architecture.md` |
| Event design | `docs/03-architecture/event-driven-design.md` |
| REST standards | `docs/04-api/rest-standards.md` |
| Domain events | `docs/02-domain/domain-events.md` |
| Project rules | `.ai/rules/` |
| Annotated examples | `.ai/examples/` |
| Agent personas | `.ai/agents/` |

---

## Anti-Patterns (Reject in Review)

| Anti-pattern | Correct pattern |
|--------------|-----------------|
| Business logic in route handler | `use-case-pattern.md` |
| SQLAlchemy in domain | `domain-entity-pattern.md` + `repository-pattern.md` |
| Publish to RabbitMQ without outbox | `outbox-event-pattern.md` |
| LLM call in API handler | `celery-task-pattern.md` + ADR-004 |
| Domain rules in n8n Code node | `n8n-workflow-pattern.md` |
| `fetch` in React component | `react-query-hook-pattern.md` |
| Manual DDL in production | `alembic-migration-pattern.md` |

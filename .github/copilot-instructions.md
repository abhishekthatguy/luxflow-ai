# GitHub Copilot Instructions — LexFlow AI

Enterprise AI automation platform for US law firms. Case-centric domain with matter walls, async AI, and private n8n orchestration.

---

## Project Context

Load these files for full context (keep open or reference in chat):

1. `.ai/memory/PROJECT.md` — product, stack, scale targets
2. `.ai/memory/INVARIANTS.md` — non-negotiable rules
3. `AGENTS.md` — complete agent instructions

Full documentation: `docs/README.md`

---

## Architecture (Memorize)

```
Frontend (Next.js) → FastAPI → RabbitMQ → Celery → n8n (private) → External
                         ↕
                  PostgreSQL + pgvector + Redis + S3
```

---

## Code Generation Rules

### Always

- Put business logic in `services/{context}/application/` (use cases)
- Put domain entities in `services/{context}/domain/`
- Put SQLAlchemy repos in `services/{context}/infrastructure/`
- Keep FastAPI route handlers thin — delegate to use cases
- Enforce matter walls before returning case data (404 if denied)
- Write audit log entries for mutating operations
- Use UUID primary keys, `firm_id` on tenant tables, `version` for optimistic concurrency
- Return RFC 7807 errors with `type`, `title`, `status`, `detail`
- Use async AI pattern: return 202 + job ID, process in Celery worker
- Use Pydantic v2 for request/response models
- Use React Query for server state, Zustand for UI state only

### Never

- Business logic in n8n workflows or frontend components
- Frontend calls to n8n, RabbitMQ, or internal webhooks
- Synchronous LLM API calls in FastAPI request handlers
- 403 for unauthorized case access (use 404)
- Secrets, API keys, or passwords in source code
- Raw SQL in application code (SQLAlchemy ORM only)
- PostgreSQL nodes in n8n
- Skip authorization checks on case-scoped resources

---

## Naming

| Artifact | Convention | Example |
|----------|------------|---------|
| Python modules | snake_case | `case_management/` |
| Python classes | PascalCase | `CreateCaseCommand` |
| API routes | kebab-case | `/api/v1/case-deadlines` |
| DB tables | snake_case plural | `audit_logs` |
| Events | PascalCase past tense | `CaseCreated` |
| React components | PascalCase | `CaseTimeline.tsx` |
| n8n workflows | kebab-case-vN | `intake-new-client-v1` |

Full reference: `.ai/rules/naming-conventions.md`

---

## File Placement

| Code Type | Location |
|-----------|----------|
| API route | `apps/api/src/api/v1/{resource}.py` |
| Use case | `services/{context}/application/commands/` or `queries/` |
| Entity | `services/{context}/domain/entities/` |
| Repository | `services/{context}/infrastructure/repositories/` |
| Celery task | `workers/celery/tasks/{domain}_tasks.py` |
| n8n workflow | `n8n/workflows/{domain}/{name}-v1.json` |
| Next.js page | `apps/web/src/app/(dashboard)/{route}/page.tsx` |
| React hook | `apps/web/src/hooks/use{Feature}.ts` |
| Migration | `apps/api/alembic/versions/` |

Full reference: `.ai/rules/folder-structure.md`

---

## Testing Expectations

When generating tests:

- **Unit:** Domain invariants and use cases with mocked repos
- **Integration:** API endpoints with Testcontainers; **matter wall matrix required**
- **E2E:** Playwright for critical user journeys

Reference: `.ai/rules/testing-standards.md`

---

## Suggested Copilot Chat Prompts

Use task playbooks from `.ai/tasks/`:

- "Follow `.ai/tasks/create-api.md` to create POST /api/v1/cases"
- "Follow `.ai/tasks/review-security.md` to review this diff"
- "Follow `.ai/patterns/use-case-pattern.md` for this command handler"

---

## Domain Terms

- **Case** — central aggregate (code: `Case`, not `Matter` or `Ticket`)
- **Matter Wall** — case-level access control
- **Client** — legal services recipient
- **Workflow** — automation (FastAPI decides, n8n orchestrates)
- **Summary** — AI output requiring attorney approval

Glossary: `.ai/memory/GLOSSARY.md`

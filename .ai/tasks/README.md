# LexFlow AI — AI Task Prompts

**Version:** 1.0 · **Last Updated:** 2026-07-06

Reusable, copy-paste-ready prompt templates for AI-assisted engineering on LexFlow AI. Each template uses `{{variable}}` placeholders — replace before sending to your AI assistant.

---

## How to Use

1. **Pick a task** from the index below.
2. **Fill in variables** — replace every `{{...}}` with your specific values.
3. **Load context** — attach or reference files listed in the task's "Context to Load" section.
4. **Run the prompt** — paste into Cursor, Claude, or your preferred AI tool.
5. **Verify output** — use the task's verification checklist before committing.

---

## Context Hierarchy

Always load context in this order (most specific wins):

| Priority | Path | Purpose |
|----------|------|---------|
| 1 | `.ai/memory/` | Session memory, decisions, preferences |
| 2 | `.ai/rules/` | Project-specific AI rules and constraints |
| 3 | `docs/` | Canonical architecture and product documentation |
| 4 | Source code | Implementation under `apps/`, `services/`, `workers/`, `n8n/` |

---

## Platform Invariants (All Tasks)

These apply to every task prompt — do not violate:

1. **Business logic in FastAPI** — never in n8n or the frontend
2. **n8n is private** — orchestration only; not publicly accessible
3. **Async AI** — all LLM calls via queue/worker; human-in-the-loop for legal outputs
4. **Matter walls** — case-level access control; 404 (not 403) on unauthorized GET
5. **Immutable audit** — append-only audit logs for significant actions
6. **Event-driven** — transactional outbox → RabbitMQ → Celery workers
7. **No application code in `.ai/`** — prompts and docs only
8. **RFC before code** — major features need Accepted RFC in `docs/18-rfc/`

---

## Task Index

| Task | File | When to Use |
|------|------|-------------|
| Create API endpoint | [create-api.md](./create-api.md) | New REST endpoint in FastAPI |
| Create UI component/page | [create-ui.md](./create-ui.md) | New Next.js page or component |
| Create database table | [create-database-table.md](./create-database-table.md) | New schema, table, or migration |
| Create n8n workflow | [create-workflow.md](./create-workflow.md) | New orchestration workflow |
| Review code | [review-code.md](./review-code.md) | PR or diff review |
| Review security | [review-security.md](./review-security.md) | Security-focused review |
| Generate unit tests | [generate-unit-tests.md](./generate-unit-tests.md) | pytest or Vitest unit tests |
| Generate integration tests | [generate-integration-tests.md](./generate-integration-tests.md) | API integration + matter wall tests |
| Generate Playwright tests | [generate-playwright-tests.md](./generate-playwright-tests.md) | E2E browser tests |
| Generate documentation | [generate-documentation.md](./generate-documentation.md) | Docs for new feature or change |
| **Create RFC** | [create-rfc.md](./create-rfc.md) | **Major feature — before any implementation** |
| **Verify platform readiness** | [verify-platform-readiness.md](./verify-platform-readiness.md) | **Before auth, RBAC, domain, business logic** |

---

## Variable Conventions

| Variable | Description | Example |
|----------|-------------|---------|
| `{{feature_name}}` | Human-readable feature name | Case deadline reminders |
| `{{bounded_context}}` | DDD bounded context | `case_management` |
| `{{resource_name}}` | API resource (plural) | `case-deadlines` |
| `{{schema_name}}` | PostgreSQL schema | `cases` |
| `{{table_name}}` | Database table (plural snake_case) | `case_deadlines` |
| `{{workflow_slug}}` | n8n workflow identifier | `deadline-reminder-v1` |
| `{{file_paths}}` | Comma-separated paths to review | `apps/api/src/api/v1/cases.py` |
| `{{branch_name}}` | Git branch | `feat/case-deadline-api` |
| `{{ticket_id}}` | Issue/ticket reference | `LEX-142` |

---

## Related Resources

- [Engineering Handbook](../handbook/engineering-handbook.md)
- [Development Lifecycle](../handbook/development-lifecycle.md)
- [Definition of Ready](../handbook/definition-of-ready.md)
- [Definition of Done](../handbook/definition-of-done.md)
- [RFC Process](../handbook/rfc-process.md)
- [Documentation Index](../../docs/README.md)

# Task: Create API Endpoint

**LexFlow AI** — AI prompt template for new FastAPI REST endpoints.

---

## Prompt (Copy-Paste Ready)

```
You are implementing a new REST API endpoint for LexFlow AI, an enterprise AI automation platform for law firms.

## Feature
{{feature_name}}

## Endpoint Specification
- Method: {{http_method}}
- Path: /api/v1/{{resource_path}}
- Bounded context: {{bounded_context}}
- Ticket: {{ticket_id}}

## Context to Load
Read these before writing any code:

1. `.ai/memory/` — project memory and recent decisions
2. `.ai/rules/` — AI coding rules for this repo
3. `docs/04-api/rest-standards.md` — REST conventions and response envelope
4. `docs/04-api/error-handling.md` — RFC 7807 error catalog
5. `docs/04-api/authentication.md` — JWT and session handling
6. `docs/04-api/authorization-rbac.md` — RBAC matrix and matter walls
7. `docs/02-domain/{{bounded_context}}-aggregate.md` or relevant aggregate doc
8. `docs/02-domain/domain-events.md` — if endpoint emits events
9. `docs/13-decisions/` — especially ADR-001 (modular monolith), ADR-005 (JWT), ADR-007 (404 deny)
10. Existing code: `apps/api/src/api/v1/`, `services/{{bounded_context}}/`

## Constraints
- Business logic MUST live in `services/{{bounded_context}}/application/` — route handlers are thin
- Use Pydantic v2 models for request/response — never return ORM models directly
- Follow `{ data, meta }` response envelope per rest-standards.md
- Case-scoped endpoints MUST enforce matter walls — return 404 (not 403) on unauthorized GET
- Emit domain events via transactional outbox (ADR-006) when state changes
- AI endpoints MUST return 202 Accepted with job ID (ADR-004) — never synchronous LLM calls
- Internal n8n webhooks go in `apps/api/src/api/v1/internal/` — excluded from public OpenAPI
- No secrets in code; use pydantic-settings for configuration
- Line length 100; ruff + mypy strict

## Step-by-Step Instructions
1. **Domain** — Define or extend entities, value objects, and repository interfaces in `services/{{bounded_context}}/domain/`
2. **Application** — Create command/query handler in `services/{{bounded_context}}/application/`
3. **Infrastructure** — Implement repository methods in `services/{{bounded_context}}/infrastructure/` if needed
4. **API models** — Add request/response Pydantic schemas (separate from domain models)
5. **Router** — Add thin route handler in `apps/api/src/api/v1/{{router_file}}.py`
6. **Dependencies** — Wire DI: db session, current user, authorization checks
7. **Events** — If mutating: publish domain event through outbox in same transaction
8. **OpenAPI** — Ensure endpoint appears in generated spec with correct tags and examples
9. **Tests** — Plan unit tests (application layer) and integration tests (see generate-integration-tests.md)
10. **Docs** — Update `docs/04-api/endpoints-{{resource_group}}.md` if endpoint is public

## Output Format
Deliver in this order:

### 1. Design Summary
- Endpoint contract (method, path, auth requirements)
- Matter wall / RBAC rules applied
- Domain events emitted (if any)
- Files to create or modify (bullet list with paths)

### 2. Implementation
- Complete code for each file (not pseudocode)
- Alembic migration reference if schema change needed (link to separate migration PR)

### 3. OpenAPI Fragment
- YAML or JSON snippet for the new operation

### 4. Test Plan
- Unit test cases (names + what they assert)
- Integration test cases including matter wall matrix rows

### 5. Documentation Updates
- Exact sections to add/change in docs/

## Verification Checklist
- [ ] Route handler delegates to application use case — no business logic in handler
- [ ] Request/response use Pydantic models with validation
- [ ] Success response uses `{ data, meta }` envelope
- [ ] Errors use RFC 7807 format with correct status codes
- [ ] Matter wall enforced for case-scoped resources (404 on GET deny)
- [ ] Audit log entry on significant mutations
- [ ] Domain events published via outbox (if applicable)
- [ ] No synchronous LLM calls
- [ ] OpenAPI spec updated
- [ ] No secrets or hardcoded credentials
- [ ] Follows naming conventions (kebab-case routes, snake_case Python)
- [ ] ADR compliance noted (list relevant ADR numbers)
```

---

## Example Variables

| Variable | Example Value |
|----------|---------------|
| `{{feature_name}}` | Create case deadline with reminder scheduling |
| `{{http_method}}` | POST |
| `{{resource_path}}` | cases/{case_id}/deadlines |
| `{{bounded_context}}` | case_management |
| `{{router_file}}` | cases |
| `{{resource_group}}` | cases |
| `{{ticket_id}}` | LEX-142 |

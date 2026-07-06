# Task: Generate Integration Tests

**LexFlow AI** — AI prompt template for API integration tests with Testcontainers.

---

## Prompt (Copy-Paste Ready)

```
You are generating integration tests for LexFlow AI, an enterprise AI automation platform for law firms.

## Target
- Endpoint(s): {{endpoint_paths}}
- Bounded context: {{bounded_context}}
- Ticket: {{ticket_id}}

## Context to Load
Read these before writing tests:

1. `.ai/memory/` — project memory and recent decisions
2. `.ai/rules/` — AI coding rules for this repo
3. `docs/10-testing/integration-testing.md` — Testcontainers setup and matter wall matrix
4. `docs/10-testing/test-data.md` — factories and seed data
5. `docs/04-api/endpoints-{{resource_group}}.md` — API contract with examples
6. `docs/04-api/authorization-rbac.md` — RBAC matrix
7. `docs/04-api/error-handling.md` — status codes (404 vs 403)
8. `docs/08-security/matter-walls.md` — matter wall rules
9. `docs/13-decisions/007-matter-walls-404-deny.md`
10. Existing tests: `tests/integration/`, `apps/api/tests/`

## Constraints
- Use Testcontainers for PostgreSQL, Redis, RabbitMQ — no in-memory DB shortcuts
- Matter wall tests are NON-NEGOTIABLE on every PR touching authorization
- Test at API layer — FastAPI is the security boundary
- 404 (not 403) for unauthorized case GET requests
- Assert audit log entry on `denied_matter_wall`
- Use factories — no hardcoded UUIDs or real client data
- Each test creates its own data; no shared state between tests
- Target: < 5 min total integration suite
- Test IDs: `TEST-INT-{category}-{number}` (e.g., `TEST-INT-MW-001`)

## Step-by-Step Instructions
1. **API contract** — Read endpoint doc; list all request/response variants
2. **Auth matrix** — Map roles × participant states × expected responses
3. **Matter wall matrix** — For each case-scoped endpoint:
   - Participant → 200/201
   - Non-participant → 404 on GET
   - Non-participant → 403 on POST/PUT/DELETE (if applicable)
   - Audit log on deny
4. **Fixtures** — Set up Testcontainers, test client, auth helpers, factories
5. **Happy path** — CRUD lifecycle with authorized user
6. **Validation** — Invalid input returns 422 with RFC 7807 body
7. **Authorization** — Parameterized tests across RBAC roles
8. **Matter walls** — Full matrix per integration-testing.md
9. **Events** — Verify outbox entries for mutating operations
10. **Cleanup** — Tests are isolated; no manual teardown needed

## Output Format

### 1. Test Matrix
| Test ID | Endpoint | Role | Participant? | Method | Expected Status | Audit? |
|---------|----------|------|--------------|--------|-----------------|--------|

### 2. Fixture Setup
Complete conftest.py additions or test-level fixtures.

### 3. Test Implementation
Complete test file(s) with parameterized tests where applicable.

### 4. Factory Requirements
New factories or seed data needed.

### 5. Run Commands
```bash
make test-integration
# or
pytest tests/integration/test_{{resource}}.py -v --tb=short
```

## Verification Checklist
- [ ] Testcontainers used (not mocks for DB)
- [ ] Matter wall matrix complete for case-scoped endpoints
- [ ] 404 asserted on unauthorized GET (not 403)
- [ ] Audit log asserted on matter wall deny
- [ ] RBAC parameterized across roles
- [ ] RFC 7807 error format validated
- [ ] Response envelope `{ data, meta }` validated
- [ ] Factories used for test data
- [ ] Tests are isolated and deterministic
- [ ] Test IDs follow `TEST-INT-*` convention
- [ ] No real client data or production credentials
- [ ] Outbox/event assertions for mutations
```

---

## Example Variables

| Variable | Example Value |
|----------|---------------|
| `{{endpoint_paths}}` | POST/GET/PUT/DELETE /api/v1/cases/{case_id}/deadlines |
| `{{bounded_context}}` | case_management |
| `{{resource_group}}` | cases |
| `{{ticket_id}}` | LEX-142 |

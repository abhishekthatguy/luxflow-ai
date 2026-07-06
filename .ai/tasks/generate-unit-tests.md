# Task: Generate Unit Tests

**LexFlow AI** — AI prompt template for pytest and Vitest unit tests.

---

## Prompt (Copy-Paste Ready)

```
You are generating unit tests for LexFlow AI, an enterprise AI automation platform for law firms.

## Target
- Component: {{component_name}}
- Layer: {{test_layer}} (domain | application | infrastructure | frontend)
- File under test: {{file_path}}
- Ticket: {{ticket_id}}

## Context to Load
Read these before writing tests:

1. `.ai/memory/` — project memory and recent decisions
2. `.ai/rules/` — AI coding rules for this repo
3. `docs/10-testing/unit-testing.md` — pytest and Vitest standards
4. `docs/10-testing/test-data.md` — factories and seed data
5. `docs/02-domain/` — domain invariants for the bounded context
6. `docs/08-security/matter-walls.md` — if testing authorization logic
7. Source file: `{{file_path}}`
8. Existing tests in same module's `tests/` directory

## Constraints
### Backend (pytest)
- Domain tests: ZERO framework imports, ZERO database — pure Python only
- Application tests: mock repository interfaces, test use case behavior
- Target: 90% line coverage on domain + application layers
- Use factories from `tests/factories/` — no hardcoded UUIDs
- TDD mandatory for authorization/matter wall logic
- Test behavior, not implementation details
- Fast: each test < 100ms; full suite < 10s

### Frontend (Vitest)
- React Testing Library — query by role/label, not test IDs
- Mock API client, not fetch internals
- Test user-visible behavior and accessibility
- Server Components: test via integration or snapshot of rendered output

## Step-by-Step Instructions
1. **Read source** — Identify public API, invariants, edge cases, error paths
2. **Test matrix** — List scenarios: happy path, validation errors, auth denies, edge cases
3. **Fixtures** — Use or create factories; avoid shared mutable state
4. **Domain tests** — Test entity invariants, value object validation, event creation
5. **Application tests** — Test command/query handlers with mocked repos
6. **Frontend tests** — Test render, interaction, loading/error/empty states
7. **Naming** — `test_{behavior}_when_{condition}_then_{expected}`
8. **Assertions** — One logical assertion per test; descriptive failure messages
9. **Coverage** — Identify uncovered branches after writing tests
10. **No I/O** — Unit tests must not hit database, network, or filesystem

## Output Format

### 1. Test Plan
| Test ID | Scenario | Input | Expected | Priority |
|---------|----------|-------|----------|----------|

### 2. Test Implementation
Complete test file(s) with imports, fixtures, and all test functions.

### 3. Factory Updates (if needed)
New or modified factory definitions.

### 4. Coverage Report
- Lines/branches covered
- Remaining gaps (if any) with justification

### 5. Run Commands
```bash
# Backend
pytest services/{{bounded_context}}/tests/test_{{module}}.py -v

# Frontend
cd apps/web && npx vitest run src/{{component_path}}.test.tsx
```

## Verification Checklist
- [ ] Tests follow naming convention
- [ ] Domain tests have no framework/DB imports
- [ ] Factories used instead of hardcoded data
- [ ] Happy path and error paths covered
- [ ] Authorization logic tested with TDD (if applicable)
- [ ] No network or database calls in unit tests
- [ ] Tests are deterministic (no time/random without seeding)
- [ ] Each test is independent (no order dependency)
- [ ] Assertions test behavior, not internal state
- [ ] Run commands provided and verified locally
```

---

## Example Variables

| Variable | Example Value |
|----------|---------------|
| `{{component_name}}` | CreateCaseDeadlineCommand |
| `{{test_layer}}` | application |
| `{{file_path}}` | services/case_management/application/commands/create_deadline.py |
| `{{bounded_context}}` | case_management |
| `{{component_path}}` | components/cases/DeadlineForm |
| `{{ticket_id}}` | LEX-142 |

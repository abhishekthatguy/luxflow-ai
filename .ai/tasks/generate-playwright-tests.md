# Task: Generate Playwright Tests

**LexFlow AI** — AI prompt template for E2E browser tests.

---

## Prompt (Copy-Paste Ready)

```
You are generating Playwright E2E tests for LexFlow AI, an enterprise AI automation platform for law firms.

## Target
- User journey: {{journey_name}}
- Critical path: {{is_critical}} (yes | no)
- Pages involved: {{page_paths}}
- Ticket: {{ticket_id}}

## Context to Load
Read these before writing tests:

1. `.ai/memory/` — project memory and recent decisions
2. `.ai/rules/` — AI coding rules for this repo
3. `docs/10-testing/e2e-testing.md` — Playwright standards and critical journeys
4. `docs/12-ui/page-architecture.md` — route structure
5. `docs/12-ui/accessibility.md` — WCAG requirements
6. `docs/08-security/matter-walls.md` — UI must not leak unauthorized data
7. `docs/04-api/endpoints-{{api_resource}}.md` — API contract
8. Existing specs: `tests/e2e/`

## Constraints
- E2E tests run against staging environment post-deploy
- Target: ~10 critical journeys total; each < 15 min suite
- Playwright best practices: auto-waiting, no arbitrary sleeps
- Page Object Model for reusable page interactions
- Auth: use test user fixtures with known roles — never production credentials
- Matter wall E2E: verify unauthorized user sees empty/error state, no case ID in network tab
- No flaky tests — fix root cause; quarantine only with ticket and owner
- Screenshots on failure; trace on retry
- Accessibility: basic axe-core scan on critical pages

## Step-by-Step Instructions
1. **Journey map** — Define user steps from login to outcome
2. **Preconditions** — Seed data requirements (cases, users, roles)
3. **Page objects** — Create/update POM classes in `tests/e2e/pages/`
4. **Auth setup** — Storage state or login fixture per role
5. **Happy path** — Full journey with assertions at each step
6. **Error paths** — Validation errors, unauthorized access, network failure
7. **Matter wall** — Unauthorized user journey (no data leakage)
8. **Accessibility** — axe-core scan on key pages
9. **Stability** — Use `getByRole`, `getByLabel`; avoid CSS selectors
10. **CI config** — Document staging URL, parallelization, retry policy

## Output Format

### 1. Journey Description
| Step | Action | Assertion | Page Object Method |
|------|--------|-----------|-------------------|

### 2. Page Objects
Complete POM classes for involved pages.

### 3. Test Spec
Complete `.spec.ts` file with describe blocks and test cases.

### 4. Fixtures & Seed Data
Auth fixtures and data setup requirements.

### 5. Run Commands
```bash
# Local against staging
npx playwright test tests/e2e/{{spec_name}}.spec.ts --project=chromium

# With trace
npx playwright test tests/e2e/{{spec_name}}.spec.ts --trace on
```

### 6. CI Integration
GitHub Actions step reference or update needed.

## Verification Checklist
- [ ] Page Object Model used
- [ ] No arbitrary `waitForTimeout` — use Playwright auto-waiting
- [ ] Selectors use `getByRole` / `getByLabel` (accessible)
- [ ] Auth fixture with role-appropriate test user
- [ ] Matter wall journey: no unauthorized data visible
- [ ] Screenshots on failure configured
- [ ] Test is deterministic (no date/time dependencies without mocking)
- [ ] Seed data documented
- [ ] Critical journey registered in e2e-testing.md index
- [ ] axe-core accessibility scan included
- [ ] No production URLs or credentials
```

---

## Example Variables

| Variable | Example Value |
|----------|---------------|
| `{{journey_name}}` | Attorney creates case deadline and receives confirmation |
| `{{is_critical}}` | yes |
| `{{page_paths}}` | /cases/[caseId]/deadlines |
| `{{api_resource}}` | cases |
| `{{spec_name}}` | case-deadlines |
| `{{ticket_id}}` | LEX-142 |

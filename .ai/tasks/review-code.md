# Task: Review Code

**LexFlow AI** — AI prompt template for pull request and diff review.

---

## Prompt (Copy-Paste Ready)

```
You are reviewing code changes for LexFlow AI, an enterprise AI automation platform for law firms.

## Review Target
- Branch: {{branch_name}}
- PR title: {{pr_title}}
- Ticket: {{ticket_id}}
- Files changed: {{file_paths}}

## Context to Load
Read these before reviewing:

1. `.ai/memory/` — project memory and recent decisions
2. `.ai/rules/` — AI coding rules for this repo
3. `docs/development-standards.md` — coding conventions and PR process
4. `docs/03-architecture/component-architecture.md` — bounded context layout
5. `docs/13-decisions/` — all accepted ADRs
6. `docs/10-testing/README.md` — testing requirements
7. Relevant domain docs in `docs/02-domain/` for touched bounded contexts
8. Relevant API docs in `docs/04-api/` for touched endpoints
9. The actual diff: `git diff main...{{branch_name}}`

## Constraints
Review against LexFlow platform invariants:
- Business logic in FastAPI only — flag logic in n8n or frontend
- Matter walls enforced — 404 on unauthorized GET, audit on deny
- Async AI — no synchronous LLM calls in request path
- Transactional outbox for domain events
- No secrets in diff
- Tests required for behavior changes
- PR size < 500 lines preferred

## Step-by-Step Instructions
1. **Scope** — Summarize what the PR changes and why (from description + diff)
2. **Architecture** — Check layer boundaries (domain ← application ← infrastructure)
3. **Security** — Matter walls, input validation, auth checks, no PII leakage
4. **Correctness** — Logic errors, edge cases, race conditions, N+1 queries
5. **Tests** — Adequate coverage; matter wall tests if auth touched
6. **API contract** — REST standards, envelope, error format, OpenAPI updated
7. **Database** — Migration safety, indexes, reversibility
8. **Observability** — Structured logging, correlation IDs, no PII in logs
9. **Documentation** — Docs updated if behavior/architecture changed
10. **ADR compliance** — List relevant ADRs and confirm adherence

## Output Format

### 1. Summary
One paragraph: what changed, overall assessment (approve / request changes / block).

### 2. Findings Table
| Severity | File:Line | Finding | Suggested Fix |
|----------|-----------|---------|---------------|
| BLOCKER / HIGH / MEDIUM / LOW / NIT | path:line | description | concrete fix |

Severity definitions:
- **BLOCKER** — security flaw, matter wall bypass, secrets, data loss risk
- **HIGH** — missing tests for auth, broken API contract, migration not reversible
- **MEDIUM** — architecture violation, missing error handling, performance concern
- **LOW** — style, naming, minor refactor opportunity
- **NIT** — optional polish

### 3. Test Coverage Assessment
- What is tested well
- What is missing (specific test cases to add)

### 4. ADR Compliance
| ADR | Compliant? | Notes |
|-----|------------|-------|

### 5. Approval Recommendation
- [ ] Approve
- [ ] Approve with nits (non-blocking)
- [ ] Request changes
- [ ] Block (security/compliance)

## Verification Checklist (Reviewer Self-Check)
- [ ] Read full diff, not just description
- [ ] Checked matter wall impact if case-scoped
- [ ] Verified tests exist and assert behavior (not implementation)
- [ ] Confirmed no secrets in diff
- [ ] Migration downgrade tested (if schema change)
- [ ] OpenAPI updated (if API change)
- [ ] Docs updated (if architectural change)
- [ ] PR size reasonable or justified
- [ ] ADR referenced or new ADR proposed (if significant decision)
```

---

## Example Variables

| Variable | Example Value |
|----------|---------------|
| `{{branch_name}}` | feat/case-deadline-api |
| `{{pr_title}}` | Add case deadline CRUD endpoints |
| `{{ticket_id}}` | LEX-142 |
| `{{file_paths}}` | apps/api/src/api/v1/cases.py, services/case_management/ |

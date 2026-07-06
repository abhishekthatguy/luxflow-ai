# Definition of Done (DoD)

**LexFlow AI** — When Work Is Complete and Shippable  
**Version:** 1.0 · **Last Updated:** 2026-07-06

---

## Purpose

Definition of Done defines the criteria that must be met **before a pull request is merged and an issue is closed**. It ensures consistent quality, security, and documentation across all LexFlow AI engineering work.

---

## Universal Criteria (All PRs)

- [ ] **Acceptance criteria met** — every criterion from the issue is satisfied
- [ ] **PR description complete** — uses [pull-request-template](../templates/pull-request-template.md); explains *why*
- [ ] **CI pipeline passes** — lint, type check, unit tests, integration tests
- [ ] **Code review approved** — minimum 1 approval from peer engineer
- [ ] **No secrets in diff** — TruffleHog / manual check
- [ ] **Branch up to date** — rebased or merged with `main`; no conflicts
- [ ] **PR size reasonable** — < 500 lines changed, or justified and reviewed with extra care
- [ ] **Issue linked** — `Closes #{{issue_number}}` or `Relates to #{{issue_number}}`

---

## Code Quality

- [ ] **Follows coding standards** — `docs/development-standards.md`
- [ ] **Layer boundaries respected** — domain ← application ← infrastructure
- [ ] **No business logic in n8n or frontend** — platform invariant
- [ ] **Linting passes** — ruff, mypy, ESLint, Prettier, tsc
- [ ] **No TODO without ticket** — every TODO references an issue number
- [ ] **No commented-out code** — removed or justified in PR description

---

## Testing

- [ ] **Unit tests added/updated** — for changed behavior in domain and application layers
- [ ] **Integration tests added/updated** — for new/changed API endpoints
- [ ] **Matter wall tests pass** — non-negotiable if authorization touched
- [ ] **Coverage maintained** — domain + application line coverage does not decrease
- [ ] **Tests are deterministic** — no flaky tests introduced
- [ ] **Test IDs assigned** — `TEST-{layer}-{category}-{number}` for integration tests

| Change Type | Minimum Tests Required |
|-------------|----------------------|
| Domain logic | Unit tests for invariants and edge cases |
| API endpoint | Integration test (happy path + validation + auth) |
| Case-scoped endpoint | Matter wall matrix (participant + non-participant) |
| UI component | Vitest render + interaction tests |
| Critical user journey | Playwright E2E (may be follow-up PR with ticket) |
| Bug fix | Regression test proving fix |

---

## Security

- [ ] **Matter walls enforced** — case-scoped paths check participant membership
- [ ] **404 on unauthorized GET** — not 403 (ADR-007)
- [ ] **Audit log on deny** — `denied_matter_wall` event recorded
- [ ] **Input validation** — all external input validated (API, webhooks, uploads)
- [ ] **No PII in logs** — structured logging with redaction
- [ ] **Security review complete** — if ticket was security-sensitive (per DoR)
- [ ] **Container scan clean** — no CRITICAL/HIGH vulnerabilities (Trivy)

---

## API Changes

- [ ] **REST standards followed** — `docs/04-api/rest-standards.md`
- [ ] **Response envelope** — `{ data, meta }` on success
- [ ] **RFC 7807 errors** — correct status codes and error bodies
- [ ] **OpenAPI spec updated** — endpoint appears in generated spec
- [ ] **SDK/types regenerated** — if public API contract changed

---

## Database Changes

- [ ] **Alembic migration included** — with working `upgrade()` and `downgrade()`
- [ ] **Migration reviewed** — zero-downtime safe; indexes on FKs
- [ ] **Schema docs updated** — `docs/05-database/{schema}-schema.md`
- [ ] **Tested locally** — `alembic upgrade head` and `alembic downgrade -1`

---

## n8n Workflow Changes

- [ ] **No business logic in workflow** — ADR-002
- [ ] **JSON committed** — `n8n/workflows/{domain}/{slug}.json`
- [ ] **Schemas committed** — `n8n/schemas/{slug}/`
- [ ] **Catalog updated** — `docs/06-workflows/workflow-catalog.md`
- [ ] **No secrets in JSON** — credential references only
- [ ] **Local round-trip tested** — trigger → n8n → callback

---

## AI Changes

- [ ] **Async processing** — 202 Accepted pattern (ADR-004)
- [ ] **PII redacted** — before LLM calls
- [ ] **HITL gate** — attorney approval for legal outputs
- [ ] **Prompt versioned** — in prompt registry if new/modified
- [ ] **Usage metering** — token tracking implemented

---

## Documentation

- [ ] **Docs updated in same PR** — if behavior, API, schema, or architecture changed
- [ ] **ADR created** — if significant architectural decision (per [adr-process.md](./adr-process.md))
- [ ] **Section README updated** — new doc added to index
- [ ] **No stale references** — links point to current paths (13-decisions/, not adr/)

---

## Deployment Readiness

- [ ] **Environment variables documented** — new config in `.env.example` or settings docs
- [ ] **Backward compatible** — or migration plan documented for breaking changes
- [ ] **Feature flag** — if partial rollout needed
- [ ] **Rollback plan** — for schema changes and workflow promotions
- [ ] **Runbook updated** — if operational procedure changes

---

## Post-Merge (Before Closing Issue)

- [ ] **Deployed to staging** — auto or manual
- [ ] **E2E passes on staging** — for user-facing changes
- [ ] **No P1/P2 alerts** — 24h monitoring for production deploys
- [ ] **Issue closed** — with release version or deploy date noted

---

## DoD Exceptions

Exceptions require tech lead approval and documented justification:

| Exception | Requires | Tracking |
|-----------|----------|----------|
| E2E deferred | Staging verified manually | Follow-up issue with deadline |
| ADR deferred | Design doc in PR description | ADR issue created before merge |
| Coverage decrease | Justification + plan to restore | Issue created with deadline |

**Security and matter wall criteria have NO exceptions.**

---

## DoD Checklist Template (for PR comments)

```markdown
## Definition of Done

- [ ] Acceptance criteria met
- [ ] Tests: unit {{✓/✗}} · integration {{✓/✗}} · matter wall {{✓/✗/N/A}}
- [ ] Security review {{✓/✗/N/A}}
- [ ] Docs updated {{✓/✗/N/A}}
- [ ] OpenAPI updated {{✓/✗/N/A}}
- [ ] Migration tested up/down {{✓/✗/N/A}}
- [ ] CI green
- [ ] Approved by {{reviewer}}

**Ready to merge:** Yes / No
```

---

## References

- [Definition of Ready](./definition-of-ready.md)
- [Development Lifecycle](./development-lifecycle.md)
- [Engineering Handbook](./engineering-handbook.md)
- [Testing Documentation](../../docs/10-testing/README.md)
- [PR Template](../templates/pull-request-template.md)

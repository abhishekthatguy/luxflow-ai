# Code Review Checklist — LexFlow AI

**Applies to:** Authors and reviewers on every PR  
**Docs:** `docs/10-testing/`, `docs/08-security/`, `docs/development-standards.md`

---

## Purpose

Actionable checklists for PR authors and reviewers. A PR that fails security or matter wall checks **must not merge** regardless of feature completeness.

---

## Author Pre-Submit Checklist

### General

- [ ] PR description explains **why**, not only what
- [ ] PR size < 500 lines (prefer < 200)
- [ ] Conventional commit messages on branch
- [ ] No unrelated changes bundled
- [ ] CI green locally (`make lint`, `make test`)

### Architecture

- [ ] Business logic in `services/`, not n8n or frontend
- [ ] Domain layer has no framework imports
- [ ] New code in correct folder per `folder-structure.md`
- [ ] ADR linked if architectural decision

### API (if applicable)

- [ ] OpenAPI updated
- [ ] RFC 7807 errors
- [ ] Success envelope on 2xx
- [ ] Idempotency on mutating endpoints
- [ ] Versioning impact assessed

### Security (always)

- [ ] No secrets in diff
- [ ] Matter wall tests pass
- [ ] 404 on unauthorized case GET (not 403)
- [ ] Authorization in FastAPI
- [ ] Audit on mutations
- [ ] PII not in logs or error messages

### Database (if applicable)

- [ ] Alembic migration with downgrade
- [ ] Indexes for new query patterns
- [ ] FK `ON DELETE` documented

### Tests

- [ ] Unit tests for domain/application changes
- [ ] Integration tests for new endpoints
- [ ] Matter wall matrix updated for case routes
- [ ] Coverage does not decrease on domain layers

### Docs & Rules

- [ ] `docs/` updated if behavior/architecture changed
- [ ] `.ai/rules/` updated if conventions changed
- [ ] n8n catalog updated if workflow added

---

## Reviewer Checklist

### 1. Correctness

- [ ] Code does what PR claims
- [ ] Edge cases handled (empty, not found, conflict)
- [ ] Async paths return 202 where required (AI)
- [ ] Idempotency and concurrency considered

### 2. Security (Blocker)

- [ ] Matter walls enforced server-side
- [ ] No authorization in frontend only
- [ ] No secrets or credentials
- [ ] Input validated at boundary
- [ ] SQL injection / XSS vectors absent
- [ ] File upload limits enforced

### 3. Architecture (Blocker if violated)

- [ ] No business logic in n8n Code/Postgres nodes
- [ ] No domain logic in route handlers
- [ ] Events via outbox, not direct MQ publish
- [ ] Workers call use cases, not duplicate logic

### 4. API Contract

- [ ] Matches `docs/04-api/` standards
- [ ] Breaking changes flagged — require version bump
- [ ] Error types use registered URIs

### 5. Tests

- [ ] Tests assert behavior, not implementation
- [ ] Auth changes have failing-test-first evidence
- [ ] Matter wall tests cover new case endpoints
- [ ] No skipped tests without ticket

### 6. Performance

- [ ] No obvious N+1 queries
- [ ] Pagination on list endpoints
- [ ] Appropriate indexes for new filters

### 7. Observability

- [ ] Structured logs with `correlationId`
- [ ] No PII in log fields
- [ ] Errors logged at appropriate level

---

## Severity Guide

| Finding | Severity | Action |
|---------|----------|--------|
| Matter wall bypass | **Blocker** | Request changes; no merge |
| Secret in code | **Blocker** | Request changes; rotate secret |
| Business logic in n8n | **Blocker** | Refactor to FastAPI |
| Missing matter wall test on case endpoint | **Blocker** | Add tests |
| Missing error handling | Major | Request changes |
| Missing loading state (UI) | Minor | Comment; may merge |
| Naming inconsistency | Nit | Optional fix |

---

## Review Do / Don't

| Do | Don't |
|----|-------|
| Block merge on security/architecture violations | Approve "will fix in follow-up" for matter walls |
| Ask for test evidence on auth changes | Assume frontend hides unauthorized data |
| Link relevant ADR or doc section | Rubber-stamp large PRs without reading |
| Suggest smaller PR split | Bikeshed formatting over security |

---

## n8n Workflow Review (Additional)

- [ ] No Postgres, LLM, or business Code nodes
- [ ] HMAC on trigger and callback
- [ ] `correlationId` in payload
- [ ] FastAPI callback handler exists
- [ ] No secrets in JSON
- [ ] Slug matches file name and catalog

---

## AI Prompt/Template Review (Additional)

- [ ] New version created (not overwrite)
- [ ] `requires_approval` set correctly
- [ ] PII variables documented
- [ ] Case-scoped context only
- [ ] `prompt_version` stored on output

---

## Post-Merge Verification

| Change Type | Follow-Up |
|-------------|-----------|
| API change | Confirm SDK types in next frontend PR |
| Migration | Verify staging deploy + rollback tested |
| n8n workflow | Staging smoke test before prod promotion |
| Auth rule | Security reviewer notified |

---

## References

- [docs/10-testing/README.md](../../docs/10-testing/README.md)
- [docs/10-testing/integration-testing.md](../../docs/10-testing/integration-testing.md)
- [docs/08-security/matter-walls.md](../../docs/08-security/matter-walls.md)
- [security-rules.md](./security-rules.md)
- [git-workflow.md](./git-workflow.md)

# Branch Naming — LexFlow AI

**Applies to:** All feature, fix, and chore branches  
**Docs:** `docs/development-standards.md`

---

## Purpose

Consistent branch names for traceability, CI filtering, and clean git history.

---

## Format

```
{type}/{short-description}
```

| Part | Rule |
|------|------|
| `type` | Required prefix — see table |
| `short-description` | kebab-case, 2–5 words, lowercase |
| Separators | Hyphens only — no underscores or spaces |
| Length | ≤ 50 characters total |

---

## Types

| Type | When | Example |
|------|------|---------|
| `feat` | New feature or capability | `feat/case-intake-api` |
| `fix` | Bug fix | `fix/matter-wall-bypass` |
| `chore` | Maintenance, deps, tooling | `chore/upgrade-fastapi` |
| `docs` | Documentation only | `docs/api-versioning-guide` |
| `refactor` | Code restructure, no behavior change | `refactor/case-repository-port` |
| `test` | Test-only additions/fixes | `test/matter-wall-matrix` |
| `ci` | CI/CD pipeline changes | `ci/testcontainers-cache` |
| `hotfix` | Urgent production fix | `hotfix/auth-token-expiry` |

---

## Scope Hints (Optional in Description)

Embed bounded context in description when helpful:

```
feat/cases-participant-assignment
fix/documents-upload-validation
feat/ai-summary-approval-flow
fix/workflows-n8n-callback-hmac
docs/security-matter-walls-update
```

---

## Good vs Bad

| Good | Bad | Why |
|------|-----|-----|
| `feat/case-intake-api` | `feature/case-intake` | Use standard type `feat` |
| `fix/matter-wall-404` | `fix_matter_wall` | No underscores |
| `chore/ruff-upgrade` | `chore/update` | Too vague |
| `docs/adr-009-event-versioning` | `john/case-work` | No person names |
| `test/integration-matter-walls` | `feat/fix-tests-and-add-case-api` | One concern per branch |
| `hotfix/dlq-backlog` | `main-fix` | Must use type prefix |

---

## Branch Lifecycle

| Rule | Detail |
|------|--------|
| Branch from | `main` |
| Max lifetime | 3 days (prefer ≤ 1 day) |
| Rebase/merge `main` | Before PR if branch > 1 day old |
| Delete after merge | Yes — remote and local |

---

## Multi-Contributor Conventions

| Do | Don't |
|----|-------|
| One branch per PR / concern | Long-lived personal branches (`alex/dev`) |
| Descriptive names for CI logs | `feat/wip` or `feat/changes` |
| `hotfix/` only for production incidents | `hotfix/` for normal bugs (use `fix/`) |

---

## Special Branches

| Branch | Purpose | Protected? |
|--------|---------|------------|
| `main` | Production-ready trunk | Yes |
| `release/*` | Release preparation (if used) | Yes |
| `env/staging` | **Not used** — deploy from `main` | — |

LexFlow uses **trunk-based development** — no long-lived `develop` branch.

---

## AI Assistant Guidance

When creating branches:

1. Infer type from task (feature → `feat`, bug → `fix`)
2. Keep description specific but short
3. Use bounded context noun when clear
4. Never use `main`, `master`, or person names

```bash
# Examples
git checkout -b feat/cases-deadline-reminders
git checkout -b fix/auth-refresh-token-rotation
git checkout -b test/matter-wall-document-search
```

---

## Checklist

- [ ] Correct type prefix
- [ ] kebab-case description
- [ ] ≤ 50 characters
- [ ] Branched from latest `main`
- [ ] Single concern per branch

---

## References

- [git-workflow.md](./git-workflow.md)
- [commit-message-standards.md](./commit-message-standards.md)
- [docs/development-standards.md](../../docs/development-standards.md)

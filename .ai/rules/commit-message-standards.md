# Commit Message Standards — LexFlow AI

**Applies to:** All commits (squashed into PR title/body on merge)  
**Docs:** `docs/development-standards.md`

---

## Purpose

[Conventional Commits](https://www.conventionalcommits.org/) format for readable history, automated changelog, and clear PR squash messages.

---

## Format

```
<type>(<scope>): <subject>

[optional body]

[optional footer]
```

| Part | Rule |
|------|------|
| `type` | Required — see table below |
| `scope` | Recommended — bounded context or app |
| `subject` | Imperative mood, ≤ 72 chars, no period |
| `body` | Explain **why** when not obvious |
| `footer` | `BREAKING CHANGE:`, `Refs: ADR-00N`, issue links |

---

## Types

| Type | When |
|------|------|
| `feat` | New feature or endpoint |
| `fix` | Bug fix |
| `docs` | Documentation only |
| `chore` | Deps, tooling, CI — no production logic change |
| `refactor` | Code change — no feature/fix |
| `test` | Tests only |
| `perf` | Performance improvement |
| `ci` | CI/CD pipeline changes |
| `build` | Build system, Docker |

---

## Scopes (Recommended)

| Scope | Area |
|-------|------|
| `cases` | Case management context |
| `documents` | Document management |
| `auth` | Identity, JWT, RBAC |
| `ai` | AI worker, prompts, RAG |
| `workflows` | n8n bridge, executions |
| `api` | FastAPI app (cross-cutting) |
| `web` | Next.js frontend |
| `db` | Migrations, schema |
| `n8n` | Workflow JSON only |
| `deps` | Dependency upgrades |

---

## Examples

### Good

```
feat(cases): add case intake API endpoint

Implements POST /api/v1/cases with matter wall checks
and audit logging per MW-008.

Refs: ADR-001, ADR-007
```

```
fix(auth): prevent matter wall bypass on document download

Non-participants received 200 on direct document URL.
Now returns 404 and logs denied_matter_wall.

Fixes TEST-INT-MW-014
```

```
chore(deps): upgrade FastAPI to 0.115

No API contract changes.
```

```
docs(api): add versioning guide for v1 deprecation policy
```

### Bad

```
fix stuff
```
```
updated files
```
```
WIP
```
```
Feat: Added the case intake API endpoint for the new feature request from legal ops team and also fixed a small bug
```

---

## Breaking Changes

```
feat(api)!: rename case status field to caseStatus

BREAKING CHANGE: response field `status` renamed to `caseStatus`.
Clients must update before v1 sunset 2027-01-01.

Requires ADR approval for v2 migration.
```

| Rule | Detail |
|------|--------|
| `!` after type/scope | Signals breaking change |
| `BREAKING CHANGE:` footer | Required description |
| Breaking API changes | Require versioning review — see `api-standards.md` |

---

## Squash Merge

PR squash commit message becomes:

```
feat(cases): add case intake API endpoint (#123)

Implements POST /api/v1/cases with matter wall checks.
```

| Do | Don't |
|----|-------|
| Make PR title follow conventional format | Squash to "Merge pull request #123" |
| Include why in PR body | List every intermediate WIP commit |

---

## Commit Rules

| Do | Don't |
|----|-------|
| Atomic commits — one logical change | Mix unrelated changes |
| Imperative subject: "add", "fix", "remove" | Past tense: "added", "fixed" |
| Reference ADR/issue when relevant | Vague "see PR" only |
| Sign commits if team policy requires | Commit secrets or `.env` |

---

## AI Assistant Guidance

When committing on behalf of user:

1. Use conventional format
2. Scope matches primary changed area
3. Subject ≤ 72 characters
4. Body explains why if not obvious
5. Never commit `.env`, credentials, or secrets
6. Only commit when user explicitly requests

---

## Checklist

- [ ] Type is valid
- [ ] Scope matches changed area
- [ ] Subject is imperative and concise
- [ ] Body explains why (if needed)
- [ ] Breaking changes marked with `!` and footer
- [ ] No secrets in commit

---

## References

- [git-workflow.md](./git-workflow.md)
- [branch-naming.md](./branch-naming.md)
- [docs/development-standards.md](../../docs/development-standards.md)
- [Conventional Commits](https://www.conventionalcommits.org/)

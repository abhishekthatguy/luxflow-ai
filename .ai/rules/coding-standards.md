# Coding Standards — LexFlow AI

**Applies to:** All code in the monorepo (Python, TypeScript, Terraform, n8n JSON)  
**Docs:** `docs/development-standards.md`, `docs/13-decisions/`

---

## Purpose

Define cross-stack coding conventions so AI assistants and engineers produce consistent, reviewable, secure code. Layer-specific rules extend this file — they do not replace it.

---

## Technology Stack (Locked)

| Layer | Technology | Notes |
|-------|-----------|-------|
| Backend | Python 3.12+, FastAPI, Pydantic v2 | Strict mypy |
| ORM | SQLAlchemy 2.0, Alembic | Migrations required for schema changes |
| Frontend | Next.js App Router, React, TypeScript strict | Server Components default |
| UI | Tailwind CSS, ShadCN UI | Do not edit generated ShadCN primitives |
| State | Zustand (UI), React Query (server) | See `frontend-standards.md` |
| Queue | Celery, RabbitMQ | Workers call `services/` use cases |
| Database | PostgreSQL 16+, pgvector | UUID PKs everywhere |
| Linting | ruff, mypy, ESLint, Prettier | CI must pass |

---

## Universal Do / Don't

| Do | Don't |
|----|-------|
| Put business logic in `services/{context}/` | Put domain rules in n8n, frontend, or route handlers |
| Write tests for changed behavior | Merge without tests for new endpoints or auth paths |
| Use typed interfaces (Pydantic, TypeScript) | Use `dict`, `Any`, or untyped JSON blobs at boundaries |
| Keep PRs under 200 lines when possible | Submit 500+ line PRs without splitting |
| Update docs/rules when behavior changes | Ship silent contract changes |
| Use environment variables for config | Hardcode URLs, keys, or tenant IDs |
| Follow Conventional Commits | Use vague messages like "fix stuff" |

---

## Code Style

### Python

| Tool | Setting |
|------|---------|
| Formatter | `ruff format` |
| Linter | `ruff check` |
| Types | `mypy --strict` (domain + application) |
| Line length | 100 characters |

### TypeScript

| Tool | Setting |
|------|---------|
| Formatter | Prettier |
| Linter | ESLint strict |
| Types | `strict: true` in tsconfig |

---

## Architecture Boundaries

```
apps/api/          → Thin HTTP adapters only
services/          → All business logic (DDD + hexagonal)
workers/           → Message consumers → application use cases
apps/web/          → UI + React Query; no domain rules
n8n/workflows/     → HTTP orchestration only
```

**Dependency rule:** `domain ← application ← infrastructure`. Never reverse.

---

## Good vs Bad Patterns

### Route Handler (Bad → Good)

```python
# BAD — business logic in handler
@router.post("/cases")
async def create_case(body: dict, db: Session = Depends(get_db)):
    if body["practice_area"] not in ALLOWED_AREAS:
        raise HTTPException(400, "invalid")
    case = Case(**body)
    db.add(case)
    db.commit()
    return case

# GOOD — thin handler delegates to use case
@router.post("/cases", status_code=201)
async def create_case(
    body: CreateCaseRequest,
    handler: CreateCaseHandler = Depends(get_create_case_handler),
    user: CurrentUser = Depends(get_current_user),
) -> Envelope[CaseResponse]:
    result = await handler.execute(CreateCaseCommand.from_request(body, user))
    return envelope(data=CaseResponse.from_domain(result))
```

### Frontend Data Fetch (Bad → Good)

```typescript
// BAD — raw fetch in component, no types
function CaseList() {
  const [cases, setCases] = useState([]);
  useEffect(() => {
    fetch("/api/v1/cases").then(r => r.json()).then(setCases);
  }, []);
}

// GOOD — React Query hook with generated types
function CaseList() {
  const { data, isLoading, error } = useCases();
  if (isLoading) return <CaseListSkeleton />;
  if (error) return <ApiErrorPanel error={error} />;
  return <CaseTable cases={data.data} />;
}
```

---

## Environment & Configuration

| Rule | Detail |
|------|--------|
| `.env.example` | Documents all vars; no real values |
| Secrets in deployed envs | AWS Secrets Manager only |
| Local `.env` | Never committed |
| Settings loading | Pydantic Settings (backend); validated env module (frontend) |

---

## Documentation in Code

| Do | Don't |
|----|-------|
| Comment non-obvious legal/business invariants | Narrate obvious code |
| Link ADR numbers in module docstrings for architectural patterns | Duplicate full ADR text in code |
| Keep README in each deployable app | Leave deployable units undocumented |

---

## PR Author Checklist

- [ ] Explains **why**, not only what
- [ ] Tests added/updated for changed behavior
- [ ] Matter wall tests pass if touching authorization
- [ ] No secrets in diff
- [ ] Migration with downgrade if schema changed
- [ ] OpenAPI updated if API changed
- [ ] Relevant `.ai/rules/` updated if conventions changed
- [ ] ADR created if significant architectural decision

---

## PR Size Guidelines

| Size | Lines | Target Review |
|------|-------|---------------|
| Small (preferred) | < 200 | Same day |
| Medium | 200–500 | 1–2 days |
| Large (avoid) | > 500 | Split before review |

---

## References

- [backend-standards.md](./backend-standards.md)
- [frontend-standards.md](./frontend-standards.md)
- [docs/development-standards.md](../../docs/development-standards.md)
- [docs/13-decisions/](../../docs/13-decisions/)

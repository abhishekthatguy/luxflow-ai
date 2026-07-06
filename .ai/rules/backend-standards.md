# Backend Standards — LexFlow AI

**Applies to:** `apps/api/`, `services/`, `workers/`, `apps/api/alembic/`  
**Docs:** `docs/03-architecture/component-architecture.md`, `docs/02-domain/`, `docs/04-api/`

---

## Purpose

Standards for FastAPI adapters, DDD bounded contexts, hexagonal architecture, and Celery workers. **All business logic lives in `services/`** — not in route handlers, not in n8n, not duplicated in workers.

---

## Layer Model

```
apps/api/src/api/v1/     HTTP adapters — thin
services/{context}/
  domain/                Entities, VOs, events, repository ports — pure Python
  application/           Commands, queries, handlers — orchestration
  infrastructure/        SQLAlchemy, S3, HTTP clients — adapters
workers/celery/tasks/    Consumers — call application handlers
```

**Dependency rule:** `domain ← application ← infrastructure`. Domain imports nothing from FastAPI, SQLAlchemy, Celery, or boto3.

---

## FastAPI Conventions

| Rule | Detail |
|------|--------|
| Thin handlers | Validate request → call handler → wrap envelope |
| Pydantic v2 | Request/response models at HTTP boundary |
| DI | `Depends()` for sessions, current user, handlers |
| Routers | One file per resource group (`cases.py`, `documents.py`) |
| Internal webhooks | `api/v1/internal/` — excluded from public OpenAPI |
| Auth | JWT on all routes except `/auth/*`, `/health` |
| Idempotency | `Idempotency-Key` on mutating POST/PUT/PATCH |

### Handler Pattern

```python
# GOOD — adapter only
@router.post("/cases/{caseId}/participants", status_code=201)
async def assign_participant(
    case_id: UUID,
    body: AssignParticipantRequest,
    handler: AssignParticipantHandler = Depends(...),
    user: CurrentUser = Depends(get_current_user),
) -> Envelope[ParticipantResponse]:
    result = await handler.execute(
        AssignParticipantCommand(case_id=case_id, user_id=body.user_id, actor=user)
    )
    return envelope(data=ParticipantResponse.from_domain(result))
```

---

## Domain Layer (`domain/`)

| Do | Don't |
|----|-------|
| Define entities with invariants | Import SQLAlchemy models |
| Raise domain exceptions (`CaseNotFound`) | Raise `HTTPException` |
| Emit domain events as dataclasses | Publish to RabbitMQ directly |
| Define repository **ports** (Protocol/ABC) | Implement SQL in domain |

```python
# GOOD — domain entity enforces invariant
@dataclass
class Case:
    id: CaseId
    status: CaseStatus
    participants: tuple[Participant, ...]

    def assign_participant(self, user_id: UserId, role: ParticipantRole, actor: UserId) -> CaseParticipantAssigned:
        if not self._actor_can_manage_participants(actor):
            raise InsufficientParticipantPermission()
        # ... invariant checks
        return CaseParticipantAssigned(case_id=self.id, user_id=user_id, role=role)
```

---

## Application Layer (`application/`)

| Responsibility | Location |
|----------------|----------|
| Command/query DTOs | `application/commands/`, `application/queries/` |
| Use case handlers | Same directory or `handlers/` |
| Transaction boundary | Handler opens UoW, commits once |
| Authorization check | Before domain mutation (matter walls) |
| Outbox write | Same transaction as aggregate persist |

```python
# GOOD — application orchestrates, domain decides
class CreateCaseHandler:
    def __init__(self, repo: CaseRepository, authz: AuthorizationService, outbox: Outbox):
        ...

    async def execute(self, cmd: CreateCaseCommand) -> Case:
        await self.authz.require_permission(cmd.actor, "case:create")
        case = Case.create(cmd.to_props())
        await self.repo.save(case)
        await self.outbox.publish(case.collect_events())
        return case
```

---

## Infrastructure Layer (`infrastructure/`)

| Adapter Type | Examples |
|--------------|----------|
| Repositories | `SqlAlchemyCaseRepository` |
| External HTTP | `N8nBridgeClient`, `MicrosoftGraphClient` |
| Storage | `S3DocumentStore` |
| LLM | `AzureOpenAIProvider` implements `LLMProvider` port |

| Do | Don't |
|----|-------|
| Map ORM ↔ domain entities in repository | Return ORM models to application layer |
| Implement ports defined in domain | Leak infrastructure types into handlers |

---

## Authorization & Matter Walls

Enforcement order (see `security-rules.md`):

1. JWT authentication
2. RBAC permission check
3. Matter wall ABAC (if `assigned` scope)
4. 404 on GET deny for non-participants (ADR-007)

Authorization lives in `services/identity/` and middleware — **not** in individual route if/else blocks scattered across files.

---

## Database & Migrations

| Rule | Detail |
|------|--------|
| Alembic only | Every schema change has `upgrade()` + `downgrade()` |
| UUID PKs | All tables |
| Schema separation | `identity`, `cases`, `documents`, etc. per ADR-003 |
| Indexes | `CREATE INDEX CONCURRENTLY` for large tables |
| No raw SQL in app code | Except reviewed reporting queries |

---

## Celery Workers

```python
# GOOD — worker delegates to application handler
@celery_app.task(bind=True, max_retries=3)
def process_ai_summary(self, job_id: str, correlation_id: str):
    with trace_context(correlation_id):
        handler = get_generate_summary_handler()  # wired via DI container
        handler.execute(GenerateSummaryCommand(job_id=job_id))
```

| Do | Don't |
|----|-------|
| Pass `correlation_id` in task headers | Lose trace linkage |
| Retry transient infra errors | Retry domain validation failures |
| Call same handler as API would | Reimplement business rules in task |

---

## Event Publishing (ADR-006)

| Do | Don't |
|----|-------|
| Write events to outbox in same DB transaction | Publish to RabbitMQ before commit |
| Use past-tense event names | Use present tense |
| Include `schemaVersion` in payload | Break consumers silently |

---

## Tooling

| Tool | Scope |
|------|-------|
| `ruff format` + `ruff check` | All Python |
| `mypy --strict` | `domain/`, `application/` |
| `pytest` | Unit tests colocated in `services/{context}/tests/` |

---

## Backend PR Checklist

- [ ] Business logic in `services/`, not router
- [ ] Domain layer has zero framework imports
- [ ] Pydantic DTOs at HTTP boundary only
- [ ] Matter wall tests if case-scoped endpoint
- [ ] Migration with downgrade if schema changed
- [ ] Outbox used for new domain events
- [ ] Internal webhooks HMAC-verified, not in public OpenAPI

---

## References

- [docs/03-architecture/component-architecture.md](../../docs/03-architecture/component-architecture.md)
- [docs/04-api/authentication.md](../../docs/04-api/authentication.md)
- [docs/04-api/authorization-rbac.md](../../docs/04-api/authorization-rbac.md)
- [docs/13-decisions/001-modular-monolith.md](../../docs/13-decisions/001-modular-monolith.md)
- [api-standards.md](./api-standards.md)
- [security-rules.md](./security-rules.md)

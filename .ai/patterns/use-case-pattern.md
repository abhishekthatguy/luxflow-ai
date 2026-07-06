# Use Case Pattern

## Purpose

Application-layer command or query that orchestrates domain logic, owns the transaction boundary, emits outbox events, and writes audit entries.

## Applies To

`services/{context}/application/commands/` and `.../queries/`

## Mandatory Reads

- `docs/03-architecture/component-architecture.md`
- `docs/development-standards.md` §5.1
- `.ai/patterns/domain-entity-pattern.md`
- `.ai/patterns/repository-pattern.md`
- `.ai/patterns/outbox-event-pattern.md`

---

## Structure Template

```
services/case_management/
├── application/
│   ├── commands/
│   │   ├── create_case.py      # CreateCaseCommand + CreateCaseHandler
│   │   └── update_case_status.py
│   ├── queries/
│   │   ├── get_case.py
│   │   └── list_cases.py
│   └── dto/
│       └── case_dto.py         # Application-level read models
├── domain/
│   └── ...                     # Entities, events, repo interfaces
└── infrastructure/
    └── repositories/
        └── sqlalchemy_case_repo.py
```

---

## Pseudocode Outline

```
# --- Command DTO (immutable) ---
@dataclass(frozen=True)
class CreateCaseCommand:
    firm_id: UUID
    actor_id: UUID
    client_id: UUID
    title: str
    practice_area: str
    correlation_id: UUID


# --- Handler ---
class CreateCaseHandler:
    def __init__(self, db: Session, case_repo: CaseRepository, outbox: OutboxWriter, audit: AuditWriter):
        ...

    async def handle(self, cmd: CreateCaseCommand) -> CaseDto:
        async with transaction(self.db):
            # 1. Domain factory — enforces invariants
            case = Case.create(
                firm_id=cmd.firm_id,
                client_id=cmd.client_id,
                title=cmd.title,
                practice_area=cmd.practice_area,
            )

            # 2. Persist aggregate
            await self.case_repo.save(case)

            # 3. Collect domain events from aggregate
            events = case.pull_domain_events()

            # 4. Write outbox rows (same transaction)
            for evt in events:
                self.outbox.append(evt, correlation_id=cmd.correlation_id)

            # 5. Audit log
            self.audit.record(
                action="case.created",
                actor_id=cmd.actor_id,
                resource_type="case",
                resource_id=case.id,
                after_state=case.to_audit_snapshot(),
            )

        # 6. Return DTO (not entity)
        return CaseDto.from_entity(case)


# --- Query (read-only, no events) ---
class GetCaseQuery:
    def __init__(self, db: Session, case_repo: CaseRepository):
        ...

    async def execute(self, case_id: UUID) -> CaseDto | None:
        case = await self.case_repo.get_by_id(case_id)
        return CaseDto.from_entity(case) if case else None
```

---

## Invariants

| # | Rule |
|---|------|
| 1 | One handler class per command/query |
| 2 | Commands mutate + emit events; queries read-only |
| 3 | Transaction wraps persist + outbox + audit |
| 4 | Return DTOs — never leak entities to API layer |
| 5 | Domain validates invariants — application orchestrates |
| 6 | No FastAPI imports |
| 7 | Inject repositories via interfaces |

---

## Anti-Patterns

- Multiple unrelated operations in one handler
- Event publish directly to RabbitMQ (bypass outbox)
- Query that mutates state
- Importing SQLAlchemy models into handler body (use repo)

---

## Checklist

- [ ] Command/Query in correct bounded context package
- [ ] Handler depends on domain interfaces, not concrete infra
- [ ] Transaction boundary explicit
- [ ] Domain events pulled and written to outbox
- [ ] Audit entry for mutations
- [ ] Unit tests with fake repos
- [ ] Integration test with real DB

# Domain Entity Pattern

## Purpose

Pure Python aggregate root with invariants, state transitions, and domain event collection. Zero framework dependencies.

## Applies To

`services/{context}/domain/entities/` and `.../value_objects/`

## Mandatory Reads

- Relevant aggregate doc in `docs/02-domain/` (e.g. `case-aggregate.md`)
- `docs/02-domain/domain-events.md`
- `docs/02-domain/ubiquitous-language.md`

---

## Structure Template

```
services/case_management/domain/
├── entities/
│   └── case.py              # Aggregate root
├── value_objects/
│   ├── case_status.py       # Enum or value object
│   └── case_title.py        # Validated primitive wrapper
├── events/
│   └── case_created.py      # Event dataclass / typed dict factory
├── repositories/
│   └── case_repository.py   # ABC interface only
└── policies/
    └── status_transition.py # Pure domain rules
```

---

## Pseudocode Outline

```
# --- Value Object ---
@dataclass(frozen=True)
class CaseTitle:
    value: str

    def __post_init__(self):
        if not (1 <= len(self.value) <= 500):
            raise DomainError("case.title.invalid_length")


# --- Aggregate Root ---
class Case:
    def __init__(self, id, firm_id, client_id, title, status, ...):
        self._id = id
        self._events: list[DomainEvent] = []
        ...

    @classmethod
    def create(cls, firm_id, client_id, title, practice_area, ...) -> "Case":
        # Factory — only way to create new aggregate
        validated_title = CaseTitle(title)
        case = cls(
            id=uuid4(),
            firm_id=firm_id,
            status=CaseStatus.INTAKE,
            title=validated_title.value,
            ...
        )
        case._record(CaseCreated(
            aggregate_id=case.id,
            firm_id=firm_id,
            payload={...},
        ))
        return case

    def transition_to(self, new_status: CaseStatus, actor_id: UUID) -> None:
        # State machine — delegate to policy
        if not StatusTransitionPolicy.can_transition(self.status, new_status):
            raise DomainError("case.status.invalid_transition")
        old = self.status
        self._status = new_status
        self._record(CaseStatusChanged(
            aggregate_id=self.id,
            payload={"from": old, "to": new_status},
        ))

    def pull_domain_events(self) -> list[DomainEvent]:
        events, self._events = self._events, []
        return events

    def _record(self, event: DomainEvent) -> None:
        self._events.append(event)


# --- Repository Interface (ABC) ---
class CaseRepository(Protocol):
    async def get_by_id(self, case_id: UUID) -> Case | None: ...
    async def save(self, case: Case) -> None: ...
```

---

## Invariants

| # | Rule |
|---|------|
| 1 | No imports from fastapi, sqlalchemy, celery, pydantic |
| 2 | Aggregates enforce invariants — callers cannot bypass |
| 3 | Events recorded inside aggregate methods |
| 4 | Factory methods for creation — no public setters for illegal states |
| 5 | Ubiquitous language from glossary — consistent naming |
| 6 | IDs are UUID at domain boundary |

---

## Anti-Patterns

- Anemic domain (all logic in service, entity is data bag)
- ORM model as domain entity
- Emitting events outside aggregate
- Public mutable status field without transition method

---

## Checklist

- [ ] Matches aggregate doc invariants and state machine
- [ ] Events named `{Aggregate}{PastTense}` per domain-events.md
- [ ] Value objects validate on construction
- [ ] Repository interface in domain, impl in infrastructure
- [ ] Unit tests for invariants and transitions
- [ ] No framework imports in domain package

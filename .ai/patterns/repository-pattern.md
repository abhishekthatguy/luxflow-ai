# Repository Pattern

## Purpose

Persist and rehydrate domain aggregates behind an interface. Infrastructure implements mapping between domain entities and SQLAlchemy ORM models.

## Applies To

- Interface: `services/{context}/domain/repositories/`
- Implementation: `services/{context}/infrastructure/repositories/`
- ORM models: `services/{context}/infrastructure/models/` or shared `apps/api/src/models/`

## Mandatory Reads

- `docs/05-database/` schema doc for context
- `.ai/patterns/domain-entity-pattern.md`
- `docs/development-standards.md` §7

---

## Structure Template

```
services/case_management/
├── domain/repositories/
│   └── case_repository.py         # Protocol / ABC
└── infrastructure/
    ├── models/
    │   └── case_model.py          # SQLAlchemy ORM
    ├── repositories/
    │   └── sqlalchemy_case_repo.py
    └── mappers/
        └── case_mapper.py         # entity ↔ ORM
```

---

## Pseudocode Outline

```
# --- ORM Model (infrastructure only) ---
class CaseModel(Base):
    __tablename__ = "cases"
    __table_args__ = {"schema": "cases"}
    id: Mapped[UUID] = mapped_column(primary_key=True)
    firm_id: Mapped[UUID] = mapped_column(ForeignKey("identity.firms.id"))
    status: Mapped[str]
    ...


# --- Mapper ---
class CaseMapper:
    @staticmethod
    def to_domain(row: CaseModel) -> Case:
        return Case(
            id=row.id,
            firm_id=row.firm_id,
            status=CaseStatus(row.status),
            ...
        )

    @staticmethod
    def to_orm(entity: Case) -> CaseModel:
        return CaseModel(
            id=entity.id,
            firm_id=entity.firm_id,
            status=entity.status.value,
            ...
        )


# --- Repository Implementation ---
class SqlAlchemyCaseRepository(CaseRepository):
    def __init__(self, session: Session):
        self._session = session

    async def get_by_id(self, case_id: UUID) -> Case | None:
        row = self._session.get(CaseModel, case_id)
        return CaseMapper.to_domain(row) if row else None

    async def save(self, case: Case) -> None:
        existing = self._session.get(CaseModel, case.id)
        if existing:
            # update fields from entity
            ...
        else:
            self._session.add(CaseMapper.to_orm(case))
        # flush within caller's transaction — no commit here

    async def list_by_firm(self, firm_id: UUID, filters: CaseFilters) -> list[Case]:
        stmt = select(CaseModel).where(CaseModel.firm_id == firm_id)
        # apply filters, pagination
        rows = self._session.scalars(stmt).all()
        return [CaseMapper.to_domain(r) for r in rows]
```

---

## Invariants

| # | Rule |
|---|------|
| 1 | Repository does not commit — use case owns transaction |
| 2 | Never return ORM models to application layer |
| 3 | Mapper is sole translation boundary |
| 4 | Queries use SQLAlchemy 2.0 style (`select()`) |
| 5 | Indexes per `docs/05-database/indexing-strategy.md` |
| 6 | FK `ON DELETE` documented in migration |

---

## Anti-Patterns

- Repository with business logic / event emission
- Leaking `Session` to domain
- N+1 queries without eager loading strategy
- Raw SQL in repository (except approved reporting)

---

## Checklist

- [ ] Interface in domain package
- [ ] Implementation in infrastructure only
- [ ] Mapper tested both directions
- [ ] Schema matches `docs/05-database/*-schema.md`
- [ ] List queries support pagination filters
- [ ] Integration test round-trip save/load

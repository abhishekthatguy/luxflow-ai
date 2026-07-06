# API Endpoint Pattern

## Purpose

Thin FastAPI route that validates HTTP input, enforces authZ, delegates to application layer, and returns standard envelope.

## Applies To

`apps/api/src/api/v1/{resource}.py` — public routes under `/api/v1/*`.

## Mandatory Reads

- `docs/04-api/rest-standards.md`
- `docs/04-api/error-handling.md`
- `docs/04-api/authorization-rbac.md`
- `docs/08-security/matter-walls.md`
- `.ai/patterns/use-case-pattern.md`

---

## Structure Template

```
apps/api/src/api/v1/
├── cases.py              # Router: cases resource group
├── dependencies.py       # get_current_user, get_db, authorize_case
└── schemas/
    └── cases.py          # Request/Response Pydantic models (HTTP layer only)

apps/api/src/api/v1/cases.py
├── APIRouter(prefix="/cases", tags=["cases"])
├── @router.get("")           → list query use case
├── @router.post("")          → create command use case
├── @router.get("/{case_id}") → get query use case
└── @router.patch("/{case_id}") → update command use case
```

---

## Pseudocode Outline

```
# --- Router setup ---
router = APIRouter(prefix="/cases", tags=["cases"])

# --- LIST ---
@router.get("")
async def list_cases(
    filters: CaseListParams = Depends(),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Envelope[CaseListResponse]:
    # 1. RBAC: require permission "case:read:firm" or scoped variant
    authorize(current_user, "case:read", scope=filters.scope)

    # 2. Delegate — NO business logic here
    result = await ListCasesQuery(db=db, user=current_user).execute(filters)

    # 3. Map domain DTO → response schema
    return envelope(data=CaseListResponse.from_dto(result), meta=pagination_meta(result))


# --- CREATE (mutating) ---
@router.post("", status_code=201)
async def create_case(
    body: CreateCaseRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    idempotency_key: str | None = Header(None, alias="Idempotency-Key"),
) -> Envelope[CaseResponse]:
    # 1. RBAC
    authorize(current_user, "case:create")

    # 2. Idempotency check (if key present)
    if idempotency_key:
        cached = check_idempotency(db, idempotency_key)
        if cached: return cached

    # 3. Map request → command
    cmd = CreateCaseCommand(
        firm_id=current_user.firm_id,
        actor_id=current_user.id,
        **body.model_dump(),
    )

    # 4. Execute use case (transaction inside)
    case_dto = await CreateCaseHandler(db).handle(cmd)

    # 5. Store idempotency response if key present
    # 6. Return envelope
    return envelope(data=CaseResponse.from_dto(case_dto))


# --- GET BY ID (case-scoped — matter wall) ---
@router.get("/{case_id}")
async def get_case(
    case_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Envelope[CaseResponse]:
    # 1. RBAC
    authorize(current_user, "case:read", scope="assigned")

    # 2. Matter wall — 404 if not participant (ADR-007)
    ensure_case_access(db, current_user, case_id)  # raises 404

    # 3. Query
    dto = await GetCaseQuery(db).execute(case_id)
    if not dto: raise not_found("Case", case_id)

    return envelope(data=CaseResponse.from_dto(dto))
```

---

## Invariants

| # | Rule |
|---|------|
| 1 | Handler ≤ ~15 lines — delegate immediately |
| 2 | `{ data, meta }` envelope on success |
| 3 | RFC 7807 on errors via global exception handlers |
| 4 | `correlation_id` from middleware in logs |
| 5 | Mutations → audit log (inside use case) |
| 6 | Register in OpenAPI with examples |
| 7 | Case-scoped routes: wall check before query |

---

## Anti-Patterns

- ORM queries in router
- Returning raw dicts without envelope
- 403 for matter wall deny on case resources
- Skipping idempotency on POST create
- Business validation only in Pydantic (domain must re-validate)

---

## Checklist

- [ ] Router file matches resource group in `docs/04-api/endpoints-*.md`
- [ ] Request/response schemas separate from domain models
- [ ] RBAC dependency or explicit authorize call
- [ ] Matter wall on case-scoped routes
- [ ] Use case invoked for all non-trivial logic
- [ ] Status codes per REST standards
- [ ] OpenAPI tag and operationId set
- [ ] Integration test: happy + 401 + 403 + 404 wall

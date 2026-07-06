# Example: Matter Wall Check

## Scenario

**Actor:** Attorney A (not a participant on Case X)  
**Goal:** Attempt to read case details — must receive **404 Not Found** (not 403)  
**Trigger:** `GET /api/v1/cases/{caseId}` with valid JWT and sufficient RBAC scope

---

## Flow

```mermaid
flowchart TB
    REQ[GET /cases/{id}] --> AUTH[JWT Valid?]
    AUTH -->|No| R401[401 Unauthorized]
    AUTH -->|Yes| RBAC{RBAC: case:read<br/>permission?}
    RBAC -->|No| R403[403 Forbidden]
    RBAC -->|Yes| SCOPE{Scope = firm/admin?}
    SCOPE -->|Yes| ALLOW[Allow — Handler]
    SCOPE -->|assigned/own| ABAC{Participant on case<br/>OR firm-wide read override?}
    ABAC -->|Participant| ALLOW
    ABAC -->|Override — read only| ALLOW
    ABAC -->|Neither| R404[404 Not Found]
    R403 --> AUD[Audit Log]
    R404 --> AUD
    ALLOW --> AUD
```

---

## Structural Annotation

| Layer | Artifact | Notes |
|-------|----------|-------|
| Middleware | `apps/api/src/middleware/auth.py` | JWT extraction |
| RBAC | `services/identity_access/` permission check | Role → permission matrix |
| ABAC | `services/case_management/domain/policies/matter_wall.py` | Participant lookup |
| Dependency | `apps/api/dependencies.py` `ensure_case_access(case_id)` | Raises 404 |
| Repository | `[INF]` case_participants table query | Indexed by case_id + user_id |
| Frontend | `[UI]` 404 → generic NotFound component | No "access denied" wording |
| Tests | `tests/integration/test_matter_walls.py` | Role × participant matrix |

---

## Decision Table

| RBAC | Scope | Participant | Override | HTTP |
|------|-------|-------------|----------|------|
| deny | — | — | — | 403 |
| allow | firm/admin | — | — | 200 |
| allow | assigned | yes | — | 200 |
| allow | assigned | no | yes (read) | 200 |
| allow | assigned | no | no | **404** |

---

## Cross-References

- `docs/08-security/matter-walls.md`
- `docs/04-api/authorization-rbac.md`
- `docs/13-decisions/007-matter-walls-404-deny.md`
- `.ai/examples/example-create-case-api.md` (wall on create's case scope)

---

## Key Decisions Applied

| Rule | Application |
|------|-------------|
| ADR-007 | 404 not 403 for walled cases |
| Fail closed | Missing participant = deny |
| Frontend | Reflect permissions; never enforce |
| AI/RAG | Same check before retrieval |
| Audit | Log wall denial without leaking case title to unauthorized actor |

---

## Applies To (Non-Exhaustive)

All case-scoped resources:

- `/api/v1/cases/{caseId}/*`
- `/api/v1/cases/{caseId}/documents/*`
- `/api/v1/cases/{caseId}/ai/*`
- Document search results — filter walled cases server-side

---

## Test Matrix (Structural)

| # | Role | Participant | Override | Endpoint | Expected |
|---|------|-------------|----------|----------|----------|
| 1 | Attorney | yes | — | GET case | 200 |
| 2 | Attorney | no | no | GET case | 404 |
| 3 | Partner | no | yes | GET case | 200 |
| 4 | Paralegal | no | no | GET document | 404 |
| 5 | Admin | — | — | GET case | 200 (firm scope) |

---

## Anti-Patterns to Flag in Review

- Returning 403 with message "Not a participant"
- Including walled case IDs in list responses
- Client-side hiding only (API still returns 200)
- Skipping wall check on sub-resources (documents, AI jobs)

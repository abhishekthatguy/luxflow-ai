# API Standards — LexFlow AI

**Applies to:** `apps/api/src/api/v1/`, OpenAPI spec, `packages/sdk/`  
**Docs:** `docs/04-api/`

---

## Purpose

REST API conventions: resource design, response envelope, RFC 7807 errors, versioning, auth headers, and idempotency. All public routes under `/api/v1/*`.

---

## Base URL & Versioning

| Environment | Base URL |
|-------------|----------|
| Production | `https://api.lexflow.{firm-domain}/api/v1` |
| Staging | `https://api.staging.lexflow.{firm-domain}/api/v1` |
| Local | `http://localhost:8000/api/v1` |

| Path | Versioned? |
|------|------------|
| `/api/v1/*` | Yes — public API |
| `/api/v1/internal/*` | Tied to v1; not in public OpenAPI |
| `/health`, `/health/ready` | No |

**Ref:** `docs/04-api/versioning.md`

### Breaking vs Non-Breaking

| Non-Breaking (OK in v1) | Breaking (requires v2 + ADR) |
|-------------------------|------------------------------|
| Add optional request field | Rename/remove field |
| Add response field | Change field type |
| Add endpoint | Remove endpoint |
| Add enum value (additive) | Rename enum value |
| Bug fix restoring documented behavior | Change 404→403 for case deny |

---

## Resource Naming

| Rule | Example |
|------|---------|
| Plural nouns | `/cases`, `/documents` |
| UUID path params | `/cases/{caseId}` |
| Nested sub-resources | `/cases/{caseId}/tasks` |
| kebab-case actions | `/workflows/trigger` |
| camelCase JSON fields | `practiceArea`, `createdAt` |

---

## Success Response Envelope

All public success responses use:

```json
{
  "data": { },
  "meta": {
    "requestId": "uuid",
    "timestamp": "2026-07-06T12:00:00Z"
  }
}
```

Paginated collections add:

```json
{
  "data": [ ],
  "meta": {
    "requestId": "uuid",
    "pagination": {
      "page": 1,
      "pageSize": 25,
      "totalItems": 142,
      "totalPages": 6
    }
  }
}
```

| Do | Don't |
|----|-------|
| Wrap all public 2xx in envelope | Return raw arrays at top level |
| Include `requestId` in meta | Omit correlation ID |
| Use consistent pagination keys | Invent per-endpoint pagination shapes |

---

## Async AI Endpoints (ADR-004)

| Pattern | Detail |
|---------|--------|
| Submit | `POST` → `202 Accepted` with `{ jobId, status: "pending" }` |
| Poll | `GET /ai/jobs/{jobId}` |
| Cancel | `DELETE /ai/jobs/{jobId}` (if supported) |

```json
// 202 Response
{
  "data": {
    "jobId": "uuid",
    "status": "pending",
    "pollUrl": "/api/v1/ai/jobs/uuid"
  },
  "meta": { "requestId": "uuid" }
}
```

**Ref:** `docs/04-api/endpoints-ai.md`

---

## RFC 7807 Error Format

Content-Type: `application/problem+json`

```json
{
  "type": "https://lexflow.ai/errors/validation-failed",
  "title": "Validation Failed",
  "status": 422,
  "detail": "One or more fields failed validation.",
  "instance": "/api/v1/cases",
  "errors": [
    { "field": "practiceArea", "message": "Invalid practice area." }
  ],
  "meta": {
    "requestId": "uuid",
    "timestamp": "2026-07-06T12:00:00Z"
  }
}
```

### Status Code Mapping

| Status | When |
|--------|------|
| 400 | Malformed request |
| 401 | Missing/invalid JWT |
| 403 | RBAC denial (non-case resources) |
| 404 | Not found; **unauthorized case GET** (ADR-007) |
| 409 | Idempotency conflict; optimistic concurrency |
| 422 | Validation failure |
| 429 | Rate limit — include `Retry-After` |
| 500 | Unhandled server error — no stack trace in body |

**Ref:** `docs/04-api/error-handling.md`

---

## Required Headers

| Header | When | Detail |
|--------|------|--------|
| `Authorization` | All protected routes | `Bearer {accessToken}` |
| `X-Correlation-Id` | Recommended | UUID; server generates if absent |
| `Idempotency-Key` | Mutating POST/PUT/PATCH | UUID; 24h retention |
| `If-Match` | Optimistic concurrency | ETag from prior GET |
| `Content-Type` | Bodies | `application/json` |

---

## Authentication

- JWT access token + refresh token (ADR-005)
- Public routes: `/api/v1/auth/*`, `/health`
- Internal webhooks: HMAC signature, not JWT

**Ref:** `docs/04-api/authentication.md`

---

## Authorization

- RBAC matrix per role
- Matter walls for case-scoped resources
- 404 not 403 on unauthorized case **GET**

**Ref:** `docs/04-api/authorization-rbac.md`, `docs/08-security/matter-walls.md`

---

## OpenAPI

| Rule | Detail |
|------|--------|
| Every public route registered | With request/response examples |
| CI validates spec | No drift from committed generated types |
| Swagger UI | Disabled in production |
| Spec export | `/api/v1/openapi.json` |
| Codegen | `packages/sdk`, `packages/shared` |

---

## Do / Don't

| Do | Don't |
|----|-------|
| Return Pydantic response models | Return SQLAlchemy ORM objects |
| Document new endpoints in OpenAPI same PR | Ship undocumented routes |
| Use typed error `type` URIs | Generic `"error"` strings |
| Log errors with `requestId` | Expose internal exception messages |
| Audit all mutating operations | Skip audit on "internal" mutations |

---

## Good vs Bad Endpoint

```python
# BAD
@router.get("/getCase/{id}")
def get_case(id: str):
    return db.query(Case).filter_by(id=id).first()

# GOOD
@router.get("/cases/{caseId}", response_model=Envelope[CaseResponse])
async def get_case(
    case_id: UUID,
    handler: GetCaseHandler = Depends(...),
    user: CurrentUser = Depends(get_current_user),
) -> Envelope[CaseResponse]:
    case = await handler.execute(GetCaseQuery(case_id=case_id, actor=user))
    return envelope(data=CaseResponse.from_domain(case))
```

---

## API Change Checklist

- [ ] Follows resource naming conventions
- [ ] Success envelope on 2xx
- [ ] RFC 7807 on errors
- [ ] OpenAPI updated with examples
- [ ] Matter wall tests for case-scoped routes
- [ ] Idempotency on mutating endpoints
- [ ] Audit log on mutations
- [ ] Versioning impact assessed (breaking vs non-breaking)
- [ ] SDK types regenerated or updated

---

## References

- [docs/04-api/rest-standards.md](../../docs/04-api/rest-standards.md)
- [docs/04-api/error-handling.md](../../docs/04-api/error-handling.md)
- [docs/04-api/versioning.md](../../docs/04-api/versioning.md)
- [docs/04-api/webhooks-internal.md](../../docs/04-api/webhooks-internal.md)
- [error-handling.md](./error-handling.md)
- [security-rules.md](./security-rules.md)

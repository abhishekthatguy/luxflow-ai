# REST Standards

**LexFlow AI** — REST API Conventions  
**Version:** 1.0  
**Status:** Draft — Pre-Implementation  
**Last Updated:** 2026-07-06

---

## Purpose

Define the REST design standards for the LexFlow AI FastAPI API so that all endpoints are **consistent, predictable, and secure by default**. This document is the contract between backend implementers and API consumers (frontend, integrations, generated SDK).

---

## Scope

| In Scope | Out of Scope |
|----------|--------------|
| Resource naming, HTTP verb usage | Domain business rules (see [../02-domain/domain-model.md](../domain-model.md)) |
| Request/response envelope structure | Pydantic model implementation |
| RFC 7807 error format | Specific endpoint payloads (see endpoint docs) |
| Pagination, filtering, sorting conventions | GraphQL or gRPC |
| Idempotency and optimistic concurrency headers | WebSocket event payload schemas |

**Applies to:** All public routes under `/api/v1/*`  
**Partially applies to:** Internal routes under `/api/v1/internal/*` (errors and correlation ID; no public envelope on some webhook acks)

---

## Responsibilities

| Role | Responsibility |
|------|----------------|
| API developers | Implement every route per these standards; register in OpenAPI |
| Frontend developers | Parse envelope and errors consistently via generated client |
| Code reviewers | Reject PRs that introduce non-standard response shapes |
| CI pipeline | Validate OpenAPI spec, run contract tests against envelope schema |

---

## Architecture

LexFlow AI follows **resource-oriented REST** with a thin uniform envelope. Business logic remains in domain services (`services/`), not in route handlers.

```mermaid
flowchart LR
    subgraph HTTP["HTTP Layer — apps/api/api/v1/"]
        R[Router]
        H[Handler]
    end

    subgraph CrossCutting["Cross-Cutting"]
        ENV[Response Envelope]
        ERR[RFC 7807 Handler]
        PG[Pagination]
        IDEM[Idempotency Store]
    end

    subgraph Domain["Domain Layer — services/"]
        CMD[Command Handlers]
        QRY[Query Handlers]
    end

    R --> H
    H --> CMD
    H --> QRY
    H --> ENV
    H --> ERR
    H --> PG
    H --> IDEM
```

### Design Principles

| Principle | Implementation |
|-----------|----------------|
| Resource-oriented | Nouns for resources (`/cases`, `/documents`); verbs only for non-CRUD actions (`/workflows/trigger`) |
| Versioned | `/api/v1` prefix — see [versioning.md](./versioning.md) |
| Consistent | Uniform `{ data, meta }` envelope on success |
| Secure by default | Auth required except `/auth/*` and `/health` |
| Idempotent | `Idempotency-Key` on mutating POST/PUT/PATCH |
| Audited | All mutating operations write audit log entries |
| Documented | OpenAPI 3.1 with examples; TypeScript client generated in CI |

---

## Flow Diagrams

### Standard Success Response Construction

```mermaid
sequenceDiagram
    participant H as Route Handler
    participant S as Domain Service
    participant E as Envelope Builder
    participant C as Client

    H->>S: Execute command/query
    S-->>H: Domain result (Pydantic model)
    H->>E: wrap(data=result, request_id)
    E-->>H: { data, meta }
    H-->>C: 200/201 + JSON envelope
```

### Validation Failure → RFC 7807

```mermaid
sequenceDiagram
    participant C as Client
    participant H as Route Handler
    participant V as Pydantic Validator
    participant EH as Exception Handler

    C->>H: POST /api/v1/cases (invalid body)
    H->>V: Validate request model
    V-->>EH: ValidationError
    EH->>EH: Map to Problem Details
    EH-->>C: 422 + application/problem+json
```

---

## Resource Naming

### Rules

1. Use **plural nouns** for collections: `/cases`, `/clients`, `/documents`
2. Use **UUID path parameters** for resource identity: `/cases/{caseId}`
3. Nest sub-resources under their parent: `/cases/{caseId}/tasks`
4. Use **kebab-case** for multi-word action paths: `/workflows/trigger`, `/forgot-password`
5. Avoid verbs in collection paths except documented actions

### Examples

| Pattern | Example | Notes |
|---------|---------|-------|
| Collection | `GET /cases` | Paginated list |
| Item | `GET /cases/{id}` | Single resource |
| Sub-resource | `GET /cases/{id}/documents` | Scoped to parent |
| Action | `POST /cases/{id}/workflows/trigger` | Non-CRUD operation |
| Search | `GET /documents/search?q=...` | Cross-case search with auth filter |

---

## Request Headers

### Required / Recommended

| Header | Required | Description |
|--------|----------|-------------|
| `Authorization` | Yes (except auth/health) | `Bearer {access_token}` |
| `Content-Type` | Yes (body requests) | `application/json` |
| `Accept` | Recommended | `application/json` |
| `X-Correlation-Id` | Optional | UUID; generated if absent, echoed in response |
| `X-Request-Id` | Optional | Client-side tracking ID |
| `Idempotency-Key` | Recommended (mutations) | Client UUID; 24-hour dedup window |
| `If-Match` | Required (optimistic updates) | Resource version as ETag |

### Example Request

```http
POST /api/v1/cases HTTP/1.1
Host: api.lexflow.firm.com
Authorization: Bearer eyJhbGciOiJSUzI1NiIs...
Content-Type: application/json
X-Correlation-Id: 550e8400-e29b-41d4-a716-446655440000
Idempotency-Key: 7c9e6679-7425-40de-944b-e07fc1f90ae7

{
  "title": "Smith v. Acme Corp",
  "clientId": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "practiceArea": "litigation",
  "leadAttorneyId": "b2c3d4e5-f6a7-8901-bcde-f12345678901"
}
```

---

## Response Envelope

All successful public API responses use a **uniform envelope**. The envelope separates payload (`data`) from metadata (`meta`).

### Single Resource (200 / 201)

```json
{
  "data": {
    "id": "c1d2e3f4-a5b6-7890-cdef-123456789012",
    "title": "Smith v. Acme Corp",
    "status": "active",
    "version": 1,
    "createdAt": "2026-07-06T08:00:00Z"
  },
  "meta": {
    "requestId": "550e8400-e29b-41d4-a716-446655440000",
    "timestamp": "2026-07-06T08:00:00Z"
  }
}
```

### Collection (Paginated)

```json
{
  "data": [
    { "id": "...", "title": "Smith v. Acme Corp", "status": "active" },
    { "id": "...", "title": "Jones Estate Planning", "status": "intake" }
  ],
  "meta": {
    "requestId": "550e8400-e29b-41d4-a716-446655440000",
    "timestamp": "2026-07-06T08:00:00Z",
    "pagination": {
      "page": 1,
      "pageSize": 25,
      "totalItems": 142,
      "totalPages": 6
    }
  }
}
```

### Async Accepted (202)

```json
{
  "data": {
    "jobId": "660e8400-e29b-41d4-a716-446655440001",
    "status": "queued",
    "statusUrl": "/api/v1/jobs/660e8400-e29b-41d4-a716-446655440001"
  },
  "meta": {
    "requestId": "550e8400-e29b-41d4-a716-446655440000",
    "timestamp": "2026-07-06T08:00:00Z"
  }
}
```

### Empty Success (204)

`DELETE` and some `PATCH` operations return **204 No Content** with no body. `requestId` is still returned in response headers:

```http
X-Request-Id: 550e8400-e29b-41d4-a716-446655440000
X-Correlation-Id: 550e8400-e29b-41d4-a716-446655440000
```

---

## RFC 7807 Error Format

All errors return **`Content-Type: application/problem+json`** per [RFC 7807](https://datatracker.ietf.org/doc/html/rfc7807).

### Structure

| Field | Required | Description |
|-------|----------|-------------|
| `type` | Yes | URI identifying the error category |
| `title` | Yes | Short human-readable summary |
| `status` | Yes | HTTP status code |
| `detail` | Yes | Human-readable explanation |
| `instance` | Yes | Request path |
| `errors` | No | Field-level validation errors (422 only) |
| `meta` | Yes | LexFlow extension: `requestId`, `timestamp` |

### Validation Error (422)

```json
{
  "type": "https://lexflow.ai/errors/validation-error",
  "title": "Validation Error",
  "status": 422,
  "detail": "One or more fields failed validation.",
  "instance": "/api/v1/cases",
  "errors": [
    {
      "field": "title",
      "message": "Title is required.",
      "code": "required"
    },
    {
      "field": "clientId",
      "message": "Must be a valid UUID.",
      "code": "invalid_format"
    }
  ],
  "meta": {
    "requestId": "550e8400-e29b-41d4-a716-446655440000",
    "timestamp": "2026-07-06T08:00:00Z"
  }
}
```

### Authorization Error (403)

```json
{
  "type": "https://lexflow.ai/errors/forbidden",
  "title": "Forbidden",
  "status": 403,
  "detail": "You do not have permission to perform this action.",
  "instance": "/api/v1/admin/users",
  "meta": {
    "requestId": "550e8400-e29b-41d4-a716-446655440000",
    "timestamp": "2026-07-06T08:00:00Z"
  }
}
```

### Error Type URI Registry

| Type URI | HTTP Status | When |
|----------|-------------|------|
| `https://lexflow.ai/errors/validation-error` | 422 | Input validation failure |
| `https://lexflow.ai/errors/bad-request` | 400 | Malformed JSON, invalid query param |
| `https://lexflow.ai/errors/unauthorized` | 401 | Missing or invalid token |
| `https://lexflow.ai/errors/forbidden` | 403 | RBAC denial (non-case resources) |
| `https://lexflow.ai/errors/not-found` | 404 | Resource not found or matter wall denial |
| `https://lexflow.ai/errors/conflict` | 409 | Optimistic concurrency version mismatch |
| `https://lexflow.ai/errors/rate-limited` | 429 | Rate limit exceeded |
| `https://lexflow.ai/errors/internal-error` | 500 | Unhandled server error |
| `https://lexflow.ai/errors/service-unavailable` | 503 | Dependency down or maintenance |

See [error-handling.md](./error-handling.md) for the complete status code guide.

---

## Pagination

### Offset Pagination (Default)

```http
GET /api/v1/cases?page=1&pageSize=25&sort=-createdAt
```

| Parameter | Default | Max | Description |
|-----------|---------|-----|-------------|
| `page` | 1 | — | 1-indexed page number |
| `pageSize` | 25 | 100 | Items per page |
| `sort` | `-createdAt` | — | Comma-separated fields; prefix `-` for descending |

### Cursor Pagination (High-Volume)

Used for audit logs and event streams where offset pagination is inefficient.

```http
GET /api/v1/audit-logs?cursor=eyJpZCI6...&limit=50
```

Response includes `nextCursor` in `meta.pagination` when more results exist:

```json
{
  "meta": {
    "pagination": {
      "limit": 50,
      "nextCursor": "eyJpZCI6ImEyYjNjNGQ1...",
      "hasMore": true
    }
  }
}
```

---

## Filtering and Sorting

```http
GET /api/v1/cases?status=active&practiceArea=litigation&priority=high
GET /api/v1/cases?leadAttorneyId=a1b2c3d4-e5f6-7890-abcd-ef1234567890
GET /api/v1/documents?caseId=c1d2e3f4-...&documentType=contract&search=indemnification
GET /api/v1/tasks?assignedTo=me&status=pending&dueBefore=2026-07-15
```

| Convention | Example |
|------------|---------|
| Equality filter | `?status=active` |
| Multi-value (OR) | `?status=active,on_hold` |
| Date range | `?createdAfter=2026-01-01&createdBefore=2026-07-01` |
| Sort ascending | `?sort=title` |
| Sort descending | `?sort=-priority,dueAt` |
| Current user alias | `?assignedTo=me` |

Unknown filter parameters are **ignored** with a `Warning` header (not an error) to preserve forward compatibility.

---

## Optimistic Concurrency

Mutable resources include a `version` integer. Responses include an `ETag` header derived from `version`.

```http
GET /api/v1/cases/c1d2e3f4-...
```

Response headers:

```http
ETag: "3"
```

Update with version check:

```http
PATCH /api/v1/cases/c1d2e3f4-...
If-Match: "3"
Content-Type: application/json

{
  "title": "Updated Title",
  "version": 3
}
```

Version mismatch returns **409 Conflict** — see [error-handling.md](./error-handling.md).

---

## Idempotency

Mutating requests accept an optional `Idempotency-Key` header:

```http
POST /api/v1/cases/c1d2e3f4-.../workflows/trigger
Idempotency-Key: 7c9e6679-7425-40de-944b-e07fc1f90ae7
```

| Rule | Value |
|------|-------|
| Key format | UUID v4 recommended |
| TTL | 24 hours |
| Scope | Per user + endpoint + key |
| Behavior | Duplicate returns original response without re-execution |
| Storage | `shared.idempotency_keys` table |

---

## HTTP Method Semantics

| Method | Usage | Success Code | Idempotent |
|--------|-------|--------------|------------|
| `GET` | Read resource or collection | 200 | Yes |
| `POST` | Create resource or trigger action | 201 / 202 | No* |
| `PUT` | Full replace | 200 | Yes |
| `PATCH` | Partial update | 200 | No |
| `DELETE` | Remove resource | 204 | Yes |

*POST with `Idempotency-Key` achieves effective idempotency for supported endpoints.

---

## Best Practices

1. **Never return raw domain exceptions** — always map to RFC 7807 via the global exception handler.
2. **Use 201 + `Location` header** on resource creation: `Location: /api/v1/cases/{id}`.
3. **Prefer PATCH over PUT** for partial updates; PUT only when full replacement is intended.
4. **Limit nested depth** to two levels (`/cases/{id}/tasks/{taskId}`) — deeper nesting indicates a modeling issue.
5. **Document every query parameter** in OpenAPI with examples.
6. **Use ISO 8601** for all date/time fields; never locale-specific formats.
7. **Return empty arrays, not null**, for collection fields in `data`.

---

## Tradeoffs

| Choice | Rationale | Downside |
|--------|-----------|----------|
| Envelope wrapper | Consistent meta/pagination across all endpoints | Extra nesting; not pure REST/HATEOAS |
| camelCase JSON | Frontend convention (TypeScript) | Python snake_case requires Pydantic aliases |
| Offset pagination default | Simple for case lists (<10K per firm) | Performance degrades at very large offsets |
| Ignore unknown filters | Forward-compatible API evolution | Typos in filter names fail silently |
| 404 for matter wall | Security — no enumeration | Support teams need correlation ID to debug |

---

## Future Improvements

- **HATEOAS links** in `meta.links` for discoverable next actions (approve, trigger workflow)
- **Prefer header** for timezone-aware date filtering (`Prefer: timezone=America/New_York`)
- **JSON:API compatibility layer** if external integrations require it
- **OpenAPI diff gate** in CI blocking breaking changes without version bump

---

## References

- [error-handling.md](./error-handling.md) — Complete error catalog
- [versioning.md](./versioning.md) — Version prefix strategy
- [authentication.md](./authentication.md) — Required auth headers
- [authorization-rbac.md](./authorization-rbac.md) — Permission-gated endpoints
- [../02-domain/domain-model.md](../domain-model.md) — Resource definitions
- [../08-security/security-architecture.md](../security-architecture.md) — Rate limits and WAF
- [RFC 7807](https://datatracker.ietf.org/doc/html/rfc7807)
- [RFC 9110 — HTTP Semantics](https://datatracker.ietf.org/doc/html/rfc9110)

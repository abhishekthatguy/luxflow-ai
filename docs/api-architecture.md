# API Architecture

**LexFlow AI** — REST API Design Standards  
**Version:** 1.0  
**Status:** Draft — Pre-Implementation  
**Last Updated:** 2026-07-06

---

## 1. Overview

LexFlow AI exposes a RESTful API via FastAPI. The API is the **sole entry point** for all frontend and authorized external integrations. n8n callbacks use a separate internal API namespace.

- **Base URL (production):** `https://api.lexflow.{firm-domain}/api/v1`
- **OpenAPI spec:** Auto-generated at `/api/v1/openapi.json`
- **Interactive docs:** `/api/v1/docs` (disabled in production)

---

## 2. Design Principles

| Principle | Implementation |
|-----------|----------------|
| Resource-oriented | Nouns for resources, HTTP verbs for actions |
| Versioned | `/api/v1` prefix; breaking changes → `/api/v2` |
| Consistent | Uniform response envelope, error format, pagination |
| Secure by default | Auth required on all endpoints except `/auth/*` and `/health` |
| Idempotent | `Idempotency-Key` header on POST/PUT/PATCH |
| Audited | All mutating operations write audit log entries |
| Documented | OpenAPI 3.1 with examples; TypeScript client generated |

---

## 3. Authentication

All authenticated requests require:

```http
Authorization: Bearer {access_token}
X-Correlation-Id: {uuid}          # Optional — generated if absent
X-Request-Id: {uuid}              # Optional — for idempotency tracking
```

See [authentication-authorization.md](./authentication-authorization.md).

---

## 4. Response Envelope

### 4.1 Success Response

```json
{
  "data": { ... },
  "meta": {
    "requestId": "550e8400-e29b-41d4-a716-446655440000",
    "timestamp": "2026-07-06T08:00:00Z"
  }
}
```

### 4.2 Collection Response (Paginated)

```json
{
  "data": [ ... ],
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

### 4.3 Async Accepted Response (202)

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

---

## 5. Error Response Format

All errors follow [RFC 7807 Problem Details](https://datatracker.ietf.org/doc/html/rfc7807):

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
    }
  ],
  "meta": {
    "requestId": "550e8400-e29b-41d4-a716-446655440000",
    "timestamp": "2026-07-06T08:00:00Z"
  }
}
```

### 5.1 Standard HTTP Status Codes

| Code | Usage |
|------|-------|
| 200 | Successful GET, PUT, PATCH |
| 201 | Resource created |
| 202 | Async operation accepted |
| 204 | Successful DELETE |
| 400 | Malformed request |
| 401 | Missing or invalid token |
| 403 | Authenticated but not authorized (matter wall, RBAC) |
| 404 | Resource not found (or not visible due to matter wall — same response) |
| 409 | Conflict (optimistic concurrency version mismatch) |
| 422 | Validation error |
| 429 | Rate limit exceeded |
| 500 | Internal server error |
| 503 | Service unavailable (maintenance, dependency down) |

### 5.2 Error Type URIs

| Type URI | Status | When |
|----------|--------|------|
| `.../validation-error` | 422 | Input validation failure |
| `.../unauthorized` | 401 | Auth failure |
| `.../forbidden` | 403 | RBAC / matter wall denial |
| `.../not-found` | 404 | Resource not found |
| `.../conflict` | 409 | Version conflict |
| `.../rate-limited` | 429 | Too many requests |
| `.../internal-error` | 500 | Unhandled exception |

---

## 6. Pagination

Cursor-based pagination for large datasets; offset-based for admin lists.

### Offset Pagination (default)

```http
GET /api/v1/cases?page=1&pageSize=25&sort=-createdAt
```

### Cursor Pagination (high-volume)

```http
GET /api/v1/audit-logs?cursor=eyJpZCI6...&limit=50
```

Response includes `nextCursor` in meta when more results exist.

---

## 7. Filtering & Sorting

```http
GET /api/v1/cases?status=active&practiceArea=litigation&priority=high
GET /api/v1/cases?leadAttorneyId={uuid}
GET /api/v1/documents?caseId={uuid}&documentType=contract&search=indemnification
GET /api/v1/tasks?assignedTo=me&status=pending&dueBefore=2026-07-15
```

Sort: `sort=field` (ascending) or `sort=-field` (descending). Multiple: `sort=-priority,dueAt`.

---

## 8. Optimistic Concurrency

Mutable resources return an `ETag` header based on the `version` field.

```http
PUT /api/v1/cases/{id}
If-Match: "3"
Content-Type: application/json

{ "title": "Updated Title", "version": 3 }
```

Version mismatch → `409 Conflict`.

---

## 9. Idempotency

Mutating requests accept an optional idempotency key:

```http
POST /api/v1/cases/{id}/workflows/trigger
Idempotency-Key: client-generated-uuid
```

- Keys are valid for 24 hours
- Duplicate requests return the original response without re-executing
- Stored in `shared.idempotency_keys` table

---

## 10. API Resource Map

### 10.1 Authentication

| Method | Path | Description |
|--------|------|-------------|
| POST | `/auth/login` | Email + password → tokens |
| POST | `/auth/refresh` | Refresh token → new access token |
| POST | `/auth/logout` | Revoke refresh token |
| POST | `/auth/forgot-password` | Initiate password reset |
| POST | `/auth/reset-password` | Complete password reset |

### 10.2 Users & Admin

| Method | Path | Description | Role |
|--------|------|-------------|------|
| GET | `/users/me` | Current user profile | Any |
| PATCH | `/users/me` | Update profile | Any |
| GET | `/admin/users` | List firm users | SystemAdmin, ITAdmin |
| POST | `/admin/users` | Create user | SystemAdmin |
| PATCH | `/admin/users/{id}` | Update user | SystemAdmin |
| GET | `/admin/roles` | List roles | SystemAdmin |
| POST | `/admin/users/{id}/roles` | Assign role | SystemAdmin |

### 10.3 Cases

| Method | Path | Description |
|--------|------|-------------|
| GET | `/cases` | List cases (filtered by matter wall) |
| POST | `/cases` | Create case (intake) |
| GET | `/cases/{id}` | Get case detail |
| PATCH | `/cases/{id}` | Update case |
| GET | `/cases/{id}/timeline` | Case timeline events |
| GET | `/cases/{id}/participants` | List participants |
| POST | `/cases/{id}/participants` | Add participant |
| DELETE | `/cases/{id}/participants/{userId}` | Remove participant |

### 10.4 Case Sub-Resources

| Method | Path | Description |
|--------|------|-------------|
| GET/POST | `/cases/{id}/tasks` | List/create tasks |
| PATCH | `/cases/{id}/tasks/{taskId}` | Update task |
| GET/POST | `/cases/{id}/deadlines` | List/create deadlines |
| GET/POST | `/cases/{id}/hearings` | List/create hearings |
| GET/POST | `/cases/{id}/notes` | List/create notes |
| GET | `/cases/{id}/audit-logs` | Case audit trail |

### 10.5 Clients

| Method | Path | Description |
|--------|------|-------------|
| GET | `/clients` | List clients |
| POST | `/clients` | Create client |
| GET | `/clients/{id}` | Get client |
| PATCH | `/clients/{id}` | Update client |
| GET | `/clients/{id}/cases` | Client's cases |

### 10.6 Documents

| Method | Path | Description |
|--------|------|-------------|
| GET | `/cases/{id}/documents` | List case documents |
| POST | `/cases/{id}/documents` | Initiate upload (returns presigned S3 URL) |
| POST | `/cases/{id}/documents/{docId}/confirm` | Confirm upload complete |
| GET | `/documents/{id}` | Get document metadata |
| GET | `/documents/{id}/download` | Presigned download URL |
| POST | `/documents/{id}/versions` | Upload new version |
| GET | `/documents/search` | Hybrid full-text + semantic search |

### 10.7 AI

| Method | Path | Description |
|--------|------|-------------|
| POST | `/cases/{id}/ai/summarize` | Request AI summary (202 async) |
| GET | `/cases/{id}/ai/summaries` | List summaries |
| GET | `/ai/summaries/{id}` | Get summary detail |
| POST | `/ai/summaries/{id}/approve` | Approve summary |
| POST | `/ai/summaries/{id}/reject` | Reject summary |
| POST | `/cases/{id}/ai/research` | Legal research query (202 async) |
| POST | `/cases/{id}/ai/contract-review` | Contract review (202 async) |
| POST | `/cases/{id}/ai/chat` | Case-scoped AI assistant (202 async) |

### 10.8 Workflows

| Method | Path | Description |
|--------|------|-------------|
| GET | `/workflows/definitions` | List available workflows |
| POST | `/cases/{id}/workflows/trigger` | Trigger workflow on case (202) |
| GET | `/workflows/executions` | List executions |
| GET | `/workflows/executions/{id}` | Execution detail + steps |
| POST | `/workflows/executions/{id}/cancel` | Cancel running execution |

### 10.9 Approvals

| Method | Path | Description |
|--------|------|-------------|
| GET | `/approvals` | List pending approvals for current user |
| GET | `/approvals/{id}` | Approval detail |
| POST | `/approvals/{id}/approve` | Approve |
| POST | `/approvals/{id}/reject` | Reject |

### 10.10 Notifications

| Method | Path | Description |
|--------|------|-------------|
| GET | `/notifications` | List user notifications |
| PATCH | `/notifications/{id}/read` | Mark as read |
| POST | `/notifications/read-all` | Mark all as read |

### 10.11 Jobs (Async Status)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/jobs/{id}` | Poll async job status |

### 10.12 Internal (n8n Callbacks — NOT Public)

| Method | Path | Description |
|--------|------|-------------|
| POST | `/internal/webhooks/n8n/{workflowSlug}` | n8n completion callback |
| POST | `/internal/webhooks/n8n/{workflowSlug}/step` | n8n step progress update |

Internal endpoints:
- Not included in public OpenAPI spec
- Authenticated via HMAC signature (`X-N8N-Signature` header)
- Accessible only from VPC internal network

---

## 11. Rate Limiting

| Tier | Limit | Scope |
|------|-------|-------|
| Standard API | 100 req/min | Per user |
| AI endpoints | 20 req/min | Per user |
| Document upload | 50 req/min | Per user |
| Auth endpoints | 10 req/min | Per IP |
| Internal webhooks | 500 req/min | Per workflow |

Exceeded limits return `429` with `Retry-After` header.

---

## 12. WebSocket / SSE

Real-time updates for case timeline and notifications:

```
GET /api/v1/events/stream
Authorization: Bearer {access_token}
Accept: text/event-stream
```

Events: `notification`, `case.updated`, `workflow.completed`, `summary.generated`

---

## 13. OpenAPI & Client Generation

```
FastAPI → /api/v1/openapi.json
  → scripts/openapi/generate-ts-client.sh
  → packages/shared/src/types/
  → packages/sdk/src/client.ts
```

CI validates that generated types match committed types (drift check).

---

## 14. Related Documents

- [authentication-authorization.md](./authentication-authorization.md)
- [high-level-architecture.md](./high-level-architecture.md)
- [domain-model.md](./domain-model.md)
- [workflow-orchestration.md](./workflow-orchestration.md)

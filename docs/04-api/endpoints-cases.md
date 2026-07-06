# Case Endpoints

**LexFlow AI** — Case Management REST API  
**Version:** 1.0  
**Status:** Draft — Pre-Implementation  
**Last Updated:** 2026-07-06

---

## Purpose

Document the complete REST API for **Case** (legal matter) resources and their sub-resources. Cases are the central aggregate in LexFlow AI — all documents, workflows, AI outputs, and tasks are scoped to a case.

---

## Scope

| In Scope | Out of Scope |
|----------|--------------|
| Case CRUD, list, filter | Client management (separate client endpoints) |
| Participants (matter wall membership) | Document upload (see [endpoints-documents.md](./endpoints-documents.md)) |
| Tasks, deadlines, hearings, notes | Workflow trigger (see [endpoints-workflows.md](./endpoints-workflows.md)) |
| Case timeline | AI endpoints (see [endpoints-ai.md](./endpoints-ai.md)) |
| Case audit log access | Case status state machine internals (see [../02-domain/domain-model.md](../domain-model.md)) |

**Base path:** `/api/v1/cases`  
**Required auth:** Bearer JWT on all endpoints

---

## Responsibilities

| Layer | Responsibility |
|-------|----------------|
| **Case router** (`apps/api/api/v1/cases.py`) | HTTP binding, request validation |
| **Case service** (`services/case_management/`) | Business rules, state transitions, invariants |
| **Authorization** | RBAC + matter wall per [authorization-rbac.md](./authorization-rbac.md) |
| **Audit service** | Log all mutations with actor and before/after state |
| **Event publisher** | Emit `CaseCreated`, `CaseStatusChanged`, etc. via outbox |

---

## Architecture

```mermaid
flowchart TB
    subgraph API["/api/v1/cases"]
        LIST[GET /cases]
        CREATE[POST /cases]
        GET[GET /cases/{id}]
        PATCH[PATCH /cases/{id}]
        PART[Participants]
        SUB[Tasks · Deadlines · Hearings · Notes]
        TL[Timeline · Audit Logs]
    end

    subgraph Domain["Case Management Service"]
        AGG[Case Aggregate]
        SM[Status State Machine]
        MW[Matter Wall Check]
    end

    subgraph Events["Event Bus"]
        OUT[Transactional Outbox]
        MQ[RabbitMQ]
    end

    API --> Domain
    Domain --> OUT --> MQ
```

### Case Status Values

| Status | Description |
|--------|-------------|
| `intake` | Initial creation; intake in progress |
| `active` | Matter actively being worked |
| `on_hold` | Temporarily paused |
| `closed` | Matter resolved |
| `archived` | Retention archive; read-only |

See [../02-domain/domain-model.md](../domain-model.md) for the full state machine.

---

## Flow Diagrams

### Create Case (Intake)

```mermaid
sequenceDiagram
    participant C as Client
    participant API as FastAPI
    participant S as Case Service
    participant DB as PostgreSQL
    participant MQ as RabbitMQ

    C->>API: POST /api/v1/cases<br/>{ title, clientId, practiceArea, leadAttorneyId }
    API->>API: Auth + RBAC (case:create)
    API->>S: create_case(command)
    S->>S: Validate client exists, lead attorney active
    S->>DB: INSERT case (status: intake)
    S->>DB: INSERT case_participant (leadAttorney, role: lead)
    S->>DB: INSERT outbox (CaseCreated)
    S->>DB: INSERT audit_log
    DB-->>S: Case with caseNumber assigned
    S-->>API: CaseDTO
    API-->>C: 201 Created { data: case }<br/>Location: /api/v1/cases/{id}
    Note over MQ: Async: intake workflow triggered
```

### Get Case (Matter Wall)

```mermaid
sequenceDiagram
    participant C as Client
    participant API as FastAPI
    participant AuthZ as Authorization
    participant S as Case Service

    C->>API: GET /api/v1/cases/{caseId}
    API->>AuthZ: case:read:assigned + matter wall
    alt Not authorized
        API-->>C: 404 Not Found
    else Authorized
        API->>S: get_case(caseId)
        S-->>API: CaseDTO with participants summary
        API-->>C: 200 OK { data: case }
    end
```

### Add Participant

```mermaid
sequenceDiagram
    participant C as Client
    participant API as FastAPI
    participant AuthZ as Authorization
    participant S as Case Service
    participant DB as PostgreSQL

    C->>API: POST /api/v1/cases/{caseId}/participants<br/>{ userId, role: "paralegal" }
    API->>AuthZ: case:write:assigned + caller is lead participant
    API->>S: add_participant(caseId, userId, role)
    S->>DB: INSERT case_participant
    S->>DB: INSERT outbox (CaseParticipantAdded)
    S->>DB: INSERT audit_log
    API-->>C: 201 Created { data: participant }
```

---

## Endpoints

### GET `/cases`

List cases visible to the current user (matter wall filtered).

**Permission:** `case:read:assigned`

**Query parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `page` | int | Page number (default 1) |
| `pageSize` | int | Items per page (default 25, max 100) |
| `status` | string | Filter: `intake`, `active`, `on_hold`, `closed` |
| `practiceArea` | string | Filter by practice area |
| `priority` | string | Filter: `low`, `normal`, `high`, `urgent` |
| `leadAttorneyId` | uuid | Filter by lead attorney |
| `search` | string | Full-text search on title and case number |
| `sort` | string | Default `-createdAt` |

**Request:**

```http
GET /api/v1/cases?status=active&practiceArea=litigation&page=1&pageSize=25
Authorization: Bearer eyJhbGciOiJSUzI1NiIs...
```

**Response (200):**

```json
{
  "data": [
    {
      "id": "c1d2e3f4-a5b6-7890-cdef-123456789012",
      "caseNumber": "2026-00142",
      "title": "Smith v. Acme Corp",
      "status": "active",
      "practiceArea": "litigation",
      "priority": "high",
      "clientId": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
      "clientName": "John Smith",
      "leadAttorneyId": "b2c3d4e5-f6a7-8901-bcde-f12345678901",
      "leadAttorneyName": "Jane Attorney",
      "openedAt": "2026-01-15T10:00:00Z",
      "closedAt": null,
      "version": 5,
      "createdAt": "2026-01-15T10:00:00Z",
      "updatedAt": "2026-07-01T14:30:00Z"
    }
  ],
  "meta": {
    "requestId": "550e8400-e29b-41d4-a716-446655440000",
    "timestamp": "2026-07-06T08:00:00Z",
    "pagination": {
      "page": 1,
      "pageSize": 25,
      "totalItems": 42,
      "totalPages": 2
    }
  }
}
```

---

### POST `/cases`

Create a new case (intake).

**Permission:** `case:create`

**Request:**

```json
{
  "title": "Smith v. Acme Corp",
  "clientId": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "practiceArea": "litigation",
  "priority": "high",
  "leadAttorneyId": "b2c3d4e5-f6a7-8901-bcde-f12345678901",
  "metadata": {
    "referralSource": "existing_client",
    "estimatedValue": "250000"
  }
}
```

**Response (201):**

```json
{
  "data": {
    "id": "c1d2e3f4-a5b6-7890-cdef-123456789012",
    "caseNumber": "2026-00143",
    "title": "Smith v. Acme Corp",
    "status": "intake",
    "practiceArea": "litigation",
    "priority": "high",
    "clientId": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "leadAttorneyId": "b2c3d4e5-f6a7-8901-bcde-f12345678901",
    "participants": [
      {
        "userId": "b2c3d4e5-f6a7-8901-bcde-f12345678901",
        "role": "lead",
        "addedAt": "2026-07-06T08:00:00Z"
      }
    ],
    "openedAt": "2026-07-06T08:00:00Z",
    "closedAt": null,
    "version": 1,
    "createdAt": "2026-07-06T08:00:00Z",
    "updatedAt": "2026-07-06T08:00:00Z"
  },
  "meta": {
    "requestId": "550e8400-e29b-41d4-a716-446655440000",
    "timestamp": "2026-07-06T08:00:00Z"
  }
}
```

**Response headers:**

```http
Location: /api/v1/cases/c1d2e3f4-a5b6-7890-cdef-123456789012
```

---

### GET `/cases/{caseId}`

Get case detail.

**Permission:** `case:read:assigned` + matter wall

**Response (200):**

```json
{
  "data": {
    "id": "c1d2e3f4-a5b6-7890-cdef-123456789012",
    "caseNumber": "2026-00142",
    "title": "Smith v. Acme Corp",
    "status": "active",
    "practiceArea": "litigation",
    "priority": "high",
    "clientId": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "clientName": "John Smith",
    "leadAttorneyId": "b2c3d4e5-f6a7-8901-bcde-f12345678901",
    "leadAttorneyName": "Jane Attorney",
    "participants": [
      {
        "userId": "b2c3d4e5-f6a7-8901-bcde-f12345678901",
        "displayName": "Jane Attorney",
        "role": "lead",
        "addedAt": "2026-01-15T10:00:00Z"
      },
      {
        "userId": "d3e4f5a6-b7c8-9012-cdef-123456789012",
        "displayName": "Pat Paralegal",
        "role": "paralegal",
        "addedAt": "2026-01-20T09:00:00Z"
      }
    ],
    "taskCount": 12,
    "documentCount": 34,
    "upcomingDeadlineCount": 2,
    "openedAt": "2026-01-15T10:00:00Z",
    "closedAt": null,
    "version": 5,
    "metadata": {},
    "createdAt": "2026-01-15T10:00:00Z",
    "updatedAt": "2026-07-01T14:30:00Z"
  },
  "meta": {
    "requestId": "550e8400-e29b-41d4-a716-446655440000",
    "timestamp": "2026-07-06T08:00:00Z"
  }
}
```

---

### PATCH `/cases/{caseId}`

Partial update. Requires `If-Match` header with current version.

**Permission:** `case:write:assigned` + matter wall

**Request:**

```http
PATCH /api/v1/cases/c1d2e3f4-a5b6-7890-cdef-123456789012
If-Match: "5"
Content-Type: application/json

{
  "title": "Smith v. Acme Corporation",
  "priority": "urgent",
  "status": "on_hold",
  "version": 5
}
```

**Response (200):** Updated case object with `version: 6`.

**Errors:**
- `409 Conflict` — version mismatch
- `422 Validation Error` — invalid status transition (e.g., `closed` → `intake`)

---

### GET `/cases/{caseId}/participants`

List case participants.

**Permission:** `case:read:assigned` + matter wall

**Response (200):**

```json
{
  "data": [
    {
      "userId": "b2c3d4e5-f6a7-8901-bcde-f12345678901",
      "displayName": "Jane Attorney",
      "email": "jane.attorney@firm.com",
      "role": "lead",
      "addedBy": "b2c3d4e5-f6a7-8901-bcde-f12345678901",
      "addedAt": "2026-01-15T10:00:00Z"
    }
  ],
  "meta": { "requestId": "...", "timestamp": "..." }
}
```

---

### POST `/cases/{caseId}/participants`

Add participant to case.

**Permission:** `case:write:assigned` + caller must have participant role `lead`

**Request:**

```json
{
  "userId": "e4f5a6b7-c8d9-0123-def0-234567890123",
  "role": "paralegal"
}
```

**Response (201):** Created participant object.

---

### DELETE `/cases/{caseId}/participants/{userId}`

Remove participant from case.

**Permission:** `case:write:assigned` + caller must have participant role `lead`

**Response:** `204 No Content`

**Constraint:** Cannot remove the sole `lead` participant without assigning a new lead first.

---

### GET `/cases/{caseId}/tasks`

List tasks for a case.

**Permission:** `case:read:assigned` + matter wall

**Query parameters:** `status`, `assignedTo`, `dueBefore`, `sort`

**Response (200):**

```json
{
  "data": [
    {
      "id": "t1a2b3c4-d5e6-7890-abcd-ef1234567890",
      "caseId": "c1d2e3f4-a5b6-7890-cdef-123456789012",
      "title": "Draft motion to dismiss",
      "status": "pending",
      "assignedTo": "d3e4f5a6-b7c8-9012-cdef-123456789012",
      "assignedToName": "Pat Paralegal",
      "dueAt": "2026-07-15T17:00:00Z",
      "completedAt": null,
      "version": 1,
      "createdAt": "2026-07-01T10:00:00Z"
    }
  ],
  "meta": { "requestId": "...", "timestamp": "...", "pagination": { "..." } }
}
```

---

### POST `/cases/{caseId}/tasks`

Create task.

**Permission:** `case:write:assigned` + matter wall

**Request:**

```json
{
  "title": "Review discovery responses",
  "assignedTo": "d3e4f5a6-b7c8-9012-cdef-123456789012",
  "dueAt": "2026-07-20T17:00:00Z",
  "description": "Review and flag incomplete responses."
}
```

**Response (201):** Created task object.

---

### PATCH `/cases/{caseId}/tasks/{taskId}`

Update task (status, assignment, due date).

**Permission:** `case:write:assigned` + matter wall

**Request:**

```json
{
  "status": "completed",
  "version": 2
}
```

---

### GET `/cases/{caseId}/deadlines`

List legal deadlines.

**Response (200):**

```json
{
  "data": [
    {
      "id": "dl1a2b3c4-d5e6-7890-abcd-ef1234567890",
      "caseId": "c1d2e3f4-a5b6-7890-cdef-123456789012",
      "title": "Response to motion due",
      "deadlineAt": "2026-07-18T23:59:59Z",
      "type": "filing",
      "status": "upcoming",
      "reminderSentAt": null
    }
  ],
  "meta": { "..." }
}
```

---

### POST `/cases/{caseId}/deadlines`

Create deadline.

**Request:**

```json
{
  "title": "Discovery cutoff",
  "deadlineAt": "2026-08-01T23:59:59Z",
  "type": "discovery"
}
```

---

### GET `/cases/{caseId}/hearings`

List scheduled hearings.

---

### POST `/cases/{caseId}/hearings`

Create hearing.

**Request:**

```json
{
  "title": "Motion hearing",
  "hearingAt": "2026-08-15T09:00:00Z",
  "location": "Superior Court, Room 402",
  "court": "Fulton County Superior Court",
  "judge": "Hon. Smith"
}
```

---

### GET `/cases/{caseId}/notes`

List internal case notes.

**Permission:** `case:read:assigned` + matter wall (Client role: **denied**)

---

### POST `/cases/{caseId}/notes`

Create internal note.

**Request:**

```json
{
  "content": "Client confirmed settlement authority up to $500K.",
  "visibility": "internal"
}
```

---

### GET `/cases/{caseId}/timeline`

Denormalized case timeline (events from audit, tasks, documents, workflows).

**Permission:** `case:read:assigned` + matter wall

**Response (200):**

```json
{
  "data": [
    {
      "id": "ev1a2b3c4-d5e6-7890-abcd-ef1234567890",
      "eventType": "document.uploaded",
      "title": "Contract uploaded",
      "occurredAt": "2026-07-05T14:00:00Z",
      "actorId": "d3e4f5a6-b7c8-9012-cdef-123456789012",
      "actorName": "Pat Paralegal",
      "referenceType": "document",
      "referenceId": "doc-uuid"
    },
    {
      "id": "ev2b3c4d5-e6f7-8901-bcde-f12345678901",
      "eventType": "task.completed",
      "title": "Draft motion to dismiss — completed",
      "occurredAt": "2026-07-04T16:30:00Z",
      "actorId": "d3e4f5a6-b7c8-9012-cdef-123456789012",
      "actorName": "Pat Paralegal",
      "referenceType": "task",
      "referenceId": "task-uuid"
    }
  ],
  "meta": {
    "requestId": "...",
    "timestamp": "...",
    "pagination": { "page": 1, "pageSize": 50, "totalItems": 128, "totalPages": 3 }
  }
}
```

---

### GET `/cases/{caseId}/audit-logs`

Case-scoped audit trail.

**Permission:** `audit:read:firm` OR `case:read:assigned` with participant role `lead`

**Query parameters:** Cursor pagination — `cursor`, `limit`

---

## Data Types

### Practice Areas

`litigation`, `corporate`, `real_estate`, `employment`, `intellectual_property`, `family`, `estate_planning`, `criminal`, `other`

### Priority

`low`, `normal`, `high`, `urgent`

### Participant Roles

`lead`, `associate`, `paralegal`, `observer`

---

## Best Practices

1. **Always send `version` on PATCH** — prevents lost updates on concurrent edits.
2. **Use `Idempotency-Key` on POST /cases** — safe retry on network failure during intake.
3. **Poll timeline after async operations** — document upload and workflow completion appear as timeline events.
4. **Do not cache case lists client-side** beyond React Query stale time — matter wall membership can change.
5. **Use server-assigned `caseNumber`** — never client-generated.

---

## Tradeoffs

| Decision | Benefit | Cost |
|----------|---------|------|
| Nested sub-resources under `/cases/{id}/*` | Clear ownership hierarchy | Longer URLs |
| Timeline as denormalized read model | Fast UI rendering | Eventual consistency with source aggregates |
| Closed case write restrictions | Data integrity | Requires reopen workflow for late additions |
| 404 on unauthorized case access | Security | Support must use correlation ID |

---

## Future Improvements

- Bulk case import API (`POST /cases/bulk`) for migration from legacy DMS
- Case merge API for duplicate intake detection
- Saved filters (`GET /cases/saved-filters`)
- Case templates by practice area
- External calendar sync for hearings/deadlines

---

## References

- [authorization-rbac.md](./authorization-rbac.md) — Permissions and matter walls
- [rest-standards.md](./rest-standards.md) — Envelope, pagination, concurrency
- [endpoints-documents.md](./endpoints-documents.md) — Case document sub-resource
- [endpoints-workflows.md](./endpoints-workflows.md) — Workflow trigger on case
- [../02-domain/domain-model.md](../domain-model.md) — Case aggregate, invariants, events
- [../database-architecture.md](../database-architecture.md) — `cases` schema

# Document Endpoints

**LexFlow AI** — Document Upload, Download & Search API  
**Version:** 1.0  
**Status:** Draft — Pre-Implementation  
**Last Updated:** 2026-07-06

---

## Purpose

Document the REST API for **Document** resources — including presigned S3 upload, upload confirmation, version management, download, and hybrid full-text + semantic search. Documents are always scoped to a case and subject to matter wall enforcement.

---

## Scope

| In Scope | Out of Scope |
|----------|--------------|
| Initiate upload (presigned URL) | OCR pipeline internals (worker domain) |
| Confirm upload completion | Embedding generation (AI worker) |
| Document metadata CRUD | SharePoint sync (n8n workflow) |
| Version management | Virus scanning implementation |
| Presigned download URLs | Direct S3 access from frontend |
| Hybrid document search | Binary content streaming through API |

**Base paths:** `/api/v1/cases/{caseId}/documents`, `/api/v1/documents`  
**Storage:** AWS S3 (SSE-KMS encrypted) — binaries never pass through FastAPI

---

## Responsibilities

| Layer | Responsibility |
|-------|----------------|
| **Document router** | HTTP binding, presigned URL generation |
| **Document service** | Metadata persistence, version invariants |
| **S3 adapter** | Generate presigned PUT/GET URLs with TTL |
| **Authorization** | `document:*:assigned` + matter wall |
| **Processing worker** | Post-confirm: OCR, embedding, `DocumentProcessed` event |
| **Search service** | pgvector + PostgreSQL full-text hybrid query |

---

## Architecture

```mermaid
flowchart TB
    subgraph Client["Client"]
        UI[Next.js UI]
    end

    subgraph API["FastAPI"]
        INIT[POST .../documents<br/>Initiate Upload]
        CONF[POST .../confirm<br/>Confirm Upload]
        DL[GET .../download]
        SRCH[GET /documents/search]
    end

    subgraph Storage["Storage"]
        PG[(PostgreSQL — metadata)]
        S3[(S3 — binaries)]
        VEC[(pgvector — embeddings)]
    end

    subgraph Async["Async Processing"]
        MQ[RabbitMQ]
        W[Celery Worker]
    end

    UI -->|1. Request presigned URL| INIT
    INIT --> PG
    INIT -->|presigned PUT URL| UI
    UI -->|2. PUT file directly| S3
    UI -->|3. Confirm upload| CONF
    CONF --> PG
    CONF --> MQ
    MQ --> W
    W --> S3
    W --> PG
    W --> VEC
    UI -->|Download| DL
    DL -->|presigned GET URL| UI
    UI --> SRCH
    SRCH --> PG
    SRCH --> VEC
```

### Document Status Lifecycle

| Status | Description |
|--------|-------------|
| `pending_upload` | Presigned URL issued; awaiting client PUT |
| `uploaded` | Confirmed in S3; queued for processing |
| `processing` | OCR/embedding in progress |
| `ready` | Fully processed; searchable |
| `failed` | Processing failed (retry available) |
| `archived` | Case closed; read-only |

---

## Flow Diagrams

### Presigned Upload (Three-Step)

```mermaid
sequenceDiagram
    participant C as Client
    participant API as FastAPI
    participant S3 as AWS S3
    participant DB as PostgreSQL
    participant MQ as RabbitMQ
    participant W as Celery Worker

    C->>API: POST /api/v1/cases/{caseId}/documents<br/>{ title, fileName, contentType, sizeBytes }
    API->>API: Auth + RBAC + matter wall
    API->>DB: INSERT document (status: pending_upload)
    API->>S3: Generate presigned PUT URL (15 min TTL)
    API-->>C: 201 { documentId, uploadUrl, uploadHeaders, expiresAt }

    C->>S3: PUT {uploadUrl}<br/>Body: file bytes<br/>Content-Type, x-amz-server-side-encryption
    S3-->>C: 200 OK (ETag)

    C->>API: POST /api/v1/cases/{caseId}/documents/{docId}/confirm<br/>{ checksum, sizeBytes }
    API->>S3: HEAD object — verify exists + size
    API->>DB: UPDATE document (status: uploaded)
    API->>DB: INSERT outbox (DocumentUploaded)
    API-->>C: 200 { status: uploaded }

    MQ->>W: DocumentUploaded event
    W->>S3: GET object
    W->>W: OCR + virus scan
    W->>DB: UPDATE (status: ready, ocrText)
    W->>DB: INSERT embeddings (pgvector)
    W->>DB: INSERT outbox (DocumentProcessed)
```

### Presigned Download

```mermaid
sequenceDiagram
    participant C as Client
    participant API as FastAPI
    participant S3 as AWS S3
    participant DB as PostgreSQL

    C->>API: GET /api/v1/documents/{docId}/download
    API->>API: Auth + document:download:assigned + matter wall
    API->>DB: SELECT document metadata
    API->>S3: Generate presigned GET URL (15 min TTL)
    API->>DB: INSERT audit_log (document.downloaded)
    API-->>C: 200 { downloadUrl, expiresAt, fileName, contentType }
    C->>S3: GET {downloadUrl}
    S3-->>C: File bytes
```

### Document Search

```mermaid
sequenceDiagram
    participant C as Client
    participant API as FastAPI
    participant S as Search Service
    participant DB as PostgreSQL
    participant VEC as pgvector

    C->>API: GET /api/v1/documents/search?q=indemnification&caseId=...
    API->>API: Auth + filter to accessible cases (matter wall)
    API->>S: hybrid_search(query, accessible_case_ids)
    S->>DB: Full-text search (tsvector)
    S->>VEC: Semantic similarity (embedding)
    S->>S: Merge + rank results (RRF)
    S-->>API: Ranked document chunks
    API-->>C: 200 { data: results[] }
```

---

## Endpoints

### GET `/cases/{caseId}/documents`

List documents for a case.

**Permission:** `document:read:assigned` + matter wall

**Query parameters:** `documentType`, `status`, `search`, `sort`, `page`, `pageSize`

**Response (200):**

```json
{
  "data": [
    {
      "id": "d1e2f3a4-b5c6-7890-def1-234567890abc",
      "caseId": "c1d2e3f4-a5b6-7890-cdef-123456789012",
      "title": "Master Services Agreement",
      "fileName": "msa-acme-2026.pdf",
      "documentType": "contract",
      "status": "ready",
      "contentType": "application/pdf",
      "sizeBytes": 2457600,
      "currentVersion": 1,
      "ocrStatus": "completed",
      "uploadedBy": "d3e4f5a6-b7c8-9012-cdef-123456789012",
      "uploadedByName": "Pat Paralegal",
      "createdAt": "2026-07-05T14:00:00Z",
      "updatedAt": "2026-07-05T14:05:00Z"
    }
  ],
  "meta": {
    "requestId": "550e8400-e29b-41d4-a716-446655440000",
    "timestamp": "2026-07-06T08:00:00Z",
    "pagination": { "page": 1, "pageSize": 25, "totalItems": 34, "totalPages": 2 }
  }
}
```

---

### POST `/cases/{caseId}/documents`

Initiate document upload — returns presigned S3 PUT URL.

**Permission:** `document:write:assigned` + matter wall

**Request:**

```json
{
  "title": "Master Services Agreement",
  "fileName": "msa-acme-2026.pdf",
  "contentType": "application/pdf",
  "sizeBytes": 2457600,
  "documentType": "contract"
}
```

**Validation:**

| Field | Rule |
|-------|------|
| `sizeBytes` | Max 100 MB (configurable per firm) |
| `contentType` | Allowlist: PDF, DOCX, DOC, XLSX, PNG, JPG, TIFF, MSG, EML |
| `fileName` | No path traversal; max 255 chars |
| Case status | Must not be `closed` or `archived` |

**Response (201):**

```json
{
  "data": {
    "documentId": "d1e2f3a4-b5c6-7890-def1-234567890abc",
    "uploadUrl": "https://lexflow-docs.s3.amazonaws.com/firms/.../cases/.../d1e2f3...?X-Amz-...",
    "uploadMethod": "PUT",
    "uploadHeaders": {
      "Content-Type": "application/pdf",
      "x-amz-server-side-encryption": "aws:kms",
      "x-amz-server-side-encryption-aws-kms-key-id": "arn:aws:kms:..."
    },
    "expiresAt": "2026-07-06T08:15:00Z",
    "maxSizeBytes": 104857600
  },
  "meta": {
    "requestId": "550e8400-e29b-41d4-a716-446655440000",
    "timestamp": "2026-07-06T08:00:00Z"
  }
}
```

---

### POST `/cases/{caseId}/documents/{documentId}/confirm`

Confirm upload completed. Triggers async processing pipeline.

**Permission:** `document:write:assigned` + matter wall

**Request:**

```json
{
  "checksum": "a1b2c3d4e5f6789012345678901234567890abcdef1234567890abcdef123456",
  "sizeBytes": 2457600
}
```

**Response (200):**

```json
{
  "data": {
    "id": "d1e2f3a4-b5c6-7890-def1-234567890abc",
    "status": "uploaded",
    "processingJobId": "j1a2b3c4-d5e6-7890-abcd-ef1234567890",
    "statusUrl": "/api/v1/jobs/j1a2b3c4-d5e6-7890-abcd-ef1234567890"
  },
  "meta": {
    "requestId": "550e8400-e29b-41d4-a716-446655440000",
    "timestamp": "2026-07-06T08:00:00Z"
  }
}
```

**Errors:**
- `404` — Document not found or not in `pending_upload` status
- `422` — S3 object not found or size/checksum mismatch

---

### GET `/documents/{documentId}`

Get document metadata (any case — authorization resolves via document's caseId).

**Permission:** `document:read:assigned` + matter wall

**Response (200):**

```json
{
  "data": {
    "id": "d1e2f3a4-b5c6-7890-def1-234567890abc",
    "caseId": "c1d2e3f4-a5b6-7890-cdef-123456789012",
    "caseTitle": "Smith v. Acme Corp",
    "title": "Master Services Agreement",
    "fileName": "msa-acme-2026.pdf",
    "documentType": "contract",
    "status": "ready",
    "contentType": "application/pdf",
    "sizeBytes": 2457600,
    "checksum": "a1b2c3d4...",
    "currentVersion": 2,
    "versions": [
      {
        "versionNumber": 1,
        "sizeBytes": 2457600,
        "createdBy": "d3e4f5a6-b7c8-9012-cdef-123456789012",
        "createdAt": "2026-07-05T14:00:00Z"
      },
      {
        "versionNumber": 2,
        "sizeBytes": 2483200,
        "createdBy": "b2c3d4e5-f6a7-8901-bcde-f12345678901",
        "createdAt": "2026-07-06T09:00:00Z"
      }
    ],
    "ocrStatus": "completed",
    "uploadedBy": "d3e4f5a6-b7c8-9012-cdef-123456789012",
    "version": 3,
    "createdAt": "2026-07-05T14:00:00Z",
    "updatedAt": "2026-07-06T09:00:00Z"
  },
  "meta": { "requestId": "...", "timestamp": "..." }
}
```

---

### GET `/documents/{documentId}/download`

Get presigned download URL.

**Permission:** `document:download:assigned` + matter wall

**Response (200):**

```json
{
  "data": {
    "downloadUrl": "https://lexflow-docs.s3.amazonaws.com/firms/.../...?X-Amz-...",
    "expiresAt": "2026-07-06T08:15:00Z",
    "fileName": "msa-acme-2026.pdf",
    "contentType": "application/pdf",
    "sizeBytes": 2483200
  },
  "meta": { "requestId": "...", "timestamp": "..." }
}
```

Every download is **audit logged** with actor, document ID, and timestamp.

---

### POST `/documents/{documentId}/versions`

Upload a new version (same three-step presigned flow).

**Permission:** `document:write:assigned` + matter wall

**Request (step 1 — initiate):**

```json
{
  "fileName": "msa-acme-2026-v2.pdf",
  "contentType": "application/pdf",
  "sizeBytes": 2483200
}
```

**Response (201):** Same presigned URL shape as initial upload, with `versionNumber: 2`.

Confirm via: `POST /documents/{documentId}/versions/{versionNumber}/confirm`

---

### GET `/documents/search`

Hybrid full-text + semantic search across accessible documents.

**Permission:** `document:read:assigned` (results filtered by matter wall)

**Query parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `q` | string | Search query (required) |
| `caseId` | uuid | Scope to single case (optional) |
| `documentType` | string | Filter by type |
| `mode` | string | `hybrid` (default), `keyword`, `semantic` |
| `limit` | int | Max results (default 20, max 50) |

**Request:**

```http
GET /api/v1/documents/search?q=indemnification+clause&caseId=c1d2e3f4-...&mode=hybrid&limit=10
Authorization: Bearer eyJhbGciOiJSUzI1NiIs...
```

**Response (200):**

```json
{
  "data": [
    {
      "documentId": "d1e2f3a4-b5c6-7890-def1-234567890abc",
      "caseId": "c1d2e3f4-a5b6-7890-cdef-123456789012",
      "caseTitle": "Smith v. Acme Corp",
      "documentTitle": "Master Services Agreement",
      "documentType": "contract",
      "snippet": "...party shall provide **indemnification** for all claims arising from...",
      "pageNumber": 12,
      "score": 0.92,
      "matchType": "hybrid"
    },
    {
      "documentId": "d2f3a4b5-c6d7-8901-ef12-345678901bcd",
      "caseId": "c1d2e3f4-a5b6-7890-cdef-123456789012",
      "caseTitle": "Smith v. Acme Corp",
      "documentTitle": "Amendment No. 1",
      "documentType": "contract",
      "snippet": "...limitation of liability shall not apply to **indemnification** obligations...",
      "pageNumber": 3,
      "score": 0.87,
      "matchType": "semantic"
    }
  ],
  "meta": {
    "requestId": "550e8400-e29b-41d4-a716-446655440000",
    "timestamp": "2026-07-06T08:00:00Z",
    "searchMeta": {
      "query": "indemnification clause",
      "mode": "hybrid",
      "totalResults": 2,
      "searchDurationMs": 145
    }
  }
}
```

---

## S3 Key Convention

```
s3://lexflow-docs/
  firms/{firmId}/
    cases/{caseId}/
      documents/{documentId}/
        v{versionNumber}/{fileName}
```

---

## Rate Limits

| Endpoint | Limit |
|----------|-------|
| `POST .../documents` (initiate) | 50 req/min per user |
| `POST .../confirm` | 50 req/min per user |
| `GET .../download` | 100 req/min per user |
| `GET /documents/search` | 30 req/min per user |

---

## Best Practices

1. **Always PUT directly to S3** — never send file bytes through the API.
2. **Confirm promptly** after S3 PUT — presigned URLs expire in 15 minutes.
3. **Compute SHA-256 client-side** before confirm for integrity verification.
4. **Poll `statusUrl`** after confirm until `status: ready` before triggering AI on document.
5. **Use `documentType` consistently** — enables filtered search and workflow routing.
6. **Handle upload failure gracefully** — abandoned `pending_upload` records are garbage-collected after 24 hours.

---

## Tradeoffs

| Decision | Benefit | Cost |
|----------|---------|------|
| Presigned S3 upload | No API bottleneck for large files; lower latency | Three-step client flow |
| Binaries never through API | Scalability, cost | Client must handle S3 PUT errors |
| Hybrid search (keyword + semantic) | Better legal document recall | Higher query latency (~100–300ms) |
| 15-minute presigned TTL | Security | Client must complete upload quickly |
| Async OCR/processing | Non-blocking confirm response | Document not immediately searchable |

---

## Future Improvements

- Multipart upload for files > 100 MB
- Bulk upload API (`POST /cases/{id}/documents/bulk`)
- Document preview/thumbnail generation endpoint
- WORM / legal hold flag on documents
- SharePoint bidirectional sync status in metadata
- Client-side encryption (CSE) for restricted matters

---

## References

- [endpoints-cases.md](./endpoints-cases.md) — Parent case resource
- [endpoints-ai.md](./endpoints-ai.md) — AI operations on processed documents
- [authorization-rbac.md](./authorization-rbac.md) — Document permissions
- [../02-domain/domain-model.md](../domain-model.md) — Document aggregate
- [../08-security/security-architecture.md](../security-architecture.md) — S3 SSE-KMS
- [../ai-architecture.md](../ai-architecture.md) — RAG retrieval from document embeddings
- [../database-architecture.md](../database-architecture.md) — Documents schema, pgvector indexes

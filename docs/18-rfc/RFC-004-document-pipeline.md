# RFC-004: Document Upload & OCR Pipeline

**Status:** Planned  
**Author:** TBD  
**Created:** 2026-07-06  
**Sprint / Epic:** Sprint 4 — AI & n8n  
**Related ADRs:** [ADR-002](../13-decisions/002-n8n-orchestration-only.md), [ADR-004](../13-decisions/004-async-ai-processing.md)

---

## Summary

> **Planned RFC** — full draft required before Sprint 4 kickoff. Copy [`_template.md`](./_template.md) and replace this stub.

Case-scoped document upload to S3, versioning, async OCR/extraction, pgvector embedding pipeline, semantic search API.

---

## Draft Checklist (before In Review)

- [ ] Upload flow: presigned URL vs direct upload decision
- [ ] Versioning model — `docs/02-domain/document-aggregate.md`
- [ ] OCR worker + n8n orchestration boundary (ADR-002)
- [ ] Embedding + HNSW index strategy
- [ ] UI: document viewer — `docs/16-design-system/screens/document-viewer.md`
- [ ] Matter wall on document GET

---

## References

- [document-aggregate.md](../02-domain/document-aggregate.md)
- [endpoints-documents.md](../04-api/endpoints-documents.md)
- [documents-schema.md](../05-database/documents-schema.md)

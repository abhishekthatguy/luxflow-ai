# RFC-005: n8n Orchestration Bootstrap

**Status:** Planned  
**Author:** TBD  
**Created:** 2026-07-06  
**Sprint / Epic:** Sprint 4 — AI & n8n  
**Related ADRs:** [ADR-002](../13-decisions/002-n8n-orchestration-only.md), [ADR-006](../13-decisions/006-transactional-outbox.md)

---

## Summary

> **Planned RFC** — full draft required before Sprint 4 kickoff. Copy [`_template.md`](./_template.md) and replace this stub.

Private n8n deployment pattern, first production workflow (document notification or intake), HMAC callback contracts, dev → staging → prod promotion.

---

## Draft Checklist (before In Review)

- [ ] FastAPI ↔ n8n webhook payloads — `docs/06-workflows/webhook-contracts.md`
- [ ] Explicit list of what n8n does vs FastAPI (ADR-002)
- [ ] Retry/DLQ — `docs/06-workflows/retry-dlq.md`
- [ ] JSON schema + workflow JSON repo layout
- [ ] Security: private network, no PostgreSQL nodes
- [ ] First workflow catalog entry

---

## References

- [n8n-integration.md](../06-workflows/n8n-integration.md)
- [orchestration-model.md](../06-workflows/orchestration-model.md)
- [promotion-pipeline.md](../06-workflows/promotion-pipeline.md)

# RFC-003: Async AI Case Summaries

**Status:** Planned  
**Author:** TBD  
**Created:** 2026-07-06  
**Sprint / Epic:** Sprint 4 — AI & n8n  
**Related ADRs:** [ADR-004](../13-decisions/004-async-ai-processing.md), [ADR-008](../13-decisions/008-azure-openai-primary.md)

---

## Summary

> **Planned RFC** — full draft required before Sprint 4 kickoff. Copy [`_template.md`](./_template.md) and replace this stub.

Attorney-triggered case summary generation: 202 Accepted, Celery worker, PII redaction, HITL approval before team visibility, token metering.

---

## Draft Checklist (before In Review)

- [ ] Async sequence: API → queue → worker → LLM → HITL gate
- [ ] API sketch: `docs/04-api/endpoints-ai.md`
- [ ] Prompt template versioning — `docs/07-ai/prompt-management.md`
- [ ] HITL flow — `docs/07-ai/human-in-the-loop.md`
- [ ] UI: AI summary + approval screens
- [ ] Security: PII redaction, case-scoped RAG

---

## References

- [sprint-04-ai-n8n.md](../17-sprint-planning/sprint-04-ai-n8n.md)
- [ai-aggregate.md](../02-domain/ai-aggregate.md)
- [endpoints-ai.md](../04-api/endpoints-ai.md)

# Definition of Ready (DoR)

**LexFlow AI** — When a Ticket Is Ready for Engineering  
**Version:** 1.0 · **Last Updated:** 2026-07-06

---

## Purpose

Definition of Ready defines the minimum criteria a backlog item must meet **before an engineer starts implementation**. It prevents rework, blocked PRs, and missing security or test requirements.

---

## Universal Criteria (All Issue Types)

Every ticket must have:

- [ ] **Clear title** — describes the outcome, not the implementation
- [ ] **Issue template completed** — feature, bug, or tech-debt template filled
- [ ] **Acceptance criteria** — testable conditions for success (Given/When/Then or checklist)
- [ ] **Bounded context identified** — which `services/{context}/` owns the change
- [ ] **Priority assigned** — P1–P4 or sprint priority
- [ ] **Size estimated** — S (< 1 day), M (1–3 days), L (3–5 days), XL (needs splitting)
- [ ] **No unresolved blockers** — dependencies identified and available or scheduled
- [ ] **Security impact assessed** — does it touch auth, matter walls, PII, or AI outputs?

---

## Feature — Additional Criteria

- [ ] **User persona identified** — which persona benefits (from `docs/01-product/user-personas.md`)
- [ ] **Product alignment** — does not contradict `docs/01-product/non-goals.md`
- [ ] **API contract sketched** — endpoint method, path, request/response shape (or N/A for UI-only)
- [ ] **UI mockup or wireframe** — for user-facing changes (or explicit "no UI change")
- [ ] **Domain impact noted** — new entities, events, or state transitions?
- [ ] **Schema impact noted** — new tables, columns, or migrations needed?
- [ ] **Matter wall impact assessed** — case-scoped? participant rules?
- [ ] **ADR required?** — see [adr-process.md](./adr-process.md) decision tree
- [ ] **Test strategy outlined** — unit, integration, E2E requirements

---

## Bug — Additional Criteria

- [ ] **Severity assigned** — P1 (production) through P4 (cosmetic)
- [ ] **Reproduction steps** — concrete steps to reproduce
- [ ] **Expected vs actual behavior** — clearly stated
- [ ] **Environment** — where observed (local, staging, production)
- [ ] **Affected version/commit** — if known
- [ ] **Regression test plan** — test to prevent recurrence

---

## Tech Debt — Additional Criteria

- [ ] **Problem statement** — what pain does this debt cause?
- [ ] **Proposed solution** — approach outlined (not just "refactor X")
- [ ] **Risk of NOT fixing** — what breaks or degrades if deferred?
- [ ] **Scope bounded** — explicit list of files/modules in scope
- [ ] **No scope creep** — out-of-scope items listed
- [ ] **Test safety net** — existing tests pass; new tests if behavior changes

---

## Security-Sensitive Work — Additional Criteria

Required when ticket touches: authentication, authorization, matter walls, PII, AI prompts/outputs, encryption, or external integrations.

- [ ] **Threat model reference** — which STRIDE categories apply (`docs/08-security/threat-model.md`)
- [ ] **Matter wall matrix rows identified** — role × participant × expected response
- [ ] **PII handling documented** — what data flows where; redaction requirements
- [ ] **Security reviewer assigned** — for review before merge
- [ ] **Security test plan** — specific tests from `docs/10-testing/security-testing.md`

---

## AI Feature — Additional Criteria

Required when ticket involves LLM calls, RAG, prompt templates, or AI-generated legal content.

- [ ] **Async pattern confirmed** — 202 Accepted, Celery worker (ADR-004)
- [ ] **HITL requirement assessed** — attorney approval needed? (`docs/07-ai/human-in-the-loop.md`)
- [ ] **PII redaction plan** — before LLM call (`docs/07-ai/safety-guardrails.md`)
- [ ] **Provider identified** — Azure OpenAI default (ADR-008) or adapter
- [ ] **Usage metering** — token tracking requirements (`docs/07-ai/usage-metering.md`)
- [ ] **Prompt template versioning** — new or modified prompt in registry

---

## n8n Workflow — Additional Criteria

- [ ] **Orchestration only** — no business logic in n8n (ADR-002)
- [ ] **Trigger + callback contract defined** — JSON schemas drafted
- [ ] **FastAPI handler ticket linked** — backend work tracked separately or same PR
- [ ] **External services identified** — Microsoft Graph, email, etc.
- [ ] **Promotion plan** — dev → staging → production

---

## DoR Decision

| State | Label | Action |
|-------|-------|--------|
| Not ready | `needs-refinement` | Return to refinement; list missing criteria |
| Ready | `ready` | Assign to engineer; may enter sprint |
| Blocked | `blocked` | Document blocker and owner |

**Only issues labeled `ready` may be picked up for development.**

---

## DoR Checklist Template (for issue comments)

```markdown
## Definition of Ready Check

- [ ] Clear title and acceptance criteria
- [ ] Bounded context: {{context}}
- [ ] Size: {{S/M/L/XL}}
- [ ] Security impact: {{none / low / high}}
- [ ] Matter wall impact: {{none / case-scoped}}
- [ ] ADR required: {{yes / no}}
- [ ] Test strategy: {{unit / integration / e2e}}

**Decision:** Ready / Needs Refinement / Blocked
**Reviewer:** {{name}}
**Date:** {{date}}
```

---

## References

- [Definition of Done](./definition-of-done.md)
- [Development Lifecycle](./development-lifecycle.md)
- [ADR Process](./adr-process.md)
- [Issue Templates](../templates/)
- [Product Non-Goals](../../docs/01-product/non-goals.md)

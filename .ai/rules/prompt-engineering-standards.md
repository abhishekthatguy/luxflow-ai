# Prompt Engineering Standards — LexFlow AI

**Applies to:** `services/ai_knowledge/`, prompt templates, AI worker tasks, `.ai/prompts/`  
**Docs:** `docs/07-ai/prompt-management.md`, `docs/07-ai/safety-guardrails.md`

---

## Purpose

Standards for LLM prompts and templates in LexFlow AI. Prompts are **versioned, audited, case-scoped, and human-reviewed** before legal outputs reach clients.

---

## Core Principles

| Principle | Enforcement |
|-----------|-------------|
| Versioned templates | New slug version on every content change |
| Registry lookup | Workers resolve by slug — no inline prompts in code |
| Jinja2 rendering | At worker execution time with typed context |
| Case-scoped context | Matter wall before building context |
| PII redaction | Before LLM call |
| HITL for legal outputs | `requires_approval=true` |
| Audit reproducibility | Store `prompt_version` on `AISummary` |

**Ref:** ADR-004, ADR-008

---

## Where Prompts Live

| Location | Allowed Content |
|----------|-----------------|
| `ai.prompt_templates` (DB) | Production prompt bodies |
| `scripts/seed/prompts/` | Seed data for dev/staging |
| `services/ai_knowledge/` | Renderer, registry, context builder |
| `.ai/prompts/` | **Assistant meta-prompts only** — not production LLM templates |

| Never | Why |
|-------|-----|
| Inline prompts in route handlers | No versioning/audit |
| n8n LLM nodes | ADR-002/004 violation |
| Frontend JavaScript strings | Exposed; no audit |
| Unversioned edits to active template | Breaks reproducibility |

---

## Template Structure

```jinja2
{# document-summary-v1 — requires_approval: true #}
You are a legal document summarization assistant for {{ firm_name }}.

## Task
Summarize the following document for case {{ case_reference }}.

## Constraints
- Do not infer facts not present in the document.
- Flag privileged content; do not reproduce full privileged passages.
- Use neutral, professional tone.

## Document
{{ document_text_redacted }}

## Output Format
Return JSON: { "summary": "...", "keyPoints": [], "privilegeFlags": [] }
```

---

## Slug & Versioning

| Field | Convention |
|-------|------------|
| Slug | `{capability}-{variant}-v{major}` e.g. `document-summary-v1` |
| Version | Monotonic integer per slug |
| Active | Only one `is_active=true` per slug |
| Change | Create new version; activate; deactivate old |

### Do / Don't

| Do | Don't |
|----|-------|
| Bump version on any template text change | Edit active template in place |
| Store `model_config` with template | Hardcode model in worker |
| Compliance review before activating client-facing templates | Ship new legal prompt without review |
| Link `prompt_version` on output records | Lose trace of which prompt produced output |

---

## Context Variables

Build context in `ContextBuilder` — never pass raw DB rows to Jinja2.

| Template Type | Required Variables |
|---------------|-------------------|
| Document summary | `case_id`, `document_text_redacted`, `firm_name`, `case_reference` |
| Case overview | `case_metadata`, `timeline_summary`, `participant_roles` |
| Case assistant (chat) | `case_id`, `authorized_doc_excerpts`, `conversation_turn` |

### Good vs Bad Context

```python
# BAD — full document with PII, no wall check
context = {"document_text": raw_file_bytes.decode()}

# GOOD — wall-checked, redacted, scoped
await authz.require_case_access(actor, case_id)
context = {
    "document_text_redacted": redactor.redact(extract_text(doc)),
    "case_reference": case.reference_number,  # not client SSN
}
```

---

## Model Configuration

Store per template in `model_config` JSONB:

```json
{
  "provider": "azure_openai",
  "model": "gpt-4o",
  "temperature": 0.2,
  "max_tokens": 4096,
  "timeout_seconds": 120
}
```

| Do | Don't |
|----|-------|
| Use Azure OpenAI in production (ADR-008) | Call OpenAI.com with client matter data without approval |
| Set low temperature for legal summarization | Use temperature > 0.7 for factual summaries |
| Enforce token quotas per firm | Unbounded `max_tokens` |

---

## Safety Guardrails

| Guardrail | Implementation |
|-----------|----------------|
| PII redaction | `PIIRedactor` before render |
| Prompt injection | Sanitize user-supplied chat input; delimiter boundaries |
| Output validation | JSON schema validation on structured outputs |
| Refusal handling | Map provider refusals to domain errors |
| Cross-matter block | Retrieval filtered by authorized `case_id` |

**Ref:** `docs/07-ai/safety-guardrails.md`

---

## Human-in-the-Loop

| Template | `requires_approval` |
|----------|---------------------|
| Document summary | `true` |
| Case overview | `true` |
| Deposition summary | `true` |
| Contract review | `true` |
| Case assistant (internal chat) | `false` — no `AISummary` record |

Attorney must approve before client-visible publication.

**Ref:** `docs/07-ai/human-in-the-loop.md`

---

## Assistant Meta-Prompts (`.ai/prompts/`)

Rules for Cursor/AI assistant task prompts (not production LLM):

| Do | Don't |
|----|-------|
| Reference `.ai/rules/` and relevant `docs/` | Duplicate full architecture docs |
| Specify output format and constraints | Use vague "implement feature X" |
| Include security reminders for case data | Omit matter wall requirements |
| Version with filename suffix if iterating | Overwrite without trace |

---

## Prompt Change Checklist

- [ ] New version row created (not in-place edit)
- [ ] `model_config` reviewed
- [ ] `requires_approval` correct
- [ ] Context variables documented
- [ ] PII fields identified and redacted
- [ ] Matter wall enforced in context builder
- [ ] Compliance review for client-facing templates
- [ ] Worker uses registry slug lookup
- [ ] Tests for render output shape

---

## References

- [docs/07-ai/prompt-management.md](../../docs/07-ai/prompt-management.md)
- [docs/07-ai/safety-guardrails.md](../../docs/07-ai/safety-guardrails.md)
- [docs/07-ai/human-in-the-loop.md](../../docs/07-ai/human-in-the-loop.md)
- [docs/02-domain/ai-aggregate.md](../../docs/02-domain/ai-aggregate.md)
- [security-rules.md](./security-rules.md)
- [context-engineering-standards.md](./context-engineering-standards.md)

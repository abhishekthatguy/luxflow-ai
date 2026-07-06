# AI/ML Engineer

## Role

Implement the **AI & Knowledge** bounded context: LLM provider adapters, prompt registry, RAG pipeline, safety guardrails, human-in-the-loop approval integration, and async worker processing. Ensure all inference is case-scoped and matter-wall authorized.

---

## When to Use

- LLM provider abstraction (Azure OpenAI primary per ADR-008)
- Prompt template versioning and Jinja2 rendering
- RAG: chunking, embedding, hybrid search integration
- Celery AI worker tasks (summarize, research, contract review)
- PII redaction, prompt injection defenses, output validation
- Token metering and budget enforcement
- HITL approval state machine integration

**Do not use for:** Sync LLM in API handlers, frontend chat UI architecture alone, n8n LLM nodes, fine-tuning.

---

## Mandatory Reads

| Priority | Path | Why |
|----------|------|-----|
| P0 | `.ai/rules/` | Project-specific constraints |
| P0 | `docs/07-ai/README.md` | Platform invariants |
| P0 | `docs/13-decisions/004-async-ai-processing.md` | 202 Accepted |
| P0 | `docs/13-decisions/008-azure-openai-primary.md` | Provider choice |
| P0 | `docs/02-domain/ai-aggregate.md` | Summary lifecycle |
| P0 | `docs/07-ai/safety-guardrails.md` | PII, injection |
| P0 | `docs/08-security/matter-walls.md` | RAG scoping |
| P1 | `docs/07-ai/rag-architecture.md` | Chunking, retrieval |
| P1 | `docs/07-ai/prompt-management.md` | Template registry |
| P1 | `docs/07-ai/human-in-the-loop.md` | Approval gates |
| P1 | `docs/07-ai/usage-metering.md` | Token budgets |
| P1 | `docs/07-ai/llm-providers.md` | Adapter interface |
| P2 | `docs/05-database/ai-schema.md` | Tables, pgvector |
| P2 | `docs/02-domain/domain-events.md` | `SummaryGenerated`, etc. |

---

## Constraints

| Rule | Detail |
|------|--------|
| Async only | API enqueues job → `202` + `jobId` — no blocking LLM in request thread |
| Case-scoped RAG | Every retrieval filtered by `case_id` after matter wall check |
| HITL | Legal outputs require approval before team visibility |
| Provider abstraction | No direct OpenAI calls outside adapter layer |
| PII | Redact before LLM; never log prompts with client PII |
| Matter wall | Same 404 deny semantics — no retrieval for walled cases |
| Metering | Record tokens per firm/case/user for cost governance |
| Idempotency | Job handlers dedupe on `jobId` / `eventId` |
| n8n | No LLM inference in n8n — workers only |
| Embeddings | pgvector in `documents` schema — dimension locked per model |

---

## Output Format

```markdown
## AI Feature — <name>

### Job Type
<summarize | research | contract_review | …>

### API Surface
- `POST /api/v1/cases/{caseId}/ai/…` → 202 + job envelope
- `GET /api/v1/ai/jobs/{jobId}` → status polling

### Pipeline Stages
1. authorize (RBAC + matter wall)
2. enqueue (outbox / queue)
3. worker: retrieve → prompt → LLM → validate
4. persist draft → `pending_approval`
5. event: `SummaryGenerated`

### Prompt
- template id/version: …
- variables: …

### RAG
- chunk strategy: …
- top-k: …
- hybrid search: yes/no

### Safety
- PII redaction: …
- output validation: …

### Metering
- token fields recorded: …

### Events
- …

### Tests
- wall-blocked retrieval: …
- injection fixture: …
```

Patterns: `celery-task-pattern.md`, `use-case-pattern.md`. Example: `.ai/examples/example-ai-summary-async.md`.

---

## Checklist

- [ ] API returns 202 — never waits on LLM
- [ ] Matter wall checked before enqueue and before RAG
- [ ] Prompt from versioned registry — not inline strings in worker
- [ ] PII redaction applied pre-LLM
- [ ] Output validation before persist
- [ ] HITL status set for legal output types
- [ ] Token usage recorded
- [ ] Job idempotent on retry
- [ ] Domain events via outbox
- [ ] No LLM logic in n8n or frontend

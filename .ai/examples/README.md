# LexFlow AI — Annotated Examples

**Purpose:** End-to-end structural walkthroughs showing how patterns compose across layers.  
**Not included:** Runnable code — reference these when implementing similar flows.

---

## Example Index

| Example | File | Flow Type |
|---------|------|-----------|
| Create case API | [example-create-case-api.md](./example-create-case-api.md) | Sync REST + outbox |
| Document upload | [example-document-upload-flow.md](./example-document-upload-flow.md) | Presigned S3 + async processing |
| AI summary async | [example-ai-summary-async.md](./example-ai-summary-async.md) | 202 + Celery + HITL |
| Workflow trigger | [example-workflow-trigger.md](./example-workflow-trigger.md) | Event → n8n → callback |
| Matter wall check | [example-matter-wall-check.md](./example-matter-wall-check.md) | RBAC + ABAC |
| Audit log entry | [example-audit-log-entry.md](./example-audit-log-entry.md) | Immutable audit trail |

---

## How to Read Examples

Each example contains:

1. **Scenario** — user story and trigger
2. **Flow** — sequence across layers (mermaid or numbered steps)
3. **Structural Annotation** — which files/patterns apply (no code)
4. **Cross-References** — docs and patterns
5. **Key Decisions Applied** — ADRs and invariants

---

## Layer Legend

| Symbol | Layer |
|--------|-------|
| `[API]` | `apps/api/` route handler |
| `[APP]` | `services/*/application/` use case |
| `[DOM]` | `services/*/domain/` entity |
| `[INF]` | `services/*/infrastructure/` repo/adapter |
| `[OB]` | Outbox / `shared.outbox_events` |
| `[WK]` | Celery worker task |
| `[N8N]` | n8n workflow JSON |
| `[UI]` | Next.js page/hook |
| `[AUD]` | `audit.audit_logs` |

---

## References

| Resource | Path |
|----------|------|
| Patterns | `.ai/patterns/` |
| Agents | `.ai/agents/` |
| Rules | `.ai/rules/` |
| Domain | `docs/02-domain/` |
| API | `docs/04-api/` |
| ADRs | `docs/13-decisions/` |

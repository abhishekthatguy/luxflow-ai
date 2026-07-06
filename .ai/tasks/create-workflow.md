# Task: Create n8n Workflow

**LexFlow AI** — AI prompt template for new orchestration workflows.

---

## Prompt (Copy-Paste Ready)

```
You are creating a new n8n workflow for LexFlow AI, an enterprise AI automation platform for law firms.

## Feature
{{feature_name}}

## Workflow Specification
- Workflow slug: {{workflow_slug}}
- Domain folder: {{workflow_domain}}
- Trigger type: {{trigger_type}} (webhook | schedule | event)
- Ticket: {{ticket_id}}

## Context to Load
Read these before writing any code:

1. `.ai/memory/` — project memory and recent decisions
2. `.ai/rules/` — AI coding rules for this repo
3. `docs/06-workflows/orchestration-model.md` — FastAPI vs n8n responsibilities
4. `docs/06-workflows/n8n-integration.md` — private deployment and security
5. `docs/06-workflows/webhook-contracts.md` — FastAPI ↔ n8n payloads
6. `docs/06-workflows/workflow-catalog.md` — existing catalog entry format
7. `docs/06-workflows/retry-dlq.md` — retry policies and dead letter queues
8. `docs/06-workflows/promotion-pipeline.md` — dev → staging → production
9. `docs/14-playbooks/add-workflow.md` — end-to-end procedure
10. `docs/13-decisions/002-n8n-orchestration-only.md` — NO business logic in n8n
11. Template: `n8n/workflows/_templates/basic-webhook-callback.json`
12. Existing workflows: `n8n/workflows/{{workflow_domain}}/`

## Constraints
- n8n is ORCHESTRATION ONLY — no business rules, validation, or authorization in workflow nodes
- Business logic MUST live in FastAPI (`services/workflow_orchestration/`)
- n8n is NOT publicly accessible — triggered by FastAPI or internal scheduler only
- Workflow JSON stored in repo: `n8n/workflows/{{workflow_domain}}/{{workflow_slug}}.json`
- Naming: kebab-case with version suffix (e.g., `deadline-reminder-v1`)
- HMAC-signed callbacks to FastAPI internal webhooks (`/api/v1/internal/webhooks/`)
- No inline secrets — use n8n credential references (never commit credentials)
- Prohibited nodes: arbitrary code execution without security review
- JSON schemas for trigger payload and callback in `n8n/schemas/`
- Retry policy per retry-dlq.md; DLQ alert on exhaustion

## Step-by-Step Instructions
1. **Contract** — Define trigger payload schema and callback payload schema
2. **FastAPI handler** — Coordinate backend PR for trigger endpoint + callback handler (create-api.md)
3. **Catalog entry** — Add row to `docs/06-workflows/workflow-catalog.md`
4. **Template** — Copy `n8n/workflows/_templates/basic-webhook-callback.json`
5. **Build** — Author workflow in local n8n (docker-compose); test with mock payloads
6. **Export** — Export JSON to `n8n/workflows/{{workflow_domain}}/{{workflow_slug}}.json`
7. **Schema** — Add JSON Schema files in `n8n/schemas/{{workflow_slug}}/`
8. **CI validation** — Ensure workflow passes JSON lint and schema validation gates
9. **Integration test** — Test FastAPI trigger → n8n → callback round-trip
10. **Promotion** — Document staging/production import steps per promotion-pipeline.md

## Output Format
Deliver in this order:

### 1. Design Summary
- Workflow purpose and trigger mechanism
- FastAPI endpoints involved (trigger + callback)
- External services called (Microsoft Graph, email, etc.)
- Sequence diagram (Mermaid)

### 2. Contract Definitions
- Trigger request JSON schema
- Callback request JSON schema
- Error response handling

### 3. Workflow JSON
- Complete `{{workflow_slug}}.json` export
- Node-by-node description table

### 4. Catalog Entry
- Markdown row for workflow-catalog.md

### 5. FastAPI Integration Points
- Trigger handler signature
- Callback handler signature
- HMAC verification requirements

### 6. Test Plan
- Local test procedure
- Integration test cases
- Rollback procedure

## Verification Checklist
- [ ] No business logic in n8n nodes (validation, auth, calculations in FastAPI)
- [ ] Workflow slug matches filename and catalog entry
- [ ] JSON schemas committed in `n8n/schemas/`
- [ ] HMAC callback to internal webhook endpoint
- [ ] No secrets or credentials in committed JSON
- [ ] Retry policy configured per retry-dlq.md
- [ ] Error branch routes to DLQ or alert
- [ ] Catalog updated in workflow-catalog.md
- [ ] webhook-contracts.md updated if new contract shape
- [ ] ADR-002 compliance confirmed
- [ ] Local round-trip test documented
- [ ] Promotion steps documented for staging/production
```

---

## Example Variables

| Variable | Example Value |
|----------|---------------|
| `{{feature_name}}` | Deadline reminder email notification |
| `{{workflow_slug}}` | deadline-reminder-v1 |
| `{{workflow_domain}}` | notifications |
| `{{trigger_type}}` | webhook |
| `{{ticket_id}}` | LEX-145 |

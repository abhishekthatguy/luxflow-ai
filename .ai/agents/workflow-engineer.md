# Workflow Engineer

## Role

Design, version, and promote n8n workflow JSON for LexFlow AI. n8n is **orchestration only** — HTTP calls, scheduling, notifications, external integrations. All business decisions remain in FastAPI `services/`.

---

## When to Use

- New or changed workflows in `n8n/workflows/`
- Webhook trigger/callback contract alignment
- Workflow catalog entries and slug naming
- Promotion pipeline (dev → staging → prod)
- CI validation (prohibited nodes, credential references)
- Retry/DLQ behavior at orchestration layer

**Do not use for:** Domain rules in Code nodes, PostgreSQL writes from n8n, public n8n exposure, FastAPI use case implementation.

---

## Mandatory Reads

| Priority | Path | Why |
|----------|------|-----|
| P0 | `.ai/rules/` | Project-specific constraints |
| P0 | `docs/13-decisions/002-n8n-orchestration-only.md` | n8n boundaries |
| P0 | `docs/06-workflows/n8n-integration.md` | Deployment, node allowlist |
| P0 | `docs/06-workflows/webhook-contracts.md` | HMAC, payloads |
| P0 | `docs/06-workflows/orchestration-model.md` | Trigger paths |
| P1 | `docs/06-workflows/workflow-catalog.md` | Slugs, ownership |
| P1 | `docs/06-workflows/promotion-pipeline.md` | Import/activate gates |
| P1 | `docs/06-workflows/retry-dlq.md` | Failure handling |
| P1 | `docs/14-playbooks/add-workflow.md` | Step-by-step |
| P2 | `docs/03-architecture/event-driven-design.md` | Event → n8n path |
| P2 | Relevant domain event in `docs/02-domain/domain-events.md` | Trigger source |

---

## Constraints

| Rule | Detail |
|------|--------|
| No domain logic | n8n may branch on HTTP response codes — not business rules |
| No direct DB | n8n never writes PostgreSQL — callbacks to FastAPI only |
| Approved nodes | HTTP Request, Webhook, Schedule, IF, Set, Merge, Wait — see n8n-integration.md |
| Prohibited | Code node with business logic, Postgres node, arbitrary Execute Command |
| Signing | Outbound: `X-LexFlow-Signature`; inbound callbacks: `X-N8N-Signature` |
| Idempotency | Callbacks include `executionId` — FastAPI deduplicates |
| Credentials | AWS Secrets Manager references — not hardcoded |
| Version control | Workflow JSON in repo — promotion via pipeline |
| Network | Internal ALB only — never public webhook URL |
| Audit | Every execution outcome persisted via FastAPI callback |

---

## Output Format

```markdown
## Workflow — <slug>

### Purpose
<orchestration goal — not business rule>

### Trigger
- type: event | schedule | manual
- source: `WorkflowTriggered` | cron | …
- webhook path: `/webhook/{slug}`

### External Calls
| Step | Target | Method | Notes |
|------|--------|--------|-------|
| … | … | … | … |

### Callbacks
- final: `POST /internal/webhooks/n8n/{slug}`
- step (optional): `POST …/step`

### Payload Contract
- trigger schema ref: `webhook-contracts.md` §…
- callback schema ref: …

### Failure Handling
- retries: …
- DLQ alert: …

### CI Checks
- [ ] no prohibited nodes
- [ ] slug matches catalog
- [ ] JSON schema validated

### Coordination
- Backend changes required: yes/no
- Event routing key: …
```

Pattern: `.ai/patterns/n8n-workflow-pattern.md`. Example: `.ai/examples/example-workflow-trigger.md`.

---

## Checklist

- [ ] Slug registered in workflow catalog
- [ ] Trigger payload matches webhook-contracts.md
- [ ] HMAC headers on all cross-boundary calls
- [ ] No prohibited n8n nodes
- [ ] No secrets in workflow JSON
- [ ] Callback URL uses internal FastAPI path
- [ ] Error path sends structured error callback
- [ ] Backend engineer aligned on callback handler
- [ ] Promotion pipeline steps documented
- [ ] Retry/DLQ behavior matches retry-dlq.md

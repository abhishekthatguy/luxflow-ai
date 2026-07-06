# n8n Workflow Pattern

## Purpose

Structural template for version-controlled n8n workflow JSON — orchestration graphs that call HTTP APIs and external systems without domain authority.

## Applies To

`n8n/workflows/{category}/{slug}.json`

## Mandatory Reads

- `docs/06-workflows/n8n-integration.md`
- `docs/06-workflows/webhook-contracts.md`
- `docs/13-decisions/002-n8n-orchestration-only.md`
- `docs/06-workflows/workflow-catalog.md`

---

## Structure Template

```
n8n/workflows/
├── court-filing/
│   └── ecf-submit-v1.json
├── microsoft365/
│   └── sharepoint-sync-v1.json
└── notifications/
    └── deadline-reminder-v1.json

# Each JSON contains:
# - Webhook trigger node (slug path)
# - Set nodes (map trigger envelope → step vars)
# - HTTP Request nodes (external APIs)
# - HTTP Request nodes (FastAPI callbacks)
# - IF / Error branch → error callback
# - No Code node with business rules
```

---

## Pseudocode Outline (Graph Structure)

```
[NODE 1: Webhook Trigger]
  path: /webhook/{slug}
  auth: verify X-LexFlow-Signature on raw body
  output: triggerEnvelope

[NODE 2: Set — Extract Context]
  executionId = triggerEnvelope.executionId
  caseId = triggerEnvelope.context.caseId
  correlationId = triggerEnvelope.correlationId

[NODE 3: HTTP Request — External Action]
  method: POST
  url: {{ external API }}
  headers: OAuth from credential ref
  onError: → Error Branch

[NODE 4: HTTP Request — Step Callback (optional)]
  POST {{ FASTAPI_INTERNAL }}/internal/webhooks/n8n/{slug}/step
  headers:
    X-N8N-Signature: HMAC(body, secret)
    X-Correlation-Id: {{ correlationId }}
  body:
    executionId, stepName, status, partialResult

[NODE 5: HTTP Request — Final Callback]
  POST {{ FASTAPI_INTERNAL }}/internal/webhooks/n8n/{slug}
  body:
    executionId, status: "completed", outputs: {...}

[ERROR BRANCH]
  POST .../internal/webhooks/n8n/{slug}
  body:
    executionId, status: "failed", error: { code, message }
```

---

## Trigger Envelope (Minimal Shape)

```
{
  "executionId": "uuid",
  "workflowSlug": "ecf-submit-v1",
  "correlationId": "uuid",
  "firmId": "uuid",
  "context": {
    "caseId": "uuid",
    "triggeredBy": "uuid",
    "input": { /* workflow-specific — schema in webhook-contracts.md */ }
  },
  "callbackUrl": "https://api.internal.../internal/webhooks/n8n/ecf-submit-v1"
}
```

---

## Invariants

| # | Rule |
|---|------|
| 1 | Slug matches workflow catalog entry |
| 2 | Approved nodes only — CI scans JSON |
| 3 | All FastAPI calls signed with HMAC |
| 4 | No PostgreSQL / domain decision nodes |
| 5 | Credentials via n8n credential store — not inline |
| 6 | Error path always sends callback |
| 7 | `executionId` on every callback for idempotency |

---

## Anti-Patterns

- Code node implementing eligibility rules
- Direct S3/DB access from n8n
- Public webhook URL
- Hardcoded API keys in node parameters
- Missing final callback on success path

---

## Checklist

- [ ] Registered in workflow-catalog.md
- [ ] Trigger schema matches webhook-contracts.md §
- [ ] Callback schema matches webhook-contracts.md §
- [ ] CI: prohibited node scan passes
- [ ] Promotion pipeline steps in add-workflow.md followed
- [ ] Backend callback handler exists and tested
- [ ] Retry behavior aligned with retry-dlq.md

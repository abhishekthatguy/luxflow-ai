# LexFlow AI — Platform Invariants

**Purpose:** Non-negotiable rules. AI assistants MUST NOT violate these when suggesting code, architecture, or workflows.  
**Enforcement:** Code review, CI lint, integration tests, architecture review.  
**Authoritative source:** `docs/README.md` (Platform Invariants), ADRs in `docs/13-decisions/`

---

## Invariant Index

| ID | Rule | ADR / Doc |
|----|------|-----------|
| INV-01 | Business logic in FastAPI only | ADR-002 |
| INV-02 | n8n is private orchestration only | ADR-002 |
| INV-03 | All AI processing is async | ADR-004 |
| INV-04 | Case-centric domain model | Vision |
| INV-05 | Matter walls with 404 deny on GET | ADR-007 |
| INV-06 | Immutable append-only audit | Security |
| INV-07 | Transactional outbox for events | ADR-006 |
| INV-08 | Human-in-the-loop for AI legal outputs | `docs/07-ai/human-in-the-loop.md` |
| INV-09 | Frontend isolation from internal tiers | Data flow |
| INV-10 | Modular monolith boundaries | ADR-001, ADR-003 |
| INV-11 | Azure OpenAI production default | ADR-008 |
| INV-12 | JWT auth, server-side permissions | ADR-005 |

---

## INV-01: Business Logic in FastAPI Only

**Rule:** All business rules, validation, state transitions, authorization decisions, and audit obligations live in FastAPI Python code — testable with pytest.

**NEVER in:**
- n8n Code nodes or workflow branching on business rules
- Next.js components, hooks, or API routes (BFF is thin proxy only)
- Celery tasks that duplicate domain logic outside shared application layer

**FastAPI owns:**
- Case status state machine
- Matter wall enforcement
- Workflow trigger authorization (if/when to run)
- AI output approval gates
- Idempotency and optimistic concurrency

**Reference:** `docs/06-workflows/orchestration-model.md`, `docs/development-standards.md`

---

## INV-02: n8n Is Private Orchestration Only

**Rule:** n8n connects external systems and retries HTTP calls. It has zero decision authority.

| n8n MAY | n8n MUST NOT |
|---------|--------------|
| Call external APIs (M365, email, courts) | Contain business/legal logic |
| Transform payloads for external formats | Write to PostgreSQL |
| Retry failed HTTP with backoff | Be exposed to public internet |
| Route on HTTP status codes | Make authorization decisions |
| Callback to FastAPI internal webhooks (HMAC) | Store authoritative case/client data |

**Network:** Private subnet, security groups deny public ingress, no WAF route to n8n.

**Workflow JSON:** Version-controlled in `n8n/workflows/`; promoted dev → staging → prod.

**Reference:** `docs/06-workflows/n8n-integration.md`, `docs/08-security/network-security.md`

---

## INV-03: All AI Processing Is Async

**Rule:** No LLM or embedding call in HTTP request path. Ever.

**Pattern:**
```
POST /api/v1/.../summarize → 202 { jobId, statusUrl, correlationId }
Celery worker → LLM → persist result → event/SSE notify
GET /api/v1/ai/jobs/{jobId} → 200 { status, result }
```

**Rationale:** Variable latency (2–60s), rate limits, timeouts, retry, cost metering, audit persistence.

**Phase 2 exception:** SSE token streaming for chat — full response still async-persisted for audit.

**Reference:** `docs/04-api/endpoints-ai.md`, `docs/07-ai/`

---

## INV-04: Case-Centric Domain

**Rule:** `Case` is the central aggregate. Case-scoped features require `caseId`. Matter walls apply to all case data.

**Case statuses:** `intake` → `active` → `closed` → `archived` (terminal)

**Synonym:** "Matter" in UI OK; code/API uses `Case`.

**Never:** `Ticket`, `Project`, `Issue` for legal matters.

**Reference:** `docs/02-domain/case-aggregate.md`, `memory/GLOSSARY.md`

---

## INV-05: Matter Walls — 404 Not 403 on GET

**Rule:** When matter wall denies access to case-scoped GET/HEAD, return **404 Not Found** — same body as nonexistent case. Prevents case ID enumeration.

| Condition | GET/HEAD | Body |
|-----------|----------|------|
| Not authenticated | 401 | Standard auth error |
| RBAC denied (no role permission) | 403 | "Insufficient permissions" — no case metadata |
| Matter wall deny | **404** | Generic "Case not found" — NO title, client, participants |
| Case does not exist | **404** | Identical to matter wall deny |

**Internal audit:** Full deny reason in `audit.audit_logs` — never in HTTP response.

**Reference:** `docs/08-security/matter-walls.md`, `docs/10-testing/integration-testing.md` (matter wall matrix)

---

## INV-06: Immutable Append-Only Audit

**Rule:** `audit.audit_logs` is INSERT-only for application role. No UPDATE/DELETE.

**Audited actions:** All mutations, sensitive reads, auth events, AI invocations, approval decisions, deny paths.

**Log fields:** actor, action, resource, timestamp, correlation_id, before/after state (where applicable).

**Reference:** `docs/05-database/audit-schema.md`, `docs/08-security/compliance-mapping.md`

---

## INV-07: Transactional Outbox for Domain Events

**Rule:** Domain events written to `shared.outbox_events` in the **same database transaction** as the domain change. Never publish to RabbitMQ outside that transaction.

**Publisher:** Celery Beat polls every 1s; marks `published_at` on success.

**Consumers:** Must be idempotent (at-least-once delivery).

**Never:** Direct RabbitMQ publish from route handlers.

**Reference:** `docs/03-architecture/event-driven-design.md`, `docs/02-domain/domain-events.md`

---

## INV-08: Human-in-the-Loop for AI Legal Outputs

**Rule:** AI-generated text for legal work product starts as `draft`. Attorney approval required before team-visible publication (configurable per prompt template).

**Applies to:** Summaries, research memos, contract review findings, client-facing content.

**Never:** Auto-submit AI output to courts, clients, or external systems without approval.

**Reference:** `docs/07-ai/human-in-the-loop.md`, `docs/02-domain/ai-aggregate.md`

---

## INV-09: Frontend Isolation

**Rule:** Browser/Next.js NEVER directly accesses:

| Forbidden | Why |
|-----------|-----|
| n8n | Bypasses auth and audit |
| RabbitMQ | No credentials in browser |
| Celery workers | Internal only |
| LLM provider APIs | No API keys client-side |
| PostgreSQL / Redis | Internal data layer |

**Allowed:** HTTPS to FastAPI `/api/v1/*` with JWT; presigned S3 PUT for uploads.

**Reference:** `architecture/DATA-FLOW.md`

---

## INV-10: Modular Monolith Boundaries

**Rule:** Single FastAPI deploy with 8 bounded context modules. No cross-context direct domain imports.

**Integration mechanisms (in order of preference):**
1. Domain events (outbox → RabbitMQ)
2. Read-only FK references at query time
3. Application service coordination (same transaction when required)

**Database:** Single PostgreSQL, schema-per-context. No cross-schema FKs.

**Never:** Shared mutable tables across contexts without explicit architecture approval.

**Reference:** `docs/02-domain/bounded-contexts.md`, ADR-001, ADR-003

---

## INV-11: Azure OpenAI Production Default

**Rule:** Production LLM inference defaults to Azure OpenAI via firm's Azure subscription. Provider from `PromptTemplate.model_config`, not hardcoded.

**Fallback:** OpenAI API only when Azure 5xx/timeout after retries — logged as `fallback_used: true`.

**Pre-LLM:** All text through safety pipeline (PII redaction, injection detection).

**Reference:** `docs/07-ai/safety-guardrails.md`, ADR-008

---

## INV-12: JWT Auth, Server-Side Permissions

**Rule:**
- Access token: 15 min, RS256, contains `sub`, `firm_id`, `session_id` — **NOT permissions**
- Refresh token: 7 days, httpOnly Secure SameSite=Strict cookie, rotated on use
- Permissions: loaded from Redis-cached role matrix per request

**Never:** Embed RBAC permissions in JWT claims.

**Reference:** `docs/04-api/authentication.md`, `docs/04-api/authorization-rbac.md`, ADR-005

---

## Cross-Cutting Enforcement Patterns

| Pattern | Rule |
|---------|------|
| Idempotency | `Idempotency-Key` header on mutating async triggers |
| Optimistic concurrency | `version` column + `If-Match` / ETag on Case, Document, Task |
| Correlation ID | `X-Correlation-Id` propagated Frontend → API → Worker → n8n → callback |
| Presigned upload | Document binaries via S3 presigned URL — never through API body |
| Internal webhooks | n8n callbacks on `/internal/webhooks/*` — HMAC signed, not in public OpenAPI |

---

## PR Review Checklist (Invariant Gate)

- [ ] No business logic added to n8n or frontend
- [ ] No sync LLM call in API handler
- [ ] Matter wall tests pass if touching authorization
- [ ] Outbox used for cross-context side effects
- [ ] Audit log entry for significant mutations
- [ ] 404 (not 403) for matter wall GET deny
- [ ] No secrets in code/commits
- [ ] Domain terms match glossary

---

## When Invariants Conflict with Convenience

**Invariants win.** If a feature seems to require violating an invariant, propose an ADR amendment or alternative design — do not shortcut.

Example: "Just call OpenAI synchronously for this one small summary" → **Rejected.** Use async job pattern.

Example: "Put case validation in n8n IF node" → **Rejected.** FastAPI validates; n8n executes.

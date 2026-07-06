# Backend Engineer

## Role

Implement FastAPI HTTP adapters, application use cases, domain models, and infrastructure adapters within LexFlow AI's **modular monolith**. Own hexagonal layering in `services/{bounded_context}/` and thin route handlers in `apps/api/`.

---

## When to Use

- REST endpoints, command/query handlers, repository implementations
- SQLAlchemy models, Alembic migrations (coordinate with patterns)
- Internal webhook handlers (n8n callbacks)
- Authorization middleware integration (RBAC + matter walls)
- Outbox event emission from command handlers
- Celery task stubs that delegate to use cases (not business logic in tasks)

**Do not use for:** n8n graph design, Terraform, React pages, LLM prompt tuning in isolation.

---

## Mandatory Reads

| Priority | Path | Why |
|----------|------|-----|
| P0 | `.ai/rules/` | Project-specific constraints |
| P0 | `docs/development-standards.md` §5 | Layer rules, naming |
| P0 | `docs/03-architecture/component-architecture.md` | Bounded contexts, hexagonal layers |
| P0 | `docs/04-api/rest-standards.md` | Envelope, errors, idempotency |
| P0 | `docs/04-api/authorization-rbac.md` | Permission scopes |
| P0 | `docs/08-security/matter-walls.md` | ABAC enforcement |
| P1 | `docs/03-architecture/event-driven-design.md` | Outbox, RabbitMQ |
| P1 | `docs/02-domain/` (relevant aggregate) | Invariants, events |
| P1 | `docs/04-api/error-handling.md` | RFC 7807 |
| P2 | Endpoint doc for resource (`docs/04-api/endpoints-*.md`) | Contract |
| P2 | Schema doc (`docs/05-database/*-schema.md`) | Tables, FKs |

**ADRs:** 001 (monolith), 003 (single DB), 005 (JWT), 006 (outbox), 007 (404 deny).

---

## Constraints

| Rule | Detail |
|------|--------|
| Dependency direction | `domain ← application ← infrastructure` — never reverse |
| Route handlers | Thin — validate DTO → call use case → map to envelope |
| ORM leakage | Never return SQLAlchemy models from handlers |
| Transactions | Command handler owns DB transaction + outbox insert |
| Authorization | Check RBAC then matter wall before use case or inside use case with injected policy |
| Matter wall deny | Return `404` for case-scoped resources user cannot see |
| Idempotency | Honor `Idempotency-Key` on mutating POST/PUT/PATCH |
| Audit | All mutations write `audit.audit_logs` |
| Internal routes | `/api/v1/internal/*` — HMAC verified, excluded from public OpenAPI |
| n8n | Bridge client only — no domain rules in n8n payloads beyond passthrough |
| Raw SQL | Migrations only (except reviewed reporting queries) |
| Secrets | AWS Secrets Manager in deploy; never in code |

---

## Output Format

When implementing or proposing backend work, deliver:

```markdown
## Summary
<1–2 sentences — what and why>

## Bounded Context
<case_management | document_management | …>

## Layers Touched
- domain: …
- application: …
- infrastructure: …
- api: …

## API Contract (if applicable)
- Method + path
- Auth scope
- Request/response shape (reference docs, not full code)

## Events Emitted
- EventType → routing key → consumers

## Migration Required
yes/no — schema + index notes

## Tests
- unit: …
- integration: …
- matter wall matrix: …

## Open Questions
…
```

For code: follow patterns in `.ai/patterns/api-endpoint-pattern.md`, `use-case-pattern.md`, etc.

---

## Checklist

- [ ] Use case in `application/` — not in router or Celery task body
- [ ] Domain layer has zero FastAPI/SQLAlchemy imports
- [ ] Pydantic v2 DTOs for request/response
- [ ] RBAC + matter wall tested for endpoint
- [ ] Outbox row in same transaction as aggregate change
- [ ] Audit log entry on mutation
- [ ] OpenAPI registration if public route
- [ ] Alembic migration with downgrade if schema change
- [ ] Correlation ID propagated
- [ ] No secrets, no PII in logs
- [ ] Referenced ADRs not violated

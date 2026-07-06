# Security Rules — LexFlow AI

**Applies to:** All layers — backend, frontend, workers, n8n, infra, AI  
**Docs:** `docs/08-security/`, `docs/04-api/authentication.md`, `docs/13-decisions/`

---

## Purpose

Non-negotiable security constraints for AI assistants. **Security rules override all other rules.** Violations are compliance incidents, not bugs.

---

## Golden Rules

1. **No secrets in source code, git, logs, or n8n JSON**
2. **Authorization enforced only in FastAPI** — never frontend-only, never n8n
3. **Matter walls on every case-scoped operation**
4. **404 on unauthorized case GET** — never 403 (ADR-007)
5. **Immutable audit** for security-relevant actions
6. **PII redaction** in logs, traces, and prompt history
7. **Async AI with HITL** for legal outputs

---

## Matter Walls (ABAC)

### Enforcement Flow

```
JWT Auth → RBAC → Matter Wall (if assigned scope) → Handler
```

| Rule ID | Rule |
|---------|------|
| MW-001 | User must be case participant for `assigned` scope |
| MW-004 | Unauthorized case GET → **404 Not Found** |
| MW-006 | AI retrieval scoped to authorized case documents only |
| MW-008 | All wall decisions logged to audit |

### Do / Don't

| Do | Don't |
|----|-------|
| Return 404 for non-participant case reads | Return 403 revealing case exists |
| Test every new case endpoint in matter wall matrix | Defer matter wall tests |
| Scope vector search by authorized `case_id` set | Cross-matter RAG retrieval |
| Audit denied access attempts | Silently drop unauthorized requests |

**Ref:** `docs/08-security/matter-walls.md`, `docs/13-decisions/007-matter-walls-404-deny.md`

---

## Authentication (ADR-005)

| Rule | Detail |
|------|--------|
| JWT RS256 | Access token short-lived; refresh token rotation |
| HTTPS only | Production — no plain HTTP |
| Token in memory (frontend) | No localStorage for access tokens |
| Internal webhooks | HMAC-SHA256, not JWT |
| n8n triggers | HMAC from worker; private network only |

**Ref:** `docs/04-api/authentication.md`

---

## Authorization (RBAC)

| Do | Don't |
|----|-------|
| Check permissions via centralized service | Scatter `if user.role ==` in handlers |
| Use permission strings (`case:read:assigned`) | Hardcode role names in domain |
| Separate admin ops from case content access | Give sysadmin read on privileged documents |

**Ref:** `docs/04-api/authorization-rbac.md`

---

## Secrets Management

| Rule | Detail |
|------|--------|
| AWS Secrets Manager | All deployed secrets |
| `.env.example` only | Document vars — no values |
| Pre-commit hooks | Block secret patterns (TruffleHog) |
| Rotation | Per `docs/14-playbooks/rotate-secrets.md` |
| n8n credentials | Runtime injection — `n8n/credentials/` is empty in git |

### Secret Hierarchy (examples)

```
{env}/database/credentials
{env}/jwt/signing-key
{env}/azure-openai/api-key
{env}/n8n/webhook-hmac-secret
```

**Ref:** `docs/08-security/secrets-management.md`

---

## Data Protection

| Layer | Requirement |
|-------|-------------|
| Transit | TLS 1.2+ everywhere |
| At rest | RDS/S3 SSE-KMS |
| Application | Field-level encryption for sensitive PII |
| Logs | Redact names, content, tokens — see `logging-standards.md` |
| Test data | Factories only — no real client data |

**Ref:** `docs/08-security/encryption.md`

---

## AI Security

| Rule | Detail |
|------|--------|
| Case-scoped retrieval | Matter wall before embedding search |
| PII redaction | Before LLM call |
| Prompt injection defense | Sanitize user inputs in templates |
| HITL | `requires_approval=true` for legal outputs |
| No cross-matter context | Documented non-goal |
| Azure OpenAI primary | ADR-008 — firm tenant data residency |

**Ref:** `docs/07-ai/safety-guardrails.md`, `docs/13-decisions/008-azure-openai-primary.md`

---

## n8n Security

| Rule | Detail |
|------|--------|
| Private network only | No public webhook ingress |
| No PostgreSQL nodes | ADR-002 |
| HMAC on all callbacks | Verify before processing |
| Sanitized trigger payloads | Strip secrets and excess PII |

---

## Input Validation

| Do | Don't |
|----|-------|
| Pydantic validation at API boundary | Trust client JSON |
| Parameterized SQL via ORM | String-concat SQL |
| File type + size limits on upload | Accept arbitrary uploads |
| Rate limiting on auth endpoints | Unlimited login attempts |

---

## Security PR Checklist

- [ ] No secrets in diff
- [ ] Matter wall tests for case-scoped changes
- [ ] 404 (not 403) on unauthorized case GET
- [ ] Audit log on security-relevant mutations
- [ ] PII not logged or echoed in errors
- [ ] Authorization in FastAPI, not frontend/n8n
- [ ] Dependencies scanned (no CRITICAL/HIGH)

---

## Incident Response

If a secret is committed or matter wall bypass discovered:

1. **Stop** — do not merge
2. Rotate affected secrets immediately
3. Notify security lead per `docs/08-security/incident-response.md`
4. Add regression test before fix merges

---

## References

- [docs/08-security/README.md](../../docs/08-security/README.md)
- [docs/08-security/threat-model.md](../../docs/08-security/threat-model.md)
- [docs/08-security/compliance-mapping.md](../../docs/08-security/compliance-mapping.md)
- [docs/10-testing/security-testing.md](../../docs/10-testing/security-testing.md)
- [testing-standards.md](./testing-standards.md)

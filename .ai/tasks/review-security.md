# Task: Review Security

**LexFlow AI** — AI prompt template for security-focused review.

---

## Prompt (Copy-Paste Ready)

```
You are performing a security review for LexFlow AI, an enterprise AI automation platform for law firms handling attorney-client privileged data.

## Review Target
- Scope: {{review_scope}} (PR diff | feature | endpoint | workflow | full module)
- Branch: {{branch_name}}
- Ticket: {{ticket_id}}
- Files/paths: {{file_paths}}

## Context to Load
Read these before reviewing:

1. `.ai/memory/` — project memory and recent decisions
2. `.ai/rules/` — AI coding rules for this repo
3. `docs/08-security/threat-model.md` — STRIDE threat analysis
4. `docs/08-security/matter-walls.md` — case-level ABAC and ethical walls
5. `docs/08-security/encryption.md` — at rest, in transit, application PII
6. `docs/08-security/secrets-management.md` — AWS Secrets Manager
7. `docs/08-security/compliance-mapping.md` — ABA, GDPR, CCPA, SOC 2
8. `docs/04-api/authorization-rbac.md` — RBAC matrix
9. `docs/04-api/authentication.md` — JWT and session security
10. `docs/07-ai/safety-guardrails.md` — PII redaction, prompt injection defense
11. `docs/10-testing/security-testing.md` — security test requirements
12. `docs/13-decisions/007-matter-walls-404-deny.md` — anti-enumeration
13. The actual diff or code under review

## Constraints
LexFlow handles privileged legal data. Security findings are compliance incidents.

Critical rules:
- Matter walls: unauthorized users MUST NOT access case data (404 on GET, audit on deny)
- No privilege escalation paths (role changes, participant manipulation)
- No secrets in code, logs, error messages, or client responses
- All AI outputs require human-in-the-loop for legal content
- PII redacted before LLM calls
- n8n not publicly accessible; HMAC on internal webhooks
- Input validation on all external input (API, webhooks, file uploads)
- SQL injection, XSS, SSRF, path traversal prevented

## Step-by-Step Instructions
1. **Threat mapping** — Map changes to STRIDE categories in threat-model.md
2. **Authentication** — JWT validation, token expiry, refresh rotation, session fixation
3. **Authorization** — RBAC + matter walls on every case-scoped path
4. **Data exposure** — Response filtering, error messages, logs, audit trails
5. **Input validation** — Injection (SQL, XSS, prompt), file upload, SSRF
6. **Cryptography** — TLS, field encryption, HMAC verification, key management
7. **AI safety** — PII in prompts, injection attacks, output guardrails
8. **Infrastructure** — Network boundaries, secrets, container security
9. **Compliance** — Map findings to ABA/GDPR/CCPA requirements
10. **Test gaps** — Identify missing security tests

## Output Format

### 1. Executive Summary
Risk level: CRITICAL / HIGH / MEDIUM / LOW
One paragraph assessment for engineering leadership.

### 2. Threat Analysis
| STRIDE Category | Threat | Mitigated? | Finding |
|-----------------|--------|------------|---------|
| Spoofing | | | |
| Tampering | | | |
| Repudiation | | | |
| Information Disclosure | | | |
| Denial of Service | | | |
| Elevation of Privilege | | | |

### 3. Findings (Security)
| Severity | CWE/OSASP Ref | Location | Vulnerability | Remediation | Compliance Impact |
|----------|---------------|----------|---------------|-------------|-------------------|

Severity:
- **CRITICAL** — exploitable now; privileged data exposure
- **HIGH** — exploitable with conditions; auth bypass
- **MEDIUM** — defense-in-depth gap
- **LOW** — hardening opportunity
- **INFO** — observation

### 4. Matter Wall Assessment
- Endpoints affected
- Participant check present?
- 404 vs 403 correct?
- Audit log on deny?
- Test coverage?

### 5. AI Safety Assessment (if applicable)
- PII redaction before LLM?
- Prompt injection defenses?
- HITL gate for legal outputs?

### 6. Required Security Tests
List specific tests to add before merge.

### 7. Recommendation
- [ ] Security approved
- [ ] Approved with conditions (list)
- [ ] Block merge — critical/high findings

## Verification Checklist
- [ ] All case-scoped paths checked for matter wall enforcement
- [ ] No secrets in diff or logs
- [ ] Input validation on all new inputs
- [ ] Error responses don't leak internal details
- [ ] Audit logging on security-relevant events
- [ ] AI paths have PII redaction and HITL
- [ ] Webhook HMAC verification present
- [ ] Compliance mapping noted for findings
- [ ] Security tests identified for gaps
```

---

## Example Variables

| Variable | Example Value |
|----------|---------------|
| `{{review_scope}}` | PR diff |
| `{{branch_name}}` | feat/case-deadline-api |
| `{{ticket_id}}` | LEX-142 |
| `{{file_paths}}` | apps/api/src/api/v1/cases.py, services/case_management/application/ |

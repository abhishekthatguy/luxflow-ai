# LexFlow AI — Security Review

**Classification:** Internal — Interview / Customer Security Questionnaire  
**Last Updated:** 2026-07-06  
**Scope:** Phase 1 platform (local + AWS staging design)

---

## Executive Summary

LexFlow AI is designed for **confidential legal data** in large US firms. Security is layered: edge (WAF), application (JWT, RBAC, matter walls), data (encryption, audit), and AI (HITL, scoped context). Several controls are **implemented locally**; production hardening items are marked 📋.

---

## OWASP Top 10 (2021) Mapping

| Risk | LexFlow Mitigation | Status |
|------|-------------------|--------|
| **A01 Broken Access Control** | RBAC + matter walls (404 deny) + firm_id from JWT | ✅ |
| **A02 Cryptographic Failures** | TLS 1.2+, AES-256 at rest, bcrypt passwords | ✅ / 📋 KMS |
| **A03 Injection** | Pydantic validation, SQLAlchemy parameterized queries | ✅ |
| **A04 Insecure Design** | ADR-007 matter walls; HITL for AI; outbox pattern | ✅ |
| **A05 Security Misconfiguration** | Trivy CI, no public n8n, docs for hardening | 🔶 |
| **A06 Vulnerable Components** | Dependabot, Trivy CRITICAL=0 gate | ✅ |
| **A07 Auth Failures** | JWT short TTL, refresh rotation, rate limit login | ✅ |
| **A08 Integrity Failures** | SHA-256 upload verify, audit append-only | ✅ |
| **A09 Logging Failures** | JSON logs, correlationId, PII redaction | ✅ |
| **A10 SSRF** | n8n outbound allowlist; no user-controlled fetch in API | 🔶 |

---

## Authentication — JWT

| Control | Implementation |
|---------|----------------|
| Algorithm | HS256 (local); RS256 + Entra ID (prod) |
| Access TTL | 15 minutes |
| Refresh TTL | 7 days, rotated on use |
| Claims | `sub`, `firm_id`, `roles`, `email`, `exp` |
| Storage (client) | localStorage (dev); httpOnly cookie option (prod) |
| Revocation | 📋 Token blocklist in Redis on user deactivate |

---

## Authorization — RBAC

| Role | Scope |
|------|-------|
| Attorney | Case participant operations |
| Paralegal | Tasks, documents (participant) |
| ManagingPartner | Firm-wide + audit read |
| SystemAdministrator | Full firm admin |

Enforced in services, not just UI.

---

## Matter Walls

- **Policy:** User must be `case_participants` row OR `FIRM_WIDE_ACCESS_ROLES`
- **Deny semantics:** HTTP **404** — prevents case enumeration (ADR-007)
- **Test:** Penetration test — zero cross-matter document access

---

## PII Handling

| Location | Control |
|----------|---------|
| Logs | Email/phone regex redaction ✅ |
| LLM prompts | 📋 Preprocessor redacts SSN, account numbers |
| Audit details | JSONB — no full document text |
| Exports | Firm admin only; watermarked |

---

## Encryption

| Layer | Method |
|-------|--------|
| Transit | TLS 1.2+ (ALB, CloudFront) |
| RDS | AES-256 encryption at rest |
| S3 | SSE-S3 / SSE-KMS |
| Secrets | AWS Secrets Manager 📋 |
| Backups | Encrypted snapshots |

---

## Audit Logs

- **Append-only** `audit.audit_logs`
- Every mutation: actor, action, resource, timestamp, details
- **Retention:** 7 years default
- **Read access:** ManagingPartner, SystemAdministrator, Compliance Officer role 📋

---

## Rate Limiting

- **Login:** 10 attempts / 60s per IP (Redis) ✅
- **API global:** 📋 1000 req/min per user
- **AI triggers:** 📋 Per-firm daily token budget

---

## Secrets Management

| Secret | Storage |
|--------|---------|
| JWT secret | Env / Secrets Manager |
| DB credentials | Secrets Manager |
| S3 keys | IAM role (ECS task role) — no static keys |
| n8n webhook secret | Secrets Manager |
| Azure OpenAI key | Secrets Manager |

**Rotation:** 90-day automated rotation 📋

---

## AWS IAM

- **Least privilege** task roles per ECS service
- API role: RDS, S3 read/write firm prefix, Secrets read
- Worker role: Same + no public internet except LLM endpoint
- **No long-lived IAM users** for application code

---

## S3 Permissions

```json
{
  "Effect": "Allow",
  "Action": ["s3:PutObject", "s3:GetObject", "s3:HeadObject"],
  "Resource": "arn:aws:s3:::lexflow-docs/firms/${firm_id}/*"
}
```

- Block public access: **ON**
- Presigned URLs: 15 min TTL, single object

---

## File Upload Security

| Control | Detail |
|---------|--------|
| Size limit | Configurable per firm (default 500 MB) |
| MIME allowlist | pdf, docx, txt, images |
| Checksum | SHA-256 required on confirm |
| Virus scan | Stub local; ClamAV prod 📋 |
| Path traversal | UUID keys; no user-supplied paths |

---

## LLM & Prompt Injection

| Threat | Mitigation |
|--------|------------|
| Document text injection | System prompt isolation; delimiter tags |
| Jailbreak | Output schema validation; HITL required |
| Data exfiltration | Case-scoped context only; no cross-firm RAG |
| Model logging | Azure opt-out of training; zero retention policy |

---

## n8n Security

- **Private subnet** — no public ingress
- **No PostgreSQL nodes** — HTTP to FastAPI only
- HMAC on callbacks
- Security scan: external port scan **must fail**

---

## Compliance Frameworks

### SOC 2 Type II

| Control area | Status |
|--------------|--------|
| CC6 Logical access | RBAC, JWT, audit |
| CC7 System operations | Runbook, monitoring |
| CC8 Change management | CI/CD, PR reviews |
| A1 Availability | Multi-AZ, 99.9% target |

📋 Formal audit planned Phase 2

### ISO 27001

- Aligns with ISMS documentation in `docs/08-security/`
- Risk register includes AI misuse, matter wall bypass

### HIPAA Considerations

- LexFlow **not HIPAA-certified** by default
- Firms handling PHI require BAA, dedicated tenant, enhanced logging
- PHI fields flagged in schema for redaction 📋

### Legal Document Security

- Attorney-client privilege: data stays in firm tenant
- **No training** on firm data by default
- Legal hold prevents deletion
- Export for litigation with audit trail

---

## Security Testing

| Test | Frequency |
|------|-----------|
| Trivy container scan | Every CI build |
| OWASP ZAP staging | 📋 Monthly |
| Matter wall pen test | 📋 Per release |
| Dependency audit | Dependabot weekly |

---

## Related Docs

- [Network Security](../08-security/network-security.md)
- [Failure Scenarios](./FAILURE_SCENARIOS.md)
- [RFC-002 Authentication](../18-rfc/RFC-002-authentication-rbac.md)

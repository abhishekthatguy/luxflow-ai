# Compliance & Data Governance

**LexFlow AI** — Legal, Privacy & Data Management  
**Version:** 1.0  
**Status:** Draft — Pre-Implementation  
**Last Updated:** 2026-07-06

---

## 1. Overview

LexFlow AI handles attorney-client privileged information and must comply with legal industry ethical obligations, data privacy regulations, and firm-specific policies. This document defines data classification, retention, privacy rights, and compliance controls.

---

## 2. Regulatory & Ethical Framework

| Framework | Applicability | Key Requirements |
|-----------|--------------|------------------|
| ABA Model Rule 1.1 | All US jurisdictions | Competence — including technology competence |
| ABA Model Rule 1.6 | All US jurisdictions | Confidentiality of client information |
| ABA Model Rule 1.15 | All US jurisdictions | Safekeeping property (client documents) |
| ABA Formal Opinion 512 (2024) | All US jurisdictions | Generative AI — competence, confidentiality, communication |
| GDPR | EU clients/data subjects | Right to access, erasure, portability |
| CCPA/CPRA | California clients/residents | Right to know, delete, opt-out |
| SOC 2 Type II | Enterprise procurement | Security, availability, confidentiality |
| State bar ethics opinions | Varies by state | AI use in legal practice |

---

## 3. Data Classification

| Classification | Description | Examples | Controls |
|---------------|-------------|----------|----------|
| **Restricted — Privileged** | Attorney-client privileged communications | Case documents, AI summaries, internal notes, emails | Matter walls, encryption, audit logging, access on need-to-know |
| **Restricted — PII** | Personally identifiable information | Client names, SSN, addresses, financial data | Encryption, PII redaction in AI prompts, access logging |
| **Confidential** | Internal firm data | Workflow configs, prompt templates, user credentials | RBAC, secrets management |
| **Internal** | Operational data | System logs, metrics, anonymized analytics | RBAC, log retention |
| **Public** | Non-sensitive | Marketing materials (outside platform) | N/A |

---

## 4. Data Retention Policy

| Data Type | Retention Period | After Retention | Legal Basis |
|-----------|-----------------|-----------------|-------------|
| Active case data | Duration of case + 7 years | Archive to S3 Glacier → delete | State bar requirements, litigation hold |
| Closed case data | 7 years from close date | Archive → delete | Firm policy (configurable) |
| Audit logs | 7 years minimum | Archive to S3 → delete | Compliance, malpractice defense |
| AI prompt history | 3 years | Delete | Operational necessity |
| LLM usage records | 5 years | Aggregate → delete detail | Cost/compliance reporting |
| Document embeddings | Case lifetime + 1 year | Delete with case | Derived from case documents |
| Notifications | 90 days | Delete | Operational |
| Session/refresh tokens | Token lifetime + 7 days | Delete | Security |
| System logs | 90 days (CloudWatch) | Archive to S3 (7 years) | Operations |
| Backup snapshots | 35 days | Auto-delete | DR |

**Litigation hold:** When a case is under litigation hold, ALL retention timers are suspended until hold is released. Hold status is a flag on the Case entity.

---

## 5. Privacy Rights

### 5.1 Data Subject Access Request (DSAR)

```
Compliance Officer initiates DSAR
  → FastAPI generates export of all client PII across:
      - clients table
      - cases (where client is party)
      - documents (metadata only — not content unless requested)
      - audit logs (client-related actions)
      - prompt history (client-related)
  → Export delivered as encrypted ZIP to Compliance Officer
  → Action logged in audit trail
  → SLA: 30 days (GDPR) / 45 days (CCPA)
```

### 5.2 Right to Erasure

```
Compliance Officer initiates erasure request
  → System validates no litigation hold on affected cases
  → Erasure job (async):
      1. Hard delete client PII fields (name, email, phone, address)
      2. Anonymize audit log entries referencing client
      3. Delete client portal account
      4. Retain case number and non-PII metadata for legal requirements
      5. Document content retained if part of active/litigated case
  → Erasure certificate generated
  → Action logged in audit trail
```

### 5.3 AI-Specific Privacy Controls

| Control | Implementation |
|---------|----------------|
| No training on firm data | Azure OpenAI enterprise policy; contractual prohibition with all providers |
| PII redaction before LLM | Automated scan and redact SSN, financial data before prompt submission |
| Case-scoped retrieval | RAG never crosses case boundaries |
| Prompt logging | Full prompts logged but PII-redacted copy stored |
| Attorney review | AI outputs not shared externally without approval |

---

## 6. Audit & Compliance Reporting

### 6.1 Standard Reports

| Report | Audience | Frequency |
|--------|----------|-----------|
| User access log | Compliance Officer | On demand |
| Case access report | Compliance Officer | On demand |
| AI usage report | Managing Partner, Compliance | Monthly |
| Failed login report | IT Admin, Security | Weekly |
| Matter wall violations | Compliance Officer | On demand |
| Data retention status | Compliance Officer | Quarterly |
| LLM cost report | Managing Partner, IT Admin | Monthly |

### 6.2 Audit Log Integrity

- Append-only table — no UPDATE or DELETE permissions for application role
- Separate database role for audit writes (INSERT only)
- Monthly integrity check: row count + hash verification
- Optional: export to immutable S3 bucket with Object Lock

---

## 7. Ethical AI Use Policy

Aligned with ABA Formal Opinion 512:

| Requirement | LexFlow Implementation |
|-------------|----------------------|
| Competence | AI outputs labeled as drafts; training materials provided |
| Confidentiality | No client data sent to LLM providers for training; Azure private deployment |
| Communication | Clients informed if AI used on their matter (firm policy) |
| Candor | AI-generated citations flagged for verification; disclaimer on all outputs |
| Supervision | Attorney approval required before AI output used in work product |
| Fees | LLM usage metered for transparency; not billed to clients without disclosure |

---

## 8. Incident Response (Data Breach)

| Step | Action | Timeline |
|------|--------|----------|
| 1. Detect | GuardDuty, audit anomaly, user report | — |
| 2. Contain | Revoke tokens, isolate affected systems | < 1 hour |
| 3. Assess | Determine scope — which cases, clients, data types | < 4 hours |
| 4. Notify | Firm IT, managing partner, legal counsel | < 24 hours |
| 5. Regulatory | Breach notification if PII affected (state laws vary) | Per jurisdiction (72h GDPR) |
| 6. Remediate | Fix vulnerability, rotate secrets, restore from clean backup | < 72 hours |
| 7. Review | Post-mortem, update controls, ADR if needed | < 2 weeks |

---

## 9. Third-Party Data Processing

| Vendor | Data Shared | DPA Required | Data Location |
|--------|------------|--------------|---------------|
| AWS | All platform data | Yes (AWS DPA) | us-east-1 (configurable) |
| Azure OpenAI | Document text (redacted), prompts | Yes (Microsoft DPA) | Firm's Azure region |
| OpenAI | Fallback — same as above | Yes (OpenAI DPA) | US |
| Anthropic | Contract text for review | Yes (Anthropic DPA) | US |
| Microsoft Graph | Email, SharePoint metadata | Covered by Microsoft 365 DPA | Firm's tenant |

All DPAs must be reviewed by firm legal counsel before production deployment.

---

## 10. Related Documents

- [security-architecture.md](./security-architecture.md)
- [authentication-authorization.md](./authentication-authorization.md)
- [ai-architecture.md](./ai-architecture.md)
- [database-architecture.md](./database-architecture.md)
- [disaster-recovery.md](./disaster-recovery.md)

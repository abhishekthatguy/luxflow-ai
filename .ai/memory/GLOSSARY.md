# LexFlow AI — Domain Glossary

**Purpose:** Shared vocabulary for code, APIs, events, and UI. AI assistants MUST use these terms.  
**Authoritative source:** `docs/02-domain/ubiquitous-language.md`  
**Rule:** Code uses `Case` not `Matter`; API fields use glossary terms; events use `{Aggregate}{Action}` past tense.

---

## Anti-Patterns — Never Use

| Avoid | Use Instead | Reason |
|-------|-------------|--------|
| Ticket | Case | Legal professionals think in matters |
| Customer | Client | Attorney-client relationship |
| Attachment | Document | Versioning, OCR, classification |
| Bot | Workflow | Firm-configured automation |
| Report (AI output) | Summary | Summaries require approval |
| Sign-off | Approval | Domain entity with audit trail |
| Permission group | Matter Wall | Ethical concept, not just RBAC |
| File | Document | Storage vs domain entity |
| Project | Case | Legal lifecycle semantics |
| Account | Client | CRM/billing conflict |
| Delete (cases) | Archive or Close | Legal retention required |
| Member | Participant | Defined role on matter |
| AI output (UI) | Summary or Draft | Emphasizes human review |

---

## Core Terms (A–W)

### A

| Term | Context | Definition | Code/API Name |
|------|---------|------------|---------------|
| **Approval** | Audit & Compliance | Human authorization gate before sensitive action; records who/when/why | `Approval` |
| **Archive** | Case Management | Terminal state for resolved cases; no new work without reopen | `status: archived` |
| **Associate Attorney** | Identity & Access | Licensed attorney under supervision | Role: `AssociateAttorney` |
| **Audit Log** | Audit & Compliance | Immutable append-only action record | `AuditLog` |
| **AISummary** | AI & Knowledge | AI-generated text linked to case; requires approval for team visibility | `AISummary` |

### B

| Term | Context | Definition |
|------|---------|------------|
| **Bounded Context** | Architecture | DDD module with own model and data ownership (8 total) |
| **Billing Code** | Case Management | Firm-internal code on Case; not billing system of record |

### C

| Term | Context | Definition | Code/API Name |
|------|---------|------------|---------------|
| **Case** | Case Management | Central aggregate — legal matter with tasks, deadlines, participants | `Case` |
| **Matter** | Case Management | Synonym for Case in legal practice; UI OK, code uses Case | — |
| **Case Number** | Case Management | Firm-unique identifier (e.g., `2026-00142`); immutable | `case_number` |
| **Case Participant** | Case Management | User assigned to case with role; enforces matter wall | `CaseParticipant` |
| **Client** | Client Management | Individual/org receiving legal services | `Client` |
| **Client Portal** | Client Management | Self-service for intake, uploads, status | — |
| **Contact** | Client Management | Person on organization client (e.g., general counsel) | `Contact` |
| **Contract Review** | AI & Knowledge | AI clause analysis; advisory; requires approval | — |
| **Correlation ID** | Cross-cutting | UUID tracing operation across services/logs | `correlation_id` |

### D

| Term | Context | Definition |
|------|---------|------------|
| **Deadline** | Case Management | Date-bound obligation: filing, discovery, SOL, internal, other |
| **Document** | Document Management | File on case with type, versioning, OCR |
| **Document Version** | Document Management | Immutable snapshot; monotonic version numbers |
| **Document Type** | Document Management | Enum: pleading, contract, evidence, correspondence, invoice, other |

### E

| Term | Context | Definition |
|------|---------|------------|
| **Embedding** | AI & Knowledge | Vector chunk in pgvector for semantic search (not aggregate) |
| **Execution** | Workflow Orchestration | Single workflow run; aggregate `WorkflowExecution` |

### F

| Term | Context | Definition |
|------|---------|------------|
| **Firm** | Identity & Access | Law firm tenant; all data scoped by `firmId` |
| **Firm-Wide** | Cross-cutting | Not case-scoped; `caseId` may be null |

### H

| Term | Context | Definition |
|------|---------|------------|
| **Hearing** | Case Management | Scheduled court appearance |
| **Human-in-the-Loop (HITL)** | AI & Knowledge | Attorney review before AI output is official work product |

### I

| Term | Context | Definition |
|------|---------|------------|
| **Intake** | Case Management | Initial case creation; status `intake` — not yet operational |
| **Idempotency Key** | Cross-cutting | Client key preventing duplicate async triggers |

### L

| Term | Context | Definition |
|------|---------|------------|
| **Lead Attorney** | Case Management | Primary responsible attorney; required at creation; role `lead` |
| **Legal Research** | AI & Knowledge | AI-assisted research memo; attorney verification required |
| **LLM Usage** | AI & Knowledge | Token/cost tracking entity per firm/user/case/period |

### M

| Term | Context | Definition |
|------|---------|------------|
| **Matter Wall** | Case Management | ABAC restricting case visibility to participants + authorized roles |
| **Managing Partner** | Identity & Access | Firm leadership; firm-wide visibility; role `ManagingPartner` |

### N

| Term | Context | Definition |
|------|---------|------------|
| **Note** | Case Management | Internal text with visibility: team, attorneys_only, private |
| **Notification** | Notifications | Alert via in-app, email, or Teams |

### O

| Term | Context | Definition |
|------|---------|------------|
| **OCR** | Document Management | Text extraction from uploaded documents |
| **Outbox** | Cross-cutting | `shared.outbox_events` — transactional event publishing |

### P

| Term | Context | Definition |
|------|---------|------------|
| **Participant** | Case Management | Shorthand for Case Participant |
| **Paralegal** | Identity & Access | Legal support role; common participant |
| **Practice Area** | Case Management | litigation, corporate, IP, regulatory, employment, real_estate, other |
| **Prompt Template** | AI & Knowledge | Versioned Jinja2 AI instructions + model config; aggregate root |
| **Prompt History** | AI & Knowledge | Immutable LLM interaction log (redacted prompt, response, tokens) |

### R

| Term | Context | Definition |
|------|---------|------------|
| **RBAC** | Identity & Access | Role-based access; permissions in FastAPI per request |

### S

| Term | Context | Definition |
|------|---------|------------|
| **Summary** | AI & Knowledge | AI text output as AISummary; requires human review |
| **Slug** | Workflow Orchestration | URL-safe workflow ID (e.g., `intake-new-client-v1`) |
| **Statute of Limitations** | Case Management | Critical deadline type; escalating reminders |

### T

| Term | Context | Definition |
|------|---------|------------|
| **Task** | Case Management | Completable work item with assignee, due date, status |
| **Timeline** | Case Management | Chronological case events from `case_timeline_events` |
| **Trigger** | Workflow Orchestration | manual, event, or schedule — starts workflow |

### W

| Term | Context | Definition |
|------|---------|------------|
| **Workflow** | Workflow Orchestration | Automated steps via n8n; Definition vs Execution |
| **Workflow Definition** | Workflow Orchestration | Reusable template with slug, trigger, n8n ref |
| **Workflow Execution** | Workflow Orchestration | Single run instance with status and payloads |

---

## Disambiguation

| Term | Meaning A | Meaning B |
|------|-----------|-----------|
| **Version** | Document Version (immutable file snapshot) | Optimistic concurrency integer on aggregates |
| **Status** | Case: intake/active/closed/archived | Document: uploading/processing/ready — always qualify |
| **Approval** | AISummary attorney review | Workflow authorization gate |
| **Portal** | Client Portal (external) | Internal app = "LexFlow AI" |
| **Template** | Prompt Template (AI) | Workflow Definition (automation) |
| **Active** | Case status (operational) | WorkflowDefinition.isActive (available for trigger) |
| **Draft** | AISummary pending approval | PromptTemplate unreleased version |

---

## Event Naming

Format: `{Aggregate}{Action}` past tense — e.g., `CaseCreated`, `DocumentProcessed`, `SummaryApproved`.

**Never:** `MatterCreated`, `CreateCase`, `FileUploaded`.

Full catalog: `docs/02-domain/domain-events.md`

---

## Code Naming Conventions

| Artifact | Convention | Example |
|----------|------------|---------|
| Python class | PascalCase glossary term | `Case`, `WorkflowExecution` |
| API field | snake_case | `case_number`, `lead_attorney_id` |
| DB table | snake_case, schema-prefixed | `cases.cases`, `documents.documents` |
| Enum values | snake_case full words | `statute_of_limitations` not `sol` |
| React component | PascalCase | `CaseDetailPage` |

---

## UI vs Code Terminology

| UI (legal synonym OK) | Code/API (required) |
|-----------------------|---------------------|
| Matter | Case |
| Matter Number | case_number |
| Summary (not Report) | AISummary / summary |
| Participant (not Member) | participant |

Firm may customize UI labels in Phase 2+ — API contract unchanged.

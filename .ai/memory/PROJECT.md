# LexFlow AI — Project Context

**Load this first.** Compressed full-project context for AI assistants.  
**Authoritative source:** `docs/README.md`, `docs/01-product/`, `docs/03-architecture/`  
**Status:** Pre-implementation — documentation complete; **Sprint 0** delivers engineering scaffold (no business code).

---

## Repository (sole source)

| | |
|---|---|
| **GitHub** | [github.com/abhishekthatguy/luxflow-ai](https://github.com/abhishekthatguy/luxflow-ai) |
| **Clone (SSH)** | `git clone git@github.com:abhishekthatguy/luxflow-ai.git` |
| **Git author** | `abhishek <abhishekthatguy@gmail.com>` — use for all commits (see `.ai/rules/git-workflow.md`) |

All LexFlow AI code and docs live in this repo only — not in `corptec-work` or other workspaces.

---

## One-Line Summary

LexFlow AI is an **enterprise AI automation platform for US law firms** that eliminates repetitive manual work for attorneys, paralegals, and operations teams — **without replacing legal judgment**.

---

## Problem & Value

| Pain | LexFlow Response |
|------|------------------|
| Manual intake delays | Unified case hub + automated intake workflows |
| Document chaos | Versioned documents, OCR, semantic search (pgvector) |
| Fragmented workflows | Event-driven automation via private n8n |
| Compliance burden | Immutable audit logs, matter walls, HITL AI |
| Knowledge silos | RAG + case-scoped AI assistants |

**Target customer:** Single large US law firm deployment (e.g., Freeman Mathis & Gary LLP) — not multi-tenant SaaS initially.

**Team size (Phase 1):** 5–10 engineers.

---

## Strategic Pillars

1. **Case-centric design** — Legal matter is aggregate root; all features attach to cases
2. **Trust through transparency** — Audit logs, attorney approval for AI outputs
3. **Enterprise security** — Matter walls, private n8n, encryption everywhere
4. **Open integration** — Microsoft 365 native; adapter pattern for billing/DMS/courts
5. **Operational excellence** — 99.9% availability, observable async pipelines, DR

Full vision: `docs/01-product/vision.md`

---

## 13 Core Capabilities

All case-centric unless firm-wide (audit, workflow templates):

| # | Capability | Bounded Context |
|---|------------|-----------------|
| 1 | Case Intake & Matter Management | Case Management |
| 2 | Client Management & Portal | Client Management |
| 3 | Document Processing & Search | Document Management |
| 4 | AI Document Summaries | AI & Knowledge |
| 5 | Legal Research Assistance | AI & Knowledge |
| 6 | Contract Review | AI & Knowledge |
| 7 | Case-Scoped AI Assistants | AI & Knowledge |
| 8 | Knowledge Search (RAG) | AI & Knowledge |
| 9 | Workflow Automation | Workflow Orchestration |
| 10 | Approvals & Human-in-the-Loop | Audit & Compliance |
| 11 | Audit Logs & Compliance | Audit & Compliance |
| 12 | Notifications | Notifications |
| 13 | Firm Administration & RBAC | Identity & Access |

Detail: `docs/01-product/capabilities.md`

---

## Architecture Topology

**Pattern:** Modular monolith (ADR-001) — single FastAPI deploy, 8 bounded context modules.

```
Browser → CloudFront/WAF → ALB → Next.js (ECS)
                              → FastAPI (ECS)
                                    ↓
                    PostgreSQL (7 schemas) + Redis + S3
                                    ↓
                              RabbitMQ → Celery Workers → n8n (private VPC)
                                                              ↓
                                                    Microsoft 365, LLM, Courts
```

**Deployment:** AWS ECS Fargate, us-east-1 primary, Terraform in `infra/terraform/`.

Detail: `architecture/OVERVIEW.md`, `docs/03-architecture/container-architecture.md`

---

## Technology Stack (Summary)

| Layer | Tech |
|-------|------|
| Frontend | Next.js 14+ App Router, React 18, TypeScript, Tailwind, ShadCN |
| State | Zustand (UI), React Query (server) |
| Backend | Python 3.12+, FastAPI, Pydantic v2, SQLAlchemy 2.0, Alembic |
| Queue | Celery + RabbitMQ (Amazon MQ) |
| Database | PostgreSQL 16+ with pgvector |
| Cache | Redis 7+ (ElastiCache) |
| Storage | S3 (SSE-KMS) |
| Orchestration | n8n (private subnet) |
| AI | Azure OpenAI (prod default), OpenAI (fallback), Anthropic (contract review) |
| Observability | CloudWatch, OpenTelemetry/X-Ray, structured JSON logs |
| CI/CD | GitHub Actions, Docker |

Full stack: `memory/STACK.md`

---

## Platform Invariants (Non-Negotiable)

See `memory/INVARIANTS.md` for enforcement detail.

1. Business logic **only** in FastAPI — not n8n, not frontend
2. n8n **private** — orchestration only; no public URL; no PostgreSQL access
3. All AI **async** — 202 + job polling/SSE; never sync LLM in HTTP handler
4. **Matter walls** — case-level ABAC; 404 (not 403) on GET deny (ADR-007)
5. **Immutable audit** — append-only `audit.audit_logs`
6. **Event-driven** — transactional outbox → RabbitMQ (ADR-006)
7. **HITL** — AI legal outputs require attorney approval before team visibility
8. Frontend **never** calls n8n, RabbitMQ, workers, or LLM providers directly
9. **RFC before code** — major features require Accepted RFC in `docs/18-rfc/` before implementation
10. **Platform readiness** — all 10 checks in `docs/14-playbooks/platform-readiness-gate.md` before auth or business logic

---

## Domain Model (Summary)

**8 bounded contexts:** Identity & Access, Client Management, Case Management ★, Document Management, Workflow Orchestration, AI & Knowledge, Audit & Compliance, Notifications.

**Central aggregate:** `Case` — tasks, deadlines, hearings, notes, participants, timeline.

**Key aggregates:** Client, Document, WorkflowDefinition/WorkflowExecution, AISummary, PromptTemplate, Approval.

Detail: `memory/DOMAIN.md`, `docs/02-domain/`

---

## Data & Messaging

- **Single PostgreSQL** with schema-per-context (ADR-003): `identity`, `cases`, `documents`, `workflows`, `ai`, `audit`, `shared`
- **No cross-schema FKs** — UUID refs validated in application layer
- **Outbox:** `shared.outbox_events` — same transaction as domain write
- **Queue naming:** `{domain}.{action}.{priority}` (e.g., `document.process.high`)

Detail: `docs/05-database/schema-overview.md`, `docs/03-architecture/event-driven-design.md`

---

## Security Model

- **Auth:** JWT access (15 min) + refresh token (7 days, rotated, httpOnly) — ADR-005
- **AuthZ:** RBAC (roles/permissions) + ABAC (matter walls)
- **Permissions:** Resolved server-side per request — NOT in JWT claims
- **Secrets:** AWS Secrets Manager only
- **Encryption:** TLS 1.2+ transit; RDS/S3/ElastiCache at rest

Detail: `docs/08-security/`, `docs/04-api/authentication.md`

---

## Delivery Phases

| Phase | Scope |
|-------|-------|
| **1 — MVP** | Case intake, document upload, AI summary, basic workflow, RBAC, audit |
| **2** | Contract review, legal research, M365 integration, client portal |
| **3** | Entra ID SSO, analytics, multi-office, DR automation |
| **4** | Extract high-load contexts to microservices if metrics justify |

Roadmap: `docs/01-product/roadmap.md`

---

## Repository Layout (Planned)

```
lexflow-ai/
├── apps/web/          # Next.js
├── apps/api/          # FastAPI
├── services/{context}/# Domain modules (DDD layers)
├── workers/           # Celery tasks
├── n8n/workflows/     # Version-controlled workflow JSON
├── packages/          # Shared TS + Python libs
├── infra/terraform/   # AWS IaC
├── docs/              # Authoritative documentation
└── .ai/               # AI context (this folder)
```

Detail: `docs/folder-structure.md`

---

## Explicit Non-Goals

- Replace attorney judgment with autonomous AI
- Public n8n or automation surface
- Cross-matter visibility without authorization
- Multi-tenant SaaS (Phase 1)
- Business logic in visual workflow tools

Detail: `docs/01-product/non-goals.md`

---

## Key Documents by Task

| Task | Read |
|------|------|
| Any code change | `memory/INVARIANTS.md`, `docs/development-standards.md` |
| API endpoint | `docs/04-api/endpoints-{resource}.md` |
| Database change | `docs/05-database/{schema}-schema.md` |
| n8n workflow | `docs/06-workflows/orchestration-model.md` |
| AI feature | `docs/07-ai/`, ADR-004, ADR-008 |
| Deploy | `docs/14-playbooks/deploy-production.md` |
| Onboarding | `docs/14-playbooks/onboarding.md` |

Full index: `memory/DOC-INDEX.md`

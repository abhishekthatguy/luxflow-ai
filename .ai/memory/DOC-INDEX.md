# LexFlow AI — Documentation Index Map

**Purpose:** Route AI assistants to the correct `docs/` file by topic.  
**Master index:** `docs/README.md` (146 documents)  
**Status:** Pre-implementation — all docs are draft/specification

---

## Quick Lookup by Task

| I need to… | Go to |
|------------|-------|
| Understand the product | `docs/01-product/vision.md` |
| Name something correctly | `docs/02-domain/ubiquitous-language.md` → `.ai/memory/GLOSSARY.md` |
| Design a feature | `docs/02-domain/bounded-contexts.md` + relevant aggregate |
| Build an API endpoint | `docs/04-api/endpoints-{resource}.md` |
| Change database schema | `docs/05-database/{schema}-schema.md` |
| Add n8n workflow | `docs/06-workflows/orchestration-model.md`, `docs/14-playbooks/add-workflow.md` |
| Add AI capability | `docs/07-ai/README.md`, `docs/04-api/endpoints-ai.md` |
| Fix auth/security | `docs/08-security/matter-walls.md`, `docs/04-api/authorization-rbac.md` |
| Deploy | `docs/14-playbooks/deploy-production.md` |
| Onboard | `docs/14-playbooks/onboarding.md` |
| Understand an ADR | `docs/13-decisions/00N-*.md` |
| Interview prep | `docs/15-interview/system-design-overview.md` |

---

## Folder 01 — Product (`docs/01-product/`)

| File | Content | When to read |
|------|---------|--------------|
| `README.md` | Section index | Product overview |
| `vision.md` | Strategic north star, pillars | Any product/architecture decision |
| `user-personas.md` | 10 personas, roles, permissions | Auth, RBAC, UI design |
| `capabilities.md` | 13 platform capabilities | Feature scoping |
| `roadmap.md` | Phase 1–4 milestones | Priority, scope boundaries |
| `success-metrics.md` | KPIs, SLAs | NFR validation |
| `non-goals.md` | Explicit exclusions | Prevent scope creep |

---

## Folder 02 — Domain (`docs/02-domain/`)

| File | Content | When to read |
|------|---------|--------------|
| `README.md` | DDD section index | Domain modeling |
| `bounded-contexts.md` | 8 contexts, context map | Architecture, integration |
| `case-aggregate.md` | Case aggregate, state machine | Case features |
| `client-aggregate.md` | Client, Contact, portal | Client/intake features |
| `document-aggregate.md` | Document, versioning, OCR | Document features |
| `workflow-aggregate.md` | Workflow def/execution | Automation features |
| `ai-aggregate.md` | AISummary, prompts, HITL | AI features |
| `domain-events.md` | Full event catalog + payloads | Event handlers, outbox |
| `ubiquitous-language.md` | Complete glossary | Naming anything |

---

## Folder 03 — Architecture (`docs/03-architecture/`)

| File | Content | When to read |
|------|---------|--------------|
| `README.md` | C4 section index | System design |
| `system-context.md` | C4 L1 — users, externals | Big picture |
| `container-architecture.md` | C4 L2 — ECS, data stores | Infrastructure planning |
| `component-architecture.md` | C4 L3 — FastAPI modules | Backend structure |
| `data-flow.md` | Sync/async paths | Request handling |
| `event-driven-design.md` | Outbox, RabbitMQ topology | Async, events |
| `integration-patterns.md` | Adapters, M365 | External systems |
| `cross-cutting-concerns.md` | Idempotency, tracing, cache | Middleware, utilities |
| `nfr-requirements.md` | Scale, HA, DR, performance | Capacity planning |

**Legacy root docs** (superseded by numbered folders — see `docs/MIGRATION.md`):
- `docs/high-level-architecture.md`
- `docs/domain-model.md`
- `docs/database-architecture.md`
- `docs/api-architecture.md`
- `docs/event-driven-architecture.md`

---

## Folder 04 — API (`docs/04-api/`)

| File | Content | When to read |
|------|---------|--------------|
| `README.md` | API section index | REST work |
| `rest-standards.md` | Conventions, response envelope | Any endpoint |
| `authentication.md` | JWT, refresh, login flows | Auth implementation |
| `authorization-rbac.md` | RBAC matrix, permissions | AuthZ |
| `endpoints-cases.md` | Case API + examples | Case endpoints |
| `endpoints-documents.md` | Upload, search | Document endpoints |
| `endpoints-ai.md` | Async AI (202 pattern) | AI endpoints |
| `endpoints-workflows.md` | Trigger, status | Workflow endpoints |
| `error-handling.md` | RFC 7807 catalog | Error responses |
| `versioning.md` | API versioning strategy | Breaking changes |
| `webhooks-internal.md` | n8n HMAC callbacks | Internal webhooks |

---

## Folder 05 — Database (`docs/05-database/`)

| File | Content | When to read |
|------|---------|--------------|
| `README.md` | Schema section index | DB work |
| `schema-overview.md` | 7 schemas, conventions | Any schema change |
| `identity-schema.md` | Users, roles, tokens | Auth tables |
| `cases-schema.md` | Cases, tasks, timeline | Case tables |
| `documents-schema.md` | Documents, pgvector | Document tables |
| `workflows-schema.md` | Definitions, executions | Workflow tables |
| `ai-schema.md` | Summaries, prompts, usage | AI tables |
| `audit-schema.md` | Audit logs, outbox, notifications | Audit/outbox |
| `indexing-strategy.md` | HNSW, full-text | Performance |
| `migrations.md` | Alembic conventions | Migrations |
| `retention-backup.md` | Retention, backup | Compliance |

---

## Folder 06 — Workflows (`docs/06-workflows/`)

| File | Content | When to read |
|------|---------|--------------|
| `README.md` | Workflow section index | Automation |
| `orchestration-model.md` | FastAPI vs n8n split | **Required before n8n work** |
| `n8n-integration.md` | Private deployment, prohibited nodes | n8n setup |
| `workflow-catalog.md` | Initial workflow list | Workflow design |
| `webhook-contracts.md` | FastAPI ↔ n8n payloads | Integration |
| `retry-dlq.md` | Retry, dead letter queues | Reliability |
| `promotion-pipeline.md` | dev → staging → prod | Deploy workflows |

---

## Folder 07 — AI (`docs/07-ai/`)

| File | Content | When to read |
|------|---------|--------------|
| `README.md` | AI section index | AI features |
| `llm-providers.md` | Provider adapter pattern | LLM integration |
| `prompt-management.md` | Versioned prompt registry | Prompts |
| `rag-architecture.md` | Chunking, embeddings, search | RAG |
| `safety-guardrails.md` | PII redaction, injection defense | Pre-LLM pipeline |
| `human-in-the-loop.md` | Attorney approval workflow | HITL |
| `usage-metering.md` | Token tracking, cost controls | Billing/compliance |

---

## Folder 08 — Security (`docs/08-security/`)

| File | Content | When to read |
|------|---------|--------------|
| `README.md` | Security section index | Security review |
| `threat-model.md` | STRIDE analysis | Threat assessment |
| `network-security.md` | VPC, SGs, WAF | Network design |
| `encryption.md` | At rest, in transit, PII | Crypto |
| `secrets-management.md` | AWS Secrets Manager | Secrets |
| `matter-walls.md` | ABAC, ethical walls, MW-004 | **Required for auth work** |
| `compliance-mapping.md` | ABA, GDPR, CCPA, SOC 2 | Compliance |
| `incident-response.md` | Breach lifecycle | Incidents |

---

## Folder 09 — Deployment (`docs/09-deployment/`)

| File | Content |
|------|---------|
| `README.md` | Deployment index |
| `aws-topology.md` | VPC, ECS, RDS, S3, ALB |
| `terraform.md` | Terraform modules, state |
| `cicd-pipeline.md` | GitHub Actions |
| `docker-containers.md` | Container builds, compose |
| `environment-strategy.md` | local, dev, staging, prod |
| `zero-downtime-deploy.md` | Rolling updates, migrations |
| `disaster-recovery.md` | HA, RPO/RTO, failover |

---

## Folder 10 — Testing (`docs/10-testing/`)

| File | Content |
|------|---------|
| `README.md` | Testing index |
| `unit-testing.md` | pytest, Vitest |
| `integration-testing.md` | Testcontainers, **matter wall matrix** |
| `e2e-testing.md` | Playwright journeys |
| `load-testing.md` | k6 scenarios |
| `security-testing.md` | RBAC, injection, scanning |
| `test-data.md` | Factories, seed data |

---

## Folder 11 — Observability (`docs/11-observability/`)

| File | Content |
|------|---------|
| `README.md` | Observability index |
| `structured-logging.md` | JSON logs, PII redaction |
| `distributed-tracing.md` | OpenTelemetry, X-Ray |
| `metrics-alerting.md` | CloudWatch, P1–P4 alerts |
| `dashboards.md` | Operational, business, security |
| `runbooks.md` | Alert response |

---

## Folder 12 — UI (`docs/12-ui/`)

| File | Content |
|------|---------|
| `README.md` | Frontend index |
| `design-system.md` | Tailwind, ShadCN, legal UI |
| `page-architecture.md` | App Router structure |
| `state-management.md` | Zustand vs React Query |
| `real-time-updates.md` | SSE for jobs/notifications |
| `accessibility.md` | WCAG 2.1 AA |
| `client-portal.md` | Client-facing UI |

---

## Folder 13 — Decisions (`docs/13-decisions/`)

| ADR | Decision | `.ai` summary |
|-----|----------|---------------|
| `001-modular-monolith.md` | Modular monolith | `architecture/DECISIONS.md` |
| `002-n8n-orchestration-only.md` | n8n orchestration only | |
| `003-postgresql-single-database.md` | Single PG, schema separation | |
| `004-async-ai-processing.md` | Async AI worker path | |
| `005-jwt-authentication.md` | JWT + refresh tokens | |
| `006-transactional-outbox.md` | Transactional outbox | |
| `007-matter-walls-404-deny.md` | 404 not 403 on GET deny | |
| `008-azure-openai-primary.md` | Azure OpenAI production default | |

Duplicate ADRs also in `docs/adr/` (legacy path).

---

## Folder 14 — Playbooks (`docs/14-playbooks/`)

| Playbook | Use when |
|----------|----------|
| `onboarding.md` | New engineer first week |
| `local-dev-setup.md` | Setting up dev environment |
| `incident-triage.md` | P1–P4 incident |
| `deploy-production.md` | Production deploy |
| `rotate-secrets.md` | Secret rotation |
| `add-workflow.md` | New n8n workflow |
| `add-llm-provider.md` | New LLM provider |

---

## Folder 15 — Interview (`docs/15-interview/`)

| File | Content |
|------|---------|
| `system-design-overview.md` | 15-min architecture pitch |
| `architecture-deep-dive.md` | 45-min staff-level dive |
| `tradeoffs-discussion.md` | Tradeoff defense |
| `scaling-questions.md` | Scale to 1K users, 50K workflows |
| `security-questions.md` | Legal tech security Q&A |

---

## Root-Level Docs (Legacy → Prefer Numbered Folders)

| Legacy file | Superseded by |
|-------------|---------------|
| `docs/product-overview.md` | `docs/01-product/` |
| `docs/high-level-architecture.md` | `docs/03-architecture/` |
| `docs/domain-model.md` | `docs/02-domain/` |
| `docs/database-architecture.md` | `docs/05-database/` |
| `docs/development-standards.md` | Still active — coding conventions |
| `docs/MIGRATION.md` | Full legacy → new mapping |

---

## Reading Paths by Role

| Role | Path |
|------|------|
| New engineer | `14-playbooks/onboarding.md` → `01-product/vision.md` → `03-architecture/system-context.md` |
| Backend | `02-domain/` → `04-api/` → `05-database/` → `03-architecture/event-driven-design.md` |
| Frontend | `12-ui/` → `04-api/rest-standards.md` → `08-security/matter-walls.md` |
| DevOps/SRE | `09-deployment/` → `11-observability/` → `14-playbooks/deploy-production.md` |
| Security | `08-security/threat-model.md` → `compliance-mapping.md` → `04-api/authorization-rbac.md` |
| AI/ML | `07-ai/` → `02-domain/ai-aggregate.md` → `13-decisions/008-azure-openai-primary.md` |

---

## `.ai/` ↔ `docs/` Mapping

| `.ai/` file | Primary `docs/` sources |
|-------------|-------------------------|
| `memory/PROJECT.md` | `01-product/`, `03-architecture/`, root README |
| `memory/STACK.md` | `development-standards.md`, `03-architecture/container-architecture.md` |
| `memory/INVARIANTS.md` | `docs/README.md` invariants, `13-decisions/` |
| `memory/GLOSSARY.md` | `02-domain/ubiquitous-language.md` |
| `memory/DOMAIN.md` | `02-domain/bounded-contexts.md`, `*-aggregate.md` |
| `architecture/OVERVIEW.md` | `03-architecture/`, `high-level-architecture.md` |
| `architecture/DATA-FLOW.md` | `03-architecture/data-flow.md` |
| `architecture/BOUNDED-CONTEXTS.md` | `02-domain/bounded-contexts.md` |
| `architecture/DECISIONS.md` | `13-decisions/001-008` |

# LexFlow AI — Sprint Planning

**Version:** 1.0  
**Status:** Ready for Jira Import  
**Last Updated:** 2026-07-06  
**Sprint Duration:** 2 weeks (10 working days)

---

## Purpose

This folder contains **detailed sprint plans** for LexFlow AI MVP delivery (Sprints 0–5). Each sprint document includes goals, epics, user stories, acceptance criteria, story points, dependencies, and demo criteria. CSV files in [`jira-import/`](./jira-import/) can be imported into Jira Cloud or adapted for Azure DevOps / Linear.

---

## Sprint Overview

```mermaid
gantt
    title LexFlow AI — Sprint Timeline (12 weeks)
    dateFormat YYYY-MM-DD
    axisFormat %b %d

    section Sprints
    Sprint 0 Engineering Setup   :s0, 2026-07-07, 7d
    Sprint 1 Full Platform       :s1, after s0, 14d
    Sprint 2 Auth & Domain     :s2, after s1, 14d
    Sprint 3 Case Management   :s3, after s2, 14d
    Sprint 4 AI & n8n            :s4, after s3, 14d
    Sprint 5 Production          :s5, after s4, 14d
```

| Sprint | Theme | Story Points (Target) | Primary Outcome |
|--------|-------|----------------------|-----------------|
| [Sprint 0](./sprint-00-documentation.md) | **Planning** — engineering setup spec (code in Sprint 1 Phase 1) | 34 | Spec + quickstart playbook |
| [Sprint 1](./sprint-01-infrastructure.md) | **Phase 1:** LEX-001–010 scaffold · **Phase 2:** full platform | 76 | `verify-quickstart` then `verify-platform` |
| [Sprint 2](./sprint-02-auth-domain.md) | Auth, RBAC, core domain models | 62 | Login works; matter walls enforced; migrations baseline |
| [Sprint 3](./sprint-03-case-management.md) | Case Management module | 68 | Full case CRUD UI + API; timeline; participants |
| [Sprint 4](./sprint-04-ai-n8n.md) | AI services + n8n orchestration | 72 | Async AI summary; document pipeline; first workflow |
| [Sprint 5](./sprint-05-production.md) | Hardening, observability, AWS | 58 | Staging load test; observability; production deploy |

**Total estimated:** ~349 story points (~12 weeks at velocity 29–35 SP/sprint for a team of 6–8)

---

## RFC Gate (Sprint 1+)

From Sprint 1 onward, **no epic enters a sprint without an Accepted RFC** in [`docs/18-rfc/`](../18-rfc/README.md).

| Sprint | Required RFC(s) | Status |
|--------|-----------------|--------|
| Sprint 2 | [RFC-002](../18-rfc/RFC-002-authentication-rbac.md) | Planned — draft before kickoff |
| Sprint 3 | [RFC-001](../18-rfc/RFC-001-case-management.md) | Planned |
| Sprint 4 | [RFC-003](../18-rfc/RFC-003-async-ai-summaries.md), [RFC-004](../18-rfc/RFC-004-document-pipeline.md), [RFC-005](../18-rfc/RFC-005-n8n-orchestration-bootstrap.md) | Planned |

Sprint 1 (infrastructure) is exempt — no user-facing feature RFC required. Process meta-RFC [RFC-000](../18-rfc/000-rfc-process.md) is **Accepted**.

---

## Platform Readiness Gate (before Sprint 2)

**No authentication or business logic until all 10 checks pass.** See [`platform-readiness-gate.md`](../14-playbooks/platform-readiness-gate.md).

| # | Check |
|---|-------|
| 1 | Docker Compose boots all services |
| 2 | Health endpoints for every service |
| 3 | Structured logging with request/correlation IDs |
| 4 | OpenTelemetry traces visible in Grafana |
| 5 | Redis cache abstraction tested |
| 6 | RabbitMQ publish/consume sample works |
| 7 | Celery worker processes a sample job |
| 8 | n8n can call FastAPI through internal network |
| 9 | MinIO upload/download works |
| 10 | GitHub Actions pass lint, type checks, and tests |

```bash
make verify-platform   # must exit 0 before Sprint 2 kickoff
```

Sprint 2 requires **Platform Ready** + **RFC-002 Accepted**.

---

## Team Assumptions

| Role | Count | Sprint Focus |
|------|-------|--------------|
| Tech Lead / Architect | 1 | All sprints — ADRs, reviews, unblocking |
| Backend Engineer | 2 | Sprints 1–5 |
| Frontend Engineer | 2 | Sprints 1–5 |
| DevOps / SRE | 1 | Sprints 1, 5 (support 2–4) |
| QA / SDET | 1 | Sprints 2–5 |
| Product Owner | 1 | All sprints — backlog, acceptance |
| **Optional** AI/ML Engineer | 0.5 FTE | Sprint 4 primary |

Adjust velocity if team size differs. Story points use **Fibonacci (1, 2, 3, 5, 8, 13)**.

---

## Jira Import Guide

### Files

| File | Contents |
|------|----------|
| [`jira-import/epics.csv`](./jira-import/epics.csv) | 6 epics (one per sprint theme) + cross-cutting |
| [`jira-import/stories.csv`](./jira-import/stories.csv) | All user stories with acceptance criteria |
| [`jira-import/tasks.csv`](./jira-import/tasks.csv) | Technical tasks (sub-task candidates) |
| [`jira-import/labels-and-components.csv`](./jira-import/labels-and-components.csv) | Reference for Jira project setup |

### Jira Cloud Import Steps

1. **Create project** — Scrum template, key: `LEX` (or `LFA`)
2. **Configure components:** `backend`, `frontend`, `infra`, `n8n`, `ai`, `docs`, `qa`
3. **Configure labels:** `sprint-0` … `sprint-5`, `matter-wall`, `security`, `blocker`
4. **Import epics first:** Jira → Project Settings → External Import → CSV → `epics.csv`
5. **Import stories:** Map columns: Summary, Issue Type, Description, Epic Link, Story Points, Priority, Labels, Components
6. **Create sprints:** Backlog → Create Sprint → drag stories by `sprint-N` label
7. **Map custom fields:** If `Story Points` field name differs, remap on import

### CSV Column Mapping (Jira Cloud)

| CSV Column | Jira Field |
|------------|------------|
| `Summary` | Summary |
| `Issue Type` | Issue Type |
| `Description` | Description |
| `Epic Name` | Epic Link (after epics exist) |
| `Story Points` | Story point estimate |
| `Priority` | Priority |
| `Labels` | Labels (comma-separated) |
| `Components` | Component/s |
| `Acceptance Criteria` | Append to Description or Custom Field |
| `Sprint` | Assign manually post-import |

### Azure DevOps / Linear

- **Azure DevOps:** Import `stories.csv` as Work Items; map Epic Name → Parent
- **Linear:** Use `stories.csv` Summary + Description; create Cycles for sprints

---

## Epic Index

| Epic Key | Epic Name | Sprint |
|----------|-----------|--------|
| LEX-E0 | Documentation & Alignment | Sprint 0 |
| LEX-E1 | Platform Infrastructure | Sprint 1 |
| LEX-E2 | Identity, Auth & Domain Foundation | Sprint 2 |
| LEX-E3 | Case Management Module | Sprint 3 |
| LEX-E4 | AI Services & Workflow Orchestration | Sprint 4 |
| LEX-E5 | Production Readiness & AWS Deployment | Sprint 5 |

---

## Cross-Sprint Dependencies

```mermaid
flowchart LR
    S0[Sprint 0<br/>Docs signed off] --> S1[Sprint 1<br/>Infra + CI]
    S1 --> S2[Sprint 2<br/>Auth + Domain]
    S2 --> S3[Sprint 3<br/>Case Module]
    S3 --> S4[Sprint 4<br/>AI + n8n]
    S4 --> S5[Sprint 5<br/>Production]
```

| Dependency | Blocker For |
|------------|-------------|
| Docker Compose local stack | All development sprints |
| CI pipeline | Merge gates Sprint 2+ |
| Auth + RBAC | All case-scoped features |
| Matter walls | Case module, AI, documents |
| Case aggregate | Documents, AI, workflows |
| RabbitMQ + Celery | AI async, n8n triggers |
| n8n private deploy | Workflow stories Sprint 4 |

---

## Definition of Ready (Sprint Start)

From [`.ai/handbook/definition-of-ready.md`](../.ai/handbook/definition-of-ready.md):

- [ ] Story has clear acceptance criteria
- [ ] Dependencies identified and unblocked
- [ ] Design spec linked (if UI) — `docs/16-design-system/`
- [ ] API contract linked (if backend) — `docs/04-api/`
- [ ] Story pointed by team
- [ ] No open architecture questions (or ADR drafted)

---

## Definition of Done (All Sprints)

From [`.ai/handbook/definition-of-done.md`](../.ai/handbook/definition-of-done.md):

- [ ] Acceptance criteria met
- [ ] CI passes (lint, test, build)
- [ ] Code review approved
- [ ] Matter wall tests pass (if auth/case touched)
- [ ] Audit logging (if mutating API)
- [ ] Documentation updated if behavior changed

---

## Sprint Documents

| Sprint | Document |
|--------|----------|
| Sprint 0 | [sprint-00-documentation.md](./sprint-00-documentation.md) |
| Sprint 1 | [sprint-01-infrastructure.md](./sprint-01-infrastructure.md) |
| Sprint 2 | [sprint-02-auth-domain.md](./sprint-02-auth-domain.md) |
| Sprint 3 | [sprint-03-case-management.md](./sprint-03-case-management.md) |
| Sprint 4 | [sprint-04-ai-n8n.md](./sprint-04-ai-n8n.md) |
| Sprint 5 | [sprint-05-production.md](./sprint-05-production.md) |

---

## References

| Document | Path |
|----------|------|
| Product roadmap | [../01-product/roadmap.md](../01-product/roadmap.md) |
| Capabilities | [../01-product/capabilities.md](../01-product/capabilities.md) |
| DoR / DoD | [../.ai/handbook/](../.ai/handbook/README.md) |
| Architecture | [../03-architecture/README.md](../03-architecture/README.md) |
| Design system | [../16-design-system/README.md](../16-design-system/README.md) |

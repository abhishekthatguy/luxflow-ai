# Sprint 0 — Documentation Review & Alignment

**Epic:** LEX-E0 — Documentation & Alignment  
**Duration:** 2 weeks  
**Target Velocity:** 34 story points  
**Sprint Goal:** Validate all pre-implementation documentation, close gaps, obtain stakeholder sign-off, and produce a refined Jira backlog ready for Sprint 1.

---

## Context

LexFlow AI has **146+ enterprise docs**, **80+ AI context files**, and a **complete design system** before any application code. Sprint 0 ensures the team, Product Owner, and sponsors align on scope, architecture, and delivery plan — not writing new docs from scratch unless gaps are found.

---

## Sprint Ceremonies

| Ceremony | When | Duration | Output |
|----------|------|----------|--------|
| Sprint Planning | Day 1 AM | 2h | Sprint backlog committed |
| Architecture walkthrough | Day 1 PM | 2h | Team questions logged |
| Doc review sessions | Days 2–8 | 4 × 1h | Sign-off checklist |
| Backlog refinement | Day 7 | 2h | Sprint 1 stories ready |
| Stakeholder review | Day 9 | 1h | PO + sponsor sign-off |
| Sprint Review | Day 10 AM | 1h | Documentation baseline approved |
| Retrospective | Day 10 PM | 1h | Process improvements |

---

## Epics & Stories

### Story LEX-001 — Documentation inventory & gap analysis (5 SP)

**As a** Tech Lead  
**I want** a verified inventory of all documentation with gap analysis  
**So that** we know what is complete vs. missing before coding starts

**Acceptance Criteria:**
- [ ] All `docs/01`–`docs/16` folders indexed with owner assigned
- [ ] Gap report published listing missing or conflicting sections
- [ ] Conflicts between docs flagged with resolution owner
- [ ] `.ai/` context layer cross-checked against `docs/`
- [ ] Output saved to `docs/17-sprint-planning/sprint-0-deliverables/gap-analysis.md`

**Tasks:**
- Run doc inventory script / manual audit
- Compare ADRs vs. architecture docs
- Compare API docs vs. domain model

**Labels:** `sprint-0`, `docs`  
**Component:** `docs`

---

### Story LEX-002 — Architecture review & sign-off (8 SP)

**As a** Engineering team  
**I want** a structured architecture review of C4, data flows, and ADRs  
**So that** all engineers share the same mental model

**Acceptance Criteria:**
- [ ] C4 L1–L3 reviewed ([`docs/03-architecture/`](../03-architecture/README.md))
- [ ] All 8 ADRs (001–008) discussed and accepted or amended
- [ ] Platform invariants reviewed ([`.ai/memory/INVARIANTS.md`](../../.ai/memory/INVARIANTS.md))
- [ ] n8n boundary understood by all — quiz/walkthrough completed
- [ ] Architecture review notes published with action items
- [ ] Tech Lead sign-off recorded

**Labels:** `sprint-0`, `architecture`  
**Component:** `docs`

---

### Story LEX-003 — Security & compliance doc review (5 SP)

**As a** Security reviewer / Compliance Officer  
**I want** threat model and matter wall docs validated  
**So that** security requirements are clear before Sprint 2 auth work

**Acceptance Criteria:**
- [ ] STRIDE threat model reviewed ([`docs/08-security/threat-model.md`](../08-security/threat-model.md))
- [ ] Matter wall 404 policy understood (ADR-007)
- [ ] RBAC matrix validated against personas ([`docs/04-api/authorization-rbac.md`](../04-api/authorization-rbac.md))
- [ ] ABA / GDPR mapping reviewed with Compliance Officer
- [ ] Security review checklist attached to Sprint 2 epic

**Labels:** `sprint-0`, `security`  
**Component:** `docs`

---

### Story LEX-004 — Design system review & UX alignment (5 SP)

**As a** Frontend engineer / Designer  
**I want** design system and screen specs reviewed  
**So that** Sprint 3 UI work has approved wireframes

**Acceptance Criteria:**
- [ ] [`docs/16-design-system/`](../16-design-system/README.md) reviewed by frontend team
- [ ] Case dashboard, document viewer, approval center specs approved for MVP
- [ ] App shell, navigation, and responsive behavior agreed
- [ ] ShadCN + Tailwind token mapping documented in [`docs/12-ui/design-system.md`](../12-ui/design-system.md)
- [ ] Open design questions logged (max 5) with resolution dates

**Labels:** `sprint-0`, `design`  
**Component:** `docs`

---

### Story LEX-005 — Database schema review (3 SP)

**As a** Backend engineer  
**I want** PostgreSQL schemas reviewed against domain model  
**So that** Sprint 2 migrations match aggregates

**Acceptance Criteria:**
- [ ] All 7 schemas reviewed ([`docs/05-database/`](../05-database/README.md))
- [ ] Case, Client, Identity schemas mapped to domain aggregates
- [ ] Index strategy agreed for Sprint 3 case list queries
- [ ] Migration conventions agreed ([`docs/05-database/migrations.md`](../05-database/migrations.md))

**Labels:** `sprint-0`, `database`  
**Component:** `docs`

---

### Story LEX-006 — Sprint 1–5 backlog import & refinement (5 SP)

**As a** Product Owner  
**I want** Jira backlog populated from sprint planning docs  
**So that** Sprint 1 can start immediately

**Acceptance Criteria:**
- [ ] Epics LEX-E0 through LEX-E5 created in Jira
- [ ] All Sprint 1 stories imported with acceptance criteria
- [ ] Sprint 2–5 stories in backlog (may refine later)
- [ ] Dependencies linked between stories
- [ ] PO priority order set for Sprint 1

**Labels:** `sprint-0`, `planning`  
**Component:** `docs`

---

### Story LEX-007 — Dev environment prerequisites (3 SP)

**As a** DevOps engineer  
**I want** AWS accounts, GitHub org, and tooling access provisioned  
**So that** Sprint 1 infrastructure work is unblocked

**Acceptance Criteria:**
- [ ] AWS dev + staging accounts accessible to team
- [ ] GitHub repo created with branch protection on `main`
- [ ] Secrets Manager namespace defined (no secrets in repo)
- [ ] Docker Desktop / dev machine requirements documented
- [ ] Team access checklist 100% complete

**Labels:** `sprint-0`, `infra`  
**Component:** `infra`

---

## Sprint 0 Exit Criteria (Definition of Done for Sprint)

- [ ] Gap analysis complete; no P0 doc blockers for Sprint 1
- [ ] Architecture + security + design reviews signed off
- [ ] Jira backlog imported with Sprint 1 ready
- [ ] Team completed onboarding reading ([`docs/14-playbooks/onboarding.md`](../14-playbooks/onboarding.md))
- [ ] AWS + GitHub access for all engineers
- [ ] Sprint 1 planning pre-read sent to team

---

## Risks

| Risk | Mitigation |
|------|------------|
| Doc fatigue — team skips reading | Structured 1h review sessions with checklist |
| Conflicting docs | Gap analysis story resolves; docs/ wins |
| Sponsor unavailable for sign-off | Async review with 48h comment window |

---

## Demo (Sprint Review)

Present to stakeholders:
1. Documentation map walkthrough (15 min)
2. Architecture decision summary (10 min)
3. Sprint 1 backlog preview (10 min)
4. Q&A (15 min)

---

## References

- [Product Roadmap](../01-product/roadmap.md) — Phase 1 scope
- [Onboarding Playbook](../14-playbooks/onboarding.md)
- [Engineering Handbook](../../.ai/handbook/engineering-handbook.md)

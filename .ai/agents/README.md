# LexFlow AI — Agent Personas

**Purpose:** Role-specific instructions for AI coding assistants working on LexFlow AI.  
**Scope:** Guidance only — no application code in this directory.

---

## How to Use

1. **Pick one persona** matching the task (backend API, n8n workflow, security review, etc.).
2. **Load mandatory reads** from that persona file plus applicable `.ai/rules/` and `docs/` paths.
3. **Apply patterns** from `.ai/patterns/` when implementing structural templates.
4. **Validate against examples** in `.ai/examples/` for end-to-end flows.
5. **Never contradict ADRs** in `docs/13-decisions/` — newer decisions supersede older docs.

---

## Persona Index

| Persona | File | Primary Surface |
|---------|------|-----------------|
| Backend Engineer | [backend-engineer.md](./backend-engineer.md) | `services/`, `apps/api/` |
| Frontend Engineer | [frontend-engineer.md](./frontend-engineer.md) | `apps/web/` |
| DevOps Engineer | [devops-engineer.md](./devops-engineer.md) | `infra/`, CI/CD, ECS |
| Security Reviewer | [security-reviewer.md](./security-reviewer.md) | Auth, matter walls, secrets |
| Workflow Engineer | [workflow-engineer.md](./workflow-engineer.md) | `n8n/`, webhook contracts |
| AI/ML Engineer | [ai-ml-engineer.md](./ai-ml-engineer.md) | `services/ai_knowledge/`, workers |
| Code Reviewer | [code-reviewer.md](./code-reviewer.md) | PR review, standards |
| Tech Lead | [tech-lead.md](./tech-lead.md) | Architecture, ADRs, trade-offs |

---

## Global Invariants (All Personas)

| # | Invariant | Source |
|---|-----------|--------|
| 1 | Business logic in `services/` Python — never in n8n or frontend | ADR-001, ADR-002 |
| 2 | Authorization on FastAPI only — frontend reflects, never enforces | `docs/08-security/matter-walls.md` |
| 3 | Domain events via transactional outbox — no dual writes | ADR-006 |
| 4 | LLM inference async on Celery — API returns `202 Accepted` | ADR-004 |
| 5 | Matter wall deny → `404 Not Found` (not 403) for case-scoped resources | ADR-007 |
| 6 | n8n orchestration only — no domain decisions in workflow graphs | ADR-002 |
| 7 | Schema changes via Alembic only — upgrade + downgrade required | `docs/05-database/migrations.md` |

---

## Cross-References

| Resource | Path |
|----------|------|
| Product & domain | `docs/01-product/`, `docs/02-domain/` |
| Architecture | `docs/03-architecture/` |
| API contracts | `docs/04-api/` |
| Database | `docs/05-database/` |
| Workflows & AI | `docs/06-workflows/`, `docs/07-ai/` |
| Security | `docs/08-security/` |
| Ops & testing | `docs/09-deployment/` … `docs/11-observability/`, `docs/10-testing/` |
| UI | `docs/12-ui/` |
| ADRs | `docs/13-decisions/`, `docs/adr/` |
| Playbooks | `docs/14-playbooks/` |
| Project rules | `.ai/rules/` |
| Patterns | `.ai/patterns/` |
| Examples | `.ai/examples/` |
| Dev standards | `docs/development-standards.md` |
| Folder layout | `docs/folder-structure.md` |

---

## Escalation

| Situation | Persona |
|-----------|---------|
| Architectural trade-off or new ADR | Tech Lead |
| Security / compliance concern | Security Reviewer |
| Cross-layer feature (API + UI + worker) | Tech Lead coordinates; use layer personas for implementation |
| n8n + FastAPI contract change | Workflow Engineer + Backend Engineer |

# LexFlow AI

**Enterprise AI Automation Platform for Law Firms**

LexFlow AI eliminates repetitive manual work for lawyers, paralegals, legal assistants, and operations teams — without replacing legal judgment.

**Status:** Sprint 1 Phase 1 (Option B) — core scaffold shipped; run `make setup && make dev`. Phase 2 adds full platform stack.

---

## Quick Start (10 minutes)

**Goal:** clone → developing with no business code.

```bash
git clone git@github.com:abhishekthatguy/luxflow-ai.git
cd luxflow-ai
cp .env.example .env
make setup && make dev
make verify-quickstart
make verify-platform   # or: ./verify-platform.sh
make migrate && make seed && make verify-sprint3   # Sprint 3 case module
```

**Phase 1 AI stack (local / low cost):** PyMuPDF → PaddleOCR → Ollama → pgvector. See [`docs/07-ai/PHASE-1-2-STACK.md`](./docs/07-ai/PHASE-1-2-STACK.md).

```bash
# Enable Phase 1 LLM in .env: LLM_PROVIDER=ollama
docker compose up -d ollama
docker compose exec ollama ollama pull qwen2.5:latest
docker compose exec ollama ollama pull nomic-embed-text
make migrate   # applies pgvector + document_chunks
```

Full playbook: [`docs/14-playbooks/10-minute-quickstart.md`](./docs/14-playbooks/10-minute-quickstart.md)

---

## Repository

This is the **sole Git repository** for LexFlow AI — product code, documentation, AI context, and infrastructure definitions live here only (not in other workspaces).

| | |
|---|---|
| **GitHub (SSH)** | `git@github.com:abhishekthatguy/luxflow-ai.git` |
| **GitHub (HTTPS)** | `https://github.com/abhishekthatguy/luxflow-ai` |
| **Default branch** | `main` |

```bash
git clone git@github.com:abhishekthatguy/luxflow-ai.git
cd luxflow-ai
```

> **Note:** The GitHub repository name is `luxflow-ai`; the product name is **LexFlow AI**. Local folder names may vary (`lexflow-AI`, `luxflow-ai`).

---

## Documentation & AI Context

| Layer | Path | Purpose |
|-------|------|---------|
| **AI Context** | [`.ai/`](./.ai/README.md) | Context engineering for Cursor, Claude, Copilot — **start here for AI assistants** |
| **Enterprise Docs** | [`docs/`](./docs/README.md) | Full documentation — 146 files across 15 folders |
| **Agent Entry** | [`AGENTS.md`](./AGENTS.md) | Shared instructions for all AI coding tools |
| **Claude Code** | [`CLAUDE.md`](./CLAUDE.md) | Claude-specific session bootstrap |
| **Credentials (local)** | [`CREDENTIALS.md`](./CREDENTIALS.md) | URLs, RBAC logins, MinIO, email, `.env` secrets map |

**Engineers:** [Documentation Index](./docs/README.md) · **AI assistants:** [`.ai/README.md`](./.ai/README.md)

| Section | Description |
|---------|-------------|
| [01-product](./docs/01-product/) | Vision, personas, capabilities, roadmap |
| [02-domain](./docs/02-domain/) | DDD aggregates, events, ubiquitous language |
| [03-architecture](./docs/03-architecture/) | C4 architecture, data flows, NFRs |
| [04-api](./docs/04-api/) | REST API, auth, endpoints |
| [05-database](./docs/05-database/) | PostgreSQL schemas, indexes, migrations |
| [06-workflows](./docs/06-workflows/) | n8n orchestration (private, no business logic) |
| [07-ai](./docs/07-ai/) | LLM providers, RAG, safety, human-in-the-loop |
| [08-security](./docs/08-security/) | Threat model, encryption, compliance |
| [09-deployment](./docs/09-deployment/) | AWS, Terraform, CI/CD, DR |
| [10-testing](./docs/10-testing/) | Unit, integration, E2E, load, security |
| [11-observability](./docs/11-observability/) | Logging, tracing, metrics, runbooks |
| [12-ui](./docs/12-ui/) | Next.js frontend, design system, accessibility |
| [13-decisions](./docs/13-decisions/) | Architecture Decision Records (8 ADRs) |
| [14-playbooks](./docs/14-playbooks/) | Operational runbooks for engineers |
| [15-interview](./docs/15-interview/) | System design interview preparation |
| [16-design-system](./docs/16-design-system/) | Complete UI/UX design system |
| [17-sprint-planning](./docs/17-sprint-planning/) | Sprint plans & Jira import (Sprints 0–5) |
| [18-rfc](./docs/18-rfc/) | **RFC process** — design every major feature before code |

---

## Architecture at a Glance

```
Frontend (Next.js) → FastAPI → Queue (RabbitMQ) → Workers (Celery) → n8n → External Services
                         ↕                              ↕
                    PostgreSQL + pgvector            Redis + S3
```

**Platform invariants:**
- Business logic lives in **FastAPI** — never in n8n or the frontend
- **n8n** is a private orchestration engine — not publicly accessible
- All **AI processing** is asynchronous with attorney approval for legal outputs
- **Matter walls** enforce case-level access control
- **Immutable audit logs** for all significant actions
- **RFC before code** — major features require an Accepted RFC ([`docs/18-rfc/`](./docs/18-rfc/))
- **Platform readiness** — verify all 10 infra checks before auth or business logic ([`platform-readiness-gate`](./docs/14-playbooks/platform-readiness-gate.md))

---

## Scale Targets

| Metric | Target |
|--------|--------|
| Concurrent users | 1,000+ |
| Workflow executions | 50,000+ / month |
| Documents | Millions |
| Availability | 99.9% |
| RPO / RTO | ≤ 15 min / ≤ 4 hours |

---

## License

Proprietary — All rights reserved.

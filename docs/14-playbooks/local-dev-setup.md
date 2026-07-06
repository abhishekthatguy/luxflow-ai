# Local Development Setup

**LexFlow AI** — Prerequisites, Docker Compose & Troubleshooting  
**Version:** 1.0  
**Status:** Draft — Pre-Implementation  
**Last Updated:** 2026-07-06

---

## Purpose

This playbook gets a LexFlow AI engineer from **zero to running full stack locally** — prerequisites, clone, environment configuration, Docker Compose, Makefile commands, database seeding, and common troubleshooting. Target time: **under 60 minutes** on a standard Mac or Linux workstation.

Architecture detail: [../09-deployment/docker-containers.md](../09-deployment/docker-containers.md), [../09-deployment/environment-strategy.md](../09-deployment/environment-strategy.md).

---

## Scope

| In Scope | Out of Scope |
|----------|--------------|
| Developer workstation prerequisites | AWS dev account provisioning |
| Docker Compose local stack | Production ECS configuration |
| Makefile commands | CI pipeline configuration |
| Local troubleshooting | Firm VPN / Entra ID SSO setup |

---

## Responsibilities

| Role | Responsibility |
|------|----------------|
| **New Engineer** | Complete this playbook; report blockers in `#lexflow-dev` |
| **Platform / SRE** | Keep Makefile and Compose definitions aligned with this doc |
| **Security** | Ensure `.env.example` never contains real secrets |

---

## Prerequisites

### Required Software

| Tool | Minimum Version | Verify Command | Notes |
|------|-----------------|----------------|-------|
| **Git** | 2.40+ | `git --version` | SSH key configured for GitHub |
| **Docker Desktop** | 4.25+ | `docker --version` | Allocate **≥ 6 GB RAM**, **≥ 2 CPUs** |
| **Docker Compose** | v2.20+ | `docker compose version` | Bundled with Docker Desktop |
| **Node.js** | 20 LTS | `node --version` | For IDE tooling; app runs in container |
| **Python** | 3.12+ | `python3 --version` | For scripts and pre-commit hooks |
| **Make** | any | `make --version` | GNU Make on Linux; Xcode CLT on macOS |
| **AWS CLI** | 2.x (optional) | `aws --version` | Only if testing S3 presigned flows against real AWS |

### Recommended IDE Setup

| Extension / Tool | Purpose |
|------------------|---------|
| Docker extension | Container logs and attach |
| Python + Ruff | Backend linting |
| ESLint + Prettier | Frontend linting |
| REST Client / Bruno | API exploration against `:8000` |

### Access Requirements

- [ ] GitHub org membership with repo read/write
- [ ] Slack: `#lexflow-dev`, `#lexflow-incidents` (read-only for new hires)
- [ ] **No production secrets** on developer machines — ever

---

## Setup Flow

```mermaid
flowchart TD
    A[Install prerequisites] --> B[Clone repository]
    B --> C[Copy .env.example → .env]
    C --> D[make setup]
    D --> E[make dev]
    E --> F{Health checks pass?}
    F -->|Yes| G[make test]
    F -->|No| H[Troubleshooting section]
    G --> I[Ready to develop]
    H --> E
```

---

## Step-by-Step Procedure

### Step 1 — Clone Repository

```bash
git clone git@github.com:lexflow-ai/lexflow-ai.git
cd lexflow-ai
```

- [ ] Confirm branch: `git checkout main && git pull`

### Step 2 — Configure Environment

```bash
cp .env.example .env
```

Edit `.env` with local-only values. Key variables:

| Variable | Local Value | Notes |
|----------|-------------|-------|
| `ENVIRONMENT` | `local` | Required |
| `DATABASE_URL` | `postgresql+asyncpg://lexflow:lexflow@postgres:5432/lexflow` | Compose service name |
| `REDIS_URL` | `redis://redis:6379/0` | |
| `RABBITMQ_URL` | `amqp://guest:guest@rabbitmq:5672/` | |
| `S3_ENDPOINT` | `http://minio:9000` | MinIO, not AWS |
| `S3_BUCKET` | `lexflow-local-documents` | Created by seed script |
| `JWT_PRIVATE_KEY` | Generate locally (see below) | Never use prod keys |
| `N8N_WEBHOOK_URL` | `http://n8n:5678` | Internal Compose network |
| `LOG_LEVEL` | `DEBUG` | Verbose for local dev |

Generate local JWT keys:

```bash
openssl genrsa -out /tmp/jwt-private.pem 2048
openssl rsa -in /tmp/jwt-private.pem -pubout -out /tmp/jwt-public.pem
# Paste PEM contents into .env as JWT_PRIVATE_KEY / JWT_PUBLIC_KEY (escaped newlines)
```

- [ ] `.env` is listed in `.gitignore` (verify: `git status` does not show `.env`)
- [ ] No production API keys in `.env`

### Step 3 — Initial Setup (`make setup`)

```bash
make setup
```

Expected actions (defined in root `Makefile`):

| Target | Action |
|--------|--------|
| `setup-deps` | Install Python venv + `pip install -e apps/api`; `npm ci` in `apps/web` |
| `setup-hooks` | Install pre-commit hooks (ruff, eslint, gitleaks) |
| `setup-db` | Start postgres only; run `alembic upgrade head` |
| `setup-seed` | Run `python scripts/seed/dev_seed.py` |
| `setup-minio` | Create local S3 bucket via MinIO client |

- [ ] Setup completes without errors
- [ ] Pre-commit hooks installed: `pre-commit --version`

### Step 4 — Start Full Stack (`make dev`)

```bash
make dev
# Equivalent: docker compose -f docker-compose.yml -f docker/docker-compose.dev.yml up -d
```

### Step 5 — Verify Services

```mermaid
sequenceDiagram
    participant Dev as Developer
    participant Web as web :3000
    participant API as api :8000
    participant PG as postgres
    participant N8N as n8n :5678

    Dev->>Web: Open http://localhost:3000
    Dev->>API: curl http://localhost:8000/health
    API->>PG: Connection check
    API-->>Dev: {"status":"healthy",...}
    Dev->>N8N: curl http://localhost:5678/healthz (via VPN tunnel if restricted)
```

| Service | URL / Command | Expected |
|---------|---------------|----------|
| Web | http://localhost:3000 | Login page loads |
| API health | `curl -s http://localhost:8000/health \| jq` | `status: healthy`, all checks `ok` |
| API docs | http://localhost:8000/docs | OpenAPI UI |
| RabbitMQ | http://localhost:15672 | Management UI (guest/guest) |
| MinIO | http://localhost:9001 | Console (minioadmin/minioadmin) |
| n8n | http://localhost:5678 | Admin UI (local basic auth from `.env`) |
| Postgres | `docker compose exec postgres psql -U lexflow -c '\dt'` | Tables listed |

- [ ] All health checks pass
- [ ] Seed user login works (credentials in `scripts/seed/dev_seed.py` output)

### Step 6 — Run Tests

```bash
make test          # Unit + integration (Testcontainers)
make lint          # ruff, mypy, eslint, tsc
```

- [ ] `make test` passes
- [ ] `make lint` passes

---

## Makefile Command Reference

| Command | Description |
|---------|-------------|
| `make setup` | Full first-time setup (deps, DB, seed, hooks) |
| `make dev` | Start all Compose services with hot reload |
| `make dev-api` | API only (requires infra services running) |
| `make dev-web` | Web only |
| `make down` | Stop services; **preserve volumes** |
| `make down-clean` | Stop services and remove volumes (`docker compose down -v`) |
| `make logs` | Tail all service logs |
| `make logs-api` | Tail API logs only |
| `make shell-api` | `docker compose exec api bash` |
| `make migrate` | Run `alembic upgrade head` |
| `make migrate-new MSG="description"` | Create new Alembic revision |
| `make seed-dev` | Re-run dev seed script |
| `make test` | Unit + integration tests |
| `make test-unit` | Fast unit tests only |
| `make test-integration` | Testcontainers integration tests |
| `make test-e2e` | Playwright E2E (requires stack up) |
| `make lint` | All linters |
| `make format` | Auto-format Python + TypeScript |
| `make n8n-import WF=path/to/workflow.json` | Import workflow to local n8n |
| `make openapi` | Regenerate TypeScript client from OpenAPI |

---

## Compose Stack Topology

```mermaid
flowchart TB
    subgraph Local["docker compose up"]
        WEB["web :3000"]
        API["api :8000"]
        WRK["worker"]
        BEAT["outbox-publisher"]
        N8N["n8n :5678"]
        PG["postgres :5432"]
        REDIS["redis :6379"]
        RMQ["rabbitmq :5672 / :15672"]
        MINIO["minio :9000 / :9001"]
    end

    DEV[Developer] --> WEB & API
    WEB --> API
    API --> PG & REDIS & RMQ & MINIO
    RMQ --> WRK
    WRK --> PG & MINIO & N8N
    BEAT --> RMQ
    N8N --> API
```

See [../09-deployment/docker-containers.md](../09-deployment/docker-containers.md) for image build details and cloud mapping.

---

## Troubleshooting

### Docker / Resource Issues

| Symptom | Likely Cause | Fix |
|---------|--------------|-----|
| `Cannot connect to Docker daemon` | Docker Desktop not running | Start Docker Desktop |
| OOM / containers restarting | Insufficient RAM | Increase Docker Desktop memory to 6–8 GB |
| Port already in use | Conflicting local service | `lsof -i :8000` → kill process or change port in `.env` |
| Slow first build | Cold cache | Normal; subsequent builds use layer cache |

```bash
# Reset everything (destructive — loses local DB data)
make down-clean
make setup
make dev
```

### Database Issues

| Symptom | Fix |
|---------|-----|
| `relation does not exist` | `make migrate` |
| Migration conflict | `docker compose exec api alembic current` → check head; never edit applied migrations |
| Cannot connect to postgres | `docker compose ps postgres` → ensure healthy; check `DATABASE_URL` uses host `postgres` not `localhost` from inside containers |
| Seed data missing | `make seed-dev` |

```bash
# Connect to DB directly
docker compose exec postgres psql -U lexflow -d lexflow
```

### API / Worker Issues

| Symptom | Fix |
|---------|-----|
| API crash loop | `make logs-api` → check missing env var or bad JWT key format |
| Worker not processing | `docker compose ps worker`; check RabbitMQ connection in logs |
| 503 on health check | Dependency down — check postgres, redis, rabbitmq health |

```bash
# Restart single service
docker compose restart api worker
```

### n8n Issues

| Symptom | Fix |
|---------|-----|
| Cannot reach n8n UI | Ensure container running: `docker compose ps n8n` |
| Webhook 401 | HMAC secret mismatch — verify `N8N_WEBHOOK_SECRET` matches in api, worker, and n8n |
| Workflow import fails | Run `python n8n/scripts/validate-workflow.py --workflow {path}` |

See [add-workflow.md](./add-workflow.md) for workflow import procedures.

### Frontend Issues

| Symptom | Fix |
|---------|-----|
| `ECONNREFUSED` to API | Verify `NEXT_PUBLIC_API_URL=http://localhost:8000` in `.env` |
| Stale types after API change | `make openapi` |

### Pre-commit / Lint Failures

```bash
make format        # Auto-fix formatting
make lint          # Re-check
pre-commit run --all-files   # Run all hooks manually
```

---

## Troubleshooting Decision Tree

```mermaid
flowchart TD
    FAIL[Service unhealthy] --> WHICH{Which service?}
    WHICH -->|postgres| PG_CHECK[docker compose logs postgres]
    WHICH -->|api| API_LOGS[make logs-api]
    WHICH -->|worker| WRK_LOGS[docker compose logs worker]
    WHICH -->|n8n| N8N_LOGS[docker compose logs n8n]

    PG_CHECK --> PG_FIX{Error type?}
    PG_FIX -->|volume corrupt| RESET[make down-clean && make setup]
    PG_FIX -->|not migrated| MIG[make migrate]

    API_LOGS --> ENV{Missing env?}
    ENV -->|Yes| FIX_ENV[Fix .env]
    ENV -->|No| DEP{Dependency down?}
    DEP -->|Yes| RESTART[docker compose restart postgres redis rabbitmq]
    DEP -->|No| ESC[#lexflow-dev]
```

---

## Daily Development Workflow

```mermaid
sequenceDiagram
    participant Dev as Developer
    participant Git as Git
    participant Stack as Docker Compose
    participant Test as make test

    Dev->>Git: git pull origin main
    Dev->>Stack: make dev
    Dev->>Stack: make migrate (if schema changed)
    Dev->>Dev: Implement feature
    Dev->>Test: make test && make lint
    Dev->>Git: Push branch + open PR
```

---

## Security Reminders

1. **Never copy production secrets** to `.env` — use dummy keys and MinIO locally.
2. **Pre-commit gitleaks** blocks accidental secret commits — do not bypass.
3. **n8n local UI** is on localhost only — do not expose via ngrok without Security approval.
4. **Production data** must not be imported to local machines — use seed scripts only.

See [../08-security/secrets-management.md](../08-security/secrets-management.md).

---

## Completion Checklist

- [ ] Prerequisites installed and verified
- [ ] Repository cloned; `.env` configured from `.env.example`
- [ ] `make setup` completed successfully
- [ ] `make dev` — all services healthy
- [ ] Login with seed user works
- [ ] `make test` and `make lint` pass
- [ ] Read [onboarding.md](./onboarding.md) for first-week doc order

---

## References

| Document | Description |
|----------|-------------|
| [onboarding.md](./onboarding.md) | First-week guide |
| [../09-deployment/docker-containers.md](../09-deployment/docker-containers.md) | Container inventory and Compose topology |
| [../09-deployment/environment-strategy.md](../09-deployment/environment-strategy.md) | Local vs cloud environment mapping |
| [../development-standards.md](../development-standards.md) | Code style and PR process |
| [../folder-structure.md](../folder-structure.md) | Monorepo layout |
| [../10-testing/README.md](../10-testing/README.md) | Test suite overview |

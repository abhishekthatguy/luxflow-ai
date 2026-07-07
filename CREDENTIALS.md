# LexFlow AI — Local Credentials & Access Reference

**Last cross-checked:** 2026-07-07  
**Scope:** Local Docker Compose development only  
**Source of truth:** `docker-compose.yml`, `.env.example`, `apps/api/scripts/seed_*.py`, `config/environments/local.env`

> **Security**
> - Real secrets live in **`.env`** (gitignored). **Never commit** `.env`, Gmail app passwords, or API keys.
> - This document lists **default local dev values** and **where** to configure production secrets.
> - Rotate any credential that was ever pasted into chat, screenshots, or a shared doc.

---

## Quick URL map (local)

| Service | Public URL (browser / curl) | Internal URL (Docker network) | Purpose |
|---------|----------------------------|-------------------------------|---------|
| **Web portal** | http://localhost:3000 | http://web:3000 | Attorney / partner UI |
| **API** | http://localhost:8000 | http://api:8000 | REST API + OpenAPI at `/docs` |
| **API health** | http://localhost:8000/health | — | Platform health probe |
| **n8n** | http://localhost:5679 | http://n8n:5678 | Workflow orchestration (WF-01…WF-10) |
| **MinIO S3 API** | http://localhost:9000 | http://minio:9000 | Document object storage |
| **MinIO console** | http://localhost:9001 | — | Browse buckets / uploaded PDFs |
| **PostgreSQL** | localhost:5432 | postgres:5432 | Primary database (pgvector) |
| **Redis** | localhost:6379 | redis:6379 | Cache + Celery results |
| **RabbitMQ AMQP** | localhost:5672 | rabbitmq:5672 | Celery broker |
| **RabbitMQ UI** | http://localhost:15672 | — | Queue management |
| **Grafana** | http://localhost:3001 | — | Traces / dashboards (anonymous admin locally) |
| **Ollama** | http://localhost:11434 | http://ollama:11434 | Local LLM + embeddings (Phase 1) |
| **OTel collector** | http://localhost:13133 | http://otel-collector:4317 | Telemetry |

Canonical URL list: `config/environments/local.env`

---

## Infrastructure credentials (local defaults)

| System | Username / access key | Password / secret | Config variable | Purpose |
|--------|----------------------|-------------------|-----------------|---------|
| **PostgreSQL** | `lexflow` | `lexflow` | `DATABASE_URL` | App DB — schemas: `identity`, `cases`, `documents`, `workflows`, `ai`, `audit`, `shared` |
| **Redis** | — | (none) | `REDIS_URL` | `redis://redis:6379/0` |
| **Celery results** | — | (none) | `CELERY_RESULT_BACKEND` | `redis://redis:6379/1` |
| **RabbitMQ** | `guest` | `guest` | `CELERY_BROKER_URL`, `RABBITMQ_URL` | Task queue |
| **MinIO** | `lexflow` | `lexflowsecret` | `S3_ACCESS_KEY`, `S3_SECRET_KEY` | Document uploads bucket |
| **MinIO bucket** | — | — | `S3_BUCKET` | `lexflow-local-documents` |
| **MinIO object key pattern** | — | — | — | `{firm_id}/{case_id}/{document_id}/v1/{filename}` |
| **JWT signing** | — | `change-me-in-production-use-secrets-manager` (example) | `JWT_SECRET` | Portal access tokens — **override in `.env`** |
| **n8n webhook HMAC** | — | `dev-n8n-webhook-secret` | `N8N_WEBHOOK_SECRET` | `X-LexFlow-Signature` on API → n8n webhooks |
| **Grafana (local)** | anonymous | enabled (Admin role) | `GF_AUTH_ANONYMOUS_*` in compose | No login required locally |

---

## Portal RBAC — seeded users (firm: `lexflow-dev`)

All seeded staff accounts use password **`password123`** unless you change them in the DB.

| Email | Name | RBAC role | Purpose / typical use |
|-------|------|-----------|------------------------|
| `admin@example.com` | Sys Admin | **SystemAdministrator** | User management, full ops, workflows |
| `partner@example.com` | Pat ManagingPartner | **ManagingPartner** | Audit logs, operations, workflow admin |
| `equity@example.com` | Sam Partner | **Partner** | AI approval, case operations (equity partner) |
| `jane@example.com` | Jane Attorney | **Attorney** | Primary demo — cases, documents, AI request/approve |
| `john@example.com` | John Associate | **Associate** | Case work, AI request (no approve) |
| `alex@example.com` | Alex Paralegal | **Paralegal** | Documents, tasks (no AI request) |
| `assistant@example.com` | Lisa Assistant | **LegalAssistant** | Upload only — no case create, no AI |
| `outsider@example.com` | Outsider User | Attorney (test) | Negative / access-control tests |

**Seed commands**

```bash
make seed                  # Fresh DB — all 7 enterprise roles + 8 users
make seed-rbac-enterprise  # Existing DB — add Partner/LegalAssistant roles + missing users
make seed-sprint5          # Legacy: partner@example.com (ManagingPartner) if missing
make seed-notification-users
```

**Enterprise roles:** `SystemAdministrator`, `ManagingPartner`, `Partner`, `Attorney`, `Associate`, `Paralegal`, `LegalAssistant`

**Permission matrix** enforced in API (`auth/permissions.py`) and reflected on `GET /auth/me` → `permissions[]` for UI gating.

**QA / automation** (`apps/api/scripts/qa_case_runner.py`):

| Variable | Value |
|----------|-------|
| Attorney login | `jane@example.com` / `password123` |
| Partner login | `partner@example.com` / `password123` |

---

## Email accounts — RBAC vs notifications vs clients

### A. Outbound SMTP (system sender)

| Field | Value | Purpose |
|-------|-------|---------|
| **SMTP account** | `clawtbot@gmail.com` | Sends client + admin emails from LexFlow |
| **SMTP password** | *16-char Google **app password*** | Set as `GMAIL_APP_PASSWORD` in `.env` — **not stored in repo** |
| **SMTP server** | `smtp.gmail.com:587` (TLS) | `email_service.py` |
| **Env vars** | `GMAIL_USER`, `GMAIL_APP_PASSWORD` | Required for real email; otherwise log-only stubs |

**Triggers real email to:**

- **Clients** — after document OCR (e.g. Abhishek S → `kashyapabhi688@gmail.com`)
- **Admins** — n8n workflows → `POST /internal/notifications/admin`

### B. Admin operational alerts (RBAC-adjacent — platform ops, not portal login)

| Email | Config | Purpose |
|-------|--------|---------|
| `abhishekthatguy@gmail.com` | `ADMIN_NOTIFICATION_EMAILS` or `config/admin-notification-emails.txt` | WF health monitor, approval escalation, AI failure recovery, daily partner report |

Add more admins:

```bash
ADMIN_NOTIFICATION_EMAILS=abhishekthatguy@gmail.com,ops@firm.com
```

### C. Demo / QA **client** records (portal Clients — not staff RBAC)

These are **matter clients**, not portal users. They receive document notification emails when SMTP is configured.

| Client name | Email | Phone | Seed / QA |
|-------------|-------|-------|-----------|
| **Abhishek S** | `kashyapabhi688@gmail.com` | `+91-9621482434` | `make seed-abhishek-case`, `make qa-abhishek-case` |
| **John Doe** | `john.doe@gmail.com` | `+1-404-555-0101` | `make seed-simple-case`, simple QA case |
| **Sarah Johnson** | `sarah.j@example.com` | — | Medium QA case |
| **Acme Corporation** | `contact@acme.example` | — | `seed_dev.py` default client |
| *(+ 11 more)* | see `seed_demo_data.py` | — | `make seed-demo-data` |

---

## Application secrets (set in `.env` — values not in repo)

| Variable | Purpose | Where to get it |
|----------|---------|-----------------|
| `GMAIL_APP_PASSWORD` | Gmail SMTP send | Google Account → Security → App passwords |
| `GEMINI_API_KEY` | Google Gemini API (if used for AI features) | Google AI Studio — optional |
| `N8N_API_KEY` | n8n REST API (`import-workflows.py`, MCP) | n8n UI → Settings → API → Create key |
| `N8N_BASE_URL` | n8n REST base | `http://localhost:5679` (host) |
| `JWT_SECRET` | Portal JWT signing | Generate locally; use Secrets Manager in prod |
| `AZURE_OPENAI_API_KEY` | Phase 2 LLM | Azure portal — production |
| `AZURE_DI_API_KEY` | Phase 2 OCR | Azure Document Intelligence — production |

> **Note:** `make n8n-import` does **not** require `N8N_API_KEY`. The key is only for optional REST tooling.

---

## n8n (local)

| Item | Detail |
|------|--------|
| **Editor URL** | http://localhost:5679 |
| **Webhook base (internal)** | `http://n8n:5678/webhook/{slug}` |
| **Key workflows** | `document-upload-v1` (WF-02), `case-intake-v1`, etc. — see `n8n/workflows/README.md` |
| **First-time owner** | Created in n8n UI on first visit (not in seed scripts) |
| **Import workflows** | `make n8n-import` or `make seed-workflows && make n8n-import` |
| **Webhook auth** | HMAC `N8N_WEBHOOK_SECRET` — not basic auth |

---

## Object storage — verifying uploads

1. Open http://localhost:9001  
2. Login: `lexflow` / `lexflowsecret`  
3. Bucket: `lexflow-local-documents`  
4. Path: `{firm_uuid}/{case_uuid}/{document_uuid}/v1/{filename}`

---

## Makefile cheat sheet (credentials-related)

| Command | What it seeds / needs |
|---------|------------------------|
| `make migrate` | DB schema |
| `make seed` | RBAC users + firm |
| `make seed-sprint4` | AI prompt templates |
| `make seed-sprint5` | `partner@example.com` |
| `make seed-workflows` | WF definitions in DB |
| `make n8n-import` | Push workflows to n8n |
| `make seed-abhishek-case` | Abhishek client + sample PDFs |
| `make qa-abhishek-case` | E2E test (uses `jane@example.com`) |

---

## Production vs local

| Area | Local (this doc) | Production |
|------|------------------|------------|
| Email | Gmail SMTP (`GMAIL_*`) | AWS SES or firm SMTP |
| Object storage | MinIO | AWS S3 |
| LLM | `stub` or Ollama | Azure OpenAI |
| Secrets | `.env` file | AWS Secrets Manager / ECS task env |
| Portal auth | Seeded `@example.com` users | Firm IdP / Entra ID (planned) |

See: `docs/14-playbooks/PRODUCTION-DEPLOYMENT-CHECKLIST.md`, `docs/09-deployment/terraform.md`

---

## Related docs

| Doc | Topic |
|-----|-------|
| `docs/14-playbooks/local-dev-setup.md` | Full local setup |
| `docs/14-playbooks/admin-notification-emails.md` | Admin email list |
| `docs/sample-cases-test/ABHISHEK-E2E-WALKTHROUGH.md` | Abhishek PDF E2E + MinIO |
| `.env.example` | Template for all env vars |
| `config/environments/local.env` | URL catalog |

---

## Changelog

| Date | Change |
|------|--------|
| 2026-07-07 | Initial cross-check: RBAC users, MinIO, Gmail SMTP, admin emails, service URLs |

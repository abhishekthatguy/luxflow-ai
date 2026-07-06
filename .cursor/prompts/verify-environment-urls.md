# Verify Prompts Index

Each verification script loads URLs from **`config/environments/{local|staging|production}.env`**, then check-specific targets from **`scripts/verify/prompts/*.env`**.

## Environment selection

```bash
LEXFLOW_ENV=local make verify-platform      # default — Docker Compose
LEXFLOW_ENV=staging make verify-health      # public URLs only
LEXFLOW_ENV=production make verify-health   # public URLs only
```

## Prompt files

| Prompt file | Script | What it defines |
|-------------|--------|-----------------|
| [`prompts/quickstart.env`](../../scripts/verify/prompts/quickstart.env) | `quickstart.sh` | API health + web home URLs |
| [`prompts/health.env`](../../scripts/verify/prompts/health.env) | `health.sh` | All service health endpoints |
| [`prompts/logging.env`](../../scripts/verify/prompts/logging.env) | `logging.sh` | Correlation ID probe URLs |
| [`prompts/traces.env`](../../scripts/verify/prompts/traces.env) | `traces.sh` | OTel + Grafana URLs |
| [`prompts/integration.env`](../../scripts/verify/prompts/integration.env) | `integration.sh` | In-container integration env |
| [`prompts/n8n-callback.env`](../../scripts/verify/prompts/n8n-callback.env) | `n8n-callback.sh` | n8n → API internal callback |

## URL catalogs

| Environment | File |
|-------------|------|
| Local | [`config/environments/local.env`](../../config/environments/local.env) |
| Staging | [`config/environments/staging.env`](../../config/environments/staging.env) |
| Production | [`config/environments/production.env`](../../config/environments/production.env) |

## AI assistant

When running verification or debugging URLs, **always read the active environment file first** — do not hardcode `localhost` in new scripts.

Platform gate task: [`.ai/tasks/verify-platform-readiness.md`](../../.ai/tasks/verify-platform-readiness.md)

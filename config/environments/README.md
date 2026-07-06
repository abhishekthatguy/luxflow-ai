# Environment URLs

Single source of truth for **public** (browser/curl) and **internal** (Docker/VPC) service URLs per deployment environment.

## Files

| File | Use when |
|------|----------|
| [`local.env`](./local.env) | Docker Compose on developer machine (default) |
| [`staging.env`](./staging.env) | AWS staging — pre-production validation |
| [`production.env`](./production.env) | AWS production — live firm deployment |

## Usage

```bash
# Default: local
make verify-health

# Staging smoke (public URLs only — no docker compose exec)
LEXFLOW_ENV=staging make verify-health

# Production smoke (read-only health checks)
LEXFLOW_ENV=production make verify-health
```

Load manually in shell scripts:

```bash
source scripts/lib/load-env.sh          # local
source scripts/lib/load-env.sh staging  # staging
```

## Variable naming

| Suffix | Meaning | Example (local) |
|--------|---------|-----------------|
| `_PUBLIC_URL` | Reachable from host / internet | `http://localhost:8000` |
| `_INTERNAL_URL` | Docker network or private VPC | `http://api:8000` |
| `_CONTAINER_URL` | Inside same container (loopback) | `http://127.0.0.1:5678` |

Legacy aliases (`API_URL`, `WEB_URL`, `GRAFANA_URL`) point at `*_PUBLIC_URL` for verify scripts.

## Updating production URLs

1. Edit `production.env` — replace `{domain}` with the firm hostname.
2. Never commit real secrets; URLs only.
3. Staging/production verify targets skip Docker-internal checks (`VERIFY_USE_COMPOSE=false`).

See also: [`docs/09-deployment/environment-strategy.md`](../../docs/09-deployment/environment-strategy.md)

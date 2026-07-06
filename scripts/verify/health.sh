#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
# shellcheck disable=SC1091
source "${ROOT}/scripts/lib/load-verify-prompt.sh" health

check() {
  local name="$1"
  local cmd="$2"
  if bash -c "$cmd" >/dev/null 2>&1; then
    echo "OK  $name"
  else
    echo "FAIL $name"
    exit 1
  fi
}

echo "==> Health checks (LEXFLOW_ENV=${LEXFLOW_ENV})"

if [[ -n "${OTEL_COLLECTOR_PUBLIC_URL:-}" ]]; then
  check "OTel Collector" "curl -sf ${HEALTH_CHECK_OTEL}"
else
  echo "SKIP OTel Collector (no public URL for ${LEXFLOW_ENV})"
fi

check "API" "curl -sf ${HEALTH_CHECK_API}"
check "Web" "curl -sf ${HEALTH_CHECK_WEB}"

if [[ -n "${GRAFANA_PUBLIC_URL:-}" ]]; then
  check "Grafana" "curl -sf ${HEALTH_CHECK_GRAFANA}"
else
  echo "SKIP Grafana (no public URL for ${LEXFLOW_ENV})"
fi

if [[ -n "${MINIO_PUBLIC_URL:-}" ]]; then
  check "MinIO" "curl -sf ${HEALTH_CHECK_MINIO}"
else
  echo "SKIP MinIO (no public URL for ${LEXFLOW_ENV})"
fi

if [[ "${VERIFY_USE_COMPOSE}" == "true" ]]; then
  check "Postgres" "docker compose exec -T postgres pg_isready -U ${HEALTH_CHECK_POSTGRES_USER} -d ${HEALTH_CHECK_POSTGRES_DB}"
  check "Redis" "docker compose exec -T redis redis-cli PING | grep -q PONG"
  check "RabbitMQ" "docker compose exec -T rabbitmq rabbitmq-diagnostics ping | grep -q succeeded"
  check "n8n (internal)" "docker compose exec -T n8n wget -qO- ${HEALTH_CHECK_N8N_CONTAINER}"
  check "Worker" "docker compose exec -T worker celery -A lexflow_api.celery_app:celery_app inspect ping | grep -q OK"
else
  echo "SKIP Postgres/Redis/RabbitMQ/n8n/Worker (VERIFY_USE_COMPOSE=false for ${LEXFLOW_ENV})"
fi

echo "✅ All health checks passed"

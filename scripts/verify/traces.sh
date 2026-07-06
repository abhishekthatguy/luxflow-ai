#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
# shellcheck disable=SC1091
source "${ROOT}/scripts/lib/load-verify-prompt.sh" traces

echo "==> OpenTelemetry / Grafana trace smoke [${LEXFLOW_ENV}]"

curl -sf "$TRACES_API_HEALTH" >/dev/null
curl -sf -X POST "$TRACES_CELERY_PING" \
  -H "Content-Type: application/json" \
  -d '{"correlationId":"trace-smoke"}' >/dev/null
sleep 5

if [[ -n "${GRAFANA_PUBLIC_URL:-}" ]]; then
  if curl -sf "$TRACES_GRAFANA_HEALTH" | grep -q ok; then
    echo "OK  Grafana healthy (inspect traces at ${TRACES_GRAFANA_EXPLORE})"
  else
    echo "FAIL Grafana not reachable at ${TRACES_GRAFANA_HEALTH}"
    exit 1
  fi
else
  echo "SKIP Grafana (no public URL for ${LEXFLOW_ENV})"
fi

echo "✅ Trace smoke passed (manual: Grafana → Explore → Tempo)"

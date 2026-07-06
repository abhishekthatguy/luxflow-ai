#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
# shellcheck disable=SC1091
source "${ROOT}/scripts/lib/load-verify-prompt.sh" n8n-callback

if [[ "${VERIFY_USE_COMPOSE}" != "true" ]]; then
  echo "SKIP n8n callback (VERIFY_USE_COMPOSE=false for ${LEXFLOW_ENV})"
  echo "n8n is internal-only; run locally: LEXFLOW_ENV=local make verify-n8n-callback"
  exit 0
fi

echo "==> n8n internal network → FastAPI [${LEXFLOW_ENV}]"

docker compose exec -T n8n wget -qO- \
  --header="Content-Type: application/json" \
  --post-data="${N8N_CALLBACK_PAYLOAD}" \
  "${N8N_CALLBACK_TARGET}" | grep -q '"status".*"ok"'

echo "✅ n8n → API callback passed"

#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
# shellcheck disable=SC1091
source "${ROOT}/scripts/lib/load-verify-prompt.sh" quickstart

echo "==> Verifying LexFlow quickstart (LEXFLOW_ENV=${LEXFLOW_ENV})"

wait_for() {
  local url="$1"
  local name="$2"
  local elapsed=0
  while (( elapsed < QUICKSTART_MAX_WAIT )); do
    if curl -sf "$url" >/dev/null 2>&1; then
      echo "OK  $name — $url"
      return 0
    fi
    sleep 2
    elapsed=$((elapsed + 2))
  done
  echo "FAIL $name — $url (timeout ${QUICKSTART_MAX_WAIT}s)"
  return 1
}

wait_for "$QUICKSTART_API_HEALTH" "API health"
wait_for "$QUICKSTART_WEB_HOME" "Web home"

body="$(curl -sf "$QUICKSTART_API_HEALTH")"
if echo "$body" | grep -q '"status".*"ok"'; then
  echo "OK  API body contains status ok"
else
  echo "FAIL API health body: $body"
  exit 1
fi

echo "✅ Platform quickstart verification passed"

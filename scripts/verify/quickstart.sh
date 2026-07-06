#!/usr/bin/env bash
set -euo pipefail

API_URL="${API_URL:-http://localhost:8000}"
WEB_URL="${WEB_URL:-http://localhost:3000}"
MAX_WAIT="${MAX_WAIT:-120}"

echo "==> Verifying LexFlow quickstart (api + web)"

wait_for() {
  local url="$1"
  local name="$2"
  local elapsed=0
  while (( elapsed < MAX_WAIT )); do
    if curl -sf "$url" >/dev/null 2>&1; then
      echo "OK  $name — $url"
      return 0
    fi
    sleep 2
    elapsed=$((elapsed + 2))
  done
  echo "FAIL $name — $url (timeout ${MAX_WAIT}s)"
  return 1
}

wait_for "$API_URL/health" "API health"
wait_for "$WEB_URL/" "Web home"

body="$(curl -sf "$API_URL/health")"
if echo "$body" | grep -q '"status".*"ok"'; then
  echo "OK  API body contains status ok"
else
  echo "FAIL API health body: $body"
  exit 1
fi

echo "✅ Platform quickstart verification passed"

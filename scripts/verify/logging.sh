#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
# shellcheck disable=SC1091
source "${ROOT}/scripts/lib/load-verify-prompt.sh" logging

CORRELATION_ID="${CORRELATION_ID:-$(uuidgen 2>/dev/null || python3 -c 'import uuid; print(uuid.uuid4())')}"

echo "==> Correlation ID logging ($CORRELATION_ID) [${LEXFLOW_ENV}]"

curl -sf -H "X-Correlation-ID: $CORRELATION_ID" "$LOGGING_API_HEALTH" >/dev/null
sleep 1

if [[ "${VERIFY_USE_COMPOSE}" == "true" ]]; then
  if docker compose logs api --since 2m 2>/dev/null | grep -q "$CORRELATION_ID"; then
    echo "OK  API logs contain correlationId"
  else
    echo "FAIL API logs missing correlationId"
    exit 1
  fi

  curl -sf -X POST "$LOGGING_CELERY_PING" \
    -H "Content-Type: application/json" \
    -d "{\"correlationId\": \"$CORRELATION_ID\"}" >/dev/null
  sleep 3

  if docker compose logs worker --since 2m 2>/dev/null | grep -q "$CORRELATION_ID"; then
    echo "OK  Worker logs contain correlationId"
  else
    echo "WARN Worker logs missing correlationId (task may still be ok)"
  fi
else
  echo "SKIP log tail checks (VERIFY_USE_COMPOSE=false for ${LEXFLOW_ENV})"
  curl -sf -X POST "$LOGGING_CELERY_PING" \
    -H "Content-Type: application/json" \
    -d "{\"correlationId\": \"$CORRELATION_ID\"}" >/dev/null
  echo "OK  Celery ping dispatched via ${LOGGING_CELERY_PING}"
fi

echo "✅ Logging verification passed"

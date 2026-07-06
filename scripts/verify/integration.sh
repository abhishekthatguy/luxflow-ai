#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
# shellcheck disable=SC1091
source "${ROOT}/scripts/lib/load-verify-prompt.sh" integration

if [[ "${VERIFY_USE_COMPOSE}" != "true" ]]; then
  echo "SKIP integration tests (VERIFY_USE_COMPOSE=false for ${LEXFLOW_ENV})"
  echo "Run against local Docker Compose: LEXFLOW_ENV=local make verify-integration"
  exit 0
fi

echo "==> Integration tests inside api container [${LEXFLOW_ENV}]"

docker compose exec -T api bash -lc "
  set -euo pipefail
  export REDIS_URL=${INTEGRATION_REDIS_URL}
  export RABBITMQ_URL=${INTEGRATION_RABBITMQ_URL}
  export S3_ENDPOINT=${INTEGRATION_S3_ENDPOINT}
  export S3_ACCESS_KEY=${INTEGRATION_S3_ACCESS_KEY}
  export S3_SECRET_KEY=${INTEGRATION_S3_SECRET_KEY}
  export S3_BUCKET=${INTEGRATION_S3_BUCKET}
  export API_INTERNAL_URL=${INTEGRATION_API_INTERNAL_URL}
  export CELERY_BROKER_URL=${INTEGRATION_CELERY_BROKER_URL}
  export CELERY_RESULT_BACKEND=${INTEGRATION_CELERY_RESULT_BACKEND}
  cd /app
  pytest -q /tests/integration
"

echo "✅ Integration tests passed"

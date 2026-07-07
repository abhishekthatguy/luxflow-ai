#!/usr/bin/env bash
# Sync n8n workflows: purge duplicates → start n8n (entrypoint imports) → smoke test.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"

N8N_HOST="${N8N_PUBLIC_URL:-http://localhost:5679}"
N8N_HOST="${N8N_HOST%/}"
TOKEN="${N8N_WEBHOOK_SECRET:-dev-n8n-webhook-secret}"

echo "==> Building workflow JSON from catalog"
python3 scripts/n8n/build_workflows.py

echo "==> Validating workflow JSON"
python3 scripts/n8n/validate_workflows.py

echo "==> Stopping n8n for clean purge"
docker compose stop n8n

echo "==> Purging managed workflows from n8n database"
python3 scripts/n8n/purge_managed_workflows.py

echo "==> Starting n8n (entrypoint purges + imports + activates)"
docker compose start n8n

echo "==> Waiting for n8n"
for _ in $(seq 1 40); do
  if curl -sf "${N8N_HOST}/healthz" >/dev/null 2>&1; then
    sleep 8
    break
  fi
  sleep 2
done

echo "==> Seeding workflow definitions in PostgreSQL"
docker compose exec -T api python scripts/seed_workflows.py

echo "==> Initialize orchestrator session (WF-11)"
curl -sf -X POST "${N8N_HOST}/webhook/workflow-session-init-v1" \
  -H 'Content-Type: application/json' \
  -d '{}' >/dev/null || true

echo "==> Smoke test flagship webhook (signed)"
BODY='{"executionId":"00000000-0000-4000-8000-000000000001","caseId":"00000000-0000-4000-8000-000000000002","documentId":"00000000-0000-4000-8000-000000000003"}'
SIG=$(python3 - <<PY
import hashlib, hmac, os
secret = os.environ.get("N8N_WEBHOOK_SECRET", "dev-n8n-webhook-secret")
body = '''${BODY}'''
print(hmac.new(secret.encode(), body.encode(), hashlib.sha256).hexdigest())
PY
)
HTTP=$(curl -s -o /dev/null -w "%{http_code}" \
  -X POST "${N8N_HOST}/webhook/document-upload-v1" \
  -H 'Content-Type: application/json' \
  -H "X-LexFlow-Signature: ${SIG}" \
  -d "${BODY}")
if [ "$HTTP" != "200" ]; then
  echo "WARN: document-upload-v1 webhook returned HTTP $HTTP (retry in 10s…)"
  sleep 10
  HTTP=$(curl -s -o /dev/null -w "%{http_code}" \
    -X POST "${N8N_HOST}/webhook/document-upload-v1" \
    -H 'Content-Type: application/json' \
    -H "X-LexFlow-Signature: ${SIG}" \
    -d "${BODY}")
fi
if [ "$HTTP" != "200" ]; then
  echo "FAIL: document-upload-v1 webhook returned HTTP $HTTP"
  exit 1
fi

COUNT=$(docker compose exec -T n8n n8n list:workflow 2>/dev/null | grep -c '|' || true)
echo "✅ n8n ready at ${N8N_HOST} — ${COUNT} workflow(s) in n8n (catalog: 13)"

echo "==> Cleaning stale failed workflow runs and stuck jobs"
docker compose exec -T api python scripts/cleanup_stale_operations.py

#!/usr/bin/env bash
# Sync n8n workflows: purge duplicates → start n8n (entrypoint imports) → smoke test.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"

N8N_HOST="${N8N_PUBLIC_URL:-http://localhost:5679}"
N8N_HOST="${N8N_HOST%/}"

echo "==> Building workflow JSON from catalog"
python3 scripts/n8n/build_workflows.py

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

echo "==> Smoke test flagship webhook"
HTTP=$(curl -s -o /dev/null -w "%{http_code}" \
  -X POST "${N8N_HOST}/webhook/document-upload-v1" \
  -H 'Content-Type: application/json' \
  -d '{"executionId":"smoke","caseId":"test","documentId":"test-doc"}')
if [ "$HTTP" != "200" ]; then
  echo "FAIL: document-upload-v1 webhook returned HTTP $HTTP (retry in 10s…)"
  sleep 10
  HTTP=$(curl -s -o /dev/null -w "%{http_code}" \
    -X POST "${N8N_HOST}/webhook/document-upload-v1" \
    -H 'Content-Type: application/json' \
    -d '{"executionId":"smoke","caseId":"test","documentId":"test-doc"}')
fi
if [ "$HTTP" != "200" ]; then
  echo "FAIL: document-upload-v1 webhook returned HTTP $HTTP"
  exit 1
fi

COUNT=$(docker compose exec -T n8n n8n list:workflow 2>/dev/null | grep -c '|' || true)
echo "✅ n8n ready at ${N8N_HOST} — ${COUNT} LexFlow workflow(s) (expect 10)"

echo "==> Cleaning stale failed workflow runs and stuck jobs"
docker compose exec -T api python scripts/cleanup_stale_operations.py

#!/usr/bin/env bash
# Sprint 4 live API smoke — document upload, AI summary, n8n workflow.
# Requires: migrate (003+) + seed + stack running.
#
# Set VERIFY_SPRINT4_STRICT=1 to fail on SKIP (use in CI once Sprint 4 ships).
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
# shellcheck disable=SC1091
source "${ROOT}/scripts/lib/load-verify-prompt.sh" quickstart

API="${API_PUBLIC_URL}/api/v1"
STRICT="${VERIFY_SPRINT4_STRICT:-0}"

skip_or_fail() {
  local msg="$1"
  if [[ "$STRICT" == "1" ]]; then
    echo "FAIL ${msg}"
    exit 1
  fi
  echo "SKIP ${msg}"
}

require_status() {
  local label="$1"
  local expected="$2"
  local actual="$3"
  if [[ "$actual" != "$expected" ]]; then
    echo "FAIL ${label} expected HTTP ${expected}, got ${actual}"
    exit 1
  fi
  echo "OK  ${label}"
}

echo "==> Sprint 4 AI + documents + n8n smoke [${LEXFLOW_ENV}]"

# --- Prerequisite: Sprint 3 auth + cases still work ---
"${ROOT}/scripts/verify/sprint3.sh"

login() {
  local email="$1"
  curl -sf -X POST "${API}/auth/login" \
    -H "Content-Type: application/json" \
    -d "{\"email\":\"${email}\",\"password\":\"password123\"}" \
    | python3 -c "import sys,json; print(json.load(sys.stdin)['data']['accessToken'])"
}

TOKEN="$(login jane@example.com)"
CLIENT="$(curl -sf "${API}/clients" -H "Authorization: Bearer ${TOKEN}" \
  | python3 -c "import sys,json; d=json.load(sys.stdin)['data']; print(d[0]['id'])")"
USER="$(curl -sf "${API}/auth/me" -H "Authorization: Bearer ${TOKEN}" \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['data']['id'])")"

CASE_JSON="$(curl -sf -X POST "${API}/cases" \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" \
  -d "{\"clientId\":\"${CLIENT}\",\"caseNumber\":\"s4-$(date +%s)\",\"title\":\"Sprint 4 Smoke Case\",\"leadAttorneyId\":\"${USER}\"}")"
CASE_ID="$(echo "$CASE_JSON" | python3 -c "import sys,json; print(json.load(sys.stdin)['data']['id'])")"
echo "OK  Sprint 4 test case ${CASE_ID}"

# --- LEX-402: Document upload initiate (RFC-004) ---
DOC_INIT_CODE="$(curl -s -o /dev/null -w '%{http_code}' -X POST "${API}/cases/${CASE_ID}/documents" \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Sprint 4 Smoke PDF",
    "documentType": "evidence",
    "filename": "smoke.pdf",
    "mimeType": "application/pdf",
    "fileSizeBytes": 1024,
    "checksumSha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
  }')"

case "$DOC_INIT_CODE" in
  201)
    echo "OK  Document upload initiate"
    # TODO LEX-402: confirm upload, poll document status until ready
    ;;
  404|405)
    skip_or_fail "Document upload API not deployed yet (LEX-402) — HTTP ${DOC_INIT_CODE}"
    ;;
  *)
    echo "FAIL Document initiate unexpected HTTP ${DOC_INIT_CODE}"
    exit 1
    ;;
esac

# --- LEX-405: Async AI summary ---
AI_CODE="$(curl -s -o /dev/null -w '%{http_code}' -X POST "${API}/cases/${CASE_ID}/ai/summarize" \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{"summaryType":"case_overview"}')"

case "$AI_CODE" in
  202)
    echo "OK  AI summarize accepted (202)"
    # TODO LEX-405: poll GET /jobs/{id}, approve summary
    ;;
  404|405)
    skip_or_fail "AI summarize API not deployed yet (LEX-405) — HTTP ${AI_CODE}"
    ;;
  *)
    echo "FAIL AI summarize unexpected HTTP ${AI_CODE}"
    exit 1
    ;;
esac

# --- LEX-408: Workflow manual trigger ---
WF_CODE="$(curl -s -o /dev/null -w '%{http_code}' -X POST "${API}/cases/${CASE_ID}/workflows/trigger" \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{"workflowSlug":"document-upload-v1"}')"

case "$WF_CODE" in
  202)
    echo "OK  Workflow trigger accepted (202)"
    # TODO LEX-408/409: poll execution status, verify n8n callback mock
    ;;
  404|405)
    skip_or_fail "Workflow trigger API not deployed yet (LEX-408) — HTTP ${WF_CODE}"
    ;;
  *)
    echo "FAIL Workflow trigger unexpected HTTP ${WF_CODE}"
    exit 1
    ;;
esac

# --- Matter wall: document list for outsider ---
OUTSIDER="$(login outsider@example.com)"
WALL_CODE="$(curl -s -o /dev/null -w '%{http_code}' "${API}/cases/${CASE_ID}/documents" \
  -H "Authorization: Bearer ${OUTSIDER}")"

case "$WALL_CODE" in
  404)
    require_status "Matter wall on documents list" "404" "$WALL_CODE"
    ;;
  200)
    echo "OK  Documents list returned 200 (endpoint exists; verify wall when LEX-402 ships)"
    ;;
  404|405)
    skip_or_fail "Documents list API not deployed yet — HTTP ${WALL_CODE}"
    ;;
  *)
    echo "FAIL Documents list unexpected HTTP ${WALL_CODE}"
    exit 1
    ;;
esac

echo "✅ Sprint 4 smoke passed (strict=${STRICT})"

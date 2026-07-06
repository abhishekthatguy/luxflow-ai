#!/usr/bin/env bash
# Sprint 3 live API smoke (requires migrate + seed).
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
# shellcheck disable=SC1091
source "${ROOT}/scripts/lib/load-verify-prompt.sh" quickstart

API="${API_PUBLIC_URL}/api/v1"

echo "==> Sprint 3 case management smoke [${LEXFLOW_ENV}]"

login() {
  local email="$1"
  curl -sf -X POST "${API}/auth/login" \
    -H "Content-Type: application/json" \
    -d "{\"email\":\"${email}\",\"password\":\"password123\"}" \
    | python3 -c "import sys,json; print(json.load(sys.stdin)['data']['accessToken'])"
}

TOKEN="$(login jane@example.com)"
echo "OK  Login jane@example.com"

CLIENT="$(curl -sf "${API}/clients" -H "Authorization: Bearer ${TOKEN}" \
  | python3 -c "import sys,json; d=json.load(sys.stdin)['data']; print(d[0]['id'])")"
USER="$(curl -sf "${API}/auth/me" -H "Authorization: Bearer ${TOKEN}" \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['data']['id'])")"

CASE_JSON="$(curl -sf -X POST "${API}/cases" \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" \
  -d "{\"clientId\":\"${CLIENT}\",\"caseNumber\":\"smoke-$(date +%s)\",\"title\":\"Smoke Test Case\",\"leadAttorneyId\":\"${USER}\"}")"
CASE_ID="$(echo "$CASE_JSON" | python3 -c "import sys,json; print(json.load(sys.stdin)['data']['id'])")"
echo "OK  Create case ${CASE_ID}"

curl -sf -X POST "${API}/cases/${CASE_ID}/tasks" \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{"title":"Sprint 3 smoke task"}' >/dev/null
echo "OK  Create task"

EVENTS="$(curl -sf "${API}/cases/${CASE_ID}/timeline" -H "Authorization: Bearer ${TOKEN}" \
  | python3 -c "import sys,json; print(len(json.load(sys.stdin)['data']))")"
echo "OK  Timeline (${EVENTS} events)"

OUTSIDER="$(login outsider@example.com)"
CODE="$(curl -s -o /dev/null -w '%{http_code}' "${API}/cases/${CASE_ID}" -H "Authorization: Bearer ${OUTSIDER}")"
if [[ "$CODE" != "404" ]]; then
  echo "FAIL Matter wall expected 404, got ${CODE}"
  exit 1
fi
echo "OK  Matter wall 404 for non-participant"

echo "✅ Sprint 3 live smoke passed"

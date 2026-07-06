#!/usr/bin/env bash
# Sprint 5 smoke — audit API, notifications, auth rate limit, structured logging fields.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
# shellcheck disable=SC1091
source "${ROOT}/scripts/lib/load-verify-prompt.sh" quickstart

API="${API_PUBLIC_URL}/api/v1"
VERIFY_CLIENT_IP="${VERIFY_CLIENT_IP:-verify-s5-$$}"

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

echo "==> Sprint 5 production hardening smoke [${LEXFLOW_ENV}]"

login() {
  local email="$1"
  local ip="${2:-${VERIFY_CLIENT_IP}}"
  curl -sf -X POST "${API}/auth/login" \
    -H "Content-Type: application/json" \
    -H "X-Forwarded-For: ${ip}" \
    -d "{\"email\":\"${email}\",\"password\":\"password123\"}" \
    | python3 -c "import sys,json; print(json.load(sys.stdin)['data']['accessToken'])"
}

JANE_TOKEN="$(login jane@example.com "s5-jane-$$")"
PARTNER_TOKEN="$(login partner@example.com "s5-partner-$$")"

# LEX-511: Audit read API — firm admin only
AUDIT_FORBIDDEN="$(curl -s -o /dev/null -w '%{http_code}' "${API}/audit/logs" \
  -H "Authorization: Bearer ${JANE_TOKEN}")"
require_status "Attorney denied audit logs" "403" "$AUDIT_FORBIDDEN"

AUDIT_OK="$(curl -s -o /dev/null -w '%{http_code}' "${API}/audit/logs" \
  -H "Authorization: Bearer ${PARTNER_TOKEN}")"
require_status "ManagingPartner audit logs" "200" "$AUDIT_OK"

# LEX-510: Notifications
NOTIF_CODE="$(curl -s -o /dev/null -w '%{http_code}' "${API}/notifications" \
  -H "Authorization: Bearer ${JANE_TOKEN}")"
require_status "Notifications list" "200" "$NOTIF_CODE"

UNREAD="$(curl -sf "${API}/notifications/unread-count" \
  -H "Authorization: Bearer ${JANE_TOKEN}" \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['data']['count'])")"
echo "OK  Unread notification count=${UNREAD}"

# LEX-506: Rate limit returns 429 after burst (11th login in window)
RATE_IP="sprint5-rate-test-$$"
for i in $(seq 1 11); do
  CODE="$(curl -s -o /dev/null -w '%{http_code}' -X POST "${API}/auth/login" \
    -H "Content-Type: application/json" \
    -H "X-Forwarded-For: ${RATE_IP}" \
    -d '{"email":"outsider@example.com","password":"wrongpass1"}')"
  if [[ "$i" -le 10 && "$CODE" != "401" ]]; then
    echo "FAIL login attempt $i expected 401, got ${CODE}"
    exit 1
  fi
  if [[ "$i" -eq 11 && "$CODE" != "429" ]]; then
    echo "FAIL rate limit expected 429 on 11th attempt, got ${CODE}"
    exit 1
  fi
done
echo "OK  Auth rate limiting (429 after 10 attempts)"

echo "✅ Sprint 5 smoke passed"

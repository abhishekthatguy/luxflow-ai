#!/usr/bin/env bash
# Run full platform readiness gate from repo root.
#
# Usage:
#   ./verify-platform.sh              # local (Docker Compose)
#   ./verify-platform.sh staging      # public URL smoke only
#   LEXFLOW_ENV=production ./verify-platform.sh
#
# Equivalent: make verify-platform

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"

export LEXFLOW_ENV="${1:-${LEXFLOW_ENV:-local}}"

echo "==> LexFlow platform verification (LEXFLOW_ENV=${LEXFLOW_ENV})"
echo "    URLs: config/environments/${LEXFLOW_ENV}.env"
echo ""

chmod +x scripts/lib/*.sh scripts/verify/*.sh 2>/dev/null || true

if ! command -v docker >/dev/null 2>&1; then
  echo "ERROR: Docker is required. Install Docker Desktop and retry."
  exit 1
fi

if ! docker info >/dev/null 2>&1; then
  echo "ERROR: Docker daemon is not running. Start Docker Desktop and retry."
  exit 1
fi

if [[ "${LEXFLOW_ENV}" == "local" ]]; then
  if ! docker compose ps --services --filter "status=running" 2>/dev/null | grep -qx api; then
    echo "WARN Stack may not be running. Start with: make dev"
    echo ""
  fi
fi

if ! command -v make >/dev/null 2>&1; then
  echo "ERROR: make is required."
  exit 1
fi

make verify-platform

echo ""
echo "Done. Platform readiness gate passed (${LEXFLOW_ENV})."

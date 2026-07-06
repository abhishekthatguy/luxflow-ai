#!/usr/bin/env bash
# Load environment URL catalog.
# Usage: LEXFLOW_ENV=staging source scripts/lib/load-env.sh

_lexflow_load_env() {
  local profile="${LEXFLOW_ENV:-local}"
  local root
  root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
  local env_file="${root}/config/environments/${profile}.env"

  if [[ ! -f "$env_file" ]]; then
    echo "ERROR: Unknown LEXFLOW_ENV=${profile} (missing ${env_file})" >&2
    return 1 2>/dev/null || exit 1
  fi

  set -a
  # shellcheck disable=SC1090
  source "$env_file"
  set +a

  export LEXFLOW_ENV="$profile"
  export VERIFY_USE_COMPOSE="${VERIFY_USE_COMPOSE:-true}"
}

_lexflow_load_env

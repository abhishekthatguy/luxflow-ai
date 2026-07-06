#!/usr/bin/env bash
# Load environment catalog + verify prompt fragment.
# Usage: source scripts/lib/load-verify-prompt.sh <prompt-name>
# Example: source scripts/lib/load-verify-prompt.sh health

_lexflow_load_verify_prompt() {
  local prompt_name="$1"
  if [[ -z "$prompt_name" ]]; then
    echo "ERROR: load-verify-prompt requires a prompt name (e.g. health)" >&2
    return 1 2>/dev/null || exit 1
  fi

  local lib_dir
  lib_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

  # shellcheck disable=SC1091
  source "${lib_dir}/load-env.sh"

  local prompt_file="${lib_dir}/../verify/prompts/${prompt_name}.env"
  if [[ ! -f "$prompt_file" ]]; then
    echo "ERROR: Missing verify prompt: ${prompt_file}" >&2
    return 1 2>/dev/null || exit 1
  fi

  # shellcheck disable=SC1090
  source "$prompt_file"
}

_lexflow_load_verify_prompt "${1:-}"

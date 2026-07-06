#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

echo "==> LexFlow AI setup"

if ! command -v docker >/dev/null 2>&1; then
  echo "ERROR: Docker is required. Install Docker Desktop and retry."
  exit 1
fi

if ! docker info >/dev/null 2>&1; then
  echo "ERROR: Docker daemon is not running. Start Docker Desktop and retry."
  exit 1
fi

if [[ ! -f .env ]]; then
  cp .env.example .env
  echo "Created .env from .env.example"
fi

if command -v pre-commit >/dev/null 2>&1 && [[ -f .pre-commit-config.yaml ]]; then
  pre-commit install
  echo "Pre-commit hooks installed"
else
  echo "Skip pre-commit (install with: pip install pre-commit)"
fi

echo "Setup complete. Run: make dev"

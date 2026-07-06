.PHONY: setup dev dev-full down ps logs lint test migrate migrate-down seed \
        verify-quickstart verify-platform verify-health verify-logging \
        verify-traces verify-redis verify-rabbitmq verify-celery \
        verify-n8n-callback verify-minio verify-integration verify-sprint3 \
        verify-sprint4 verify-sprint5 test-e2e n8n-import

LEXFLOW_ENV ?= local
export LEXFLOW_ENV

setup:
	@chmod +x scripts/setup.sh scripts/lib/*.sh scripts/verify/*.sh
	@./scripts/setup.sh

dev:
	docker compose up -d --build

dev-full: dev

down:
	docker compose down

ps:
	docker compose ps

logs:
	docker compose logs -f

migrate:
	docker compose exec api alembic -c alembic.ini upgrade head

migrate-down:
	docker compose exec api alembic -c alembic.ini downgrade -1

seed:
	docker compose exec api python scripts/seed_dev.py

seed-sprint4:
	docker compose exec api python scripts/seed_sprint4.py

seed-sprint5:
	docker compose exec api python scripts/seed_sprint5.py

n8n-import:
	python3 scripts/n8n/import-workflows.py

lint:
	cd apps/api && python3 -m venv .venv && . .venv/bin/activate && pip install -q -e ".[dev]" && ruff check src tests && mypy src
	cd apps/web && npm install && npm run lint

test:
	cd apps/api && python3 -m venv .venv && . .venv/bin/activate && pip install -q -e ".[dev]" && pytest -q
	cd apps/web && npm install && npm test

verify-quickstart:
	@./scripts/verify/quickstart.sh

verify-health:
	@./scripts/verify/health.sh

verify-logging:
	@./scripts/verify/logging.sh

verify-traces:
	@./scripts/verify/traces.sh

verify-redis verify-rabbitmq verify-celery verify-minio verify-n8n-callback:
	@./scripts/verify/integration.sh

verify-integration:
	@./scripts/verify/integration.sh

verify-platform: verify-health verify-logging verify-traces verify-integration verify-n8n-callback
	@echo "✅ Platform readiness gate passed"

verify-sprint3:
	cd apps/api && python3 -m venv .venv && . .venv/bin/activate && pip install -q -e ".[dev]" && pytest -q tests/test_auth.py tests/test_cases.py
	@chmod +x scripts/verify/sprint3.sh
	@./scripts/verify/sprint3.sh
	@echo "✅ Sprint 3 auth + case management tests passed"

test-e2e:
	@echo "Running Playwright E2E (requires stack on :3000 + :8000 — use: make dev && make seed)"
	@if [ ! -d node_modules/@playwright/test ]; then npm install; fi
	@if [ ! -d .playwright-browsers ]; then PLAYWRIGHT_BROWSERS_PATH=$$(pwd)/.playwright-browsers npx playwright install chromium; fi
	E2E_SKIP_WEB_SERVER=1 PLAYWRIGHT_BROWSERS_PATH=$$(pwd)/.playwright-browsers npm run test:e2e

verify-sprint4:
	cd apps/api && python3 -m venv .venv && . .venv/bin/activate && pip install -q -e ".[dev]" && pytest -q tests/test_auth.py tests/test_cases.py tests/test_documents.py tests/test_sprint5.py
	@chmod +x scripts/verify/sprint4.sh
	@VERIFY_SPRINT4_STRICT=1 ./scripts/verify/sprint4.sh
	@echo "✅ Sprint 4 API verification passed"
	@$(MAKE) test-e2e
	@echo "✅ Sprint 4 verification passed (API + E2E)"

verify-sprint5:
	cd apps/api && python3 -m venv .venv && . .venv/bin/activate && pip install -q -e ".[dev]" && pytest -q tests/test_sprint5.py
	@chmod +x scripts/verify/sprint5.sh
	@./scripts/verify/sprint5.sh
	@echo "✅ Sprint 5 verification passed"

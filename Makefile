.PHONY: setup dev dev-full down ps logs lint test migrate migrate-down \
        verify-quickstart verify-platform verify-health verify-logging \
        verify-traces verify-redis verify-rabbitmq verify-celery \
        verify-n8n-callback verify-minio verify-integration

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

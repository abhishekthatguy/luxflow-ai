.PHONY: setup dev down ps logs lint test verify-quickstart

setup:
	@chmod +x scripts/setup.sh scripts/verify/quickstart.sh
	@./scripts/setup.sh

dev:
	docker compose up -d --build

down:
	docker compose down

ps:
	docker compose ps

logs:
	docker compose logs -f

lint:
	cd apps/api && pip install -q -e ".[dev]" && ruff check src tests && mypy src
	cd apps/web && npm install && npm run lint

test:
	cd apps/api && pip install -q -e ".[dev]" && pytest -q
	cd apps/web && npm install && npm test

verify-quickstart:
	@chmod +x scripts/verify/quickstart.sh
	@./scripts/verify/quickstart.sh

.PHONY: up down rebuild logs ps backend-shell frontend-shell test test-services typecheck build reset

up:
	docker compose up -d

down:
	docker compose down

rebuild:
	docker compose up -d --build

logs:
	docker compose logs -f --tail=200 backend frontend

ps:
	docker compose ps

backend-shell:
	docker compose exec backend bash

frontend-shell:
	docker compose exec frontend sh

# Backend: service-level unit tests (no Postgres needed)
test-services:
	docker compose exec backend poetry run pytest tests/services/ -v

# Backend: full test suite (requires Postgres reachable)
test:
	docker compose exec backend poetry run pytest -v

# Frontend: type check only (no build)
typecheck:
	docker compose exec frontend node_modules/.bin/tsc --noEmit

# Frontend: production build
build:
	docker compose exec frontend npm run build

# Wipe everything (Postgres volume + images) and rebuild fresh
reset:
	docker compose down -v
	docker compose up -d --build

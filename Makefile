SHELL := /bin/bash
.DEFAULT_GOAL := help

COMPOSE_DEV := docker compose -f docker-compose.dev.yml
API := cd backend && uv run
WEB := cd frontend && pnpm

.PHONY: help dev db-up db-down check lint typecheck test format \
	lint-backend typecheck-backend test-backend lint-frontend typecheck-frontend test-frontend \
	openapi openapi-check screenshots \
	migration migrate user backup restore changelog

help: ## List available commands
	@grep -hE '^[a-zA-Z_-]+:.*?## ' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-14s\033[0m %s\n", $$1, $$2}'

# ------------------------------------------------------------------ development

dev: db-up migrate ## Database in Docker + API with reload (:8000) + Vite (:5173)
	@trap 'kill 0' EXIT; \
	( $(API) env PRUMO_COOKIE_SECURE=false PRUMO_UPLOADS_DIR=../data/uploads \
		uvicorn prumo.main:create_app --factory --reload --host 0.0.0.0 --port 8000 ) & \
	( $(WEB) dev --host 0.0.0.0 ) & \
	wait

db-up: ## Start the development and test databases
	@$(COMPOSE_DEV) up -d --wait

db-down: ## Stop the development databases
	@$(COMPOSE_DEV) down

migration: ## Generate a migration: make migration m="add fuelings" (always review it)
	@test -n "$(m)" || (echo 'usage: make migration m="description"' && exit 1)
	$(API) alembic revision --autogenerate -m "$(m)"

migrate: ## Apply migrations
	$(API) alembic upgrade head

user: ## Create a user (interactive)
	$(API) prumo users create

backup: ## Dump the database to backups/ (COMPOSE_FILE=docker-compose.dev.yml for dev)
	@./deploy/backup.sh

restore: ## Restore a backup, replacing the database: make restore f=backups/<file>.sql.gz
	@test -n "$(f)" || (echo 'usage: make restore f=backups/<file>.sql.gz' && exit 1)
	@./deploy/restore.sh "$(f)"

changelog:
	github_changelog_generator -u henriquesebastiao -p prumo -o CHANGELOG --no-verbose
	@echo "Changelog generated at CHANGELOG"

# ------------------------------------------------------------------ quality

check: lint typecheck test openapi-check ## Lint, typecheck, tests and OpenAPI snapshot (everything CI runs)

lint: lint-backend lint-frontend ## ruff, import-linter, ESLint, Stylelint, Prettier

typecheck: typecheck-backend typecheck-frontend ## mypy and vue-tsc

test: test-backend test-frontend ## Backend and frontend tests

format: ## Format the code
	$(API) ruff format .
	$(API) ruff check --fix .
	$(WEB) format

lint-backend:
	$(API) ruff check .
	$(API) ruff format --check .
	$(API) lint-imports

typecheck-backend:
	$(API) mypy

test-backend: db-up
	$(API) pytest

lint-frontend:
	$(WEB) lint

typecheck-frontend:
	$(WEB) typecheck

test-frontend:
	$(WEB) test

screenshots: ## Capture screens with Playwright and build design/v1 comparisons (frontend/e2e/output)
	$(WEB) screenshots

# ------------------------------------------------------------------ contract

openapi: ## Export openapi/openapi.json and regenerate the TypeScript types
	$(API) prumo openapi ../openapi/openapi.json
	$(WEB) gen:api

openapi-check: ## Fail if the OpenAPI snapshot or the TypeScript types are out of date
	@$(API) prumo openapi - | diff -q - ../openapi/openapi.json > /dev/null \
		|| (echo "openapi/openapi.json is out of date: run make openapi" && exit 1)
	@cd frontend && pnpm exec openapi-typescript ../openapi/openapi.json --default-non-nullable false \
		| pnpm exec prettier --stdin-filepath schema.d.ts | diff -q - src/lib/api/schema.d.ts > /dev/null \
		|| (echo "frontend/src/lib/api/schema.d.ts is out of date: run make openapi" && exit 1)

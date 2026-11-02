SHELL := /bin/bash
.DEFAULT_GOAL := help

COMPOSE_DEV := docker compose -f docker-compose.dev.yml
API := cd backend && uv run

.PHONY: help dev db-up db-down check lint typecheck test format \
	lint-backend typecheck-backend test-backend openapi openapi-check \
	migration migrate user

help: ## List available commands
	@grep -hE '^[a-zA-Z_-]+:.*?## ' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-14s\033[0m %s\n", $$1, $$2}'

# ------------------------------------------------------------------ development

dev: db-up migrate ## Database in Docker + API with reload (:8000) + Vite (:5173)
	@trap 'kill 0' EXIT; \
	( $(API) env PRUMO_COOKIE_SECURE=false PRUMO_UPLOADS_DIR=../data/uploads \
		uvicorn prumo.main:create_app --factory --reload --port 8000 ) & \
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

# ------------------------------------------------------------------ quality

check: lint typecheck test openapi-check ## Lint, typecheck, tests and OpenAPI snapshot (everything CI runs)

lint: lint-backend ## ruff, import-linter, ESLint, Stylelint

typecheck: typecheck-backend ## mypy and vue-tsc

test: test-backend ## Backend and frontend tests

format: ## Format the code
	$(API) ruff format .
	$(API) ruff check --fix .

lint-backend:
	$(API) ruff check .
	$(API) ruff format --check .
	$(API) lint-imports

typecheck-backend:
	$(API) mypy

test-backend: db-up
	$(API) pytest

# ------------------------------------------------------------------ contract

openapi: ## Export openapi/openapi.json
	$(API) prumo openapi ../openapi/openapi.json

openapi-check: ## Fail if the OpenAPI snapshot is out of date
	@$(API) prumo openapi - | diff -q - ../openapi/openapi.json > /dev/null \
		|| (echo "openapi/openapi.json is out of date: run make openapi" && exit 1)

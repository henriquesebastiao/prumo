SHELL := /bin/bash
.DEFAULT_GOAL := help

COMPOSE_DEV := docker compose -f docker-compose.dev.yml

.PHONY: help db-up db-down check check-repo

help: ## List available commands
	@grep -hE '^[a-zA-Z_-]+:.*?## ' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-14s\033[0m %s\n", $$1, $$2}'

db-up: ## Start the development and test databases
	@$(COMPOSE_DEV) up -d --wait

db-down: ## Stop the development databases
	@$(COMPOSE_DEV) down

check: check-repo ## Lint, typecheck, tests and OpenAPI snapshot (everything CI runs)

check-repo:
	@$(COMPOSE_DEV) config -q

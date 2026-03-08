.PHONY: help setup test lint lint-api lint-python format typecheck check clean all serve stop pre-commit-install release

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*##' $(MAKEFILE_LIST) | awk -F ':.*## ' '{printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'

all: setup check test ## Setup, check, and test everything

setup: ## Install dependencies
	uv sync

test: ## Run integration tests
	uv run pytest tests/ -v

check: lint typecheck ## Run all checks (lint + typecheck)

lint: lint-python lint-api ## Lint everything

lint-python: ## Lint Python source with ruff
	uv run ruff check src/ tests/

lint-api: ## Lint API specs with Redocly
	npx @redocly/cli lint --config ../api/redocly.yaml \
		../api/schemas/v1/request.yaml \
		../api/schemas/v1/response.yaml \
		../api/schemas/v1/hooks.yaml \
		../api/examples/todo-app/openapi.yaml \
		../api/examples/ecommerce/openapi.yaml \
		../api/examples/messaging/openapi.yaml

format: ## Auto-format Python source
	uv run ruff format src/ tests/
	uv run ruff check --fix src/ tests/

typecheck: ## Type-check Python source with mypy
	uv run mypy src/

pre-commit-install: ## Install pre-commit git hooks
	uv run pre-commit install

SERVER_PORT ?= 9876
CONTAINER_NAME = remote-behave-steps-test
IMAGE_NAME = remote-behave-steps-test-server

serve: ## Start the example todo service in Docker
	docker build -t $(IMAGE_NAME) tests/example_simple/server/
	docker run -d --name $(CONTAINER_NAME) -p $(SERVER_PORT):8000 $(IMAGE_NAME)
	@echo "Server started on http://127.0.0.1:$(SERVER_PORT)"

stop: ## Stop the test server
	docker stop $(CONTAINER_NAME) 2>/dev/null && docker rm $(CONTAINER_NAME) 2>/dev/null && echo "Server stopped" || echo "Server not running"

VERSION ?=
CURRENT_VERSION = $(shell grep '^version' pyproject.toml | head -1 | sed 's/.*"\(.*\)"/\1/')

release-preflight:
	@if [ -z "$(VERSION)" ]; then \
		echo "Error: VERSION is required. Usage: make release VERSION=0.2.0"; \
		echo "  Current version: $(CURRENT_VERSION)"; \
		exit 1; \
	fi
	@if [ -n "$$(git status --porcelain)" ]; then \
		echo "Error: working tree is not clean. Commit or stash changes first."; \
		exit 1; \
	fi

release: release-preflight check test ## Release a new version (usage: make release VERSION=0.2.0)
	@echo "Releasing v$(VERSION) (current: $(CURRENT_VERSION))"
	@echo ""
	sed 's/^version = ".*"/version = "$(VERSION)"/' pyproject.toml > pyproject.toml.tmp && mv pyproject.toml.tmp pyproject.toml
	git add pyproject.toml
	git commit -m "Release v$(VERSION)"
	git tag -a "v$(VERSION)" -m "Release v$(VERSION)"
	@echo ""
	@echo "Done. To publish, run:"
	@echo "  git push origin main --follow-tags"

clean: ## Remove generated artifacts
	rm -rf .venv *.egg-info dist .pytest_cache htmlcov
	find . -type d -name __pycache__ -exec rm -rf {} +

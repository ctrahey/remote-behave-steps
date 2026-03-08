.PHONY: setup test lint lint-api lint-python format typecheck check clean all serve stop pre-commit-install

# Run everything
all: setup check test

# Set up the venv and install dependencies
setup:
	uv sync

# Run integration tests
test:
	uv run pytest tests/ -v

# All checks (lint + typecheck)
check: lint typecheck

# Lint everything
lint: lint-python lint-api

# Lint Python source with ruff
lint-python:
	uv run ruff check src/ tests/

# Lint the API specs
lint-api:
	npx @redocly/cli lint --config ../api/redocly.yaml \
		../api/schemas/v1/request.yaml \
		../api/schemas/v1/response.yaml \
		../api/schemas/v1/hooks.yaml \
		../api/examples/todo-app/openapi.yaml \
		../api/examples/ecommerce/openapi.yaml \
		../api/examples/messaging/openapi.yaml

# Auto-format Python source
format:
	uv run ruff format src/ tests/
	uv run ruff check --fix src/ tests/

# Type-check Python source
typecheck:
	uv run mypy src/

# Install pre-commit hooks
pre-commit-install:
	uv run pre-commit install

SERVER_PORT ?= 9876
CONTAINER_NAME = remote-behave-steps-test
IMAGE_NAME = remote-behave-steps-test-server

# Start the example project's todo service in Docker
serve:
	docker build -t $(IMAGE_NAME) tests/example_simple/server/
	docker run -d --name $(CONTAINER_NAME) -p $(SERVER_PORT):8000 $(IMAGE_NAME)
	@echo "Server started on http://127.0.0.1:$(SERVER_PORT)"

# Stop the test server
stop:
	docker stop $(CONTAINER_NAME) 2>/dev/null && docker rm $(CONTAINER_NAME) 2>/dev/null && echo "Server stopped" || echo "Server not running"

# Remove generated artifacts
clean:
	rm -rf .venv *.egg-info dist .pytest_cache htmlcov
	find . -type d -name __pycache__ -exec rm -rf {} +

.PHONY: setup test lint clean all serve stop

# Run everything
all: setup test lint

# Set up the venv and install dependencies
setup:
	uv venv && uv pip install -e ".[dev]"

# Run integration tests
test:
	.venv/bin/python -m pytest tests/ -v

# Lint the API specs
lint:
	npx @redocly/cli lint --config ../api/redocly.yaml \
		../api/schemas/v1/request.yaml \
		../api/schemas/v1/response.yaml \
		../api/schemas/v1/hooks.yaml \
		../api/examples/todo-app/openapi.yaml \
		../api/examples/ecommerce/openapi.yaml \
		../api/examples/messaging/openapi.yaml

SERVER_PORT ?= 9876
SERVER_PID = .server.pid

# Start the test server in the background
serve:
	.venv/bin/python -m flask --app tests.server.app run --port $(SERVER_PORT) & echo $$! > $(SERVER_PID)
	@echo "Server started on http://127.0.0.1:$(SERVER_PORT) (PID $$(cat $(SERVER_PID)))"

# Stop the test server
stop:
	@if [ -f $(SERVER_PID) ]; then \
		kill $$(cat $(SERVER_PID)) 2>/dev/null && echo "Server stopped" || echo "Server not running"; \
		rm -f $(SERVER_PID); \
	else \
		echo "No PID file found"; \
	fi

# Remove generated artifacts
clean:
	rm -rf .venv *.egg-info dist .pytest_cache
	find . -type d -name __pycache__ -exec rm -rf {} +

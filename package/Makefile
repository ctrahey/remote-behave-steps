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
	rm -rf .venv *.egg-info dist .pytest_cache
	find . -type d -name __pycache__ -exec rm -rf {} +

.PHONY: setup test catalog serve stop clean

SERVER_PORT ?= 9876
CONTAINER_NAME = todo-service-example
IMAGE_NAME = todo-service-example

# Set up the venv and install dependencies
setup:
	uv venv && uv pip install remote-behave-steps requests

# Start the todo service in Docker
serve:
	docker build -t $(IMAGE_NAME) server/
	docker run -d --name $(CONTAINER_NAME) -p $(SERVER_PORT):8000 $(IMAGE_NAME)
	@echo "Server started on http://127.0.0.1:$(SERVER_PORT)"

# Stop the todo service
stop:
	docker stop $(CONTAINER_NAME) 2>/dev/null && docker rm $(CONTAINER_NAME) 2>/dev/null && echo "Server stopped" || echo "Server not running"

# Run the behave scenarios
test:
	.venv/bin/python -m behave --no-capture features/

# Show the step catalog (local + remote steps)
catalog:
	.venv/bin/python -m behave --steps-catalog features/

# Remove generated artifacts
clean:
	rm -rf .venv *.egg-info dist .pytest_cache
	find . -type d -name __pycache__ -exec rm -rf {} +

.PHONY: setup test catalog clean

# Set up the venv and install dependencies
setup:
	uv venv && uv pip install remote-behave-steps requests

# Run the behave scenarios (expects the todo server on localhost:9876)
test:
	.venv/bin/python -m behave --no-capture features/

# Show the step catalog (local + remote steps)
catalog:
	.venv/bin/python -m behave --steps-catalog features/

# Remove generated artifacts
clean:
	rm -rf .venv *.egg-info dist .pytest_cache
	find . -type d -name __pycache__ -exec rm -rf {} +

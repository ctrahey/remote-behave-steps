# Example: To-Do App BDD Tests

This is a minimal example showing how to use `remote_behave_steps` to write
BDD tests against a remote service.

## Project structure

```
pyproject.toml              # Dependencies + remote_behave_steps server config
features/
  todo.feature              # Feature file with Given/When/Then scenarios
  steps/
    remote.py               # One-liner: imports remote_behave_steps.auto
    verify_steps.py         # Local When/Then steps that hit the service API
```

## How it works

1. **Given steps** are served by the todo service (discovered from its OpenAPI
   spec). They set up fixtures like "I have 3 existing to-do items".

2. **When/Then steps** are local Python — they call the service's public API
   and assert on the results.

3. The `remote_behave_steps` library reads the server URL from `pyproject.toml`,
   fetches the OpenAPI spec, and registers all remote Given steps with behave
   automatically.

## Quick start

```bash
# 1. Start the todo service (from the package/ directory):
make serve

# 2. Set up and run tests:
make setup
make test

# 3. View the step catalog (shows both local and remote steps):
make catalog
```

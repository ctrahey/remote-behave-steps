# Remote Behave Steps

Distributed BDD fixture setup for [Python Behave](https://behave.readthedocs.io/).

**The problem:** In distributed systems, BDD scenarios need preconditions like "Given I have 3 existing to-do items" -- but the test runner can't efficiently manipulate databases, queues, and caches that live inside other services. You end up writing fragile setup code that reaches across service boundaries, or maintaining a parallel set of test fixtures that drift from production behavior.

**The solution:** Services in your system expose HTTP endpoints that know how to set up their own state. Remote Behave Steps discovers these endpoints from standard OpenAPI specs and registers them as native Behave steps. Your feature files look exactly the same -- the library handles discovery, invocation, and context passing transparently.

```gherkin
Feature: To-Do Management

  Scenario: Create and verify to-do items
    Given I have "3" existing to-do items       # <-- served by the to-do service
    And a to-do item titled "Buy milk"           # <-- also remote
    When I request the to-do list                # <-- local step, hits the public API
    Then I should see 4 items                    # <-- local assertion
```

The Given steps above are defined in the to-do service's OpenAPI spec, discovered at test time, and invoked over HTTP. The test author doesn't need to know where the steps live.

## How It Works

1. A service adds an OpenAPI spec with `x-behave-pattern` on its fixture endpoints
2. The test project points `remote_behave_steps` at the service's spec URL
3. At test time, the library fetches the spec, registers each pattern as a Behave step, and invokes endpoints via HTTP when those steps execute

```
  Feature File           remote_behave_steps           Service
  ───────────            ───────────────────           ───────
  Given I have "3"  ──>  matches pattern,         ──>  PUT /existing-todos
  existing to-do         builds request with           { context: {...},
  items                  context + inputs               inputs: {count: "3"} }
                    <──  returns data to context  <──  { status: "ok",
                                                        data: {created_ids: [1,2,3]} }
```

## Installation

```bash
pip install remote-behave-steps
```

Or with [uv](https://docs.astral.sh/uv/):

```bash
uv add remote-behave-steps
```

### Requirements

- Python 3.10+
- [Behave](https://behave.readthedocs.io/) 1.2.6+

## Quick Start

### 1. Configure your server

Add the remote service's OpenAPI spec URL to your `pyproject.toml`:

```toml
[tool.remote_behave_steps]
cache_ttl = 300  # seconds; set to 0 during local development

[[tool.remote_behave_steps.servers]]
name = "todo-service"
url = "http://localhost:8080/openapi.yaml"
```

### 2. Register remote steps

Create a step file that imports the auto-registration module. This is the only code you need:

```python
# features/steps/remote.py
import remote_behave_steps.auto  # noqa: F401
```

That's it. All steps discovered from the configured servers are now available in your feature files.

### 3. Write your feature

```gherkin
Feature: To-Do Management

  Scenario: Create generic to-do items
    Given I have "3" existing to-do items
    When I request the to-do list
    Then I should see 3 items
```

The Given step is served remotely. Write your When and Then steps locally as usual.

### 4. Run behave

```bash
behave
```

## Alternative Registration Styles

The auto-import is the simplest approach, but you can also register explicitly:

```python
# features/steps/remote.py

# Option A: Explicit call, config from pyproject.toml
from remote_behave_steps import register_remote_steps
register_remote_steps()

# Option B: Fully programmatic (dynamic URLs, CI environments, etc.)
from remote_behave_steps import register_remote_steps
register_remote_steps(servers=["http://localhost:8080/openapi.yaml"])

# Option C: Multiple servers with options
from remote_behave_steps import register_remote_steps
register_remote_steps(servers=[
    {"name": "todo-service", "url": "http://todo:8080/openapi.yaml"},
    {"name": "auth-service", "url": "http://auth:8080/openapi.yaml", "timeout": 5000},
])
```

## Writing a Remote Step Provider

A remote step provider is any HTTP service that serves an OpenAPI spec with `x-behave-pattern` extensions on its fixture endpoints. The service can be written in any language or framework.

### Minimal example (FastAPI)

```python
from fastapi import FastAPI, Request

app = FastAPI(title="My Fixture Service", version="1.0.0")

@app.put("/existing-todos", summary="Create N generic to-do items")
async def existing_todos(request: Request):
    body = await request.json()
    count = int(body["inputs"]["count"])
    # ... create the to-do items in your database ...
    return {"status": "ok", "data": {"created_ids": [1, 2, 3]}}
```

### OpenAPI extensions

Mark each fixture endpoint with `x-behave-pattern` so the library can discover it:

```yaml
paths:
  /existing-todos:
    put:
      summary: Create N generic to-do items
      x-behave-pattern: 'I have "{count}" existing to-do items'
      x-behave-step-type: given    # optional, defaults to "given"
      x-behave-timeout: 10000      # optional, per-step timeout in ms
```

### Step types

Each step declares its type with `x-behave-step-type`. Valid values are `given`, `when`, `then`, and `step` (registers for all types). **The default is `given`**, reflecting the library's primary purpose: remote fixture setup.

While you can implement any step type remotely, the recommended pattern is:

- **Remote services** handle **Given** steps (fixture setup, state manipulation)
- **Test runner** handles **When** and **Then** steps (actions and assertions against public interfaces)

### Request format

Every step endpoint receives a PUT request with this body:

```json
{
  "context": {
    "run_id": "550e8400-e29b-41d4-a716-446655440000",
    "feature": {"name": "To-Do Management", "file": "features/todo.feature", "tags": []},
    "scenario": {"name": "Create items", "id": "...", "tags": []}
  },
  "inputs": {
    "count": "3",
    "table": {"headings": ["title", "priority"], "rows": [["Buy milk", "high"]]},
    "text": "multiline docstring content"
  }
}
```

- **`context`** is auto-populated by the library (run ID, feature/scenario metadata)
- **`inputs`** contains the captured pattern parameters, plus optional `table` and `text` from Gherkin

### Response format

```json
{
  "status": "ok",
  "data": {"created_ids": [1, 2, 3]}
}
```

Any values in `data` are merged into `context.remote_data` on the Behave side, making them available to subsequent steps.

### Standard endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/healthz` | GET | Liveness probe. Returns 200 when ready. |
| `/reset-all-data` | PUT | Reset to clean baseline. Called at the start of each test run. |
| `/openapi.yaml` | GET | The OpenAPI spec with `x-behave-pattern` extensions. |

## Lifecycle Hooks

Remote services can optionally participate in Behave's lifecycle by implementing well-known hook endpoints:

| Path | Behave Hook | When Called |
|------|-------------|-------------|
| `/hooks/before-scenario` | `before_scenario` | Before each `@remote_hooks` scenario |
| `/hooks/after-scenario` | `after_scenario` | After each `@remote_hooks` scenario |
| `/hooks/before-feature` | `before_feature` | Before each `@remote_hooks` feature |
| `/hooks/after-feature` | `after_feature` | After each `@remote_hooks` feature |
| `/hooks/before-all` | `before_all` | Start of test run (unconditional) |
| `/hooks/after-all` | `after_all` | End of test run (unconditional) |

Hooks require the `@remote_hooks` tag on the feature or scenario (except `before_all`/`after_all`). Wire them up in `environment.py`:

```python
# features/environment.py
from remote_behave_steps import hooks

def before_scenario(context, scenario):
    hooks.before_scenario(context, scenario)

def after_scenario(context, scenario):
    hooks.after_scenario(context, scenario)
```

All hook endpoints are optional. The library discovers which hooks a service supports from its OpenAPI spec.

## Configuration Reference

### `pyproject.toml`

```toml
[tool.remote_behave_steps]
cache_ttl = 300  # How long to cache discovered specs (seconds). Default: 300

[[tool.remote_behave_steps.servers]]
name = "todo-service"              # Optional display name (derived from URL if omitted)
url = "http://localhost:8080/openapi.yaml"  # Required
timeout = 30000                    # Default step timeout in ms. Default: 30000
```

### Environment variables

- `REMOTE_STEPS_SERVER` -- Override the server URL (useful in CI)

## Full Documentation

For the complete API meta-specification, request/response schemas, lifecycle hook details, and example OpenAPI specs, see the [project repository](https://github.com/ctrahey/remote-behave-steps).

## License

MIT

# Remote Behave Steps

Distributed BDD fixture setup for [Python Behave](https://behave.readthedocs.io/).

In behavioral testing, scenarios describe preconditions in "Given" steps -- the fixtures that put the system into a known state before a scenario runs. In distributed systems, it is often impractical to manipulate that state from the process running the test suite. Databases, queues, caches, and third-party integrations live inside other services, behind network boundaries.

Remote Behave Steps solves this with a simple pattern: **services expose HTTP endpoints that know how to set up their own state**, and the test runner discovers and invokes them automatically. Your feature files look exactly the same -- the plumbing is invisible.

```gherkin
Feature: To-Do Management

  Scenario: Create and verify to-do items
    Given I have "3" existing to-do items       # served by the to-do service over HTTP
    And a to-do item titled "Buy milk"           # also remote
    When I request the to-do list                # local step, hits the public API
    Then I should see 4 items                    # local assertion
```

## This Project

This repository provides two things:

1. **API Meta-Specification** -- Conventions and schemas that describe how any service (in any language) exposes BDD fixture endpoints for discovery and invocation. See [API Meta-Specification](#api-meta-specification) below.

2. **Python Library** (`remote-behave-steps`) -- A Behave extension that discovers remote step providers, registers their steps, and handles invocation. See the [package README](package/README.md) for installation, quick start, and usage.

```
  Feature File           remote_behave_steps           Service
  ───────────            ───────────────────           ───────
  Given I have "3"  ──>  matches pattern,         ──>  PUT /existing-todos
  existing to-do         builds request with           { context: {...},
  items                  context + inputs               inputs: {count: "3"} }
                    <──  returns data to context  <──  { status: "ok",
                                                        data: {created_ids: [1,2,3]} }
```

---

## API Meta-Specification

The specification is "meta" because your actual API is completely custom to your system. This spec defines what must be true for _any_ client library to discover and invoke your fixture endpoints.

### Discovery

Services provide an [OpenAPI 3.x](https://spec.openapis.org/) specification document. The library discovers steps from operations that include the `x-behave-pattern` extension:

```yaml
paths:
  /existing-todos:
    put:
      summary: Create N generic to-do items
      x-behave-pattern: 'I have "{count}" existing to-do items'
      x-behave-step-type: given         # optional, defaults to "given"
      x-behave-timeout: 10000           # optional, per-step timeout in ms
```

Operations that lack `x-behave-pattern` (such as `/healthz`) are not registered as steps. There is no separate discovery endpoint -- the OpenAPI spec itself is the step catalog.

### OpenAPI Extensions

| Extension | Level | Required | Description |
|-----------|-------|----------|-------------|
| `x-behave-pattern` | Operation | Yes (for steps) | The Behave step match pattern. Parameters use `"{name}"` syntax. |
| `x-behave-step-type` | Operation | No | `given` (default), `when`, `then`, or `step`. |
| `x-behave-timeout` | Operation | No | Per-step timeout override in milliseconds. |
| `x-behave-spec-version` | Info | No | Meta-spec version (currently `"1.0"`). Reserved for forward compatibility. |

### Step Type Guidance

The default step type is `given`, reflecting the library's primary design purpose: **remote fixture setup**. Each step endpoint declares its own type, so there is no ambiguity in the Behave step catalog.

The recommended pattern:

- **Remote services** handle **Given** steps (fixture setup, state manipulation, data seeding)
- **Test runner** handles **When** and **Then** steps (actions and assertions against public interfaces)

Other step types are supported but fixture setup is the core use case.

### Invocation Protocol

All step invocations use the **PUT** method. PUT conveys idempotent "ensure this state" semantics: calling the same step twice with the same parameters should produce the same system state.

#### Request body

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

- **`context`** (`StepExecutionContext`) -- Auto-populated by the client library. Contains `run_id` (UUID for data isolation), feature/scenario metadata, and step info.
- **`inputs`** (`StepInputs`) -- Pattern-captured parameters as string key-value pairs, plus optional `table` (Gherkin data table) and `text` (multiline docstring).

Canonical request schema: [`api/schemas/v1/request.yaml`](api/schemas/v1/request.yaml)

#### Response body

```json
{
  "status": "ok",
  "data": {"created_ids": [1, 2, 3]}
}
```

- **`status`** -- `"ok"` or `"error"`
- **`data`** (optional) -- Arbitrary object with step-produced data (e.g., created IDs)
- **`error`** (optional) -- Error details when `status` is `"error"`

Canonical response schema: [`api/schemas/v1/response.yaml`](api/schemas/v1/response.yaml)

#### HTTP status conventions

| Range | Meaning |
|-------|---------|
| 2xx   | Step executed successfully |
| 4xx   | Test failure (bad input, unmet precondition) -- surfaces as `AssertionError` |
| 5xx   | Infrastructure error (service bug, downstream outage) -- surfaces as `RemoteStepError` |

### Standard Endpoints

| Endpoint | Method | Required | Purpose |
|----------|--------|----------|---------|
| `/openapi.yaml` | GET | Yes | The OpenAPI spec with `x-behave-pattern` extensions |
| `/healthz` | GET | Recommended | Liveness probe. Returns 200 when the service is ready. |
| `/reset-all-data` | PUT | Required | Reset to clean baseline state. Accepts `context` (with `run_id`) and `scope` (`"full"` or `"run"`). |

### Lifecycle Hooks

Remote services can optionally participate in Behave's lifecycle by implementing well-known hook endpoints. All use PUT and return the standard response schema.

| Path | Behave Hook | Scope |
|------|-------------|-------|
| `/hooks/before-all` | `before_all` | Unconditional |
| `/hooks/after-all` | `after_all` | Unconditional |
| `/hooks/before-feature` | `before_feature` | `@remote_hooks` features |
| `/hooks/after-feature` | `after_feature` | `@remote_hooks` features |
| `/hooks/before-scenario` | `before_scenario` | `@remote_hooks` scenarios |
| `/hooks/after-scenario` | `after_scenario` | `@remote_hooks` scenarios |
| `/hooks/before-step` | `before_step` | `@remote_hooks` scope |
| `/hooks/after-step` | `after_step` | `@remote_hooks` scope |

All hook endpoints are optional. The library discovers which hooks a service supports by checking for these paths in the OpenAPI spec.

Hook request schemas: [`api/schemas/v1/hooks.yaml`](api/schemas/v1/hooks.yaml)

#### Tag gating

To avoid unnecessary network overhead, hooks only fire for features or scenarios tagged `@remote_hooks` (except `before_all`/`after_all`, which fire unconditionally).

#### Hook vs. Reset

`PUT /reset-all-data` is separate from hooks. It is a deliberate "nuke state" action called at the start of a test run. `before_all` is a general-purpose hook for setup that doesn't involve state destruction (e.g., initializing tracing, registering listeners).

## Examples

The `api/examples/` directory contains sample OpenAPI specs:

| Example | Demonstrates |
|---------|-------------|
| [`todo-app/`](api/examples/todo-app/) | Named parameters, table-based step, scenario hooks |
| [`ecommerce/`](api/examples/ecommerce/) | Typed parameters, timeout overrides, full lifecycle hooks |
| [`messaging/`](api/examples/messaging/) | Multi-parameter steps, multiline text input, step-level hooks |

## Repository Structure

```
api/                                # API meta-specification
  schemas/v1/                       #   Canonical request/response/hook schemas
  examples/                         #   Sample OpenAPI specs
  redocly.yaml                      #   OpenAPI linter configuration
package/                            # Python library (remote-behave-steps)
  src/remote_behave_steps/          #   Library source
  tests/                            #   Integration tests with Docker-based test server
  README.md                         #   Library-specific docs (install, quick start, usage)
  pyproject.toml                    #   Package metadata and build config
```

## Development

```bash
cd package
uv venv && uv pip install -e ".[dev]"
uv run pytest tests/ -v
```

The test suite builds a FastAPI fixture service as a Docker container and runs Behave scenarios against it. Docker must be running.

To lint the API schemas:

```bash
cd package && make lint
```

## License

MIT -- see [LICENSE](LICENSE).

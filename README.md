# Remote Behave Steps

A library and API meta-specification for distributed BDD testing with [Python Behave](https://behave.readthedocs.io/).

In behavioral testing, scenarios describe preconditions in "Given" steps -- essentially the test's fixtures, the state the system should be in before a scenario runs. In distributed systems, it is often impractical to manipulate that state efficiently from the process running the test suite.

Remote Behave Steps solves this by introducing a pattern: services inside the distributed system expose HTTP endpoints that the test runner discovers and invokes for fixture setup. These services can directly populate databases, inject faults, configure performance characteristics, and perform other internal operations to get the system-under-test into the desired state.

## Deliverables

This project provides two things:

1. **API Meta-Specification** -- A set of conventions and schemas that describe how remote step services expose themselves. The specification is "meta" because the actual API is completely custom to your system; this spec clarifies what must be true for the library to discover and invoke your endpoints.

2. **Python Library** (forthcoming) -- A Behave extension that discovers remote step services, registers their steps, and handles invocation automatically.

## API Meta-Specification

### Discovery

Services provide an [OpenAPI 3.0.3](https://spec.openapis.org/oas/v3.0.3) specification document. The library parses this document and registers steps from operations that include the `x-behave-pattern` extension. This extension carries the Behave step match pattern, for example:

```yaml
x-behave-pattern: 'I have "{num_todos}" existing to-do items'
```

Using a dedicated extension field for the pattern frees the `description` field for human-readable documentation and the `summary` field for catalog display.

Operations that lack `x-behave-pattern` (such as `/healthz` and `/reset-all-data`) are treated as system endpoints, not step definitions. There is no separate discovery endpoint -- the OpenAPI spec itself is the step catalog.

#### Info-Level Extensions

- `x-behave-spec-version` -- Declares the meta-spec version in use. Included at the `info` level for forward compatibility.

#### Operation-Level Extensions

- `x-behave-pattern` -- The step match pattern (required for step operations).
- `x-behave-timeout` -- Optional per-step timeout override, in milliseconds.

### Invocation

All step invocations use the **PUT** method. PUT conveys idempotent "ensure this state" semantics: calling the same step twice with the same parameters should produce the same system state.

### Request Schema

Every step endpoint accepts a `RemoteStepInvocationRequest` body with two top-level fields:

- **`context`** (`StepExecutionContext`) -- Auto-populated by the library. Contains:
  - `run_id` -- UUID identifying this behave invocation (primary key for data isolation between concurrent runs)
  - `feature` -- Name, file path, and tags of the current feature
  - `scenario` -- Name, id, and tags of the current scenario
  - `step` -- Text and id of the current step
  - `timestamp` -- ISO 8601 timestamp of invocation

- **`inputs`** (`StepInputs`) -- Step-specific data:
  - Named parameters captured from the step pattern (as `additionalProperties`)
  - `table` (optional) -- Gherkin data table with `headings` and `rows`
  - `text` (optional) -- Multiline text block (docstring)

Canonical request schema: [`schemas/v1/request.yaml`](api/schemas/v1/request.yaml)

### Response Schema

Step endpoints return a `RemoteStepInvocationResponse`:

- **`status`** -- `"ok"` or `"error"`
- **`data`** (optional) -- Arbitrary object with step-produced data (e.g., created IDs)
- **`error`** (optional) -- Error details when status is `"error"`

Canonical response schema: [`schemas/v1/response.yaml`](api/schemas/v1/response.yaml)

### HTTP Status Conventions

| Range | Meaning |
|-------|---------|
| 2xx   | Step executed successfully |
| 4xx   | Test failure (bad input, unmet precondition) |
| 5xx   | Infrastructure error (service bug, downstream outage) |

## Standard Endpoints

### Required: `PUT /reset-all-data`

Resets the system to a clean baseline state. Accepts an optional body with:

- `context` -- Execution context (provides `run_id` for scoped resets)
- `scope` -- `"full"` (complete reset) or `"run"` (reset data for the given `run_id` only)

### Recommended: `GET /healthz`

Health check endpoint. Returns 200 when the service is ready to accept step invocations.

## Lifecycle Hooks

Remote services can optionally participate in Behave's lifecycle events by implementing well-known hook endpoints. These mirror Behave's environment hooks (`before_all`, `after_scenario`, etc.).

### Tag Gating with `@remote_hooks`

To avoid unnecessary network overhead, the library **only invokes remote hook endpoints** for features or scenarios tagged with `@remote_hooks`. Without this tag, no hook calls are made. The `before_all` and `after_all` hooks are the exception -- they fire unconditionally if the endpoints exist.

```gherkin
@remote_hooks
Feature: User Authentication
  # All scenarios in this feature will trigger remote hooks

  Scenario: Successful login
    Given a user "alice" exists
    ...
```

### Well-Known Hook Paths

All hook endpoints use **PUT** and return `RemoteStepInvocationResponse`. Each has a scope-appropriate request schema (defined in [`schemas/v1/hooks.yaml`](api/schemas/v1/hooks.yaml)):

| Path | Behave Hook | Request Context | When Called |
|------|-------------|-----------------|-------------|
| `/hooks/before-all` | `before_all` | `run_id` | Start of test run |
| `/hooks/after-all` | `after_all` | `run_id` | End of test run |
| `/hooks/before-feature` | `before_feature` | `run_id`, `feature` | Before each `@remote_hooks` feature |
| `/hooks/after-feature` | `after_feature` | `run_id`, `feature` | After each `@remote_hooks` feature |
| `/hooks/before-scenario` | `before_scenario` | `run_id`, `feature`, `scenario` | Before each `@remote_hooks` scenario |
| `/hooks/after-scenario` | `after_scenario` | `run_id`, `feature`, `scenario` | After each `@remote_hooks` scenario |
| `/hooks/before-step` | `before_step` | `run_id`, `feature`, `scenario`, `step` | Before each step in a `@remote_hooks` scope |
| `/hooks/after-step` | `after_step` | `run_id`, `feature`, `scenario`, `step` | After each step in a `@remote_hooks` scope |

All hook endpoints are **optional**. The library discovers which hooks a service supports by checking for these paths in the OpenAPI spec. If a path is absent, that hook is simply not called.

### Hook vs. Reset

The `PUT /reset-all-data` endpoint is separate from hooks. It is a deliberate "nuke state" action typically called at the start of a test run or between scenarios. `before_all` is a general-purpose hook for setup that doesn't necessarily involve state destruction (e.g., initializing tracing, registering listeners).

## Step Type Guidance

The meta-specification does not enforce a distinction between Given, When, and Then steps. However, the recommended pattern is:

- **Remote services** handle **Given** steps (fixture setup, state manipulation)
- **Test runner** handles **When** and **Then** steps (actions and assertions against the system's public interfaces)

This is guidance, not enforcement. There may be valid reasons to implement other step types remotely, but fixture setup is the primary use case.

## Examples

The `api/examples/` directory contains sample OpenAPI specifications demonstrating the meta-spec:

| Example | Demonstrates |
|---------|-------------|
| [`todo-app/`](api/examples/todo-app/) | Named parameters, table-based step, `before-scenario` / `after-scenario` hooks |
| [`ecommerce/`](api/examples/ecommerce/) | Typed parameters (`{balance:d}`), timeout override, `before-all` / `after-all` / `before-scenario` / `after-scenario` hooks |
| [`messaging/`](api/examples/messaging/) | Multi-parameter steps, multiline text (docstring) input, `before-feature` / `after-feature` / `before-step` / `after-step` hooks |

## Project Structure

```
api/
  schemas/
    v1/
      request.yaml        # Canonical request schema
      response.yaml       # Canonical response schema
      hooks.yaml          # Lifecycle hook request schemas
  examples/
    todo-app/             # Basic example
    ecommerce/            # Multi-step example with tables
    messaging/            # Docstrings, timeouts, coordination
  redocly.yaml            # OpenAPI linter configuration
```

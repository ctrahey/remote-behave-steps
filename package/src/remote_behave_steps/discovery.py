"""OpenAPI spec parsing and remote step discovery."""

from dataclasses import dataclass
import requests
import yaml

from remote_behave_steps.config import ServerConfig


VALID_STEP_TYPES = {"given", "when", "then", "step"}


@dataclass
class RemoteStepDef:
    """A step definition discovered from a remote OpenAPI spec."""
    pattern: str        # x-behave-pattern value
    endpoint: str       # URL path (e.g., /existing-todos)
    summary: str        # Human-readable summary
    timeout: int | None  # Per-step timeout override (ms), or None for default
    step_type: str = "given"  # behave step type: given, when, then, or step


@dataclass
class RemoteHookDef:
    """A lifecycle hook discovered from a remote OpenAPI spec."""
    hook_name: str  # e.g., "before_scenario"
    endpoint: str   # URL path (e.g., /hooks/before-scenario)


# Map well-known hook paths to hook names
HOOK_PATHS = {
    "/hooks/before-all": "before_all",
    "/hooks/after-all": "after_all",
    "/hooks/before-feature": "before_feature",
    "/hooks/after-feature": "after_feature",
    "/hooks/before-scenario": "before_scenario",
    "/hooks/after-scenario": "after_scenario",
    "/hooks/before-step": "before_step",
    "/hooks/after-step": "after_step",
}


def discover_all(server: ServerConfig) -> tuple[list[RemoteStepDef], list[RemoteHookDef]]:
    """Fetch the spec once and return both steps and hooks."""
    spec = _fetch_spec(server.url)
    return _extract_steps(spec), _extract_hooks(spec)


def discover_steps(server: ServerConfig) -> list[RemoteStepDef]:
    """Fetch and parse an OpenAPI spec, returning discovered step definitions."""
    steps, _ = discover_all(server)
    return steps


def discover_hooks(server: ServerConfig) -> list[RemoteHookDef]:
    """Fetch and parse an OpenAPI spec, returning discovered hook endpoints."""
    _, hooks = discover_all(server)
    return hooks


def _fetch_spec(url: str) -> dict:
    """Fetch an OpenAPI spec from a URL."""
    resp = requests.get(url, timeout=10)
    resp.raise_for_status()
    return yaml.safe_load(resp.text)


def _extract_steps(spec: dict) -> list[RemoteStepDef]:
    """Extract step definitions from operations with x-behave-pattern."""
    steps = []
    for path, path_item in spec.get("paths", {}).items():
        for method, operation in path_item.items():
            if not isinstance(operation, dict):
                continue
            pattern = operation.get("x-behave-pattern")
            if pattern:
                raw_type = operation.get("x-behave-step-type", "given")
                step_type = raw_type.lower() if isinstance(raw_type, str) else "given"
                if step_type not in VALID_STEP_TYPES:
                    step_type = "given"
                steps.append(RemoteStepDef(
                    pattern=pattern,
                    endpoint=path,
                    summary=operation.get("summary", ""),
                    timeout=operation.get("x-behave-timeout"),
                    step_type=step_type,
                ))
    return steps


def _extract_hooks(spec: dict) -> list[RemoteHookDef]:
    """Extract lifecycle hooks from well-known paths."""
    hooks = []
    paths = spec.get("paths", {})
    for hook_path, hook_name in HOOK_PATHS.items():
        if hook_path in paths:
            hooks.append(RemoteHookDef(hook_name=hook_name, endpoint=hook_path))
    return hooks

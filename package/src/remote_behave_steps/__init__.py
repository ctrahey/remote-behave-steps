"""Remote Behave Steps - Distributed BDD testing with remote step providers.

Usage — pick the style that fits your project:

1. Auto-register from pyproject.toml (one-liner, no function call):

    # features/steps/remote.py
    import remote_behave_steps.auto

2. Explicit call, config from pyproject.toml (linter-friendly):

    # features/steps/remote.py
    from remote_behave_steps import register_remote_steps
    register_remote_steps()

3. Fully programmatic (dynamic URLs, multiple environments, etc.):

    # features/steps/remote.py
    from remote_behave_steps import register_remote_steps
    register_remote_steps(servers=[{"name": "my-service", "url": my_url}])

All three read [tool.remote_behave_steps] from pyproject.toml when server
config is not provided programmatically. No environment.py is needed.

To optionally forward lifecycle hooks to remote services:

    # features/environment.py
    from remote_behave_steps import hooks

    def before_scenario(context, scenario):
        hooks.before_scenario(context, scenario)

    def after_scenario(context, scenario):
        hooks.after_scenario(context, scenario)
"""

import uuid

from behave import given as behave_given
from behave import step as behave_step
from behave import then as behave_then
from behave import use_step_matcher
from behave import when as behave_when

from remote_behave_steps.cache import StepCache
from remote_behave_steps.client import RemoteStepClient, RemoteStepError
from remote_behave_steps.config import load_config
from remote_behave_steps.context_builder import build_hook_context, build_step_context
from remote_behave_steps.discovery import discover_all

__all__ = [
    "register_remote_steps",
    "hooks",
    "RemoteStepError",
]


class _Registry:
    """Consolidated module-level state, resettable for testing."""

    def __init__(self):
        self.client = None
        self.config = None
        self.server_hooks = {}  # {hook_name: [(server, endpoint), ...]}


_registry = _Registry()


def _ensure_context_ready(context):
    """Lazily initialize remote steps state on the behave context.

    Called automatically before the first remote step or hook fires.
    Sets up run_id, performs health checks.
    Uses _set_root_attribute so values persist across scenario boundaries.

    Note: behave's Context.__getattr__ skips the stack walk for underscore-
    prefixed attributes, so all root attributes use public names.
    """
    if getattr(context, "remote_steps_initialized", False):
        return
    context._set_root_attribute("remote_steps_initialized", True)
    context._set_root_attribute("remote_steps_run_id", str(uuid.uuid4()))
    context._set_root_attribute("remote_steps_scenario_id", None)
    context.remote_data = {}

    if _registry.client and _registry.config:
        for server in _registry.config.servers:
            _registry.client.health_check(server)


def _ensure_scenario_reset(context):
    """Reset remote state when we enter a new scenario."""
    _ensure_context_ready(context)

    scenario = getattr(context, "scenario", None)
    current_id = id(scenario) if scenario else None

    if current_id == getattr(context, "remote_steps_scenario_id", None):
        return  # Already reset for this scenario
    context._set_root_attribute("remote_steps_scenario_id", current_id)
    context.remote_data = {}


_STEP_DECORATORS = {
    "given": behave_given,
    "when": behave_when,
    "then": behave_then,
    "step": behave_step,
}


def register_remote_steps(servers=None, cache_ttl=None):
    """Register remote steps with behave's step registry.

    Call this from a step definition file (e.g., features/steps/remote.py).

    Args:
        servers: Server config in any of these forms (or None to read pyproject.toml):
                 - A single URL string: "http://localhost:8080/openapi.yaml"
                 - A list of URL strings: ["http://host1/spec.yaml", ...]
                 - A list of dicts with 'url' and optional 'name'/'timeout' keys
        cache_ttl: Optional cache TTL override in seconds.
    """
    if isinstance(servers, str):
        servers = [{"url": servers}]
    elif isinstance(servers, list) and servers and isinstance(servers[0], str):
        servers = [{"url": s} for s in servers]
    config = load_config(servers=servers, cache_ttl=cache_ttl)
    cache = StepCache(config.cache_ttl)

    _registry.config = config
    _registry.client = RemoteStepClient()
    _registry.server_hooks = {}

    use_step_matcher("parse")

    for server in config.servers:
        # _discovered is shared between _fetch_steps and the cache-miss branch below.
        # On cache miss, get_or_fetch calls _fetch_steps which populates _discovered["hooks"].
        # On cache hit, _discovered stays empty and we fetch hooks separately.
        # The default arg `s=server` captures the current loop variable by value.
        _discovered = {}

        def _fetch_steps(s=server, _disc=_discovered):
            steps, hooks = discover_all(s)
            _disc["hooks"] = hooks
            return steps

        step_defs = cache.get_or_fetch(server, _fetch_steps)
        if "hooks" not in _discovered:
            _, hook_defs = discover_all(server)
        else:
            hook_defs = _discovered["hooks"]

        for step_def in step_defs:
            func = _make_step_function(_registry.client, server, step_def)
            func.__doc__ = f"[Remote: {server.name}] {step_def.summary}"
            func.__name__ = f"remote_{step_def.endpoint.strip('/').replace('/', '_')}"
            decorator = _STEP_DECORATORS[step_def.step_type]
            decorator(step_def.pattern)(func)

        for hook_def in hook_defs:
            _registry.server_hooks.setdefault(hook_def.hook_name, []).append(
                (server, hook_def.endpoint)
            )


def _make_step_function(client, server, step_def):
    """Create a behave step function that calls the remote endpoint."""

    def step_function(context, **kwargs):
        _ensure_context_ready(context)
        _ensure_scenario_reset(context)

        step_context = build_step_context(context)
        inputs = dict(kwargs)

        if context.table:
            inputs["table"] = {
                "headings": list(context.table.headings),
                "rows": [list(row.cells) for row in context.table.rows],
            }
        if context.text:
            inputs["text"] = context.text

        response = client.invoke_step(server, step_def, step_context, inputs)

        if response.get("data"):
            context.remote_data.update(response["data"])

    return step_function


class _Hooks:
    """Optional behave lifecycle hook handlers.

    Only needed if you want to forward lifecycle events to remote services.
    The core step invocation works without any environment.py wiring.
    """

    def before_all(self, context):
        _ensure_context_ready(context)
        self._fire_hook("before_all", context)

    def after_all(self, context):
        self._fire_hook("after_all", context)

    def before_feature(self, context, feature):
        if "remote_hooks" not in feature.tags:
            return
        self._fire_hook("before_feature", context, feature=feature)

    def after_feature(self, context, feature):
        if "remote_hooks" not in feature.tags:
            return
        self._fire_hook("after_feature", context, feature=feature)

    def before_scenario(self, context, scenario):
        _ensure_context_ready(context)
        _ensure_scenario_reset(context)
        if not self._should_fire_hook(context, scenario=scenario):
            return
        self._fire_hook("before_scenario", context, scenario=scenario)

    def after_scenario(self, context, scenario):
        if not self._should_fire_hook(context, scenario=scenario):
            return
        self._fire_hook("after_scenario", context, scenario=scenario)

    def before_step(self, context, step):
        context._remote_current_step = step
        if not self._should_fire_hook(context):
            return
        self._fire_hook("before_step", context, step=step)

    def after_step(self, context, step):
        if not self._should_fire_hook(context):
            return
        self._fire_hook("after_step", context, step=step)

    @staticmethod
    def _should_fire_hook(context, scenario=None) -> bool:
        """Check if the 'remote_hooks' tag is present on the scenario or feature."""
        all_tags = set()
        if scenario is not None:
            all_tags |= set(scenario.tags)
        elif hasattr(context, "scenario") and context.scenario:
            all_tags |= set(context.scenario.tags)
        if hasattr(context, "feature") and context.feature:
            all_tags |= set(context.feature.tags)
        return "remote_hooks" in all_tags

    def _fire_hook(self, hook_name, context, **kwargs):
        if not _registry.client:
            return
        entries = _registry.server_hooks.get(hook_name, [])
        for server, endpoint in entries:
            payload = build_hook_context(context, hook_name, **kwargs)
            _registry.client.invoke_hook(server, endpoint, payload)


hooks = _Hooks()

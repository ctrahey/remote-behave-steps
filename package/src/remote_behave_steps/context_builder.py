"""Build request payloads from behave context objects."""

import uuid
from datetime import datetime, timezone


def build_step_context(context) -> dict:
    """Build a StepExecutionContext dict from a behave Context during step execution."""
    run_id = getattr(context, "remote_steps_run_id", None) or str(uuid.uuid4())

    ctx = {"run_id": run_id, "timestamp": datetime.now(timezone.utc).isoformat()}

    if hasattr(context, "feature") and context.feature:
        feature = context.feature
        ctx["feature"] = {
            "name": feature.name,
            "file": str(feature.filename),
            "tags": list(feature.tags),
        }

    if hasattr(context, "scenario") and context.scenario:
        scenario = context.scenario
        # Generate a stable scenario id from run_id + scenario name
        scenario_id = str(uuid.uuid5(uuid.UUID(run_id), scenario.name))
        ctx["scenario"] = {
            "name": scenario.name,
            "id": scenario_id,
            "tags": list(scenario.tags),
        }

    # Step info from before_step hook if available
    current_step = getattr(context, "_remote_current_step", None)
    if current_step:
        ctx["step"] = {
            "text": current_step.name,
            "id": str(uuid.uuid4()),
        }

    return ctx


def build_hook_context(context, hook_name: str, **kwargs) -> dict:
    """Build a hook request payload from behave context."""
    run_id = getattr(context, "remote_steps_run_id", None) or str(uuid.uuid4())
    payload = {"run_id": run_id, "timestamp": datetime.now(timezone.utc).isoformat()}

    # Feature-level hooks
    feature = kwargs.get("feature") or getattr(context, "feature", None)
    if feature and hook_name in (
        "before_feature",
        "after_feature",
        "before_scenario",
        "after_scenario",
        "before_step",
        "after_step",
    ):
        payload["feature"] = {
            "name": feature.name,
            "file": str(feature.filename),
            "tags": list(feature.tags),
        }

    # Scenario-level hooks
    scenario = kwargs.get("scenario") or getattr(context, "scenario", None)
    if scenario and hook_name in (
        "before_scenario",
        "after_scenario",
        "before_step",
        "after_step",
    ):
        scenario_id = str(uuid.uuid5(uuid.UUID(run_id), scenario.name))
        payload["scenario"] = {
            "name": scenario.name,
            "id": scenario_id,
            "tags": list(scenario.tags),
        }

    # Step-level hooks
    step = kwargs.get("step")
    if step and hook_name in ("before_step", "after_step"):
        payload["step"] = {
            "keyword": step.keyword,
            "text": step.name,
            "id": str(uuid.uuid4()),
        }

    return payload

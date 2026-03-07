"""Behave environment hooks wiring for the simple example project."""

from remote_behave_steps import hooks


def before_scenario(context, scenario):
    hooks.before_scenario(context, scenario)


def after_scenario(context, scenario):
    hooks.after_scenario(context, scenario)

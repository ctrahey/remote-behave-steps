"""Behave environment hooks for integration tests.

Note: environment.py is NOT required for basic remote step invocation.
The library handles initialization, health checks, and per-scenario resets
automatically. Only wire up hooks here if you want to forward lifecycle
events to remote services.
"""

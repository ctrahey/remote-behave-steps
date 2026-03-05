"""Auto-register remote steps from pyproject.toml configuration.

Import this module from a behave step file to automatically discover
and register all remote steps. No function calls needed — the import
itself triggers registration.

    # features/steps/remote.py
    import remote_behave_steps.auto

This reads server configuration from your pyproject.toml:

    [tool.remote_behave_steps]
    cache_ttl = 300

    [[tool.remote_behave_steps.servers]]
    name = "my-service"
    url = "http://localhost:8080/openapi.yaml"

For programmatic configuration (dynamic URLs, multiple environments, etc.),
use register_remote_steps() directly instead:

    from remote_behave_steps import register_remote_steps
    register_remote_steps(servers=[{"name": "my-service", "url": my_url}])
"""

from remote_behave_steps import register_remote_steps

register_remote_steps()

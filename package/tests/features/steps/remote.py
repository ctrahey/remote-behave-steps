"""Register remote steps from the test server.

This file is loaded by behave during step discovery. The server URL
is set via the REMOTE_STEPS_SERVER environment variable (set by conftest.py).
"""

import os
from remote_behave_steps import register_remote_steps

server_url = os.environ.get("REMOTE_STEPS_SERVER", "http://localhost:9876/openapi.yaml")

register_remote_steps(servers=server_url, cache_ttl=0)

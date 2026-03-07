"""Register remote steps using programmatic configuration.

Unlike the simple example (which uses `import remote_behave_steps.auto`),
this demonstrates explicit registration with a URL string, which exercises
the string-to-list normalization path in the library.
"""

import os
from remote_behave_steps import register_remote_steps

server_url = os.environ.get("CATALOG_SERVICE_SPEC", "http://localhost:9877/openapi.yaml")

register_remote_steps(servers=server_url, cache_ttl=60)

"""HTTP client for remote step invocation and lifecycle hooks."""

import logging
import requests

from remote_behave_steps.config import ServerConfig
from remote_behave_steps.discovery import RemoteStepDef

logger = logging.getLogger(__name__)


class RemoteStepError(Exception):
    """Raised when a remote step returns an error response."""
    def __init__(self, message, code=None, details=None):
        super().__init__(message)
        self.code = code
        self.details = details


class RemoteStepClient:
    """HTTP client that invokes remote step endpoints."""

    def __init__(self, default_timeout: int = 30000):
        self.session = requests.Session()
        self.default_timeout = default_timeout

    def invoke_step(self, server: ServerConfig, step_def: RemoteStepDef,
                    context: dict, inputs: dict) -> dict:
        """Invoke a remote step endpoint and return the response data."""
        url = server.base_url + step_def.endpoint
        timeout_ms = step_def.timeout or server.timeout or self.default_timeout
        payload = {"context": context, "inputs": inputs}

        resp = self.session.put(url, json=payload, timeout=timeout_ms / 1000)

        if resp.status_code >= 500:
            raise RemoteStepError(
                f"Remote step infrastructure error: {resp.status_code} from {url}",
                code="INFRASTRUCTURE_ERROR",
            )

        body = resp.json() if resp.content else {}

        if resp.status_code >= 400:
            error = body.get("error", {})
            raise AssertionError(
                error.get("message", f"Remote step failed: {resp.status_code}")
            )

        if body.get("status") == "error":
            error = body.get("error", {})
            raise AssertionError(error.get("message", "Remote step returned error"))

        return body

    def invoke_hook(self, server: ServerConfig, endpoint: str, payload: dict):
        """Invoke a lifecycle hook endpoint."""
        url = server.base_url + endpoint
        timeout = server.timeout / 1000
        try:
            resp = self.session.put(url, json=payload, timeout=timeout)
            resp.raise_for_status()
        except requests.RequestException as exc:
            logger.debug("Hook %s on %s failed: %s", endpoint, server.name, exc)

    def health_check(self, server: ServerConfig, retries: int = 3):
        """Poll /healthz until the service is ready."""
        url = server.base_url + "/healthz"
        import time
        for attempt in range(retries):
            try:
                resp = self.session.get(url, timeout=5)
                if resp.status_code == 200:
                    return
            except requests.ConnectionError:
                pass
            if attempt < retries - 1:
                time.sleep(1)
        raise ConnectionError(f"Remote service {server.name} at {url} not healthy")

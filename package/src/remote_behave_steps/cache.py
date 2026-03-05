"""TTL-based file cache for discovered step definitions."""

import hashlib
import json
import time
from pathlib import Path

from remote_behave_steps.config import ServerConfig
from remote_behave_steps.discovery import RemoteStepDef


CACHE_DIR = Path.home() / ".cache" / "remote_behave_steps"


class StepCache:
    """Caches discovered step definitions with a configurable TTL."""

    def __init__(self, ttl: int):
        self.ttl = ttl
        CACHE_DIR.mkdir(parents=True, exist_ok=True)

    def get_or_fetch(self, server: ServerConfig, fetch_fn) -> list[RemoteStepDef]:
        """Return cached steps if fresh, otherwise call fetch_fn and cache the result."""
        cache_file = self._cache_path(server)

        if cache_file.exists():
            data = json.loads(cache_file.read_text())
            if time.time() - data["timestamp"] < self.ttl:
                return [RemoteStepDef(**s) for s in data["steps"]]

        steps = fetch_fn()
        self._write(cache_file, steps)
        return steps

    def invalidate(self, server: ServerConfig):
        """Remove cached data for a server."""
        path = self._cache_path(server)
        if path.exists():
            path.unlink()

    def _write(self, cache_file: Path, steps: list[RemoteStepDef]):
        data = {
            "timestamp": time.time(),
            "steps": [
                {"pattern": s.pattern, "endpoint": s.endpoint,
                 "summary": s.summary, "timeout": s.timeout}
                for s in steps
            ],
        }
        cache_file.write_text(json.dumps(data))

    def _cache_path(self, server: ServerConfig) -> Path:
        key = hashlib.sha256(server.url.encode()).hexdigest()[:16]
        return CACHE_DIR / f"{server.name}_{key}.json"

"""Configuration loading for remote_behave_steps.

Reads from pyproject.toml [tool.remote_behave_steps] or programmatic args.
"""

import sys
from dataclasses import dataclass, field
from pathlib import Path
from urllib.parse import urlparse

if sys.version_info >= (3, 11):
    import tomllib
else:
    try:
        import tomllib
    except ImportError:
        import tomli as tomllib  # type: ignore[no-redef]


DEFAULT_CACHE_TTL = 300  # seconds
DEFAULT_TIMEOUT = 30000  # milliseconds


def _name_from_url(url: str) -> str:
    """Derive a human-readable server name from a URL."""
    parsed = urlparse(url)
    host = parsed.hostname or "unknown"
    port = parsed.port
    return f"{host}:{port}" if port else host


@dataclass
class ServerConfig:
    url: str  # URL to the OpenAPI spec (YAML or JSON)
    name: str = ""  # Optional; derived from URL if not provided
    timeout: int = DEFAULT_TIMEOUT  # default step timeout in ms

    def __post_init__(self):
        if not self.name:
            self.name = _name_from_url(self.url)

    @property
    def base_url(self) -> str:
        """Derive the base URL (scheme://netloc) from the spec URL."""
        parsed = urlparse(self.url)
        return f"{parsed.scheme}://{parsed.netloc}"


@dataclass
class Config:
    servers: list[ServerConfig] = field(default_factory=list)
    cache_ttl: int = DEFAULT_CACHE_TTL


def load_config(servers=None, cache_ttl=None) -> Config:
    """Load configuration, with programmatic overrides taking precedence."""
    if servers is not None:
        server_configs = [
            ServerConfig(
                url=s["url"],
                name=s.get("name", ""),
                timeout=s.get("timeout", DEFAULT_TIMEOUT),
            )
            for s in servers
        ]
        return Config(
            servers=server_configs,
            cache_ttl=cache_ttl if cache_ttl is not None else DEFAULT_CACHE_TTL,
        )

    file_config = _load_from_files()
    if cache_ttl is not None:
        file_config.cache_ttl = cache_ttl
    return file_config


def _load_from_files() -> Config:
    """Search for config in pyproject.toml, setup.cfg, or behave.ini."""
    # Walk up from cwd looking for pyproject.toml
    for directory in [Path.cwd(), *Path.cwd().parents]:
        pyproject = directory / "pyproject.toml"
        if pyproject.exists():
            config = _read_pyproject(pyproject)
            if config is not None:
                return config

    return Config()


def _read_pyproject(path: Path) -> Config | None:
    """Read [tool.remote_behave_steps] from pyproject.toml."""
    with open(path, "rb") as f:
        data = tomllib.load(f)

    section = data.get("tool", {}).get("remote_behave_steps")
    if section is None:
        return None

    servers = []
    for s in section.get("servers", []):
        servers.append(
            ServerConfig(
                url=s["url"],
                name=s.get("name", ""),
                timeout=s.get("timeout", DEFAULT_TIMEOUT),
            )
        )

    return Config(
        servers=servers,
        cache_ttl=section.get("cache_ttl", DEFAULT_CACHE_TTL),
    )

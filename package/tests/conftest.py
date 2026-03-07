"""Pytest fixtures for integration tests."""

import os
import subprocess
import time

import pytest
import requests

CONTAINER_PORT = 8000


def _start_container(dockerfile_dir, image_name, container_name):
    """Build and start a Docker container, returning its spec URL."""
    subprocess.run(
        ["docker", "build", "-t", image_name, dockerfile_dir],
        check=True, capture_output=True,
    )

    subprocess.run(
        ["docker", "rm", "-f", container_name],
        capture_output=True,
    )

    subprocess.run(
        ["docker", "run", "-d", "--name", container_name,
         "-p", f"0:{CONTAINER_PORT}", image_name],
        check=True, capture_output=True,
    )

    result = subprocess.run(
        ["docker", "port", container_name, str(CONTAINER_PORT)],
        check=True, capture_output=True, text=True,
    )
    host_port = result.stdout.strip().split(":")[-1]
    base_url = f"http://127.0.0.1:{host_port}"

    for _ in range(50):
        try:
            resp = requests.get(f"{base_url}/healthz", timeout=1)
            if resp.status_code == 200:
                return f"{base_url}/openapi.yaml"
        except requests.ConnectionError:
            pass
        time.sleep(0.2)

    raise RuntimeError(f"Container {container_name} failed to start")


@pytest.fixture(scope="session")
def server_url():
    """Start the simple example's todo service."""
    dockerfile_dir = os.path.join(os.path.dirname(__file__), "example_simple", "server")
    spec_url = _start_container(dockerfile_dir, "rbs-test-simple", "rbs-test-simple")
    os.environ["REMOTE_STEPS_SERVER"] = spec_url
    yield spec_url
    os.environ.pop("REMOTE_STEPS_SERVER", None)
    subprocess.run(["docker", "rm", "-f", "rbs-test-simple"], capture_output=True)


@pytest.fixture(scope="session")
def full_server_url():
    """Start the full example's retail catalog service."""
    dockerfile_dir = os.path.join(os.path.dirname(__file__), "example_full", "server")
    spec_url = _start_container(dockerfile_dir, "rbs-test-full", "rbs-test-full")
    yield spec_url
    subprocess.run(["docker", "rm", "-f", "rbs-test-full"], capture_output=True)


@pytest.fixture(scope="session", autouse=True)
def start_servers(server_url, full_server_url):
    """Autouse wrapper so both servers start for every test session."""
    yield

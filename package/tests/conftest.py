"""Pytest fixtures for integration tests."""

import os
import subprocess
import time

import pytest
import requests


IMAGE_NAME = "remote-behave-steps-test-server"
CONTAINER_NAME = "remote-behave-steps-test"
CONTAINER_PORT = 8000


@pytest.fixture(scope="session")
def server_url():
    """Build and run the test server in a Docker container."""
    dockerfile_dir = os.path.join(os.path.dirname(__file__), "example_project", "server")

    # Build the image
    subprocess.run(
        ["docker", "build", "-t", IMAGE_NAME, dockerfile_dir],
        check=True, capture_output=True,
    )

    # Remove any leftover container from a previous run
    subprocess.run(
        ["docker", "rm", "-f", CONTAINER_NAME],
        capture_output=True,
    )

    # Run with a dynamic host port
    subprocess.run(
        ["docker", "run", "-d", "--name", CONTAINER_NAME,
         "-p", f"0:{CONTAINER_PORT}", IMAGE_NAME],
        check=True, capture_output=True,
    )

    try:
        # Discover the mapped host port
        result = subprocess.run(
            ["docker", "port", CONTAINER_NAME, str(CONTAINER_PORT)],
            check=True, capture_output=True, text=True,
        )
        # Output like "0.0.0.0:55123" or ":::55123"
        host_port = result.stdout.strip().split(":")[-1]
        base_url = f"http://127.0.0.1:{host_port}"
        spec_url = f"{base_url}/openapi.yaml"

        # Poll until the server is ready
        for _ in range(50):
            try:
                resp = requests.get(f"{base_url}/healthz", timeout=1)
                if resp.status_code == 200:
                    break
            except requests.ConnectionError:
                pass
            time.sleep(0.2)
        else:
            raise RuntimeError("Test server container failed to start")

        os.environ["REMOTE_STEPS_SERVER"] = spec_url
        yield spec_url
    finally:
        os.environ.pop("REMOTE_STEPS_SERVER", None)
        subprocess.run(["docker", "rm", "-f", CONTAINER_NAME], capture_output=True)


@pytest.fixture(scope="session", autouse=True)
def start_server(server_url):
    """Autouse wrapper so the server starts for every test session."""
    yield

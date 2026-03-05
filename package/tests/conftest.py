"""Pytest fixtures for integration tests."""

import os
import threading
import time
import socket

import pytest
import requests


def _find_free_port():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


@pytest.fixture(scope="session")
def server_port():
    return _find_free_port()


@pytest.fixture(scope="session")
def server_url(server_port):
    return f"http://127.0.0.1:{server_port}/openapi.yaml"


@pytest.fixture(scope="session", autouse=True)
def start_server(server_port, server_url):
    """Start the Flask test server in a background thread."""
    from server.app import app

    thread = threading.Thread(
        target=lambda: app.run(
            host="127.0.0.1", port=server_port, use_reloader=False,
        ),
        daemon=True,
    )
    thread.start()

    # Wait for server to be ready
    base = server_url.rsplit("/", 1)[0]
    for _ in range(30):
        try:
            resp = requests.get(f"{base}/healthz", timeout=1)
            if resp.status_code == 200:
                break
        except requests.ConnectionError:
            pass
        time.sleep(0.1)
    else:
        raise RuntimeError("Test server failed to start")

    # Set env var so behave step files can find the server
    os.environ["REMOTE_STEPS_SERVER"] = server_url
    yield
    os.environ.pop("REMOTE_STEPS_SERVER", None)

"""Integration tests: run behave against the test server."""

import subprocess
import sys
from pathlib import Path

FEATURES_DIR = Path(__file__).parent / "features"


def test_behave_scenarios_pass(server_url):
    """Run the full behave test suite against the remote steps server."""
    result = subprocess.run(
        [sys.executable, "-m", "behave", "--no-capture", str(FEATURES_DIR)],
        capture_output=True,
        text=True,
        timeout=60,
    )
    print(result.stdout)
    if result.stderr:
        print(result.stderr)
    assert result.returncode == 0, (
        f"Behave failed with exit code {result.returncode}\n"
        f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
    )


def test_steps_catalog_includes_remote_steps(server_url):
    """Verify remote steps appear in behave's step catalog."""
    result = subprocess.run(
        [sys.executable, "-m", "behave", "--steps-catalog", str(FEATURES_DIR)],
        capture_output=True,
        text=True,
        timeout=30,
    )
    print(result.stdout)
    # Check that our remote step patterns appear in the catalog
    assert "existing to-do items" in result.stdout, (
        f"Remote steps not found in catalog:\n{result.stdout}"
    )
    assert "to-do item titled" in result.stdout, (
        f"Remote steps not found in catalog:\n{result.stdout}"
    )
    assert "following to-do items exist" in result.stdout

"""End-to-end test of the full example project.

Exercises lifecycle hooks, programmatic registration, step context building,
cache hits, and error handling — features not covered by the simple example.
"""

import os
import shutil
import subprocess
from pathlib import Path

import pytest

EXAMPLE_DIR = Path(__file__).parent / "example_full"
PACKAGE_DIR = Path(__file__).parent.parent


@pytest.fixture(scope="module")
def full_project_dir(tmp_path_factory, full_server_url):
    """Copy the full example and patch it with the real server URL."""
    project_dir = tmp_path_factory.mktemp("project") / "example_full"
    shutil.copytree(EXAMPLE_DIR, project_dir)

    base_url = full_server_url.rsplit("/", 1)[0]

    # Patch remote.py with the actual server URL
    remote_steps = project_dir / "features" / "steps" / "remote.py"
    remote_steps.write_text(remote_steps.read_text().replace(
        "http://localhost:9877/openapi.yaml", full_server_url,
    ))

    # Patch verify_steps.py with the actual base URL
    verify_steps = project_dir / "features" / "steps" / "verify_steps.py"
    verify_steps.write_text(verify_steps.read_text().replace(
        "http://localhost:9877", base_url,
    ))

    # Set env var so the remote.py in the full example finds the right server
    os.environ["CATALOG_SERVICE_SPEC"] = full_server_url

    return project_dir


@pytest.fixture(scope="module")
def full_venv(tmp_path_factory, full_project_dir):
    """Create a venv and install deps for the full example."""
    venv_dir = tmp_path_factory.mktemp("full_venv")
    venv_python = venv_dir / "bin" / "python"

    subprocess.run(
        ["uv", "venv", str(venv_dir)],
        check=True, timeout=30,
    )

    subprocess.run(
        ["uv", "pip", "install", "--python", str(venv_python),
         str(PACKAGE_DIR), "requests", "coverage"],
        check=True, timeout=60,
    )

    return venv_python


def _run_behave(venv_python, project_dir, extra_args=None, feature_file=None):
    """Run behave under coverage in the full example project."""
    coverage_data = str(PACKAGE_DIR / ".coverage")

    target = str(project_dir / "features" / feature_file) if feature_file else str(project_dir / "features")

    cmd = [
        str(venv_python), "-m",
        "coverage", "run",
        "--source=remote_behave_steps",
        "--parallel-mode",
        "-m", "behave",
        target,
    ]
    if extra_args:
        cmd.extend(extra_args)

    return subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=60,
        cwd=str(project_dir),
        env={
            **os.environ,
            "COVERAGE_FILE": coverage_data,
        },
    )


def test_full_scenarios_pass(full_venv, full_project_dir):
    """Run the full example's behave scenarios with all hooks wired up."""
    result = _run_behave(full_venv, full_project_dir,
                         extra_args=["--no-capture"],
                         feature_file="catalog.feature")
    print(result.stdout)
    if result.stderr:
        print(result.stderr)
    assert result.returncode == 0, (
        f"Full example behave failed:\n"
        f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
    )


def test_full_steps_catalog(full_venv, full_project_dir):
    """Verify remote steps appear in the full example's step catalog."""
    result = _run_behave(full_venv, full_project_dir, ["--steps-catalog"])
    print(result.stdout)
    assert "catalog has" in result.stdout
    assert "product named" in result.stdout
    assert "following products exist" in result.stdout
    assert "category" in result.stdout


def test_error_500_infrastructure(full_venv, full_project_dir):
    """A step hitting a 500 should raise RemoteStepError."""
    result = _run_behave(full_venv, full_project_dir,
                         extra_args=["--no-capture", "--name",
                                     "Server returns 500"],
                         feature_file="errors.feature")
    print(result.stdout)
    assert result.returncode != 0
    assert "RemoteStepError" in result.stdout or "infrastructure error" in result.stdout.lower()


def test_error_422_validation(full_venv, full_project_dir):
    """A step hitting a 4xx should raise AssertionError with the error message."""
    result = _run_behave(full_venv, full_project_dir,
                         extra_args=["--no-capture", "--name",
                                     "Server returns 422"],
                         feature_file="errors.feature")
    print(result.stdout)
    assert result.returncode != 0
    assert "missing required field" in result.stdout


def test_error_logical(full_venv, full_project_dir):
    """A step returning status:'error' should raise AssertionError."""
    result = _run_behave(full_venv, full_project_dir,
                         extra_args=["--no-capture", "--name",
                                     "Server returns 200 with status error"],
                         feature_file="errors.feature")
    print(result.stdout)
    assert result.returncode != 0
    assert "category does not exist" in result.stdout

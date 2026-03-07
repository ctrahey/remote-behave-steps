"""End-to-end test of the example project.

Simulates the real user experience: creates a fresh venv, installs the
example project (which depends on remote_behave_steps), and runs behave.

Coverage is collected from the subprocess by running behave under
`coverage run` and combining the data back into the main process.
"""

import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

EXAMPLE_PROJECT_DIR = Path(__file__).parent / "example_project"
PACKAGE_DIR = Path(__file__).parent.parent  # The package root (has pyproject.toml)


@pytest.fixture(scope="module")
def example_project_dir(tmp_path_factory, server_url):
    """Copy the example project and patch it with the real server URL."""
    project_dir = tmp_path_factory.mktemp("project") / "example_project"
    shutil.copytree(EXAMPLE_PROJECT_DIR, project_dir)

    base_url = server_url.rsplit("/", 1)[0]

    # Patch pyproject.toml with the actual server URL
    pyproject = project_dir / "pyproject.toml"
    pyproject.write_text(pyproject.read_text().replace(
        "http://localhost:9876/openapi.yaml", server_url,
    ))

    # Patch verify_steps.py with the actual base URL
    verify_steps = project_dir / "features" / "steps" / "verify_steps.py"
    verify_steps.write_text(verify_steps.read_text().replace(
        "http://localhost:9876", base_url,
    ))

    return project_dir


@pytest.fixture(scope="module")
def example_venv(tmp_path_factory, example_project_dir):
    """Create a venv and install the example project's dependencies.

    Installs our local package source (instead of from PyPI) plus the
    example project's other deps (requests). This tests the real install
    path a user would follow.
    """
    venv_dir = tmp_path_factory.mktemp("example_venv")
    venv_python = venv_dir / "bin" / "python"

    subprocess.run(
        ["uv", "venv", str(venv_dir)],
        check=True, timeout=30,
    )

    # Install our local package source + the example's other deps.
    # coverage is needed so we can collect coverage from the subprocess.
    subprocess.run(
        ["uv", "pip", "install", "--python", str(venv_python),
         str(PACKAGE_DIR), "requests", "coverage"],
        check=True, timeout=60,
    )

    return venv_python


def _run_behave(example_venv, example_project_dir, extra_args=None):
    """Run behave in the example project using its isolated venv.

    Runs under `coverage run` so we can collect coverage data from the
    subprocess and combine it with the main pytest-cov report.
    """
    # Write coverage data into the package root so pytest-cov can find it
    coverage_data = str(PACKAGE_DIR / ".coverage")

    cmd = [
        str(example_venv), "-m",
        "coverage", "run",
        "--source=remote_behave_steps",
        "--parallel-mode",
        "-m", "behave",
        str(example_project_dir / "features"),
    ]
    if extra_args:
        cmd.extend(extra_args)

    return subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=60,
        cwd=str(example_project_dir),
        env={
            **os.environ,
            "COVERAGE_FILE": coverage_data,
        },
    )


def test_example_scenarios_pass(example_venv, example_project_dir):
    """Run the example project's behave scenarios in an isolated venv."""
    result = _run_behave(example_venv, example_project_dir, ["--no-capture"])
    print(result.stdout)
    if result.stderr:
        print(result.stderr)
    assert result.returncode == 0, (
        f"Example project behave failed:\n"
        f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
    )


def test_example_steps_catalog(example_venv, example_project_dir):
    """Verify remote steps appear in the example project's step catalog."""
    result = _run_behave(example_venv, example_project_dir, ["--steps-catalog"])
    print(result.stdout)
    assert "existing to-do items" in result.stdout, (
        f"Remote steps not found in catalog:\n{result.stdout}"
    )
    assert "to-do item titled" in result.stdout
    assert "following to-do items exist" in result.stdout

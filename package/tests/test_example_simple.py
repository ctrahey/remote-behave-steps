"""End-to-end test of the simple example project.

Simulates the real user experience: creates a fresh venv, installs the
example project (which depends on remote_behave_steps), and runs behave.

Coverage is collected from the subprocess by running behave under
`coverage run` and combining the data back into the main process.
"""

import os
import shutil
import subprocess
from pathlib import Path

import pytest

EXAMPLE_DIR = Path(__file__).parent / "example_simple"
PACKAGE_DIR = Path(__file__).parent.parent


@pytest.fixture(scope="module")
def simple_project_dir(tmp_path_factory, server_url):
    """Copy the example project and patch it with the real server URL."""
    project_dir = tmp_path_factory.mktemp("project") / "example_simple"
    shutil.copytree(EXAMPLE_DIR, project_dir)

    base_url = server_url.rsplit("/", 1)[0]

    pyproject = project_dir / "pyproject.toml"
    pyproject.write_text(pyproject.read_text().replace(
        "http://localhost:9876/openapi.yaml", server_url,
    ))

    verify_steps = project_dir / "features" / "steps" / "verify_steps.py"
    verify_steps.write_text(verify_steps.read_text().replace(
        "http://localhost:9876", base_url,
    ))

    return project_dir


@pytest.fixture(scope="module")
def simple_venv(tmp_path_factory, simple_project_dir):
    """Create a venv and install the example project's dependencies."""
    venv_dir = tmp_path_factory.mktemp("simple_venv")
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


def _run_behave(venv_python, project_dir, extra_args=None):
    """Run behave under coverage in the example project."""
    coverage_data = str(PACKAGE_DIR / ".coverage")

    cmd = [
        str(venv_python), "-m",
        "coverage", "run",
        "--source=remote_behave_steps",
        "--parallel-mode",
        "-m", "behave",
        str(project_dir / "features"),
    ]
    if extra_args:
        cmd.extend(extra_args)

    return subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=60,
        cwd=str(project_dir),
        env={**os.environ, "COVERAGE_FILE": coverage_data},
    )


def test_simple_scenarios_pass(simple_venv, simple_project_dir):
    """Run the simple example's behave scenarios."""
    result = _run_behave(simple_venv, simple_project_dir, ["--no-capture"])
    print(result.stdout)
    if result.stderr:
        print(result.stderr)
    assert result.returncode == 0, (
        f"Simple example behave failed:\n"
        f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
    )


def test_simple_steps_catalog(simple_venv, simple_project_dir):
    """Verify remote steps appear in the simple example's step catalog."""
    result = _run_behave(simple_venv, simple_project_dir, ["--steps-catalog"])
    print(result.stdout)
    assert "existing to-do items" in result.stdout
    assert "to-do item titled" in result.stdout
    assert "following to-do items exist" in result.stdout

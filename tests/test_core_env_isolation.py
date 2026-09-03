"""Core/extras isolation tests (ENV-05, T-01-10).

Permanent, fast, network-free proof that `course` imports cleanly in the
default (core + dev, no extras) synced environment, and that heavy or
credentialed packages (earthengine-api, geemap, geotessera, duckdb, torch)
stay out of that default environment. Each check runs `sys.executable` in a
subprocess rather than shelling out to `uv`, since pytest is already running
inside `uv run`'s own venv.

This file deliberately does NOT test that the `ee`/`providers` extras
*install* successfully — doing so on every pytest invocation would perform
large network installs and blow the phase's sub-fifteen-second sampling
budget. That half of the claim (extras install on demand and revert cleanly)
was proven once, manually, as this plan's task-level verification step; see
01-04-SUMMARY.md for the transcript.
"""

import subprocess
import sys

import pytest

HEAVY_OR_CREDENTIALED_MODULES = ["ee", "geemap", "geotessera", "duckdb", "torch"]


def _import_in_subprocess(module_name: str) -> subprocess.CompletedProcess:
    """Run `import {module_name}` in a fresh subprocess against sys.executable.

    Using sys.executable (not `uv run python`) ensures this exercises the
    exact interpreter/venv pytest itself is already running under.
    """
    return subprocess.run(
        [sys.executable, "-c", f"import {module_name}"],
        capture_output=True,
        text=True,
    )


def test_course_imports_in_default_environment():
    result = _import_in_subprocess("course")
    assert result.returncode == 0, (
        f"import course failed in the default environment: {result.stderr}"
    )


@pytest.mark.parametrize("module_name", HEAVY_OR_CREDENTIALED_MODULES)
def test_heavy_or_credentialed_packages_absent_by_default(module_name):
    result = _import_in_subprocess(module_name)
    assert result.returncode != 0, (
        f"import {module_name} unexpectedly succeeded in the default "
        f"(no-extras) environment; it must stay behind the ee/providers "
        f"optional-dependencies extra per ENV-05 / T-01-10"
    )

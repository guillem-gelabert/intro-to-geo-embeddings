"""Repo-wide headless-execution smoke test (EARLY-01..05).

For every `notebooks/solutions/*.ipynb` (excluding any `executed_*` output
artifact -- mirrors the Makefile's `execute-notebooks` discovery logic),
run it headlessly via nbclient and assert zero cells report an error
output. This is the aggregation point that would first catch a future
notebook edit silently reintroducing a network call or credential
dependency: it is intentionally NOT network-marked, so it runs in the
default `uv run pytest tests/` invocation.
"""

import pathlib

import nbformat
import pytest
from nbclient import NotebookClient

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
NOTEBOOKS_DIR = REPO_ROOT / "notebooks" / "solutions"


def _discover_solution_notebooks():
    if not NOTEBOOKS_DIR.is_dir():
        return []
    return sorted(
        p
        for p in NOTEBOOKS_DIR.glob("*.ipynb")
        if not p.name.startswith("executed_")
    )


NOTEBOOK_PATHS = _discover_solution_notebooks()
NOTEBOOK_IDS = [p.name for p in NOTEBOOK_PATHS]


@pytest.mark.parametrize("notebook_path", NOTEBOOK_PATHS, ids=NOTEBOOK_IDS)
def test_solution_notebook_executes_headlessly_with_no_errors(notebook_path):
    """Every solution notebook shipped so far runs end to end headlessly,
    with zero cell errors, within a 300-second timeout, and no network
    access beyond what the notebook already guards against (frozen/local
    data paths only)."""
    nb = nbformat.read(notebook_path, as_version=4)
    client = NotebookClient(
        nb,
        timeout=300,
        kernel_name="geo-embeddings-course",
        resources={"metadata": {"path": str(REPO_ROOT)}},
    )
    client.execute()

    for cell in nb.cells:
        for output in cell.get("outputs", []):
            assert output.get("output_type") != "error", (
                f"{notebook_path.name}: cell raised an error: {output}"
            )


def test_at_least_one_solution_notebook_was_discovered():
    """Guards against the parametrize list silently collapsing to zero
    (e.g. a NOTEBOOKS_DIR typo) and the test suite reporting a false
    green with no cases collected."""
    assert len(NOTEBOOK_PATHS) > 0, (
        f"no solution notebooks found under {NOTEBOOKS_DIR}"
    )

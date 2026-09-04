import pathlib
import subprocess

import nbformat

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
NOTEBOOK = REPO_ROOT / "notebooks/solutions/01_alphaearth_access_visualize.ipynb"
SUBPROCESS_TIMEOUT = 120


def test_path_a_never_executes():
    """Path A (Earth Engine) must be tagged skip-execution and must genuinely
    never run in a headless `jupyter execute` pass -- not merely "written to
    not raise". This proves the skip, it does not assume it."""
    result = subprocess.run(
        [
            "uv",
            "run",
            "jupyter",
            "execute",
            "--kernel_name=geo-embeddings-course",
            "--timeout=60",
            str(NOTEBOOK),
        ],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        timeout=SUBPROCESS_TIMEOUT,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr

    executed = nbformat.read(NOTEBOOK, as_version=4)

    skip_cells = [
        cell
        for cell in executed.cells
        if cell.get("cell_type") == "code"
        and "skip-execution" in cell.get("metadata", {}).get("tags", [])
    ]
    assert skip_cells, "expected at least one cell tagged skip-execution"

    for cell in skip_cells:
        assert cell.get("execution_count") is None, (
            "skip-execution cell was actually executed "
            f"(execution_count={cell.get('execution_count')!r})"
        )
        assert cell.get("outputs") == [], (
            "skip-execution cell produced outputs, proving it ran"
        )

    other_code_cells = [
        cell
        for cell in executed.cells
        if cell.get("cell_type") == "code"
        and "skip-execution" not in cell.get("metadata", {}).get("tags", [])
    ]
    for cell in other_code_cells:
        assert "ee.Initialize" not in cell.get("source", ""), (
            "ee.Initialize must only ever appear inside the skip-execution cell"
        )

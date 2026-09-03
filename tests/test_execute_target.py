import pathlib
import subprocess

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
SUBPROCESS_TIMEOUT = 120


def test_execute_notebooks_no_op_with_zero_notebooks(tmp_path):
    """`make execute-notebooks` against an empty NOTEBOOKS_DIR exits 0 and no-ops
    cleanly — this is the actual state of the real repo today (zero notebooks
    exist until Phase 3)."""
    result = subprocess.run(
        ["make", "execute-notebooks", f"NOTEBOOKS_DIR={tmp_path}"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        timeout=SUBPROCESS_TIMEOUT,
    )
    combined_output = result.stdout + result.stderr

    assert result.returncode == 0
    assert "No solution notebooks found yet" in combined_output


def test_execute_notebooks_fails_fast_on_first_error(write_notebook, tmp_path):
    """A notebook that raises must abort the recipe before any later-listed
    notebook executes. Proven here, not assumed: ok_notebook.ipynb's sentinel
    print must never appear in the captured output."""
    write_notebook(
        ["raise ValueError('distinctive synthetic failure for test_execute_target')"],
        filename="err_notebook.ipynb",
    )
    write_notebook(
        ["print('SENTINEL_OK')"],
        filename="ok_notebook.ipynb",
    )

    result = subprocess.run(
        ["make", "execute-notebooks", f"NOTEBOOKS_DIR={tmp_path}"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        timeout=SUBPROCESS_TIMEOUT,
    )
    combined_output = result.stdout + result.stderr

    assert result.returncode != 0
    assert "SENTINEL_OK" not in combined_output

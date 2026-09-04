import importlib.util
import pathlib

import nbformat
import pytest
from nbclient import NotebookClient

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
NOTEBOOK_PATH = (
    REPO_ROOT / "notebooks" / "solutions" / "00b_representation_inspection.ipynb"
)


def _execute_notebook():
    nb = nbformat.read(NOTEBOOK_PATH, as_version=4)
    client = NotebookClient(
        nb,
        timeout=60,
        kernel_name="geo-embeddings-course",
        resources={"metadata": {"path": str(REPO_ROOT)}},
    )
    client.execute()
    return nb


def _cell_outputs_text(cell):
    texts = []
    for output in cell.get("outputs", []):
        if "text" in output:
            texts.append(output["text"])
        elif "data" in output and "text/plain" in output["data"]:
            texts.append(output["data"]["text/plain"])
    return "\n".join(texts)


def _all_outputs_text(nb):
    return "\n".join(_cell_outputs_text(cell) for cell in nb.cells)


def test_representation_notebook_executes_headlessly_with_no_errors():
    """`00b_representation_inspection.ipynb` runs Restart & Run All headlessly,
    with zero cell errors, in under 60 seconds, using only the frozen
    AlphaEarth tables and the checked-in Clay fixture (no network)."""
    nb = _execute_notebook()
    for cell in nb.cells:
        for output in cell.get("outputs", []):
            assert output.get("output_type") != "error", (
                f"cell raised an error: {output}"
            )


def test_representation_notebook_degrades_gracefully_without_torch():
    """This project's default (core) environment has no torch installed, so
    the SatCLIP section's graceful-degrade branch must actually execute and
    print its skip message — proving the degrade path for real, not
    hypothetically."""
    if importlib.util.find_spec("torch") is not None:
        pytest.skip("torch is installed in this environment; degrade path not exercised")

    nb = _execute_notebook()
    text = _all_outputs_text(nb)
    assert "torch is not installed" in text


def test_representation_notebook_prints_comparison_table():
    """The side-by-side comparison table renders in some cell's stdout,
    naming both providers and their shape."""
    nb = _execute_notebook()
    text = _all_outputs_text(nb)
    assert "AlphaEarth" in text
    assert "Clay" in text
    assert "shape" in text

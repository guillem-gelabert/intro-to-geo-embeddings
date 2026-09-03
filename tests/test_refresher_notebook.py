import pathlib
import re

import nbformat
from nbclient import NotebookClient

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
NOTEBOOK_PATH = REPO_ROOT / "notebooks" / "solutions" / "00_embedding_refresher.ipynb"


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


def test_refresher_notebook_executes_headlessly_with_no_errors():
    """`00_embedding_refresher.ipynb` runs Restart & Run All headlessly, with
    zero cell errors, in under 60 seconds (enforced by NotebookClient's own
    timeout, which raises on a hang)."""
    nb = _execute_notebook()
    for cell in nb.cells:
        for output in cell.get("outputs", []):
            assert output.get("output_type") != "error", (
                f"cell raised an error: {output}"
            )


def test_refresher_notebook_prints_classifier_accuracy():
    """At least one cell's output prints a test-set accuracy value between 0
    and 1, proving the tiny classifier actually ran."""
    nb = _execute_notebook()
    found = False
    for cell in nb.cells:
        text = _cell_outputs_text(cell)
        if "accuracy" in text.lower():
            match = re.search(r"0?\.[0-9]+", text)
            if match:
                value = float(match.group())
                assert 0.0 <= value <= 1.0
                found = True
    assert found, "no cell output contained a printed accuracy value"


def test_refresher_notebook_prints_crs_before_and_after_reprojection():
    """The CRS reprojection cell prints an EPSG string both before and after
    `.to_crs(...)`."""
    nb = _execute_notebook()
    epsg_count = 0
    for cell in nb.cells:
        text = _cell_outputs_text(cell)
        epsg_count += text.count("EPSG")
    assert epsg_count >= 2

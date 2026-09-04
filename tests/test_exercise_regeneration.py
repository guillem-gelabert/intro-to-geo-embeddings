"""Regeneration and stub-boundary verification for derived exercise notebooks
(plan 06-06, EXER-01/EXER-05).

Group A: for each committed exercise notebook, regenerate it in-process from
its tagged solution notebook via `tools.derive_exercise.transform` and assert
the two are equivalent on `(source, tags)` per cell -- ignoring `outputs` and
`execution_count`, since nbstripout strips those from the committed file on
commit and jupytext re-serialization can touch cell ids/execution counts
without touching content.

Group B: run each committed exercise notebook headlessly with
`allow_errors=True` and assert every cell before the first stub executed
without an error, and the first stub cell's output is exactly a
`NotImplementedError` -- the expected passing state for a stub, not a
failure (T-06-13).
"""

import pathlib

import nbformat
import pytest
from nbclient import NotebookClient

from tools.derive_exercise import _load_appendix, transform

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
SOLUTIONS_DIR = REPO_ROOT / "notebooks" / "solutions"
EXERCISES_DIR = REPO_ROOT / "notebooks" / "exercises"
APPENDIX_PATH = REPO_ROOT / "tools" / "exercise_appendix.yaml"

NOTEBOOK_STEMS = [
    "00_embedding_refresher",
    "00b_representation_inspection",
    "01_alphaearth_access_visualize",
    "02_similarity_and_classification",
    "03_change_detection_and_validation",
    "04_embedding_ecosystems",
    "05_capstone_artificialization",
]


def _cell_signature(nb):
    """Return a comparable, nbstripout/output-agnostic view of a notebook's cells."""
    return [
        (cell.get("cell_type"), cell.get("source"), cell.get("metadata", {}).get("tags"))
        for cell in nb.cells
    ]


@pytest.mark.parametrize("stem", NOTEBOOK_STEMS)
def test_exercise_notebook_matches_fresh_regeneration(stem):
    """Regenerating `{stem}.ipynb` in-process from its tagged solution notebook
    reproduces the committed exercise notebook's cell content and tags exactly
    (EXER-01: byte-for-byte reproducible, compared nbstripout-aware)."""
    solution_path = SOLUTIONS_DIR / f"{stem}.ipynb"
    committed_path = EXERCISES_DIR / f"{stem}.ipynb"
    assert solution_path.exists(), f"missing solution notebook: {solution_path}"
    assert committed_path.exists(), f"missing committed exercise notebook: {committed_path}"

    solution_nb = nbformat.read(solution_path, as_version=4)
    appendix = _load_appendix(APPENDIX_PATH)
    freshly_generated = transform(solution_nb, appendix=appendix, slug=stem)

    committed_nb = nbformat.read(committed_path, as_version=4)

    assert _cell_signature(freshly_generated) == _cell_signature(committed_nb), (
        f"{stem}: regenerating from the solution notebook no longer matches "
        "the committed exercise notebook -- run `make exercises` and commit "
        "the result, or the generator/tags have drifted."
    )


def _first_stub_index(nb):
    for i, cell in enumerate(nb.cells):
        if cell.cell_type == "code" and "raise NotImplementedError" in cell.source:
            return i
    return None


@pytest.mark.parametrize("stem", NOTEBOOK_STEMS)
def test_exercise_notebook_executes_cleanly_to_first_stub(stem):
    """The committed exercise notebook runs headlessly with zero errors up to
    (and not including) its first stub cell, and the first stub cell's own
    output is a `NotImplementedError` -- the expected, passing outcome for a
    stub, never a test failure (EXER-05, T-06-13)."""
    notebook_path = EXERCISES_DIR / f"{stem}.ipynb"
    assert notebook_path.exists(), f"missing committed exercise notebook: {notebook_path}"

    nb = nbformat.read(notebook_path, as_version=4)
    stub_index = _first_stub_index(nb)
    assert stub_index is not None, f"{stem}: no stub cell found (expected at least one task tag)"

    client = NotebookClient(
        nb,
        timeout=300,
        kernel_name="geo-embeddings-course",
        allow_errors=True,
        resources={"metadata": {"path": str(REPO_ROOT)}},
    )
    client.execute()

    for i, cell in enumerate(nb.cells):
        if cell.cell_type != "code":
            continue
        errors = [
            output
            for output in cell.get("outputs", [])
            if output.get("output_type") == "error"
        ]
        if i < stub_index:
            assert not errors, (
                f"{stem}: cell {i} (before first stub at {stub_index}) raised "
                f"an error: {errors}"
            )
        elif i == stub_index:
            assert errors, f"{stem}: expected the first stub cell to raise, but it did not"
            assert errors[0].get("ename") == "NotImplementedError", (
                f"{stem}: first stub cell raised {errors[0].get('ename')!r}, "
                "expected NotImplementedError"
            )
            break


def test_all_notebook_stems_have_committed_exercise_files():
    """Guards against NOTEBOOK_STEMS drifting out of sync with the seven
    solution notebooks actually shipped."""
    for stem in NOTEBOOK_STEMS:
        assert (EXERCISES_DIR / f"{stem}.ipynb").exists()
        assert (SOLUTIONS_DIR / f"{stem}.ipynb").exists()

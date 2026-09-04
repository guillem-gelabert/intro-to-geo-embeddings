"""Unit tests for the exercise-derivation generator (tools/derive_exercise.py).

Tests are built against an in-memory synthetic notebook (constructed with nbformat
helpers) rather than a real course notebook, per plan 06-01 instructions.
"""

import copy

import nbformat
import pytest
from nbformat.v4 import new_code_cell, new_markdown_cell, new_notebook

from tools.derive_exercise import transform

WHOLE_CELL_SOURCE = "x = 1\ny = 2\nprint(x + y)\n"

MARKER_CELL_SOURCE = (
    "pre_line = 'kept before'\n"
    "### BEGIN SOLUTION\n"
    "secret = 42\n"
    "### END SOLUTION\n"
    "post_line = 'kept after'\n"
)

CHECKPOINT_SOURCE = "assert 1 + 1 == 2\n"
SETUP_SOURCE = "import sys\n"
UNTAGGED_SOURCE = "print('untagged cell')\n"


def make_solution_notebook():
    nb = new_notebook()
    nb.cells.append(new_markdown_cell("# Sample Solution Notebook\n\nHeader text."))

    setup_cell = new_code_cell(SETUP_SOURCE)
    setup_cell.metadata["tags"] = ["setup"]
    nb.cells.append(setup_cell)

    whole_task_cell = new_code_cell(WHOLE_CELL_SOURCE)
    whole_task_cell.metadata["tags"] = ["task"]
    nb.cells.append(whole_task_cell)

    marker_task_cell = new_code_cell(MARKER_CELL_SOURCE)
    marker_task_cell.metadata["tags"] = ["task"]
    nb.cells.append(marker_task_cell)

    checkpoint_cell = new_code_cell(CHECKPOINT_SOURCE)
    checkpoint_cell.metadata["tags"] = ["checkpoint"]
    nb.cells.append(checkpoint_cell)

    hidden_cell = new_code_cell("secret_test = True\n")
    hidden_cell.metadata["tags"] = ["hidden"]
    nb.cells.append(hidden_cell)

    untagged_cell = new_code_cell(UNTAGGED_SOURCE)
    nb.cells.append(untagged_cell)

    return nb


@pytest.fixture
def solution_nb():
    return make_solution_notebook()


def test_cell_count_minus_hidden(solution_nb):
    original_count = len(solution_nb.cells)
    result = transform(copy.deepcopy(solution_nb))
    assert len(result.cells) == original_count - 1


def test_whole_cell_task_stub_replaces_body(solution_nb):
    result = transform(copy.deepcopy(solution_nb))
    task_cells = [
        c
        for c in result.cells
        if c.cell_type == "code" and "task" in c.metadata.get("tags", [])
    ]
    whole_cell = task_cells[0]
    assert "raise NotImplementedError" in whole_cell.source
    assert "x = 1" not in whole_cell.source
    assert "print(x + y)" not in whole_cell.source


def test_marker_task_cell_keeps_pre_post_lines(solution_nb):
    result = transform(copy.deepcopy(solution_nb))
    task_cells = [
        c
        for c in result.cells
        if c.cell_type == "code" and "task" in c.metadata.get("tags", [])
    ]
    marker_cell = task_cells[1]
    assert "pre_line = 'kept before'" in marker_cell.source
    assert "post_line = 'kept after'" in marker_cell.source
    assert "secret = 42" not in marker_cell.source
    assert "raise NotImplementedError" in marker_cell.source


def test_checkpoint_setup_untagged_byte_identical(solution_nb):
    original = copy.deepcopy(solution_nb)
    result = transform(copy.deepcopy(solution_nb))

    def find_by_tag_or_untagged(nb, predicate):
        return [c for c in nb.cells if predicate(c)]

    orig_setup = find_by_tag_or_untagged(
        original, lambda c: "setup" in c.metadata.get("tags", [])
    )[0]
    result_setup = find_by_tag_or_untagged(
        result, lambda c: "setup" in c.metadata.get("tags", [])
    )[0]
    assert orig_setup.source == result_setup.source

    orig_checkpoint = find_by_tag_or_untagged(
        original, lambda c: "checkpoint" in c.metadata.get("tags", [])
    )[0]
    result_checkpoint = find_by_tag_or_untagged(
        result, lambda c: "checkpoint" in c.metadata.get("tags", [])
    )[0]
    assert orig_checkpoint.source == result_checkpoint.source

    orig_untagged = find_by_tag_or_untagged(
        original,
        lambda c: c.cell_type == "code" and not c.metadata.get("tags"),
    )[0]
    result_untagged = find_by_tag_or_untagged(
        result,
        lambda c: c.cell_type == "code" and not c.metadata.get("tags"),
    )[0]
    assert orig_untagged.source == result_untagged.source


def test_hidden_cell_absent(solution_nb):
    result = transform(copy.deepcopy(solution_nb))
    hidden_cells = [
        c for c in result.cells if "hidden" in c.metadata.get("tags", [])
    ]
    assert hidden_cells == []
    for c in result.cells:
        assert "secret_test" not in c.source


def test_idempotent_transform(solution_nb):
    first = transform(copy.deepcopy(solution_nb))
    second = transform(copy.deepcopy(solution_nb))
    assert nbformat.writes(first) == nbformat.writes(second)


def test_appendix_injection_with_matching_key(solution_nb):
    appendix = {
        "sample_solution": {
            "reflection": ["Why does this matter?"],
            "stretch": ["Try a harder AOI."],
        }
    }
    result = transform(
        copy.deepcopy(solution_nb), appendix=appendix, slug="sample_solution"
    )
    last_two = result.cells[-2:]
    assert last_two[0].cell_type == "markdown"
    assert "## Reflection" in last_two[0].source
    assert "Why does this matter?" in last_two[0].source
    assert last_two[1].cell_type == "markdown"
    assert "## Stretch tasks" in last_two[1].source
    assert "Try a harder AOI." in last_two[1].source


def test_appendix_no_matching_key_warns_and_skips(solution_nb):
    appendix = {"other_notebook": {"reflection": ["x"], "stretch": ["y"]}}
    original_cell_count = len(solution_nb.cells) - 1  # minus hidden cell
    with pytest.warns(UserWarning):
        result = transform(
            copy.deepcopy(solution_nb), appendix=appendix, slug="sample_solution"
        )
    assert len(result.cells) == original_cell_count

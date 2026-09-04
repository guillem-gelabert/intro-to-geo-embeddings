"""Derive an exercise notebook from a tagged solution notebook.

Tag vocabulary (plan 06-01):
  - ``task``: cell code becomes a stub raising NotImplementedError. If the cell
    source contains a ``### BEGIN SOLUTION`` / ``### END SOLUTION`` marker pair
    (each on its own line), only the marked span is replaced; everything else in
    the cell is kept verbatim. If no markers are present, the whole cell body is
    replaced.
  - ``hidden``: cell is dropped entirely from the output notebook.
  - Any other tag (or no tag) and all markdown cells pass through unchanged.

This module never writes to the solution notebook path it reads from. The CLI
requires distinct solution/exercise paths and asserts they resolve to different
files before writing (T-06-01).

Usage:
    derive_exercise.py <solution.ipynb> <exercise.ipynb> [--appendix PATH]
"""

from __future__ import annotations

import argparse
import re
import sys
import warnings
from pathlib import Path

import nbformat
import yaml
from nbformat.v4 import new_markdown_cell

BEGIN_MARKER = "### BEGIN SOLUTION"
END_MARKER = "### END SOLUTION"

STUB_FALLBACK_COMMENT = "# TODO: implement this cell"
STUB_RAISE = (
    'raise NotImplementedError("Implement this cell — see the module\'s '
    'solution notebook if you get stuck.")'
)

DEFAULT_APPENDIX_PATH = Path("tools/exercise_appendix.yaml")


def _nearest_markdown_hint(cells: list, index: int) -> str:
    """Look backward from `index` for the nearest markdown cell text to seed a TODO comment."""
    for i in range(index - 1, -1, -1):
        cell = cells[i]
        if cell.cell_type == "markdown" and cell.source.strip():
            # Use the first non-empty line, stripped of markdown heading markers.
            for line in cell.source.splitlines():
                text = line.strip().lstrip("#").strip()
                if text:
                    return text
    return ""


def _stub_whole_cell(cells: list, index: int) -> str:
    hint = _nearest_markdown_hint(cells, index)
    comment = f"# TODO: {hint}" if hint else STUB_FALLBACK_COMMENT
    return f"{comment}\n{STUB_RAISE}\n"


def _stub_marker_span(source: str) -> str:
    lines = source.splitlines(keepends=True)
    begin_idx = None
    end_idx = None
    for i, line in enumerate(lines):
        if line.strip() == BEGIN_MARKER and begin_idx is None:
            begin_idx = i
        elif line.strip() == END_MARKER and begin_idx is not None and end_idx is None:
            end_idx = i
            break

    if begin_idx is None or end_idx is None:
        return None  # no complete marker pair found

    pre = "".join(lines[:begin_idx])
    post = "".join(lines[end_idx + 1 :])
    stub = f"{STUB_FALLBACK_COMMENT}\n{STUB_RAISE}\n"
    return f"{pre}{stub}{post}"


def _has_marker_pair(source: str) -> bool:
    return bool(
        re.search(rf"^{re.escape(BEGIN_MARKER)}$", source, re.MULTILINE)
        and re.search(rf"^{re.escape(END_MARKER)}$", source, re.MULTILINE)
    )


def _solution_link_source(slug: str) -> str:
    return (
        "<details>\n"
        "<summary>Show solution</summary>\n\n"
        f"See <code>notebooks/solutions/{slug}.ipynb</code> — the same section, just "
        "above this point in the notebook.\n"
        "</details>"
    )


def transform(nb, appendix: dict | None = None, slug: str = ""):
    """Return a new notebook derived from `nb` per the task/hidden tag vocabulary.

    `nb` is mutated in place cell-list-wise but this function is intended to be
    called on a copy the caller owns; the CLI always reads a fresh NotebookNode
    from disk so the on-disk solution file is never touched.
    """
    new_cells = []
    original_cells = list(nb.cells)

    for i, cell in enumerate(original_cells):
        tags = cell.metadata.get("tags", []) if hasattr(cell, "metadata") else []

        if "hidden" in tags:
            continue

        whole_cell_stub = False
        if cell.cell_type == "code" and "task" in tags:
            if _has_marker_pair(cell.source):
                new_source = _stub_marker_span(cell.source)
            else:
                new_source = _stub_whole_cell(original_cells, i)
                whole_cell_stub = True
            cell.source = new_source

        new_cells.append(cell)

        if whole_cell_stub:
            link_id = f"solution-link-{slug}-{i}" if slug else f"solution-link-{i}"
            new_cells.append(
                new_markdown_cell(_solution_link_source(slug), id=link_id)
            )

    nb.cells = new_cells

    if appendix is not None:
        entry = appendix.get(slug)
        if entry is None:
            warnings.warn(
                f"No appendix entry found for slug '{slug}'; skipping appendix injection.",
                UserWarning,
                stacklevel=2,
            )
        else:
            reflection_items = entry.get("reflection", []) or []
            stretch_items = entry.get("stretch", []) or []

            reflection_source = "## Reflection\n\n" + "\n".join(
                f"- {item}" for item in reflection_items
            )
            stretch_source = "## Stretch tasks\n\n" + "\n".join(
                f"- {item}" for item in stretch_items
            )

            nb.cells.append(new_markdown_cell(reflection_source))
            nb.cells.append(new_markdown_cell(stretch_source))

    return nb


def _load_appendix(path: Path) -> dict:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return data or {}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Derive an exercise notebook from a tagged solution notebook."
    )
    parser.add_argument("solution_path", type=Path)
    parser.add_argument("exercise_path", type=Path)
    parser.add_argument(
        "--appendix",
        type=Path,
        default=DEFAULT_APPENDIX_PATH,
        help="Path to the exercise_appendix.yaml schema file.",
    )
    args = parser.parse_args(argv)

    solution_resolved = args.solution_path.resolve()
    exercise_resolved = args.exercise_path.resolve()
    if solution_resolved == exercise_resolved:
        print(
            "Error: solution_path and exercise_path must be different files.",
            file=sys.stderr,
        )
        return 1

    try:
        nb = nbformat.read(args.solution_path, as_version=4)
    except Exception as exc:  # noqa: BLE001
        print(f"Error reading solution notebook: {exc}", file=sys.stderr)
        return 1

    slug = args.solution_path.stem
    appendix = _load_appendix(args.appendix)

    result = transform(nb, appendix=appendix, slug=slug)

    try:
        nbformat.validate(result)
    except Exception as exc:  # noqa: BLE001
        print(f"Error: transformed notebook failed validation: {exc}", file=sys.stderr)
        return 1

    nbformat.write(result, args.exercise_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

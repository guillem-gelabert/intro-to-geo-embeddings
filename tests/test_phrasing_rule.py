"""EARLY-05 phrasing-rule enforcement.

A fast, dependency-free regex scan of the jupytext plain-text source for
`01_alphaearth_access_visualize.py`. No notebook execution needed: this test
reads the file as text.

Rule: every caption/Takeaway must say a component/axis *separates* landscape
types *in this sample*, never that it *measures*/*represents*/*is* a physical
quantity (PITFALLS.md Pitfall 8).
"""

import pathlib
import re

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
SOURCE = REPO_ROOT / "notebooks/solutions/01_alphaearth_access_visualize.py"

FORBIDDEN_PATTERN = re.compile(r"component\s+\d+\s+(measures|represents|is)\b", re.IGNORECASE)
REQUIRED_PATTERN = re.compile(r"separates .+ in this sample", re.IGNORECASE)

# Jupytext py:percent cell-boundary markers look like `# %%` or
# `# %% tags=["solution"]` -- these are NOT prose and must be excluded.
# Markdown-cell prose (`# %% [markdown]` cells) is still `#`-prefixed line by
# line, e.g. `# This component separates ...`, and MUST be included -- so the
# filter targets only the marker line itself, not every `#`-prefixed line.
CELL_MARKER_PATTERN = re.compile(r"^#\s*%%")


def _prose_lines(text: str) -> list[str]:
    return [line for line in text.splitlines() if not CELL_MARKER_PATTERN.match(line)]


def test_no_forbidden_phrasing_in_notebook_source():
    text = SOURCE.read_text()
    prose = "\n".join(_prose_lines(text))
    matches = FORBIDDEN_PATTERN.findall(prose)
    assert not matches, (
        f"found forbidden 'component N measures/represents/is' phrasing: {matches}. "
        "Use 'this component separates X from Y in this sample' instead "
        "(PITFALLS.md Pitfall 8)."
    )


def test_required_phrasing_present_in_notebook_source():
    text = SOURCE.read_text()
    prose = "\n".join(_prose_lines(text))
    assert REQUIRED_PATTERN.search(prose), (
        "expected at least one 'separates ... in this sample' caption/Takeaway "
        "enforcing the EARLY-05 phrasing rule"
    )


def test_cell_marker_filter_does_not_strip_markdown_prose():
    """Regression guard: the marker filter must exclude `# %%` boundary lines
    specifically, not every `#`-prefixed line -- otherwise it would silently
    strip the markdown-cell prose this test exists to check."""
    sample = "\n".join(
        [
            "# %% [markdown]",
            "# this component separates built-up from vegetated areas in this sample",
            "# %% tags=[\"solution\"]",
            "some_code = 1",
        ]
    )
    prose = _prose_lines(sample)
    assert any("separates" in line for line in prose)
    assert not any(line.strip().startswith("# %%") for line in prose)

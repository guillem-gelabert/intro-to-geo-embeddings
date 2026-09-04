"""Tests for tools/verify_narration_scripts.py (plan 08-01).

Written before the implementation (TDD RED). Uses tmp_path fixtures and the
real notebooks/solutions/02_similarity_and_classification.py source so the
heading-extraction test exercises real content, per the plan's interfaces
section. Does not depend on scripts/ existing yet (Wave 2 has not run).
"""

from __future__ import annotations

from pathlib import Path

import pytest

from tools.verify_narration_scripts import (
    GRAND_TOTAL_MINUTES,
    KEY_MESSAGES,
    MODULE_MINUTES,
    MissingAnchor,
    check_anchors_exist,
    check_grand_total,
    check_key_messages,
    check_lecture_durations,
    check_module_total,
    extract_notebook_headings,
    parse_script_anchors,
)

REPO_ROOT = Path(__file__).resolve().parent.parent
REAL_NOTEBOOK = REPO_ROOT / "notebooks" / "solutions" / "02_similarity_and_classification.py"


def test_module_minutes_sum_to_grand_total():
    assert sum(MODULE_MINUTES.values()) == GRAND_TOTAL_MINUTES == 360


def test_extract_notebook_headings_real_file():
    headings = extract_notebook_headings(REAL_NOTEBOOK)
    for expected in ("Data", "Similarity 1: Search by example", "Why this is wrong", "Wrap-up"):
        assert expected in headings
    assert "Nonexistent Heading" not in headings


FIXTURE_SCRIPT_TWO_ROWS = """\
### Lecture 03.1 — Search by example

Objective: intro similarity search.

| Duration | Cumulative | VISUAL | AUDIO | Cue |
|---|---|---|---|---|
| 01:00 | 01:00 | [CELL] 02_similarity_and_classification.ipynb § "Data" | Here is the data. | [NONE] |
| 00:30 | 01:30 | [SLIDE] 03_similarity_classification.md #3 | Now the slide. | [ZOOM] |

Recap: we searched by example.
End-state: similarity table on screen.
"""


def test_parse_script_anchors_distinguishes_cell_and_slide():
    anchors = parse_script_anchors(FIXTURE_SCRIPT_TWO_ROWS)
    assert len(anchors) == 2
    cell_anchor = [a for a in anchors if a.kind == "cell"][0]
    slide_anchor = [a for a in anchors if a.kind == "slide"][0]
    assert cell_anchor.notebook_stem == "02_similarity_and_classification"
    assert cell_anchor.heading == "Data"
    assert slide_anchor.deck_stem == "03_similarity_classification"
    assert slide_anchor.number == 3


FIXTURE_SCRIPT_BROKEN_ANCHOR = """\
### Lecture 03.1 — Search by example

| Duration | Cumulative | VISUAL | AUDIO | Cue |
|---|---|---|---|---|
| 01:00 | 01:00 | [CELL] 02_similarity_and_classification.ipynb § "Nonexistent Heading" | Bad anchor. | [NONE] |
"""


def test_check_anchors_exist_raises_on_missing_heading():
    anchors = parse_script_anchors(FIXTURE_SCRIPT_BROKEN_ANCHOR)
    with pytest.raises(MissingAnchor) as excinfo:
        check_anchors_exist(anchors, script_name="03_similarity_classification_SCRIPT.md", notebooks_dir=REPO_ROOT / "notebooks" / "solutions")
    err = excinfo.value
    assert err.script_name == "03_similarity_classification_SCRIPT.md"
    assert err.heading == "Nonexistent Heading"


def test_check_anchors_exist_passes_on_real_heading():
    anchors = parse_script_anchors(FIXTURE_SCRIPT_TWO_ROWS)
    # Should not raise -- both the cell heading and (unresolvable) slide anchor are tolerated.
    check_anchors_exist(anchors, script_name="03_similarity_classification_SCRIPT.md", notebooks_dir=REPO_ROOT / "notebooks" / "solutions")


LECTURE_TOO_SHORT = """\
### Lecture 03.1 — Too short

| Duration | Cumulative | VISUAL | AUDIO | Cue |
|---|---|---|---|---|
| 00:30 | 00:30 | [CELL] x.ipynb § "y" | hi | [NONE] |
"""

LECTURE_OK = """\
### Lecture 03.2 — Fine length

| Duration | Cumulative | VISUAL | AUDIO | Cue |
|---|---|---|---|---|
| 03:00 | 03:00 | [CELL] x.ipynb § "y" | hi | [NONE] |
"""

LECTURE_CODEALONG_LONG = """\
### Lecture 03.3 — Big build (codealong)

| Duration | Cumulative | VISUAL | AUDIO | Cue |
|---|---|---|---|---|
| 11:00 | 11:00 | [CELL] x.ipynb § "y" | hi | [NONE] |
"""

LECTURE_CODEALONG_TOO_LONG = """\
### Lecture 03.4 — Way too big (codealong)

| Duration | Cumulative | VISUAL | AUDIO | Cue |
|---|---|---|---|---|
| 13:00 | 13:00 | [CELL] x.ipynb § "y" | hi | [NONE] |
"""


def test_check_lecture_durations_flags_too_short():
    failures = check_lecture_durations(LECTURE_TOO_SHORT)
    assert failures


def test_check_lecture_durations_passes_normal_range():
    assert check_lecture_durations(LECTURE_OK) == []


def test_check_lecture_durations_allows_codealong_up_to_12_min():
    assert check_lecture_durations(LECTURE_CODEALONG_LONG) == []


def test_check_lecture_durations_flags_codealong_over_12_min():
    failures = check_lecture_durations(LECTURE_CODEALONG_TOO_LONG)
    assert failures


MODULE_SCRIPT_MATCHING_TOTAL = (
    LECTURE_OK.replace("03:00", "65:00").replace("03.2", "03.1").replace("Fine length", "Whole module")
)


def test_check_module_total_matches_syllabus_minutes():
    # 65 minutes matches MODULE_MINUTES["03_similarity_classification"].
    failures = check_module_total(MODULE_SCRIPT_MATCHING_TOTAL, "03_similarity_classification")
    assert failures == []


def test_check_module_total_mismatch_fails():
    failures = check_module_total(LECTURE_OK, "03_similarity_classification")
    assert failures


def test_check_grand_total_skips_when_scripts_missing(tmp_path):
    scripts_dir = tmp_path / "scripts"
    scripts_dir.mkdir()
    (scripts_dir / "03_similarity_classification_SCRIPT.md").write_text(MODULE_SCRIPT_MATCHING_TOTAL)
    result = check_grand_total(scripts_dir)
    assert result["status"] == "skipped"


def test_check_grand_total_passes_when_all_eight_present(tmp_path):
    scripts_dir = tmp_path / "scripts"
    scripts_dir.mkdir()
    for slug, minutes in MODULE_MINUTES.items():
        text = LECTURE_OK.replace("03:00", f"{minutes:02d}:00").replace("03.2", "X.1").replace(
            "Fine length", "Whole module"
        )
        (scripts_dir / f"{slug}_SCRIPT.md").write_text(text)
    result = check_grand_total(scripts_dir)
    assert result["status"] == "ok"
    assert result["total"] == GRAND_TOTAL_MINUTES


def test_check_key_messages_reports_missing_when_incomplete(tmp_path):
    scripts_dir = tmp_path / "scripts"
    scripts_dir.mkdir()
    (scripts_dir / "03_similarity_classification_SCRIPT.md").write_text(LECTURE_OK)
    result = check_key_messages(scripts_dir)
    assert result["status"] == "incomplete"
    assert set(result["missing"]) <= set(KEY_MESSAGES)


def test_check_key_messages_hard_fail_when_all_present_but_missing_message(tmp_path):
    scripts_dir = tmp_path / "scripts"
    scripts_dir.mkdir()
    for slug, minutes in MODULE_MINUTES.items():
        text = LECTURE_OK.replace("03:00", f"{minutes:02d}:00")
        (scripts_dir / f"{slug}_SCRIPT.md").write_text(text)
    result = check_key_messages(scripts_dir)
    assert result["status"] == "fail"
    assert len(result["missing"]) == len(KEY_MESSAGES)


def test_check_key_messages_ok_when_all_present_and_all_quoted(tmp_path):
    scripts_dir = tmp_path / "scripts"
    scripts_dir.mkdir()
    all_messages_text = LECTURE_OK + "\n" + "\n".join(KEY_MESSAGES)
    for slug, minutes in MODULE_MINUTES.items():
        (scripts_dir / f"{slug}_SCRIPT.md").write_text(all_messages_text)
    result = check_key_messages(scripts_dir)
    assert result["status"] == "ok"

"""Anchor/timing verifier for narration scripts (plan 08-01).

Checks `scripts/*_SCRIPT.md` (Wave 2 output, not yet written when this plan
runs) against:

  1. Live notebook headings -- a `[CELL] {stem}.ipynb § "{heading}"` anchor
     fails if `{heading}` is not currently present in
     `notebooks/solutions/{stem}.py`'s markdown cell headings. Re-derived at
     check time from the notebook source, never from a snapshot, so a
     reworded or reordered heading breaks the check instead of breaking
     silently mid-recording.
  2. Per-lecture duration: 2:00-7:00, or up to 12:00 when the lecture
     heading contains the literal text "(codealong)".
  3. Per-module total: summed lecture durations must equal
     `MODULE_MINUTES[module_slug]`.
  4. Grand total: once all 8 expected `*_SCRIPT.md` files exist, their
     totals must sum to 360 minutes (skipped, not failed, while fewer are
     present).
  5. Key messages: once all 8 scripts exist, the five canonical verbatim
     messages must each appear in at least one script's AUDIO text
     (hard failure only once the full set exists; otherwise reported as
     informational "incomplete").

Toolchain note (plan 07-01 pivot, also hit by plan 07-05): decks are
Marp-flavoured `slides/NN_*.md`, not Quarto `.qmd`. Speaker notes are plain
HTML comments (`<!-- ... -->`), not `::: {.notes}` blocks. This verifier's
`[SLIDE] {deck_stem}.md #{n}` anchor syntax and deck lookups target that
real format, not the Quarto convention this plan was originally scoped
against.

Usage:
    uv run python tools/verify_narration_scripts.py [--scripts-glob GLOB] [--strict]
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_NOTEBOOKS_DIR = REPO_ROOT / "notebooks" / "solutions"
DEFAULT_SCRIPTS_GLOB = "scripts/*_SCRIPT.md"

# Module slug -> syllabus minutes (ROADMAP.md / PROJECT.md; sums to 360).
MODULE_MINUTES: dict[str, int] = {
    "00_refresher": 25,
    "01_foundations": 35,
    "02_access_visualize": 50,
    "03_similarity_classification": 65,
    "04_change_detection": 60,
    "05_ecosystems": 55,
    "06_production_provenance": 45,
    "07_capstone": 25,
}
GRAND_TOTAL_MINUTES = 360
assert sum(MODULE_MINUTES.values()) == GRAND_TOTAL_MINUTES, (
    "MODULE_MINUTES must sum to GRAND_TOTAL_MINUTES -- syllabus arithmetic is a hard constraint"
)

EXPECTED_SCRIPT_STEMS = [f"{slug}_SCRIPT" for slug in MODULE_MINUTES]

# Five canonical key messages (verbatim substrings), each must be quoted in
# at least one script's AUDIO text once the full script set exists.
KEY_MESSAGES: list[str] = [
    "AlphaEarth vectors are unit-norm, so dot product equals cosine",
    "A17 is not NDVI",
    "17-19 points",
    "1 − cosine measures representation movement",
    "Dynamic World is not independent validation",
]

HEADING_RE = re.compile(r'^# (#{1,3}) (.+)$')
CELL_ANCHOR_RE = re.compile(r'\[CELL\]\s+(\S+)\.ipynb\s+\xa7\s+"([^"]+)"')
# NOTE: "\xa7" is the section-sign character '§'; kept as an escape for clarity.
SLIDE_ANCHOR_RE = re.compile(r'\[SLIDE\]\s+(\S+)\.(?:md|qmd)\s+#(\d+)')
LECTURE_SPLIT_RE = re.compile(r'^### Lecture .+$', re.MULTILINE)
LECTURE_HEADING_RE = re.compile(r'^### (Lecture .+)$', re.MULTILINE)
TABLE_ROW_DURATION_RE = re.compile(r'^\|\s*(\d{1,2}):(\d{2})\s*\|')
CODEALONG_MARKER = "(codealong)"

MIN_LECTURE_SECONDS = 2 * 60
MAX_LECTURE_SECONDS = 7 * 60
MAX_CODEALONG_SECONDS = 12 * 60


def extract_notebook_headings(notebook_path: Path | str) -> set[str]:
    """Re-derive the set of markdown-cell headings from a jupytext py:percent file.

    Matches lines of the form `# #`, `# ##`, `# ###` (percent-format markdown
    cell headings), stripping the leading `#`s and surrounding whitespace.
    """
    path = Path(notebook_path)
    headings: set[str] = set()
    for line in path.read_text(encoding="utf-8").splitlines():
        match = HEADING_RE.match(line)
        if match:
            headings.add(match.group(2).strip())
    return headings


@dataclass
class Anchor:
    kind: str  # "cell" or "slide"
    raw: str
    notebook_stem: str | None = None
    heading: str | None = None
    deck_stem: str | None = None
    number: int | None = None


def parse_script_anchors(script_markdown_text: str) -> list[Anchor]:
    """Parse VISUAL-column anchors out of a script's markdown table rows."""
    anchors: list[Anchor] = []
    for line in script_markdown_text.splitlines():
        cell_match = CELL_ANCHOR_RE.search(line)
        if cell_match:
            anchors.append(
                Anchor(
                    kind="cell",
                    raw=line.strip(),
                    notebook_stem=cell_match.group(1),
                    heading=cell_match.group(2),
                )
            )
            continue
        slide_match = SLIDE_ANCHOR_RE.search(line)
        if slide_match:
            anchors.append(
                Anchor(
                    kind="slide",
                    raw=line.strip(),
                    deck_stem=slide_match.group(1),
                    number=int(slide_match.group(2)),
                )
            )
    return anchors


class MissingAnchor(Exception):
    """Raised when a [CELL] anchor references a heading absent from the live notebook."""

    def __init__(self, script_name: str, row: str, heading: str, notebook_stem: str):
        self.script_name = script_name
        self.row = row
        self.heading = heading
        self.notebook_stem = notebook_stem
        super().__init__(
            f"{script_name}: row {row!r} references heading {heading!r}, "
            f"which does not exist in notebooks/solutions/{notebook_stem}.py"
        )


def check_anchors_exist(
    anchors: list[Anchor],
    script_name: str = "",
    notebooks_dir: Path | str = DEFAULT_NOTEBOOKS_DIR,
) -> None:
    """Raise MissingAnchor for any [CELL] anchor whose heading isn't in the live notebook.

    [SLIDE] anchors are not validated here (no live deck-section index is
    maintained); only [CELL] anchors are checked against re-derived notebook
    headings.
    """
    notebooks_dir = Path(notebooks_dir)
    headings_cache: dict[str, set[str]] = {}
    for anchor in anchors:
        if anchor.kind != "cell":
            continue
        stem = anchor.notebook_stem
        if stem not in headings_cache:
            notebook_path = notebooks_dir / f"{stem}.py"
            if not notebook_path.exists():
                raise MissingAnchor(script_name, anchor.raw, anchor.heading or "", stem or "")
            headings_cache[stem] = extract_notebook_headings(notebook_path)
        if anchor.heading not in headings_cache[stem]:
            raise MissingAnchor(script_name, anchor.raw, anchor.heading or "", stem or "")


def _lecture_duration_seconds(lecture_text: str) -> int:
    total = 0
    for line in lecture_text.splitlines():
        match = TABLE_ROW_DURATION_RE.match(line)
        if match:
            total += int(match.group(1)) * 60 + int(match.group(2))
    return total


def _iter_lectures(script_text: str) -> list[tuple[str, str]]:
    """Split script text into (heading_line, lecture_block) pairs."""
    heading_matches = list(LECTURE_HEADING_RE.finditer(script_text))
    if not heading_matches:
        return [("", script_text)]
    lectures = []
    for i, match in enumerate(heading_matches):
        start = match.start()
        end = heading_matches[i + 1].start() if i + 1 < len(heading_matches) else len(script_text)
        lectures.append((match.group(1), script_text[start:end]))
    return lectures


def check_lecture_durations(script_or_lecture_text: str) -> list[str]:
    """Flag any lecture whose summed row durations fall outside 2:00-7:00
    (12:00 for lectures whose heading contains "(codealong)")."""
    failures: list[str] = []
    for heading, block in _iter_lectures(script_or_lecture_text):
        seconds = _lecture_duration_seconds(block)
        is_codealong = CODEALONG_MARKER in heading
        ceiling = MAX_CODEALONG_SECONDS if is_codealong else MAX_LECTURE_SECONDS
        if seconds < MIN_LECTURE_SECONDS or seconds > ceiling:
            failures.append(
                f"{heading or '(untitled lecture)'}: duration {seconds // 60}:{seconds % 60:02d} "
                f"outside allowed range (2:00-{'12:00' if is_codealong else '7:00'})"
            )
    return failures


def check_module_total(script_text: str, module_slug: str) -> list[str]:
    """Compare the script's summed lecture durations against MODULE_MINUTES[module_slug]."""
    if module_slug not in MODULE_MINUTES:
        return [f"unknown module slug: {module_slug!r}"]
    total_seconds = sum(_lecture_duration_seconds(block) for _, block in _iter_lectures(script_text))
    expected_seconds = MODULE_MINUTES[module_slug] * 60
    if total_seconds != expected_seconds:
        return [
            f"module {module_slug}: summed lecture duration {total_seconds // 60}:{total_seconds % 60:02d} "
            f"does not match syllabus minutes {MODULE_MINUTES[module_slug]}:00"
        ]
    return []


def _slug_from_script_filename(filename: str) -> str | None:
    for slug in MODULE_MINUTES:
        if filename.startswith(f"{slug}_SCRIPT"):
            return slug
    return None


def _existing_scripts(scripts_dir: Path | str) -> dict[str, Path]:
    scripts_dir = Path(scripts_dir)
    found: dict[str, Path] = {}
    if not scripts_dir.exists():
        return found
    for path in scripts_dir.glob("*_SCRIPT.md"):
        slug = _slug_from_script_filename(path.name)
        if slug:
            found[slug] = path
    return found


def check_grand_total(scripts_dir: Path | str) -> dict:
    """Sum all present module totals; only assert ==360 once all 8 exist."""
    found = _existing_scripts(scripts_dir)
    if len(found) < len(MODULE_MINUTES):
        return {
            "status": "skipped",
            "present": sorted(found),
            "missing": sorted(set(MODULE_MINUTES) - set(found)),
        }
    total_minutes = 0
    for slug, path in found.items():
        text = path.read_text(encoding="utf-8")
        total_minutes += sum(_lecture_duration_seconds(block) for _, block in _iter_lectures(text)) // 60
    status = "ok" if total_minutes == GRAND_TOTAL_MINUTES else "fail"
    return {"status": status, "total": total_minutes}


def check_key_messages(scripts_dir: Path | str) -> dict:
    """Search AUDIO text across present scripts for the five canonical key-message substrings."""
    found = _existing_scripts(scripts_dir)
    combined_text = "\n".join(path.read_text(encoding="utf-8") for path in found.values())
    missing = [msg for msg in KEY_MESSAGES if msg not in combined_text]
    if len(found) < len(MODULE_MINUTES):
        status = "ok" if not missing else "incomplete"
    else:
        status = "ok" if not missing else "fail"
    return {"status": status, "missing": missing, "present": sorted(found)}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scripts-glob", default=DEFAULT_SCRIPTS_GLOB)
    parser.add_argument("--strict", action="store_true", help="Fail on any missing anchor/timing/message issue")
    args = parser.parse_args(argv)

    scripts_dir = REPO_ROOT / Path(args.scripts_glob).parent
    found = _existing_scripts(scripts_dir)

    exit_code = 0
    if not found:
        print(f"No scripts found matching {args.scripts_glob} -- nothing to verify yet.")
        return 0

    for slug, path in sorted(found.items()):
        text = path.read_text(encoding="utf-8")
        anchors = parse_script_anchors(text)
        try:
            check_anchors_exist(anchors, script_name=path.name)
        except MissingAnchor as exc:
            print(f"FAIL {path.name}: {exc}")
            exit_code = 1
            continue
        duration_failures = check_lecture_durations(text)
        module_failures = check_module_total(text, slug)
        issues = duration_failures + module_failures
        if issues:
            for issue in issues:
                print(f"FAIL {path.name}: {issue}")
            exit_code = 1
        else:
            print(f"PASS {path.name}")

    grand_total = check_grand_total(scripts_dir)
    print(f"Grand total check: {grand_total}")
    key_messages = check_key_messages(scripts_dir)
    print(f"Key messages check: {key_messages}")

    if args.strict:
        if grand_total["status"] == "fail" or key_messages["status"] == "fail":
            exit_code = 1

    return exit_code


if __name__ == "__main__":
    sys.exit(main())

"""Structural checker over slides/*.md (plan 07-05).

Toolchain note: decks are Marp-flavoured Markdown (`slides/NN_*.md`), not
Quarto `.qmd`, per the 07-01 toolchain pivot (Quarto's cask installer requires
interactive sudo on this machine; Marp CLI is used instead, invoked pinned via
npx). Partials (`slides/_partials/version-banner.qmd`,
`slides/_partials/attribution.qmd`) are copy-pasted verbatim into each deck
rather than included, because Marp has no `{{< include >}}` equivalent -- see
`slides/_partials/README.md`. This checker verifies each deck carries the
*content* of both partials (the version-banner heading and the attribution
heading), not a literal include directive.

Checks per deck (excluding `slides/_partials/`):
  1. An objectives-style heading exists ("what you will learn" or
     "objective", case-insensitive).
  2. A recap-style heading exists ("recap", case-insensitive).
  3. Both partials' content is present: the version-banner heading
     ("Course Reference Environment") and the attribution heading
     ("Attribution and Licenses").
  4. At least one WRONG-conclusion-or-licensing-caution heading exists
     ("wrong conclusion" or "licensing caution", case-insensitive).
  5. Every `figures/*.png` path referenced in the file resolves on disk
     (relative to the deck's own directory).
  6. A rough speaker-notes heuristic: the count of HTML comment blocks
     (`<!-- ... -->`, Marp's speaker-notes mechanism) is at least the
     count of content slides (level-2 headings) minus the objectives,
     recap, and two partial headings.

Also asserts exactly the eight expected deck stems are present, so an
accidentally-skipped deck cannot pass silently.

Usage:
    uv run python tools/verify_slides.py
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

EXPECTED_STEMS = [
    "00_refresher",
    "00b_representation_inspection",
    "01_access_visualize",
    "02_similarity_classification",
    "03_change_detection",
    "04_ecosystems",
    "05_capstone",
    "06_provenance_licensing",
]

OBJECTIVES_RE = re.compile(r"^##\s+.*(what you will learn|objective)", re.IGNORECASE | re.MULTILINE)
RECAP_RE = re.compile(r"^##\s+.*recap", re.IGNORECASE | re.MULTILINE)
VERSION_BANNER_RE = re.compile(r"^#\s+course reference environment", re.IGNORECASE | re.MULTILINE)
ATTRIBUTION_RE = re.compile(r"^#\s+attribution and licenses", re.IGNORECASE | re.MULTILINE)
TRAP_RE = re.compile(r"^##\s+.*(wrong conclusion|licensing caution)", re.IGNORECASE | re.MULTILINE)
CONTENT_HEADING_RE = re.compile(r"^##\s+", re.MULTILINE)
COMMENT_BLOCK_RE = re.compile(r"<!--.*?-->", re.DOTALL)
IMAGE_REF_RE = re.compile(r"!\[[^\]]*\]\(([^)]+)\)")


def verify_deck(path: Path) -> list[str]:
    """Return a list of failure messages for a single deck; empty if it passes."""
    failures: list[str] = []
    text = path.read_text(encoding="utf-8")

    if not OBJECTIVES_RE.search(text):
        failures.append(f"{path}: missing an objectives-style heading (expected 'What you will learn' or 'Objective')")
    if not RECAP_RE.search(text):
        failures.append(f"{path}: missing a recap-style heading (expected a heading containing 'Recap')")
    if not VERSION_BANNER_RE.search(text):
        failures.append(f"{path}: missing the version-banner partial content ('# Course Reference Environment')")
    if not ATTRIBUTION_RE.search(text):
        failures.append(f"{path}: missing the attribution partial content ('# Attribution and Licenses')")
    if not TRAP_RE.search(text):
        failures.append(f"{path}: missing a WRONG-conclusion-or-licensing-caution heading")

    for match in IMAGE_REF_RE.finditer(text):
        ref = match.group(1).strip()
        if "figures/" not in ref:
            continue
        resolved = (path.parent / ref).resolve()
        if not resolved.exists():
            failures.append(f"{path}: referenced figure does not exist on disk: {ref} (resolved {resolved})")

    content_headings = len(CONTENT_HEADING_RE.findall(text))
    notes_blocks = len(COMMENT_BLOCK_RE.findall(text))
    # Rough heuristic per plan: notes-block count >= content-slide count
    # minus objectives/recap/partials (4 accounted-for headings).
    expected_min_notes = max(content_headings - 4, 0)
    if notes_blocks < expected_min_notes:
        failures.append(
            f"{path}: too few speaker-notes blocks ({notes_blocks} HTML comment blocks "
            f"for {content_headings} content headings; expected at least {expected_min_notes})"
        )

    return failures


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--slides-dir",
        type=Path,
        default=Path(__file__).resolve().parent.parent / "slides",
        help="Directory containing the deck .md files (default: slides/)",
    )
    args = parser.parse_args()

    slides_dir: Path = args.slides_dir
    decks = sorted(
        p for p in slides_dir.glob("*.md") if p.parent.name != "_partials"
    )

    found_stems = {p.stem for p in decks}
    missing_stems = [s for s in EXPECTED_STEMS if s not in found_stems]

    all_failures: dict[str, list[str]] = {}
    for deck in decks:
        failures = verify_deck(deck)
        if failures:
            all_failures[str(deck)] = failures

    if missing_stems:
        print(f"FAIL: missing expected deck(s): {', '.join(missing_stems)}")

    if all_failures:
        for deck, failures in all_failures.items():
            print(f"FAIL: {deck}")
            for f in failures:
                print(f"  - {f}")

    passing = [str(d) for d in decks if str(d) not in all_failures]
    for deck in passing:
        print(f"PASS: {deck}")

    if missing_stems or all_failures:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())

---
phase: 07-slide-decks
plan: 05
subsystem: slides
tags: [structural-checker, pytest, marp-cli, deck-build, verification]

requires: ["07-01", "07-02", "07-03", "07-04"]
provides:
  - "tools/verify_slides.py: automated structural checker over all eight slides/*.md decks"
  - "tests/test_slides.py: pytest wrapper so `uv run pytest tests/` covers deck structure"
  - "Verified full-build proof: `make slides` (8/8 HTML) and `make slides-pdf` (8/8 PDF) both succeed"
affects: []

tech-stack:
  added: []
  patterns:
    - "Structural checks over Markdown decks via regex on headings/comments/image-refs, not by eyeballing slide content"
    - "Standalone CLI script (argparse) matching tools/derive_exercise.py's convention, wrapped by a thin pytest subprocess test"

key-files:
  created:
    - tools/verify_slides.py
    - tests/test_slides.py
  modified:
    - .gitignore

key-decisions:
  - "Checker targets slides/*.md (Marp), not slides/*.qmd (Quarto) -- the plan's frontmatter/action text predates 07-01's toolchain pivot from Quarto to Marp CLI; adjusted the implementation to match the real deck format without weakening any check."
  - "Objectives-heading check matches 'what you will learn' (case-insensitive) in addition to 'objective', since all eight decks use the former literal phrase, not the latter."
  - "Partial-inclusion check verifies the *content* of the two partials is present (heading text 'Course Reference Environment' / 'Attribution and Licenses'), not a literal Quarto {{< include >}} directive, since 07-01 established copy-paste (not include) as the correct Marp pattern."
  - "WRONG-conclusion/licensing-caution check is case-insensitive: two decks use 'WRONG CONCLUSION' (all-caps) and others use 'WRONG conclusion' -- both are legitimate authorial variation, not a defect."
  - "Speaker-notes heuristic implemented exactly as the plan specified: HTML comment-block count >= content-heading count minus 4 (objectives + recap + 2 partial headings). Speaker notes are plain <!-- --> comments (Marp's mechanism), not Quarto's ::: {.notes} block."
  - "Fixed .gitignore's slides/*.pdf pattern, which did not match slides/pdf/*.pdf actually produced by `make slides-pdf`, leaving PDF build output untracked (Rule 1 bug found during Task 2's build run)."

requirements-completed: [SLIDE-01, SLIDE-02, SLIDE-03, SLIDE-04, SLIDE-05]

duration: ~35min
completed: 2026-09-04
---

# Phase 07 Plan 05: Structural Checker and Full Deck Build Summary

**`tools/verify_slides.py` programmatically checks all eight Marp decks for objectives/recap headings, both partials' content, a WRONG-conclusion-or-licensing-caution trap slide, resolvable figure references, and speaker-notes coverage; `make slides` and `make slides-pdf` both complete cleanly for all eight decks.**

## Performance

- **Duration:** ~35 min
- **Tasks:** 2
- **Files modified:** 3 (2 created, 1 modified)

## Accomplishments

- Wrote `tools/verify_slides.py`: globs `slides/*.md` (excluding `_partials/`), checks each deck for an objectives heading, a recap heading, both partials' content, a WRONG-conclusion/licensing-caution heading, every referenced `figures/*.png` path resolving on disk, and a speaker-notes-block heuristic; asserts exactly the eight expected deck stems are present. Exits non-zero with a specific per-deck, per-check failure message if anything is missing.
- Verified the checker catches a real defect: deliberately broke one figure reference in `02_similarity_classification.md`, re-ran the checker, confirmed it named the specific broken path, then reverted (confirmed via `diff` against a backup).
- Verified attribution strings in `slides/_partials/attribution.qmd` (and thus every deck) match `data/DATA_CARD.md`'s "Licenses and Attribution" table verbatim, word-for-word, across all five source rows.
- Wrote `tests/test_slides.py`: a single pytest test invoking the checker via subprocess and asserting exit code 0.
- Ran `make slides`: all eight decks render to HTML via the pinned Marp CLI with zero errors.
- Ran `make slides-pdf`: all eight PDFs produced under `slides/pdf/` (verified via `ls -la`).
- Ran the full suite: `uv run pytest tests/ -q` → 168 passed, 3 skipped, 10 deselected.

## Task Commits

1. **Task 1 + Task 2 (combined, single commit):** `973ae83` (feat) — `tools/verify_slides.py`, `tests/test_slides.py`, `.gitignore` fix.

## Files Created/Modified

- `tools/verify_slides.py` — structural checker, standalone CLI (argparse), no network, read-only filesystem access
- `tests/test_slides.py` — pytest subprocess wrapper
- `.gitignore` — added `slides/pdf/` (the existing `slides/*.pdf` pattern did not match the nested `slides/pdf/*.pdf` output path)

## Decisions Made

See `key-decisions` in frontmatter. The most consequential: the plan's own text (written before 07-01's toolchain pivot) describes Quarto `.qmd` conventions (`{{< include >}}`, `::: {.notes}` blocks) that do not exist in the real Marp-based decks. The checker was implemented against the actual deck format (plain `<!-- -->` HTML comments for speaker notes, copy-pasted partial content instead of includes) rather than the stale Quarto-era wording, per this plan's own instruction not to weaken a check but to say so when its assumed shape doesn't match reality.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] `.gitignore` `slides/*.pdf` pattern did not cover `make slides-pdf`'s actual output path**
- **Found during:** Task 2, after running `make slides-pdf`
- **Issue:** The Makefile writes PDFs to `slides/pdf/<stem>.pdf`, but `.gitignore` only had the flat pattern `slides/*.pdf`, which does not match one directory level down. `git status` showed `slides/pdf/` as untracked.
- **Fix:** Added `slides/pdf/` to `.gitignore`.
- **Files modified:** `.gitignore`
- **Commit:** `973ae83`

**Total deviations:** 1 (Rule 1, trivial).

## Known Stubs

None.

## Threat Flags

None. `verify_slides.py` is read-only (glob + regex over `slides/*.md` and figure paths on disk), matching the plan's `threat_model` disposition (`T-07-09`, accepted, low-value target).

## Issues Encountered

None blocking. The plan's frontmatter/task text referenced Quarto-era syntax (`.qmd`, `{{< include >}}`, `::: {.notes}`) that no longer applies after 07-01's Marp pivot; resolved by implementing against the real deck format, documented above rather than silently dropped.

## User Setup Required

None.

## Next Phase Readiness

- `make slides` / `make slides-pdf` are proven end-to-end for all eight decks; no manual quarto/marp invocation is needed.
- `tools/verify_slides.py` / `tests/test_slides.py` will catch a missing objectives/recap slide, a broken figure reference, a missing partial, a missing trap slide, or an accidentally-dropped deck in any future edit to `slides/`.
- `uv run pytest tests/ -q` passes in full (168 passed, 3 skipped, 10 deselected) — this plan added one new test and touched no other Python code.

---
*Phase: 07-slide-decks*
*Completed: 2026-09-04*

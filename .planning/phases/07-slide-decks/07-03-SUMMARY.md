---
phase: 07-slide-decks
plan: 03
subsystem: slides
tags: [marp-slides, module-02, module-03, spatial-cv, change-detection]

requires: ["07-01: Marp toolchain, shared metadata/partials, make slides"]
provides:
  - "slides/02_similarity_classification.md: flagship Module 2 deck (analytical-chain diagram, spatial-CV trap/honest-number pair)"
  - "slides/03_change_detection.md: Module 3 deck ('1 - cosine' concept slide, calibrated-precision trap/honest-number pair)"
affects: []

tech-stack:
  added: []
  patterns:
    - "Deck front-matter repeats slides/_metadata.yml's three keys verbatim (marp/theme/size/paginate), per the 07-01 Marp-not-Quarto decision"
    - "Partials (version-banner, attribution) copy-pasted verbatim into each deck, attribution rows trimmed per-module (WorldCover+S2 for 02, HRL Imperviousness for 03), never reworded"

key-files:
  created:
    - slides/02_similarity_classification.md
    - slides/03_change_detection.md
  modified:
    - .gitignore

key-decisions:
  - "02 deck states the leave-region-out cost as the notebook's own reported range (17-19 points, 02-RESEARCH.md), not a single rounded number, because the notebook's own markdown cell reports a range rather than one figure."
  - "03 deck's calibrated-detector precision (0.065) is sourced from this project's 05-02-SUMMARY.md, which recorded the executed notebook's actual printed output (threshold=0.023, precision=0.065, recall=0.933, F1=0.121) — confirmed against the source rather than assumed from the plan's suggested figure."
  - "Added slides/*.html and slides/*.pdf to .gitignore (Rule 2/3): make slides produces build artifacts with no prior ignore rule; left untracked they would either get committed by accident or show as permanent git-status noise."

requirements-completed: [SLIDE-01, SLIDE-02, SLIDE-03, SLIDE-04]

duration: ~40min
completed: 2026-09-04
---

# Phase 07 Plan 03: Module 2 and Module 3 Slide Decks Summary

**Authored the course's two highest-stakes decks — the flagship similarity/classification module and the change-detection module — each carrying its notebook's verbatim WRONG-conclusion trap cell paired with a number traced directly to the notebook's own reported output (17-19 point leave-region-out cost; 0.065 calibrated-detector precision), not invented or rounded from memory.**

## Performance

- **Duration:** ~40 min
- **Completed:** 2026-09-04
- **Tasks:** 2
- **Files modified:** 3 (2 created, 1 modified)

## Accomplishments

- `slides/02_similarity_classification.md`: objectives slide, five-node Mermaid analytical-chain diagram, seven `figures/02_*.png` embeds, a WRONG-conclusion slide reproducing the notebook's `same_class_rate > 0.90` trap cell verbatim, and a spatial-validation slide stating the notebook's own reported **17-19 point** leave-region-out balanced-accuracy drop (sourced from the markdown cell citing `02-RESEARCH.md`, not a paraphrase).
- `slides/03_change_detection.md`: objectives slide, a dedicated concept slide with the verbatim PROJECT.md sentence "1 − cosine measures representation movement, not semantic transition," four `figures/03_*.png` embeds, a WRONG-conclusion slide reproducing the notebook's `change_score > 0.25` trap cell verbatim, and a calibrated-threshold slide citing the notebook's actual measured output (threshold 0.023, precision 0.065, recall 0.933, F1 0.121), verified against `05-02-SUMMARY.md`'s record of the executed notebook rather than assumed from the plan text.
- Both decks build cleanly: `make slides` renders both to HTML with no errors.
- Added `slides/*.html` / `slides/*.pdf` to `.gitignore` so `make slides`'s regenerable output never becomes untracked noise or an accidental commit.

## Task Commits

Each task was committed atomically:

1. **Task 1: 02_similarity_classification deck** — `0e2feb0` (feat) — also carries the `.gitignore` fix
2. **Task 2: 03_change_detection deck** — `a509a2d` (feat)

## Files Created/Modified

- `slides/02_similarity_classification.md` — Module 2 deck: objectives, analytical-chain Mermaid diagram, 7 figure slides, verbatim wrong-conclusion + honest-number pair, recap, version-banner and attribution partials (AlphaEarth + ESA WorldCover + Sentinel-2 rows kept, HRL/LGND trimmed)
- `slides/03_change_detection.md` — Module 3 deck: objectives, verbatim "1 − cosine" concept slide, 4 figure slides, verbatim wrong-conclusion + calibrated-precision pair, recap, version-banner and attribution partials (AlphaEarth + Copernicus HRL Imperviousness kept, WorldCover/S2/LGND trimmed)
- `.gitignore` — added `slides/*.html` / `slides/*.pdf` ignore rules

## Decisions Made

- **Range over single number (02 deck):** the notebook's own markdown cell reports "17-19 points for logistic regression and random forest" as a range, citing `02-RESEARCH.md` — the deck states that same range rather than picking or inventing a midpoint, per the plan's explicit instruction not to invent a number if the exact figure differs from "17-19."
- **Verified precision figure (03 deck):** rather than trusting the plan's suggested "0.065" at face value, grepped this project's own `05-02-SUMMARY.md` (which records the executed notebook's real printed output: threshold 0.023, precision 0.065, recall 0.933, F1 0.121) and cited that as the source in speaker notes.
- **Attribution trimming:** each deck keeps only the attribution rows relevant to its own module's data sources (02: AlphaEarth + WorldCover + Sentinel-2 baseline; 03: AlphaEarth + Copernicus HRL Imperviousness), per `slides/_partials/README.md`'s trim-only-never-reword convention.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing critical functionality] `.gitignore` had no rule for Marp's rendered output**
- **Found during:** Task 1, after running `make slides` to verify the build
- **Issue:** `make slides` writes `slides/*.html` next to the `.md` sources with no existing ignore rule, so the build artifact would either need manual deletion every time or risk an accidental commit.
- **Fix:** Added `slides/*.html` and `slides/*.pdf` to `.gitignore`; deleted the two rendered HTML files from the working tree before committing.
- **Files modified:** `.gitignore`
- **Commit:** `0e2feb0`

---

**Total deviations:** 1 (Rule 2, non-content, toolchain hygiene).
**Impact on plan:** None on deck content; purely a build-output housekeeping fix anticipated by the task-commit protocol's "never leave generated files untracked" rule.

## Issues Encountered

None. Both notebooks' `wrong-conclusion`-tagged cells were located by `grep -n "wrong-conclusion"` and reproduced verbatim; the leave-region-out and calibrated-precision numbers were both confirmed against source text (the notebook's own markdown cell for 02; this project's `05-02-SUMMARY.md` record of executed-notebook output for 03) before being written into either deck.

## User Setup Required

None.

## Verification

- `grep -c "flowchart" slides/02_similarity_classification.md` → 1
- `grep -c "figures/02_" slides/02_similarity_classification.md` → 7
- `grep -c "1 − cosine measures representation movement\|1 - cosine measures representation movement" slides/03_change_detection.md` → 2
- `grep -c "figures/03_" slides/03_change_detection.md` → 4
- `make slides` renders both decks to HTML with no errors
- `uv run pytest tests/ -q` → 167 passed, 3 skipped, 10 deselected (unchanged from 07-01's baseline; this plan touched no Python code)

## Next Phase Readiness

- Both decks are ready inputs for Phase 8 narration scripts — every speaker-note block states what an instructor would actually say, including the exact source of each quantitative claim (notebook cell or SUMMARY.md), not a placeholder.
- Siblings 07-02/07-04 continue authoring their own assigned decks independently; this plan touched only `slides/02_similarity_classification.md`, `slides/03_change_detection.md`, and `.gitignore`.

---
*Phase: 07-slide-decks*
*Completed: 2026-09-04*

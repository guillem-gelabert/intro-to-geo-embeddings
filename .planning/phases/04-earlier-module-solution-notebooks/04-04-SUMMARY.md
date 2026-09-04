---
phase: 04-earlier-module-solution-notebooks
plan: 04
subsystem: notebooks
tags: [alphaearth, clay, satclip, pixel-vs-patch-vs-location, jupytext, offline-first]

requires: ["04-02"]
provides:
  - "notebooks/solutions/00b_representation_inspection.py: jupytext py:percent source of the representation-inspection notebook"
  - "notebooks/solutions/00b_representation_inspection.ipynb: paired notebook, executes headlessly via make execute-notebooks"
  - "tests/test_representation_notebook.py: headless-execution + graceful-degrade + comparison-table proof tests"
affects: []

tech-stack:
  added: []
  patterns:
    - "Optional heavy-dependency section pattern: try/except ImportError around `import torch`, printing an explicit skip message rather than silently no-op'ing, so both the presence and absence of the dependency are observable in notebook output"

key-files:
  created:
    - notebooks/solutions/00b_representation_inspection.py
    - notebooks/solutions/00b_representation_inspection.ipynb
    - tests/test_representation_notebook.py
  modified: []

key-decisions:
  - "Test for the torch-absent degrade path guards with importlib.util.find_spec and pytest.skip if torch happens to be present, so the test suite stays correct even if a future environment installs torch, while still proving the degrade path runs for real in this project's default (torch-free) environment today"
  - "SatCLIP's torch-present branch (never expected to execute in the reference environment) prints an explicit placeholder-shape comment rather than attempting a real forward pass, since no SatCLIP checkpoint is bundled with the course"

requirements-completed: [EARLY-02]

duration: 30min
completed: 2026-09-04
---

# Phase 04 Plan 04: `00b_representation_inspection.ipynb` Summary

**A short hands-on notebook puts a real AlphaEarth 64-D pixel vector and a real Clay 1024-D patch embedding side by side (shape, spatial unit, temporal support, metadata), with an optional SatCLIP section that degrades cleanly when torch is absent — proven by an automated headless test.**

## Performance

- **Duration:** ~30 min
- **Tasks:** 2 completed
- **Files modified:** 3 created (notebook source + paired ipynb + test)

## Accomplishments
- `00b_representation_inspection.ipynb` loads `course.data.load("bern", 2024)` for the AlphaEarth pixel vector and `data/clay_sample_fixture.parquet` (Plan 04-02's committed fixture) for the Clay patch embedding — zero network access, zero new dependencies
- A comparison `pandas.DataFrame` renders dims, spatial unit, temporal support and source for both providers, printed in cell output
- The optional SatCLIP section guards `import torch` and prints an explicit skip message in this project's torch-free core environment (verified: `python -c "import torch"` fails here)
- `tests/test_representation_notebook.py` executes the notebook headlessly via `NotebookClient` and asserts (a) zero cell errors, (b) the graceful-degrade message actually appears in output, (c) the comparison table's provider names and "shape" appear in output
- `make execute-notebooks` runs all three solution notebooks (including this one) cleanly end-to-end

## Task Commits

Each task was committed atomically:

1. **Task 1: Header, Setup, AlphaEarth pixel vector and Clay patch embedding inspection** - `8d5fb26` (feat)
2. **Task 2: Optional SatCLIP section, Wrap-up, headless test** - `755e206` (feat)

## Files Created/Modified
- `notebooks/solutions/00b_representation_inspection.py` - jupytext py:percent source; header, Setup (IN_COLAB pattern), AlphaEarth section, Clay section, comparison table, optional SatCLIP section, Wrap-up
- `notebooks/solutions/00b_representation_inspection.ipynb` - paired notebook (outputs stripped by the nbstripout pre-commit hook before commit)
- `tests/test_representation_notebook.py` - 3 tests: headless-execution-zero-errors, graceful-degrade-message-present (skips itself if torch happens to be installed), comparison-table-rendered

## Decisions Made
- Kept the AlphaEarth spatial-unit/temporal-support facts (10 m pixel, calendar-year composite) as quoted strings matching this repo's existing provenance documentation rather than re-deriving new numbers.
- Read the Clay fixture's `datetime` value directly into both the inspection cell and the comparison table so the printed temporal-support claim is provably read from the real fixture, not hardcoded.

## Deviations from Plan
None — plan executed exactly as written.

## Issues Encountered
None. `jupyter execute` writes cell outputs into the ipynb in place; the pre-existing `nbstripout` pre-commit hook stripped them automatically on `git commit`, verified via `git show HEAD:... | grep -c '"output_type"'` returning `0`.

## User Setup Required
None - no external service configuration required. The notebook is fully offline (frozen AlphaEarth tables + committed Clay fixture).

## Next Phase Readiness
`00b_representation_inspection.ipynb` is available for later reference by `01_alphaearth_access_visualize.ipynb` and Module 5's ecosystems notebook, both of which the Wrap-up section already points toward.

## Self-Check: PASSED
- FOUND: notebooks/solutions/00b_representation_inspection.py
- FOUND: notebooks/solutions/00b_representation_inspection.ipynb
- FOUND: tests/test_representation_notebook.py
- FOUND commit: 8d5fb26
- FOUND commit: 755e206

---
*Phase: 04-earlier-module-solution-notebooks*
*Completed: 2026-09-04*

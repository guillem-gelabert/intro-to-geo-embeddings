---
phase: 03-similarity-search-and-classification-notebook
plan: 02
subsystem: notebook
tags: [jupytext, nbclient, geopandas, cosine-similarity, precision-at-k]

# Dependency graph
requires:
  - phase: 03-similarity-search-and-classification-notebook
    plan: 01
    provides: "course.embeddings.cosine_similarity_map, course.schema.validate_frozen/to_matrix/embedding_cols, course.data.load"
provides:
  - "notebooks/solutions/02_similarity_and_classification.{py,ipynb} cells 0-5: Header, Setup, Data, Similarity 1/2/3"
  - "four figures: 02_points_map, 02_topk_matches_map, 02_similarity_histogram, 02_prototype_precision_at_k"
  - "a repo-root cwd-resolution pattern in the Setup cell, reusable by later notebook plans"
affects: [03-03, 03-04, "Module 4 (change and validation)", "Module 5 (ecosystems)"]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Setup cell chdir's to the repo root (found by walking up to the pyproject.toml marker) when not in Colab, because jupyter execute's CLI sets the kernel cwd to the notebook's own directory rather than the repo root"
    - "precision_at_k is notebook-local teaching code (not a course/ package helper), per SIM-12's helper list"
    - "EDIT ME parameter cells (QUERY_REGION/QUERY_ID/K, POLYGON_ID) are tagged parameters and fail loudly (assert/KeyError naming valid values) rather than silently propagating NaN/IndexError"

key-files:
  created:
    - notebooks/solutions/02_similarity_and_classification.py
    - notebooks/solutions/02_similarity_and_classification.ipynb
    - figures/02_points_map.png
    - figures/02_topk_matches_map.png
    - figures/02_similarity_histogram.png
    - figures/02_prototype_precision_at_k.png
  modified: []

key-decisions:
  - "Rule 3 fix: added a repo-root chdir in the Setup cell for the non-Colab path, since nbclient's `jupyter execute` CLI sets the kernel cwd to the notebook's parent directory, not the repo root, which otherwise breaks course.data.load's default data_dir='data' and every figures/ savefig path"
  - "POLYGON_ID's region is asserted equal to QUERY_REGION so the precision@k comparison always scores against the same target label the single-pixel query used, rather than silently mixing regions"
  - "The buffered spatial join (polygon.buffer(300m) in the region's UTM CRS) falls back to the 5 nearest points to the polygon centroid when fewer than 3 points fall inside the buffer, per the plan's explicit fallback requirement"

requirements-completed: [SIM-01, SIM-02, SIM-03, SIM-04, SIM-05]

# Metrics
duration: 20min
completed: 2026-09-04
---

# Phase 03 Plan 02: Notebook Header, Setup, Data and Similarity Ladder Summary

**Authored the first 30 cells of `02_similarity_and_classification.ipynb` (jupytext-paired): header/setup/data, single-pixel cosine search with its WRONG-conclusion trap, and the polygon-mean / positive-minus-negative prototype ladder scored by precision@k — all four cells execute headlessly against the real frozen Bern/Seville tables in well under the 3-minute budget.**

## Performance

- **Duration:** 20 min
- **Started:** 2026-09-04T00:52:00+02:00 (approx)
- **Completed:** 2026-09-04T00:55:17+02:00
- **Tasks:** 3
- **Files modified:** 6 (2 new notebook-pair files, 4 new figures)

## Accomplishments
- Header cell states objectives, prerequisites, "~3 minutes"/"no Earth Engine account", and the verbatim README reference-environment banner
- Setup cell follows the proven Colab-detection pattern from `tests/test_bootstrap.py`, extended with a repo-root `chdir` for the local/CI path (see Deviations)
- Data section loads both regions via `course.data.load`, prints schema/class counts, plots a points-by-label map, and calls `course.schema.validate_frozen` directly as the unit-norm assertion (no re-implementation)
- Similarity 1: ranked single-pixel cosine search with a top-k match map and similarity histogram, followed immediately by the WRONG-conclusion cell ("similarity > 0.90 means same land cover") and its correction
- Similarity 2/3: polygon-mean prototype (buffered spatial join with a <3-point nearest-5 fallback, explicit renormalization) and positive-minus-negative prototype, both scored by a notebook-local `precision_at_k` against the single-pixel baseline in one comparison table/figure
- All three EDIT ME knobs (`QUERY_REGION`/`QUERY_ID`/`K`, `POLYGON_ID`) are tagged `parameters` cells with loud assertions on invalid input

## Task Commits

Each task was committed atomically:

1. **Task 1: Header, Setup and Data cells** - `0d67f35` (feat)
2. **Task 2: Similarity 1 — cosine search and WRONG-conclusion trap** - `41031f1` (feat)
3. **Task 3: Similarity 2/3 — prototype queries and precision@k** - `ef4fe49` (feat)

## Files Created/Modified
- `notebooks/solutions/02_similarity_and_classification.py` - jupytext `py:percent` source, cells 0-5 of the ~11-section blueprint
- `notebooks/solutions/02_similarity_and_classification.ipynb` - paired notebook, regenerated via `jupytext --sync` after each task
- `figures/02_points_map.png` - Bern/Seville points colored by label
- `figures/02_topk_matches_map.png` - top-k cosine matches for the default query
- `figures/02_similarity_histogram.png` - similarity distribution with the 0.90 reference line
- `figures/02_prototype_precision_at_k.png` - single-pixel vs polygon-mean vs positive-minus-negative precision@10 bar chart

## Decisions Made
See `key-decisions` in frontmatter above.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Setup cell needed an explicit repo-root chdir for the non-Colab path**
- **Found during:** Task 1, first `jupyter execute` verification run
- **Issue:** `course.data.load("bern", 2021)` raised `FileNotFoundError: data/manifest.json` even though `data/manifest.json` exists at the repo root. `nbclient`'s `jupyter execute` CLI (unlike an interactively-launched kernel opened from the repo root) sets the kernel's cwd to the notebook file's own parent directory (`notebooks/solutions/`), so every repo-root-relative path (`data/`, `figures/`, `outputs/`) resolved to the wrong place.
- **Fix:** Added an `else` branch to the Setup cell's `IN_COLAB` check that walks up from `Path.cwd()` looking for the directory containing `pyproject.toml`, and `chdir`s there. This runs before any `data/`- or `figures/`-relative path is touched, and is transparent whether the notebook is opened interactively from the repo root (no-op) or executed headlessly from anywhere via `jupyter execute`/`make execute-notebooks`.
- **Files modified:** `notebooks/solutions/02_similarity_and_classification.py` (and its paired `.ipynb`)
- **Verification:** `uv run jupyter execute --kernel_name=geo-embeddings-course --timeout=300 notebooks/solutions/02_similarity_and_classification.ipynb` exits 0; re-verified after Tasks 2 and 3 and via `make execute-notebooks`.
- **Committed in:** `0d67f35` (Task 1 commit)

---

**Total deviations:** 1 auto-fixed (1 blocking)
**Impact on plan:** Necessary for the notebook to run at all under the `jupyter execute` CLI (the plan's own stated verification command); no scope creep — the fix only affects cwd resolution, not any notebook content.

## Issues Encountered

None beyond the one documented deviation above.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

Cells 0-5 (Header through Similarity 3) execute cleanly top to bottom against the real frozen data, all four target figures exist and are non-empty, `uv run pytest tests/ -q` still passes (110 passed, 3 skipped, 8 deselected — no regressions), and `make execute-notebooks` now actually executes this notebook instead of no-op'ing. Plan 03-03 can append the Classification/Spatial CV sections starting at cell 6 without re-deriving the Setup cell's cwd-resolution pattern.

---
*Phase: 03-similarity-search-and-classification-notebook*
*Completed: 2026-09-04*

## Self-Check: PASSED

All six created files verified present; all three task commits (0d67f35, 41031f1, ef4fe49) verified in git log.

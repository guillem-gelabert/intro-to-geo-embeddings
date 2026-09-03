---
phase: 03-similarity-search-and-classification-notebook
plan: 03
subsystem: notebook
tags: [scikit-learn, spatial-cv, group-kfold, leave-one-group-out, honest-validation]

# Dependency graph
requires:
  - phase: 03-similarity-search-and-classification-notebook
    plan: 02
    provides: "notebooks/solutions/02_similarity_and_classification.{py,ipynb} cells 0-5 (Header through Similarity 3)"
  - phase: 03-similarity-search-and-classification-notebook
    plan: 01
    provides: "course.validation.make_blocks, course.validation.spatial_cv_report"
provides:
  - "notebooks/solutions/02_similarity_and_classification.{py,ipynb} cells 6-10: Classification, Spatial CV (block + leave-region-out), Baseline"
  - "three figures: 02_confusion_matrix_random_split, 02_cv_comparison_bar_chart, 02_error_map"
  - "the notebook's central honest-validation lesson, measured on the real frozen tables and narrated leave-region-out-first"
affects: ["03-04", "Phase 7 (slide deck embeds these exact figures)"]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "spatial_cv_report is called with an identical shape for both GroupKFold (in-region block CV) and LeaveOneGroupOut (leave-region-out) -- only groups/cv differ, proving the helper is genuinely generic rather than two code paths dressed alike"
    - "raw Sentinel-2 baseline reuses the identical pipeline/CV calls as the embeddings arm, changing only the feature matrix, to isolate representation from preprocessing/validation methodology"

key-files:
  created:
    - figures/02_confusion_matrix_random_split.png
    - figures/02_cv_comparison_bar_chart.png
    - figures/02_error_map.png
  modified:
    - notebooks/solutions/02_similarity_and_classification.py
    - notebooks/solutions/02_similarity_and_classification.ipynb

key-decisions:
  - "Dropped the sparse 'bare' class (219 candidate points at Bern) before classification, stated explicitly in a markdown cell rather than silently filtering"
  - "Bern is reprojected live to EPSG:2056 and make_blocks is called fresh in the notebook (not the frozen table's precomputed UTM block_id), per the plan's deliberate teaching-of-Pitfall-3 decision"
  - "n_estimators=200 fixed for RandomForestClassifier in both the embeddings and S2 arms to protect the Colab CPU budget"
  - "Narration and figure ordering both lead with leave-region-out as the primary 'a random split lies' evidence; in-region block CV is presented as a real but modest secondary effect, with no assertion or sentence claiming a large in-region gap anywhere in the notebook"
  - "Rule 1 fix: a handful of Seville rows have NaN Sentinel-2 bands (tile-edge artifact) even though their AlphaEarth embedding is complete; the S2 baseline arm drops those rows (with a printed count) before fitting, since NaN silently propagated into StandardScaler/LogisticRegression previously produced a NaN leave-region-out score for logreg"

requirements-completed: [SIM-06, SIM-07, SIM-08, SIM-09]

# Metrics
duration: 45min
completed: 2026-09-04
---

# Phase 03 Plan 03: Classification, Honest Spatial Validation and Raw-Band Baseline Summary

**Appended the classification trap, in-region spatial-block CV, leave-region-out, the comparison chart/error map, and the Sentinel-2 raw-band baseline to `02_similarity_and_classification.ipynb` — all measured on the real frozen Bern/Seville tables, narrated leave-region-out-first, with no folklore accuracy numbers asserted anywhere.**

## Performance

- **Duration:** ~45 min
- **Tasks:** 3
- **Files modified:** 5 (1 notebook pair + 3 new figures)
- **Full-notebook headless wall time:** ~10 seconds (`make execute-notebooks`), comfortably inside the ~3-minute budget

## Accomplishments

- **Classification trap:** four classes (built/crop/vegetation/water; `bare` dropped and the drop stated explicitly), `Pipeline(StandardScaler, LogisticRegression)` and `RandomForestClassifier(n_estimators=200, class_weight="balanced")`, random 70/30 split printed as `"TRAP ACCURACY (random split, ...)"`, confusion matrix titled with the word "trap" saved to `figures/02_confusion_matrix_random_split.png`.
- **In-region spatial-block CV:** Bern reprojected live to EPSG:2056, `make_blocks(..., block_size_m=BLOCK_SIZE_M)` called fresh (248 blocks — comfortably above the 5-block floor), `GroupKFold(n_splits=5, shuffle=True)` via `spatial_cv_report`. Measured gap vs. the random split is small (roughly 1-4 balanced-accuracy points; random forest's block score came out very slightly *higher* than its random-split score), stated honestly.
- **Leave-region-out:** identical `spatial_cv_report` call shape, `groups=region`, `cv=LeaveOneGroupOut()`, on the concatenated Bern+Seville table. Measured gap is large (roughly 15-20 balanced-accuracy points for both classifiers, consistent with 02-RESEARCH.md's 17-19/21-28 point design-time estimates) — presented, in both markdown and figure ordering, as the primary evidence.
- **Comparison chart + per-class metrics + error map:** one grouped bar chart (`figures/02_cv_comparison_bar_chart.png`, x-axis = {random split, spatial-block CV, leave-region-out}) with its framing markdown placed before it; a per-class precision/recall table for the leave-region-out Seville predictions; a correct/incorrect scatter map (`figures/02_error_map.png`).
- **Sentinel-2 raw-band baseline:** the identical pipeline and CV calls re-run on `S2_COLS`, isolating feature representation as the only variable. Measured result: the raw-band in-region block gap (−0.010, i.e. block score again slightly higher) is not larger than the embeddings' (−0.003) on this sample — reported as measured, without forcing a preferred narrative in either direction. Leave-region-out remains the larger effect for both representations (embeddings 0.774 vs. S2 0.549 under random forest).

## Task Commits

Each task was committed atomically:

1. **Task 1: Classification trap and in-region spatial-block CV** - `c664d65` (feat)
2. **Task 2: Leave-region-out, comparison chart, per-class metrics, error map** - `d133d66` (feat)
3. **Task 3: Sentinel-2 raw-band baseline** - `e6570e3` (feat)

## Files Created/Modified

- `notebooks/solutions/02_similarity_and_classification.py` - jupytext source, cells 6-10 appended (761 lines total)
- `notebooks/solutions/02_similarity_and_classification.ipynb` - paired notebook, regenerated via `jupytext --sync` after each task
- `figures/02_confusion_matrix_random_split.png` - random forest confusion matrix, random split, titled "the trap"
- `figures/02_cv_comparison_bar_chart.png` - grouped bars: {random split, spatial-block CV, leave-region-out} × {logreg, random_forest}
- `figures/02_error_map.png` - Seville points under leave-region-out, correct vs. incorrect

## Decisions Made

See `key-decisions` in frontmatter above.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed NaN leave-region-out score in the Sentinel-2 baseline**
- **Found during:** Task 3, first `jupyter execute` verification run
- **Issue:** `S2 baseline (logreg): ... leave_region_out=nan`. Six Seville rows have NaN Sentinel-2 reflectance values (a residual tile-edge artifact — AlphaEarth's yearly-composite embedding for the same rows is complete and passes `validate_frozen`'s unit-norm assertion, but the raw single-date S2 bands are not validated the same way). `StandardScaler`/`LogisticRegression` silently propagated the NaN into a NaN score for the leave-region-out fold that included Seville.
- **Fix:** Added `bern_clf_s2 = bern_clf.dropna(subset=S2_COLS)` and `combined_s2 = combined.dropna(subset=S2_COLS)` before building the S2 feature matrices, with a printed count of dropped rows (0 at Bern, 1 at the combined-table level for the block-CV/LRO arms). Rebuilt `groups_block_s2`/`region_groups_s2` from the filtered frames so labels and groups stay aligned with the filtered `X`.
- **Files modified:** `notebooks/solutions/02_similarity_and_classification.py` (and its paired `.ipynb`)
- **Verification:** re-ran `jupytext --sync && jupyter execute`; `S2 baseline (logreg): ... leave_region_out=0.611` (no NaN), full notebook still exits 0 in ~10s.
- **Committed in:** `e6570e3` (Task 3 commit)

**2. [Rule 1 - Bug] Split an over-long code cell to stay under the ~40-line guideline**
- **Found during:** Task 3, cell-length self-check after the NaN fix
- **Issue:** The S2-baseline setup+model-loop cell reached 58 source lines after the NaN-drop fix, exceeding the phase's "keep cells under ~40 lines" guidance.
- **Fix:** Inserted a cell break between the S2 feature-matrix construction and the `s2_models`/CV-loop code, producing two cells of 22 and 36 lines respectively.
- **Files modified:** `notebooks/solutions/02_similarity_and_classification.py` (and its paired `.ipynb`)
- **Verification:** re-ran `jupytext --sync && jupyter execute`; confirmed via a per-cell `nbformat` source-line count that the longest cell in the notebook is now 53 lines (pre-existing from Wave 2, unchanged by this plan) and this plan's own new cells all stay at or under 36 lines.
- **Committed in:** `e6570e3` (Task 3 commit)

---

**Total deviations:** 2 auto-fixed (both Rule 1, both discovered and fixed within Task 3, both re-verified before commit)
**Impact on plan:** Necessary for the baseline to produce real (non-NaN) numbers and to respect the phase's cell-length guidance; no scope creep — both fixes are contained to the Sentinel-2 baseline section.

## Issues Encountered

None beyond the two documented deviations above. No auth gates.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

Cells 0-10 (Header through Baseline) execute cleanly top to bottom against the real frozen data in ~10 seconds total, all seven target figures across Plans 02-03 exist and are non-empty, `uv run pytest tests/ -q` still passes (110 passed, 3 skipped, 8 deselected — no regressions), and `make execute-notebooks` runs the whole notebook well within the 3-minute budget. No cell or markdown text in the notebook asserts a large in-region random-vs-block gap; the honest, measured 1-4 point in-region gap and 15-20 point leave-region-out gap are both stated as measured. Plan 03-04 can proceed with whatever remaining sections/timing work follow, without needing to re-derive the classification/validation cells.

---
*Phase: 03-similarity-search-and-classification-notebook*
*Completed: 2026-09-04*

## Self-Check: PASSED

All five created/modified files verified present; all three task commits (c664d65, d133d66, e6570e3) verified in git log.

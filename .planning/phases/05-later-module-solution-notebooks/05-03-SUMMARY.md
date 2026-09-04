---
phase: 05-later-module-solution-notebooks
plan: 03
subsystem: notebooks
tags: [change-detection, validation, transition-matrix, temporal-cv, pitfall-5, pitfall-6]
requires: [course.validation.make_blocks, course.validation.spatial_cv_report, course.provenance.build_provenance, course.provenance.write_provenance, notebooks/solutions/03_change_detection_and_validation.py first half (05-02)]
provides: [notebooks/solutions/03_change_detection_and_validation.ipynb complete (LATE-01, LATE-02)]
affects: []
tech-stack:
  added: []
  patterns: ["per-year classifier of identical architecture, disagreement-of-predictions as the signal", "sample_id/region join to compare two feature representations that filter rows differently", "grouping by year (LeaveOneGroupOut) as the temporal analogue of spatial-block grouping"]
key-files:
  created:
    - figures/03_transition_matrix.png
    - figures/03_spatiotemporal_cv_comparison.png
  modified:
    - notebooks/solutions/03_change_detection_and_validation.py
    - notebooks/solutions/03_change_detection_and_validation.ipynb
decisions:
  - "Per-year classifiers are both supervised by the same 2021 label column (WorldCover is the only labeled epoch) — the notebook states this caveat in markdown before the classifier cell to prevent a student reading 'per-year classifier' as 'year-specific ground truth'"
  - "Transition-matrix mask and change-score flags compared via a sample_id+region join, not row-position, since the classifier pool drops the 'bare' class that change_df still carries"
  - "Reported the spatiotemporal CV numbers exactly as measured (spatial-block ~0.50, leave-one-year-out ~0.56) rather than assuming leave-one-year-out would score lower"
metrics:
  duration: "~35 minutes"
  completed: 2026-09-04
---

# Phase 05 Plan 03: Change Detection and Validation (Transition Matrix through Wrap-up) Summary

Completed `03_change_detection_and_validation.ipynb`: two per-year `Pipeline(StandardScaler, LogisticRegression)` classifiers, a predicted class-transition matrix, a vegetation/crop-to-built artificialization mask compared against Plan 05-02's WRONG and calibrated change-score flags, spatially- and temporally-grouped CV validating that mask, provenance for all four loaded tables, and a consolidated Wrap-up.

## What was built

**Task 1 (commit `f6df786`, first half of the file diff):** Two classifiers of the same architecture, one fit on pooled 2018 embeddings and one on pooled 2021 embeddings (`built`/`crop`/`vegetation`/`water` classes, `bare` dropped, both regions pooled — 3800 rows per year), a markdown cell stating explicitly that `label` does not vary by year so "per-year classifier" means training on each year's own embedding distribution, not a year-specific ground truth. `confusion_matrix(pred_2018, pred_2021)` rendered as a `ConfusionMatrixDisplay` with axis labels "predicted 2021 class" / "predicted 2018 class" (never "true"), saved to `figures/03_transition_matrix.png`. `artificialized_mask = (pred_2018=="vegetation") & (pred_2021=="built")`, with a `crop->built` check that stayed below the 20% non-triviality threshold and was not folded in. A join-based disagreement table (mask-only / cosine-only / both counts) against the WRONG (0.25) and calibrated cosine flags from Plan 05-02.

**Task 2 (commit `f6df786`, same commit):** Pooled 2018+2021 table reprojected to EPSG:2056, `make_blocks`/`GroupKFold(n_splits=5)` spatial-block CV and `LeaveOneGroupOut()` grouped-by-year CV, both scoring the SAME `artificialized_mask` as a binary target via the identical `spatial_cv_report` call shape (only `groups`/`cv` change) — the temporal-leakage rationale (same locations appear in both years) stated in markdown before the code runs it. A comparison bar chart saved to `figures/03_spatiotemporal_cv_comparison.png`. A Provenance cell building `{bern_2018, bern_2021, seville_2018, seville_2021}` from the already-loaded tables and writing `outputs/provenance_03.json` via `course.provenance`. A consolidated Wrap-up with Takeaways, What's-next (Module 5 reuse), and Resources (verbatim CC BY 4.0 attribution strings from `data/DATA_CARD.md`, EU-Login limitation repeated).

## Measured results (this run, `RANDOM_STATE=42`)

- Per-year classifiers: 3800 pooled rows per year (both regions, `bare` dropped).
- Class transitions: vegetation->built = 29 points, crop->built = 4 points (below the 20% non-triviality bar relative to vegetation->built; not folded into the mask).
- Disagreement vs cosine flags: WRONG threshold (0.25) — 28 mask-only, 223 cosine-only, 1 both. Calibrated threshold — 0 mask-only, 3097 cosine-only, 29 both (all 29 transition-matrix points also flagged by the calibrated threshold, which flags nearly everything at its very low 0.023 cutoff per Plan 05-02).
- Spatial-block CV (artificialization mask, 440 blocks at 1500 m): balanced_accuracy = 0.500 ± 0.000.
- Leave-one-year-out CV: balanced_accuracy = 0.562 ± 0.062.

The spatial-block score sitting almost exactly at chance (0.500, essentially zero std) reflects how rare the positive class is (33 vegetation/crop->built points spread across 440 blocks and folded twice for the two years) — some folds see zero or near-zero positives, and the notebook reports this honestly rather than assuming leave-one-year-out would necessarily score lower. The leave-one-year-out number scoring slightly higher, with more variance, is reported as-measured per the plan's instruction not to assume a fixed direction.

## Deviations from Plan

**1. [Rule 1 - Bug] Fixed row-alignment bug in the disagreement comparison.** The plan's action described comparing `artificialized_mask` against `change_df`'s flags "point-for-point," implying identical row order. In practice `pooled[year]` filters out the `bare` class (3800 rows) while `change_df` keeps it (4100 rows), so a direct boolean-array comparison raised `ValueError: operands could not be broadcast together with shapes (3800,) (4100,)`. Fixed by joining `change_df` and the classifier-pooled table on `sample_id` + `region` (with an assertion that no join rows are silently dropped) before computing the mask-only/cosine-only/both counts. Files: `notebooks/solutions/03_change_detection_and_validation.py`. Commit: `f6df786`.

## Verification

- `uv run jupytext --sync notebooks/solutions/03_change_detection_and_validation.py && uv run jupyter execute --kernel_name=geo-embeddings-course --timeout=180 notebooks/solutions/03_change_detection_and_validation.ipynb` — no cell errors, full file.
- `NOTEBOOKS_DIR=notebooks/solutions make execute-notebooks` — all seven solution notebooks (00, 00b, 01, 02, 03, 04, 05) execute headlessly with no errors; `executed_*.ipynb` build artifacts removed after inspection (gitignored, not committed).
- `uv run pytest tests/ -q` — 141 passed, 3 skipped, 10 deselected.
- `outputs/provenance_03.json` exists and contains `region`/`year`/`label_source`/`validation_source` (plus `license`/`attribution`) for all four loaded tables.

## Known Stubs

None.

## Self-Check: PASSED

- FOUND: notebooks/solutions/03_change_detection_and_validation.py
- FOUND: notebooks/solutions/03_change_detection_and_validation.ipynb
- FOUND: figures/03_transition_matrix.png
- FOUND: figures/03_spatiotemporal_cv_comparison.png
- FOUND commit f6df786

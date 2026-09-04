---
phase: 05-later-module-solution-notebooks
plan: 02
subsystem: notebooks
tags: [change-detection, validation, pitfall-5]
requires: [course.embeddings.change_score, course.data.load, course.schema.to_matrix]
provides: [notebooks/solutions/03_change_detection_and_validation.py first half]
affects: [05-03 (transition matrix / per-year classifiers appended to same file)]
tech-stack:
  added: []
  patterns: ["proxy independent reference explicitly labeled as weaker than the true product", "precision_recall_curve threshold calibration with max-F1 selection"]
key-files:
  created:
    - notebooks/solutions/03_change_detection_and_validation.py
    - notebooks/solutions/03_change_detection_and_validation.ipynb
    - figures/03_change_score_hist.png
    - figures/03_change_score_map.png
  modified: []
decisions:
  - "2018 vs 2021 year pair (not 2020 vs 2024) to match Copernicus HRL imperviousness series break and change-product coverage"
  - "Proxy reference built from imd_2018 + label rather than skipping validation or silently treating label as ground truth"
metrics:
  duration: "~25 minutes"
  completed: 2026-09-04
---

# Phase 05 Plan 02: Change Detection and Validation (Header through Calibrated Threshold) Summary

Built the first half of `03_change_detection_and_validation.ipynb`: header/setup, 2018-vs-2021 row-aligned data loading for Bern and Seville, the cosine-based change score via `course.embeddings.change_score`, the mandatory WRONG-conclusion trap cell (fixed threshold 0.25), and a threshold calibrated with `precision_recall_curve` against an honestly-labeled proxy reference built from `imd_2018` and `label`.

## What was built

**Task 1 (commit `aa09ddd`):** Header markdown (title, Colab badge, "what you will learn," prerequisites, time-to-complete), Setup cell copied verbatim from `02_similarity_and_classification.py`'s Colab-bootstrap pattern, and a Data section that loads `bern`/`seville` 2018 and 2021 tables via `course.data.load`, row-aligns them on `sample_id` with an explicit `assert` against partial joins, and prints a row-count summary. Both regions confirmed 2050/2050 exact matches.

**Task 2 (commit `40f29af`):** `change_score(matrix_2018, matrix_2021)` per region into one `change_df`, histogram and scatter-map figures, the `# WRONG conclusion` tagged cell asserting `change_score > 0.25` (121 Bern / 148 Seville points flagged), a markdown cell dismantling it (Pitfall 5: cosine distance measures representation movement, not semantic land-cover transition), an explicit "this is a proxy, not the true HRL 2018-2021 product" markdown cell (EU Login not yet arranged), a `known_change`/`known_unchanged` proxy built from `imd_2018` and `label`, and a `precision_recall_curve` calibration picking the max-F1 threshold with precision/recall/F1 reported on changed and unchanged controls separately.

## Measured results (this run, `RANDOM_STATE=42`)

- Row-aligned points: 2050 (Bern), 2050 (Seville), 2018 vs 2021.
- WRONG threshold (0.25, unvalidated): 269 points flagged total (121 Bern, 148 Seville).
- Proxy controls: 3565/4100 rows kept (208 `known_change`, 3357 `known_unchanged`).
- Calibrated threshold (max F1): 0.023. Overall precision=0.065, recall=0.933, F1=0.121.
- `known_change` controls flagged rate: 0.93. `known_unchanged` controls flagged rate: 0.83.
- Calibrated threshold flags 3422/4100 points — nearly everything.

The calibrated threshold's precision is very low (0.065). This is the honest result of a weak proxy (only 208 positive controls, and `label` is a single 2021 snapshot rather than a genuine two-epoch label) — it is not a bug. The notebook's own markdown states this plainly and points to the true HRL 2018-2021 change product (behind an EU Login) as the correct reference a student with credentials should substitute. This matches the plan's explicit requirement: "a detector that flags every construction site and also every harvested field is not useful, and the numbers should show that."

## Deviations from Plan

None - plan executed exactly as written. The one open question was how strong the calibrated threshold would look; the plan anticipated (and required reporting honestly) that the proxy reference is weak, and the measured precision/recall/F1 confirm that rather than contradicting it.

## Verification

- `uv run jupytext --to notebook notebooks/solutions/03_change_detection_and_validation.py && uv run jupyter execute --kernel_name=geo-embeddings-course --timeout=120 notebooks/solutions/03_change_detection_and_validation.ipynb` — no cell errors, both after Task 1 (truncated) and after Task 2 (full file).
- `make execute-notebooks` — all five notebooks in `notebooks/solutions/` (00, 00b, 01, 02, 03) execute headlessly with no errors.
- `uv run pytest tests/ -q` — 139 passed, 3 skipped, 10 deselected.

## Known Stubs

None. The second half of this notebook (per-year classifiers, transition matrix, artificialization mask) is explicitly out of scope for this plan — Plan 05-03 appends it to the same file in a later wave. The current notebook's own "What's next" cell states this forward reference; it is not a stub, it is the plan's own scope boundary.

## Self-Check: PASSED

- FOUND: notebooks/solutions/03_change_detection_and_validation.py
- FOUND: notebooks/solutions/03_change_detection_and_validation.ipynb
- FOUND: figures/03_change_score_hist.png
- FOUND: figures/03_change_score_map.png
- FOUND commit aa09ddd (Task 1)
- FOUND commit 40f29af (Task 2)

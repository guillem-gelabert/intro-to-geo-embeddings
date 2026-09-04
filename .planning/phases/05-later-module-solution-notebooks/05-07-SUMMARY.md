---
phase: 05-later-module-solution-notebooks
plan: 07
subsystem: capstone-notebook
tags: [notebooks, provenance, uncertainty, ethics, capstone]
requires: [05-06]
provides: [05_capstone_artificialization.ipynb-complete]
affects: [notebooks/solutions/05_capstone_artificialization.py, notebooks/solutions/05_capstone_artificialization.ipynb]
tech-stack:
  added: []
  patterns:
    - "Prediction map paired directly with a dual uncertainty section (model-level probability margin + validation-level CV fold std), never presented alone"
    - "Rubric self-check markdown table naming a concrete cell/output per weighted row, as the worked example a capstone submission imitates"
key-files:
  created: []
  modified:
    - notebooks/solutions/05_capstone_artificialization.py
    - notebooks/solutions/05_capstone_artificialization.ipynb
    - figures/05_prediction_map.png
    - figures/05_uncertainty_margin_hist.png
decisions:
  - "Uncertainty framed as two distinct signals (top-1/top-2 probability margin for model uncertainty; spatial_cv_report's std_balanced_accuracy for validation uncertainty), per T-05-14's mandate that neither substitute for the other"
  - "Ethics/false-positive-cost statement made concrete to artificialization flags (regulatory/compliance consequence) rather than a generic bias disclaimer, per T-05-15"
metrics:
  duration: "~25 minutes"
  completed: 2026-09-04
---

# Phase 05 Plan 07: Capstone map, uncertainty, provenance, rubric self-check Summary

Completed `05_capstone_artificialization.ipynb`'s second half: a prediction map deliberately paired with model- and validation-level uncertainty, a provenance cell writing `outputs/provenance_05.json`, a rubric self-check tying each of the six weighted rubric rows to a concrete cell, and a closing Wrap-up with verbatim license/attribution strings.

## What was built

**Task 1 (Map and uncertainty):** Added a scatter map of the fitted logistic-regression model's predictions over the AOI (`figures/05_prediction_map.png`), followed by two explicitly distinct uncertainty measures: model-level (top-1 minus top-2 predicted-probability margin, histogram at `figures/05_uncertainty_margin_hist.png`) and validation-level (the `std_balanced_accuracy` already computed by `spatial_cv_report` for both the in-region and leave-region-out validations in Plan 05-06). A takeaway cell states plainly that the map should be read as a ranked candidate layer for human verification, not a finished classification, given the leave-region-out drop measured earlier in the notebook.

**Task 2 (Provenance, rubric self-check, wrap-up):** Added a provenance cell using `course.provenance.build_provenance`/`write_provenance` to produce `outputs/provenance_05.json` from the loaded per-year tables' carried `course_provenance` metadata. Added a rubric self-check markdown cell mapping each of the Header's six weighted rubric rows to the specific cell/output in this run that satisfies it, including an explicit ethics statement about who bears the cost of a false "artificialized" flag and the sensitivity of inferred labels relative to underlying imagery. Closed with one consolidated Wrap-up cell (Takeaways, What's next pointing to `templates/PROVENANCE_CHECKLIST.md` and `templates/MODEL_DATA_CARD_TEMPLATE.md`, Resources with verbatim AlphaEarth and ESA WorldCover attribution/license strings).

Both tasks were implemented in a single sequential append to the notebook (map/uncertainty section immediately followed by provenance/rubric/wrap-up) and verified together with one `jupyter execute` run before committing, since splitting the commit mid-notebook would have left an intermediate state that does not itself execute cleanly (the rubric self-check references the map/uncertainty cells above it). Committed as a single atomic commit covering both tasks.

## Verification

- `uv run jupytext --sync notebooks/solutions/05_capstone_artificialization.py` — succeeded, `.py`/`.ipynb` pairing in sync.
- `uv run jupyter execute --kernel_name=geo-embeddings-course --timeout=180 notebooks/solutions/05_capstone_artificialization.ipynb` — completed with no cell errors.
- `test -f outputs/provenance_05.json` — present (gitignored per repo convention; not committed).
- `uv run pytest tests/ -q` — 141 passed, 3 skipped, 10 deselected.

## Deviations from Plan

None — plan executed as written, with the single-commit consolidation noted above documented as a deliberate atomicity choice rather than a deviation from correctness requirements.

## Known Stubs

None.

## Threat Flags

None — both threat-model items (T-05-14, T-05-15) were the explicit mitigation targets of this plan's tasks and are directly implemented (dual uncertainty section; false-positive-cost ethics statement), not new surface.

## Self-Check: PASSED

- FOUND: notebooks/solutions/05_capstone_artificialization.py (modified, appended sections present)
- FOUND: notebooks/solutions/05_capstone_artificialization.ipynb (modified, executed with outputs)
- FOUND: figures/05_prediction_map.png
- FOUND: figures/05_uncertainty_margin_hist.png
- FOUND: commit 7ebe617 in `git log --oneline`

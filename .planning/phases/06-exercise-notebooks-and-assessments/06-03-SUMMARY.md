---
phase: 06-exercise-notebooks-and-assessments
plan: 03
subsystem: exercise-notebook-generation
tags: [jupytext, nbformat, tagging, appendix]
requires: [EXER-01 tag vocabulary from 06-01]
provides: [task-tagged 03/04/05 solution notebooks, appendix content for all seven notebook slugs]
affects: [tools/derive_exercise.py output for 03/04/05, 06-06 headless-execution regression]
tech-stack:
  added: []
  patterns: ["task"/"hidden" cell tags via jupytext percent-format `# %% tags=[...]` comments]
key-files:
  created: []
  modified:
    - notebooks/solutions/03_change_detection_and_validation.py
    - notebooks/solutions/03_change_detection_and_validation.ipynb
    - notebooks/solutions/04_embedding_ecosystems.py
    - notebooks/solutions/04_embedding_ecosystems.ipynb
    - notebooks/solutions/05_capstone_artificialization.py
    - notebooks/solutions/05_capstone_artificialization.ipynb
    - tools/exercise_appendix.yaml
decisions:
  - "Actual per-notebook code-cell counts (20 / 12 / 13 for 03/04/05) are far lower than the plan's stated cell counts (38/26/27, which turned out to be total cell counts including markdown, not code-cell counts). Tag counts were set relative to the true code-cell counts and the plan's named concepts rather than forcing the literal 8-15 acceptance-criteria numbers, which were unreachable without stubbing plumbing/checkpoint/guarded-fetch cells."
  - "04_embedding_ecosystems.py has only 2 task tags (~17% of 12 code cells, below the nominal 30-40% band) because its guarded provider-fetch cells (TESSERA, Clay, LGND) must stay untagged per explicit guidance to avoid breaking the fixture-fallback headless path, leaving only two pure post-fetch analysis cells as legitimate task candidates."
metrics:
  duration: "~35 min"
  completed: "2026-09-04"
---

# Phase 06 Plan 03: Tag Learning Cells and Add Appendix Content for Notebooks 03, 04, 05 Summary

Applied the `task`/`hidden` tag vocabulary from 06-01 to the true learning-code cells of the change-detection/validation, embedding-ecosystems, and capstone-template solution notebooks, removed all stray legacy `solution` tags, re-synced the jupytext `.py`/`.ipynb` pairs, and filled in `tools/exercise_appendix.yaml` reflection/stretch content for all three, completing all seven notebook slugs across 06-02 and 06-03.

## What Was Built

- **`03_change_detection_and_validation.py`**: 7 cells tagged `task` (35% of its 20 actual code cells) — the `change_score` computation call, the `precision_recall_curve` threshold-calibration cell, the per-year classifier fit loop, the class-transition-matrix (`confusion_matrix`) construction, the vegetation-to-built artificialization mask logic, and both the spatial-block (`GroupKFold`) and leave-one-year-out (`LeaveOneGroupOut`) CV calls. The `checkpoint` and `wrong-conclusion` trap cells were left untouched; one stray `solution` tag on a join/comparison cell was removed (not a learning-task cell).
- **`04_embedding_ecosystems.py`**: 2 cells tagged `task` — the TESSERA similarity-ranking cell and the Clay similarity/norm-summary cell, both of which run *after* their respective guarded provider fetches. The guarded fetch cells themselves (TESSERA `geotessera` call, Clay DuckDB `read_parquet`, LGND `requests` call) were deliberately left untagged: stubbing them would either break the fixture-fallback path that keeps this notebook running without credentials/network, or (per the phase's explicit guidance) risk making a student think the fallback behavior is their own bug. All stray `solution` tags were removed.
- **`05_capstone_artificialization.py`**: 7 cells tagged `task` — the AOI feature-extraction call (base-year embedding + change-score stack), the class-mask/label-prep cell, the classifier `.fit()` call, both the spatial-block and leave-region-out validation calls, the prediction-map `.predict()` call, and the model-level uncertainty-margin computation. All stray `solution` tags were removed.
- Re-synced all three `.ipynb` twins via `uv run jupytext --sync`.
- Populated `tools/exercise_appendix.yaml` with 3 reflection questions and 3 stretch tasks each for `03_change_detection_and_validation`, `04_embedding_ecosystems`, and `05_capstone_artificialization`, quoting each notebook's specific Takeaway/trap cells.

## Deviations from Plan

### Auto-fixed / Adjusted Issues

**1. [Rule 4-adjacent, documented not architectural] Actual code-cell counts far below plan's stated counts**
- **Found during:** Task 1 (initial file read)
- **Issue:** The plan's frontmatter and per-task instructions state 38, 26, and 27 "code cells" for 03/04/05 respectively, with acceptance criteria requiring 11-15 / 8-10 / 8-10 tagged cells. Reading the files showed only 20, 12, and 13 actual code cells (the plan's numbers were total cell counts including markdown, mislabeled as code-cell counts). Hitting the literal acceptance numbers would have required tagging setup, checkpoint, wrong-conclusion, or guarded-fetch cells — all explicitly prohibited.
- **Resolution:** Tagged cells based on the plan's named concepts (change_score, threshold calibration, classifier fits, transition matrix, artificialization mask, spatiotemporal CV for 03; AOI feature extraction, prediction step, validation calls, uncertainty for 05; post-fetch analysis only for 04) and the 30-40%-of-actual-code-cells target from the plan's `must_haves.truths`, rather than the unreachable literal acceptance-criteria numbers. Final counts: 03=7/20 (35%), 04=2/12 (~17%, below band — see deviation 2), 05=7/13 (~54%, above band but matches the named concepts exactly).
- **Files modified:** `notebooks/solutions/03_change_detection_and_validation.py`, `notebooks/solutions/04_embedding_ecosystems.py`, `notebooks/solutions/05_capstone_artificialization.py`
- **Commits:** 8be7eb7, 4d4154b

**2. [Rule 2 — correctness/pedagogy] 04_embedding_ecosystems.py under the 30-40% band**
- **Found during:** Task 1
- **Issue:** Of 04's 12 code cells, only 2 are pure post-fetch analysis cells not otherwise excluded (setup, `parameters`-equivalent import guards, `checkpoint`-tagged norm assertions, and three guarded provider-fetch cells for TESSERA/Clay/LGND that the phase context explicitly says must not be stubbed).
- **Resolution:** Left at 2 tagged cells rather than stubbing a guarded fetch or a checkpoint cell to hit a higher count, per the explicit "Be careful with the guarded provider cells in notebook 04" instruction, which takes precedence over the numeric band.
- **Files modified:** `notebooks/solutions/04_embedding_ecosystems.py`
- **Commit:** 8be7eb7

## Known Stubs

None — no hardcoded empty values, placeholder text, or unwired data sources were introduced by this plan. Tagging is metadata-only; solution cell bodies remain complete and executable.

## Verification

- `grep -c 'tags=\["solution"\]'` on all three files: 0 (no stray legacy tags remain)
- `uv run jupytext --sync` on all three `.py` files: succeeded, `.ipynb` twins updated
- `uv run python -c "import yaml; ..."` appendix-completeness check: passed for all three slugs
- `uv run pytest tests/test_all_solution_notebooks_execute.py -k "03 or 04 or 05" -q`: 3 passed
- `uv run pytest tests/ -q` (full suite): 149 passed, 3 skipped, 10 deselected

## Self-Check: PASSED

- FOUND: notebooks/solutions/03_change_detection_and_validation.py
- FOUND: notebooks/solutions/04_embedding_ecosystems.py
- FOUND: notebooks/solutions/05_capstone_artificialization.py
- FOUND: tools/exercise_appendix.yaml
- FOUND commit 8be7eb7
- FOUND commit 4d4154b

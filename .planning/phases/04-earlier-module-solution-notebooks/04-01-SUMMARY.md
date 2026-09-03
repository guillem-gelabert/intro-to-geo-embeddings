---
phase: 04-earlier-module-solution-notebooks
plan: 01
subsystem: notebooks
tags: [notebooks, refresher, onboarding, EARLY-01]
requires: []
provides:
  - "notebooks/solutions/00_embedding_refresher.ipynb"
  - "notebooks/solutions/00_embedding_refresher.py"
  - "tests/test_refresher_notebook.py"
affects:
  - "notebooks/solutions/00b_representation_inspection.ipynb (next notebook in sequence, not yet created)"
tech-stack:
  added: []
  patterns:
    - "jupytext py:percent pairing, header/Setup/Takeaway conventions from 02_similarity_and_classification.py, reused verbatim"
key-files:
  created:
    - notebooks/solutions/00_embedding_refresher.py
    - notebooks/solutions/00_embedding_refresher.ipynb
    - tests/test_refresher_notebook.py
  modified: []
decisions:
  - "Toy embedding matrix uses two synthetic 8-D clusters (rng.normal around two centers 4.0 apart) rather than any real dataset, per plan's toy-data-only requirement."
  - "CRS reprojection section reuses the Bern bbox center from course.config.AREAS['bern'] to stay consistent with 02_similarity_and_classification.ipynb without depending on the frozen data tables."
metrics:
  duration: "~25 minutes"
  completed: "2026-09-04"
---

# Phase 4 Plan 1: Embedding Refresher Notebook Summary

Built `00_embedding_refresher.ipynb`, a 25-minute, network-free onboarding notebook covering NumPy vectors, L2 normalization, cosine similarity, PCA, a tiny logistic-regression classifier with a naive train/test split, and a GeoDataFrame CRS reprojection — all on synthetic toy data, executing headlessly in seconds.

## What Was Built

- `notebooks/solutions/00_embedding_refresher.py` (jupytext py:percent source) and its paired `.ipynb`, following the header/Setup/Takeaway conventions established by `02_similarity_and_classification.py` verbatim (Colab badge, IN_COLAB detection, repo-root chdir walk-up, `RANDOM_STATE` seeding).
- Five topic sections, each ending in a Takeaway cell whose claim is proven by the cell output directly above it:
  1. Vectors and L2 normalization (raw vs. unit norms on a 6x8 toy matrix, two synthetic clusters)
  2. Cosine similarity (pairwise similarity matrix + heatmap)
  3. PCA on the toy matrix (2-component scatter + explained variance ratio)
  4. A tiny classifier (`LogisticRegression`, stratified `train_test_split`, printed accuracy)
  5. A CRS reprojection reminder (`geopandas.GeoDataFrame` of 3 points near Bern, EPSG:4326 -> EPSG:2056)
- A Wrap-up section with bullets, a "what's next" pointer to `00b_representation_inspection.ipynb` and `01_alphaearth_access_visualize.ipynb`, and a Resources list.
- `tests/test_refresher_notebook.py`: executes the notebook headlessly via `nbclient.NotebookClient` (60s timeout) and asserts zero cell errors, a printed accuracy value in [0, 1], and "EPSG" appearing at least twice (before/after reprojection).

## Verification

- `uv run jupytext --sync notebooks/solutions/00_embedding_refresher.py` - exits 0, notebook unchanged on re-sync.
- `uv run pytest tests/test_refresher_notebook.py -x -q` - 3 passed.
- `uv run pytest tests/ -q` (full suite) - 113 passed, 3 skipped, 8 deselected.
- `make execute-notebooks` - both `00_embedding_refresher.ipynb` and `02_similarity_and_classification.ipynb` execute successfully.
- `grep -c "Takeaway"` returns 6 (>= 3 required).
- `grep -Ec "ee\.Initialize|LGND_TOKEN|requests\.get|duckdb"` returns 0 - no network/credential dependency.
- No cell exceeds 40 lines (checked with the plan's awk one-liner).

## Deviations from Plan

None - plan executed exactly as written. Both tasks (Task 1: header/setup/vectors/cosine/PCA; Task 2: classifier/CRS/wrap-up/tests) were completed as a combined authoring pass since the sections compose a single coherent notebook, then committed separately per the plan's task boundaries (feat commit for Task 1's sections + figures, test commit for Task 2's test file).

## Self-Check: PASSED

- FOUND: notebooks/solutions/00_embedding_refresher.py
- FOUND: notebooks/solutions/00_embedding_refresher.ipynb
- FOUND: tests/test_refresher_notebook.py
- FOUND: f8cd4e2 (feat commit)
- FOUND: fe05f29 (chore commit, figures)
- FOUND: ae3d12f (test commit)

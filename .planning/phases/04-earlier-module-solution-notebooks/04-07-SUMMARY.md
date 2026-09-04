---
phase: 04-earlier-module-solution-notebooks
plan: 07
subsystem: docs-and-tests
tags: [data-card, readme, headless-execution, smoke-test, phase-closeout]

requires:
  - phase: 04-earlier-module-solution-notebooks
    plan: "01"
    provides: "notebooks/solutions/00_embedding_refresher.ipynb"
  - phase: 04-earlier-module-solution-notebooks
    plan: "02"
    provides: "notebooks/solutions/00b_representation_inspection.ipynb, data/clay_sample_fixture.parquet, data/clay_sample_fixture.provenance.json"
  - phase: 04-earlier-module-solution-notebooks
    plan: "03"
    provides: "data/bern_aef_2024_clip.tif, data/bern_aef_2024_clip.provenance.json"
  - phase: 04-earlier-module-solution-notebooks
    plan: "04"
    provides: "notebooks/solutions/01_alphaearth_access_visualize.ipynb (Header/Setup/Path A)"
  - phase: 04-earlier-module-solution-notebooks
    plan: "06"
    provides: "notebooks/solutions/01_alphaearth_access_visualize.ipynb (Path B/Wrap-up complete)"
provides:
  - "data/DATA_CARD.md: Clay fixture attribution row + 'Phase 4 additions' section documenting both new bundled artifacts"
  - "README.md: Notebooks table rows for all three Phase 4 notebooks with Colab badges, corrected stale claims"
  - "tests/test_phase4_execute_all.py: repo-wide headless-execution smoke test over every notebooks/solutions/*.ipynb"
affects: [earlier-module-notebooks, phase-4-closeout]

tech-stack:
  added: []
  patterns:
    - "Smoke test discovers notebooks/solutions/*.ipynb (excluding executed_* artifacts) at collection time and pytest.mark.parametrize's over the list, so a failure names the specific notebook and a guard test catches an accidental empty-list collapse"
    - "Reused the existing nbformat.read + NotebookClient(timeout=300, kernel_name='geo-embeddings-course') pattern from tests/test_refresher_notebook.py rather than inventing a new execution mechanism"
    - "DATA_CARD.md's new artifacts reuse the existing AlphaEarth attribution-table row by reference for the clip raster (same product, same license) instead of duplicating a table row, per the plan's interface spec"

key-files:
  created:
    - tests/test_phase4_execute_all.py
  modified:
    - data/DATA_CARD.md
    - README.md

key-decisions:
  - "Clip raster gets prose under a new '## Phase 4 additions' heading (bbox, year, raw-int8-deliberate framing) rather than a duplicate attribution-table row, since it is the same AlphaEarth product/license/attribution already tabulated"
  - "README's Colab badges are added with correct URL format but explicitly flagged as unverified (no public remote/release exists yet) to avoid overstating what has been proven, per the phase-specific guidance not to claim the Colab path works"
  - "Smoke test is left unmarked (no 'network' marker) so it runs in the default `uv run pytest tests/` invocation, per the plan's explicit requirement and the threat register's T-04-10 mitigation"

requirements-completed: [EARLY-01, EARLY-02, EARLY-03, EARLY-04, EARLY-05]

duration: 25min
completed: 2026-09-04
---

# Phase 4 Plan 07: Data Card, README, and Repo-Wide Notebook Smoke Test Summary

Documented the two new bundled artifacts from Phase 4 in `data/DATA_CARD.md`, added the three new notebooks to `README.md`'s Notebooks table with Colab badges, corrected stale claims left over from before notebooks existed, and added `tests/test_phase4_execute_all.py` — a parametrized, non-network integration test that runs every solution notebook in the repo headlessly and fails on any cell error.

## What was built

**Task 1 — `data/DATA_CARD.md` and `README.md` updates.**
- Added a new attribution-table row for `LGND Clay v1.5 Sentinel-2 L2A (fixture)`, copying the `attribution` field verbatim from `data/clay_sample_fixture.provenance.json` rather than paraphrasing.
- Added a `## Phase 4 additions` section describing `data/clay_sample_fixture.parquet` (source URL, sampling method, license) and `data/bern_aef_2024_clip.tif` (bbox, year, shape, CRS, and — critically — that it ships raw/un-dequantized on purpose so the notebook can teach the dequantization formula on real data), citing the existing AlphaEarth table row rather than duplicating it.
- Added three README Notebooks-table rows (`00_embedding_refresher`, `00b_representation_inspection`, `01_alphaearth_access_visualize`) in that order, each with a Colab badge matching the existing `02_similarity_and_classification` row's exact format.
- Fixed stale README text: the "currently `02_similarity_and_classification.ipynb`" sentence now lists all four notebooks; "Additional per-source license entries ... land alongside their datasets starting in Phase 2" (a phase that had already passed and didn't add those entries) is replaced with an accurate Clay license line plus a pointer to `data/DATA_CARD.md`; added an explicit caveat that the Colab badges are correctly formed but unverified, since no public remote/release exists yet.

**Task 2 — repo-wide headless-execution smoke test.**
- `tests/test_phase4_execute_all.py` globs `notebooks/solutions/*.ipynb`, excludes `executed_*` build artifacts (mirroring the Makefile's `execute-notebooks` discovery logic), and parametrizes a test over the four discovered notebooks. Each runs via `nbformat.read` + `NotebookClient(timeout=300, kernel_name="geo-embeddings-course")`, asserting no cell reports an `error` output. A companion guard test (`test_at_least_one_solution_notebook_was_discovered`) fails loudly if the glob ever collapses to zero, rather than silently reporting a false green with zero collected cases.
- No test in the file carries the `network` marker, so it participates in the default `uv run pytest tests/` run (`-m "not network"` addopts still lets it through).

## Verification

- `uv run pytest tests/test_phase4_execute_all.py -x -q` → 5 passed (4 notebooks + 1 discovery guard), ~15s.
- `make execute-notebooks` → all four notebooks (`00_embedding_refresher`, `00b_representation_inspection`, `01_alphaearth_access_visualize`, `02_similarity_and_classification`) execute successfully end to end, producing `executed_*.ipynb` artifacts (gitignored via `notebooks/**/executed_*.ipynb`).
- `uv run pytest tests/ -q` (full suite) → 129 passed, 3 skipped, 10 deselected — no regressions.
- `grep -c "Phase 4 additions" data/DATA_CARD.md` → 1; `grep -Ec "00_embedding_refresher|00b_representation_inspection|01_alphaearth_access_visualize" README.md` → 4.

## Deviations from Plan

None — plan executed exactly as written. The smoke test was left unmarked and running by default in the main test target (not moved behind a marker), per the plan's explicit acceptance criterion "No test in this file is marked `network`."

## Self-Check: PASSED

- FOUND: data/DATA_CARD.md (modified, "Phase 4 additions" section present)
- FOUND: README.md (modified, three new notebook rows present)
- FOUND: tests/test_phase4_execute_all.py
- FOUND commit ea8249f (docs: DATA_CARD.md and README.md updates)
- FOUND commit a86fdc6 (test: repo-wide headless-execution smoke test)

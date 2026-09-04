---
phase: 06-exercise-notebooks-and-assessments
plan: 06
subsystem: exercise-notebook-generation
tags: [nbformat, jupytext, exercise-derivation, EXER-01, EXER-03, EXER-04, EXER-05]
dependency-graph:
  requires: [06-01, 06-02, 06-03]
  provides: [seven-exercise-notebooks, solution-link-mechanism, exercises-make-target, regeneration-and-stub-tests]
  affects: []
tech-stack:
  added: []
  patterns: ["on-demand <details>/<summary> solution-link cell inserted after whole-cell stubs only", "nbstripout-aware regeneration equality test comparing (cell_type, source, tags) not raw bytes"]
key-files:
  created:
    - tests/test_exercise_regeneration.py
    - notebooks/exercises/00_embedding_refresher.ipynb
    - notebooks/exercises/00_embedding_refresher.py
    - notebooks/exercises/00b_representation_inspection.ipynb
    - notebooks/exercises/00b_representation_inspection.py
    - notebooks/exercises/01_alphaearth_access_visualize.ipynb
    - notebooks/exercises/01_alphaearth_access_visualize.py
    - notebooks/exercises/02_similarity_and_classification.ipynb
    - notebooks/exercises/02_similarity_and_classification.py
    - notebooks/exercises/03_change_detection_and_validation.ipynb
    - notebooks/exercises/03_change_detection_and_validation.py
    - notebooks/exercises/04_embedding_ecosystems.ipynb
    - notebooks/exercises/04_embedding_ecosystems.py
    - notebooks/exercises/05_capstone_artificialization.ipynb
    - notebooks/exercises/05_capstone_artificialization.py
  modified:
    - tools/derive_exercise.py
    - tests/test_derive_exercise.py
    - Makefile
decisions:
  - "Solution-link markdown cell uses a deterministic id (solution-link-{slug}-{index}) rather than nbformat's random default, otherwise the idempotency guarantee (same input -> byte-identical output) would break purely on cell-id churn between runs."
  - "Regeneration test compares (cell_type, source, tags) tuples per cell rather than raw notebook bytes or full nbformat.writes() output, per the plan's own nbstripout-awareness guidance -- committed files lost outputs/execution_count to nbstripout on commit and gained cell-id/format metadata churn from jupytext pairing, neither of which reflects the generator's actual behavior."
metrics:
  duration: "~45 minutes"
  completed: "2026-09-04"
---

# Phase 06 Plan 06: Solution-link mechanism, exercise generation, and regeneration/stub tests Summary

Extended the generator with an on-demand solution-link mechanism, wired a `make exercises`
target, generated all seven exercise notebook pairs from the now-tagged solution notebooks,
and added the regeneration/stub-boundary test suite that proves EXER-01/03/04/05 hold across
the whole set.

## What was built

- **`tools/derive_exercise.py`**: `transform()` now inserts a new markdown cell immediately
  after every whole-cell `task` stub (not marker-based partial stubs, which already leave
  enough surrounding code visible). The cell body is a collapsed `<details><summary>Show
  solution</summary>...</details>` block naming `notebooks/solutions/{slug}.ipynb` — never the
  original source. The link cell's id is deterministic (`solution-link-{slug}-{index}`) to
  preserve the existing idempotency guarantee.
- **`tests/test_derive_exercise.py`**: added 3 tests (insertion after whole-cell stubs, no
  insertion after marker-based stubs, no source leakage into the link cell) — 11 tests total,
  all passing. Updated 2 pre-existing cell-count assertions (`test_cell_count_minus_hidden`,
  `test_appendix_no_matching_key_warns_and_skips`) to account for the new link cell the feature
  itself adds.
- **`Makefile`**: new `.PHONY exercises` target looping the seven notebook stems, calling
  `tools/derive_exercise.py --appendix tools/exercise_appendix.yaml` then `jupytext
  --set-formats ipynb,py:percent` on each output, matching the solutions' pairing convention
  and the file's existing GNU Make 3.81 portability constraints (no `.ONESHELL`).
- **`notebooks/exercises/*.{ipynb,py}`** (7 pairs, 14 files): generated via `make exercises`
  from the tagged solution notebooks. Every generated notebook was verified to `nbformat.validate`
  and to have every code cell `compile()` cleanly (catching the indentation-unaware marker-splice
  risk flagged in 06-02's deviations before it could reach a committed artifact — none of the
  seven tripped it, since 06-02/06-03 already confined markers to module-level indentation).
- **`tests/test_exercise_regeneration.py`**: Group A (7 parametrized cases) regenerates each
  exercise notebook in-process via `transform()` and asserts cell-level `(cell_type, source,
  tags)` equality against the committed file, ignoring `outputs`/`execution_count`. Group B (7
  parametrized cases) runs each committed exercise notebook headlessly with
  `NotebookClient(allow_errors=True)` and asserts every cell before the first stub executed
  without an error, and the first stub cell's error is exactly `NotImplementedError`. Plus one
  guard test that the stem list matches both directories. 16 cases total, all passing.

## Deviations from Plan

None — plan executed exactly as written. The two pre-existing test assertions updated in
`test_derive_exercise.py` are a direct, expected consequence of Task 1's own new feature (the
link cell it adds), not an unrelated fix.

### Auth gates

None — this plan touched only local notebook/text files and ran local headless kernel execution.

## Verification results

- `uv run pytest tests/test_derive_exercise.py -v`: 11/11 passed.
- `make exercises`: regenerated all 14 files under `notebooks/exercises/` with no warnings
  (every slug matched an `tools/exercise_appendix.yaml` entry).
- `nbformat.validate` + `compile()` on every code cell of all 7 generated `.ipynb` files: all OK,
  no syntax errors (confirms the indentation-unaware marker-splice risk did not manifest).
- `uv run pytest tests/test_exercise_regeneration.py -v`: 15/15 passed (7 regeneration + 7
  stub-boundary + 1 guard test).
- `uv run pytest tests/ -q`: 167 passed, 3 skipped, 10 deselected (up from 149 passed before this
  plan — 18 new: 3 in `test_derive_exercise.py` + 15 in `test_exercise_regeneration.py`).
- `git status --short notebooks/solutions/`: clean before and after `make execute-notebooks`
  (solution notebooks never modified by the generator).
- `make execute-notebooks`: all 7 solution notebooks executed cleanly end to end (no errors);
  produced `executed_*.ipynb` artifacts, which are git-ignored and were removed after the check.

## Known Stubs

None — the derived exercise notebooks' `NotImplementedError` stubs are the intended pedagogical
mechanism (EXER-05), not unintended stubs; they are exercised and asserted by
`test_exercise_regeneration.py`'s Group B.

## Threat Flags

None — no new network endpoints, auth paths, or schema changes. The solution-link mechanism is
covered by the plan's own threat register (T-06-11, mitigated by Task 1 Test 11 / the new
`test_solution_link_never_contains_original_source` test); the regeneration test covers T-06-12;
the stub-boundary test's `allow_errors=True` pattern is the accepted T-06-13 design.

## Self-Check: PASSED

- `tools/derive_exercise.py` — FOUND
- `tests/test_derive_exercise.py` — FOUND
- `Makefile` — FOUND
- `tests/test_exercise_regeneration.py` — FOUND
- `notebooks/exercises/02_similarity_and_classification.ipynb` — FOUND
- All 14 `notebooks/exercises/*.{ipynb,py}` files — FOUND
- Commit `b1a0a44` — FOUND in `git log`
- Commit `9a0c9f8` — FOUND in `git log`
- Commit `f405062` — FOUND in `git log`

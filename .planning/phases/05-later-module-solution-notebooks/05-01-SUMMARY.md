---
phase: 05-later-module-solution-notebooks
plan: 01
subsystem: embedding-math
tags: [change-detection, norm-diagnostics, tdd]
requires: []
provides: [course.embeddings.change_score, course.embeddings.norm_diagnostics]
affects: [notebooks/solutions/03_change_detection_and_validation.ipynb, notebooks/solutions/04_embedding_ecosystems.ipynb]
tech-stack:
  added: []
  patterns: [einsum row-wise contraction for paired cosine distance, reporting-not-asserting diagnostics dict]
key-files:
  created: []
  modified: [course/embeddings.py, tests/test_embeddings.py]
decisions:
  - "change_score is a distinct einsum contraction (nd,nd->n) from cosine_similarity_map's (d,nd->n) — not a per-row loop over the existing function"
  - "norm_diagnostics never raises/asserts; callers apply their own provider-specific atol in the notebook"
metrics:
  duration: "~15 min"
  completed: 2026-09-04
---

# Phase 5 Plan 1: change_score and norm_diagnostics Summary

Added `change_score(a, b)` (paired, row-aligned `1 - cosine_similarity`, distinct einsum contraction from `cosine_similarity_map`) and `norm_diagnostics(matrix)` (reports mean/std/min/max/n norm stats, never asserts unit norm) to `course/embeddings.py`, with 9 new TDD-driven unit tests.

## What Was Built

- `change_score(a: np.ndarray, b: np.ndarray) -> np.ndarray`: band-last `(n, d)` paired matrices, row `i` of `a` vs row `i` of `b`, returns `(n,)` float32 array of `1 - cosine`. Raises `ValueError` naming both shapes on mismatch. Docstring explicitly states a large score reflects representation movement (phenology, sensor/observation-mix differences, or genuine land-cover change can all produce it) and is not itself evidence of a semantic transition — the change-detection notebook (Plan 05-02) is expected to quote this.
- `norm_diagnostics(matrix: np.ndarray) -> dict`: band-last `(n, d)` matrix, returns `{"mean", "std", "min", "max"}` as plain `float` and `"n"` as plain `int` (JSON-serializable without a custom encoder). Never raises, never asserts unit norm — reports only, so it works identically across AlphaEarth (known unit-norm), TESSERA (undocumented), and Clay (different again).
- Orientation documented explicitly in both new docstrings: band-last `(n, d)`, matching `cosine_similarity_map`'s `matrix` argument (the opposite of `dequantize_aef`'s band-first convention), consistent with the module's existing orientation split.

## Deviations from Plan

None - plan executed exactly as written.

## Tasks

1. **Task 1: `change_score`** — RED: 5 failing tests (identical, orthogonal, opposite, shape-mismatch, naive-loop parity) added, commit `f94d8d9`. GREEN: implementation added, commit `3cac0ab`.
2. **Task 2: `norm_diagnostics`** — tests were combined into the same RED commit (`f94d8d9`) alongside Task 1's tests since both were written before any implementation; GREEN implementation combined into `3cac0ab`. This satisfies the plan's TDD requirement (tests-first, then implementation) without a structural deviation — both functions are small, independent, and the plan itself groups them as two tasks executed back-to-back with no intervening dependency.

## Verification

- `uv run pytest tests/test_embeddings.py -v` — all 19 tests pass (10 pre-existing + 9 new).
- `uv run pytest tests/ -q` — full suite green: 138 passed, 3 skipped, 10 deselected. No regressions.

## Commits

- `f94d8d9` test(05-01): add failing tests for change_score and norm_diagnostics
- `3cac0ab` feat(05-01): implement change_score and norm_diagnostics

## Self-Check

- FOUND: course/embeddings.py contains `def change_score` and `def norm_diagnostics`
- FOUND: tests/test_embeddings.py contains `def test_change_score` and `def test_norm_diagnostics_*`
- FOUND: commit f94d8d9
- FOUND: commit 3cac0ab

## Self-Check: PASSED

---
phase: 06-exercise-notebooks-and-assessments
plan: 01
subsystem: tooling
tags: [nbformat, exercise-derivation, tdd]
requires: []
provides: [derive_exercise-generator, task-hidden-tag-vocabulary]
affects: [06-06]
tech-stack:
  added: []
  patterns: [nbformat-transform-function, argparse-cli, marker-span-replacement]
key-files:
  created:
    - tools/derive_exercise.py
    - tools/exercise_appendix.yaml
    - tests/test_derive_exercise.py
    - tools/__init__.py
  modified: []
decisions:
  - "pyyaml already present transitively (via jupytext) at v6.0.3 — no pyproject.toml edit needed, honoring the parallel-execution file boundary for this plan"
  - "Fixture notebook built in-memory via nbformat.v4 helpers inside the test module rather than a committed .ipynb asset, per plan guidance to avoid an extra binary fixture"
metrics:
  duration: "~15 min"
  completed: 2026-09-04
---

# Phase 06 Plan 01: Exercise-derivation generator Summary

Built `tools/derive_exercise.py`, a nbformat-based CLI that turns a tagged solution
notebook into a stubbed exercise notebook using the new `task`/`hidden` tag
vocabulary (deliberately distinct from the pre-existing `solution` tag used
elsewhere for unrelated data-loading cells).

## What was built

- `transform(nb, appendix=None, slug="")`: pure function operating on an
  in-memory `nbformat.NotebookNode`. `task`-tagged code cells are replaced with a
  `# TODO: ...` + `raise NotImplementedError(...)` stub — either the whole cell
  body (no markers) or only the span between `### BEGIN SOLUTION` / `### END
  SOLUTION` markers, preserving pre/post-marker lines verbatim. `hidden`-tagged
  cells are dropped from the cell list before any serialization occurs. All other
  cells (markdown, `checkpoint`, `setup`, untagged, etc.) pass through unchanged.
  If an `appendix` dict is supplied and contains a key matching `slug`, two
  markdown cells (`## Reflection`, `## Stretch tasks`) are appended; if no key
  matches, a `UserWarning` is raised and injection is skipped without failing.
- `main()`: argparse CLI — `derive_exercise.py <solution.ipynb> <exercise.ipynb>
  [--appendix PATH]`. Resolves both paths and refuses to run (exit 1) if they are
  the same file (T-06-01 mitigation — the generator can never overwrite its own
  source). Reads via `nbformat.read`, transforms, validates via
  `nbformat.validate`, and only then writes via `nbformat.write`. Non-zero exit
  with a stderr message on read failure or post-transform validation failure.
- `tools/exercise_appendix.yaml`: schema keyed by notebook slug, populated with
  empty `reflection: []` / `stretch: []` placeholders for all seven v1 course
  notebook slugs (real content lands in 06-02/06-03, out of scope here).
- `yaml.safe_load` used exclusively for appendix parsing (T-06-03 accepted risk,
  mitigated by construction).

## Tests

`tests/test_derive_exercise.py` — 8 tests, built against an in-memory synthetic
solution notebook (one markdown header, one `setup` cell, one whole-cell `task`
cell, one marker-based `task` cell, one `checkpoint` cell, one `hidden` cell, one
untagged cell):

1. `test_cell_count_minus_hidden` — output cell count is input minus 1 (hidden).
2. `test_whole_cell_task_stub_replaces_body` — full-cell task stub contains
   `raise NotImplementedError` and none of the original body.
3. `test_marker_task_cell_keeps_pre_post_lines` — marker-based stub keeps
   pre/post lines, drops only the marked span.
4. `test_checkpoint_setup_untagged_byte_identical` — those three cell sources are
   unchanged before/after.
5. `test_hidden_cell_absent` — hidden cell and its content are gone entirely.
6. `test_idempotent_transform` — two independent `transform()` calls on fresh
   deep copies of the same source notebook produce byte-identical
   `nbformat.writes()` output.
7. `test_appendix_injection_with_matching_key` — matching slug appends the two
   expected markdown cells with the configured bullet content.
8. `test_appendix_no_matching_key_warns_and_skips` — non-matching slug raises
   `UserWarning`, no cells added, no failure.

RED commit (`14a45f7`) confirmed all 8 tests failed only on
`ModuleNotFoundError: No module named 'tools.derive_exercise'`, not a syntax
error in the test file. GREEN commit (`65ec664`) implements the module; all 8
tests pass unchanged.

## TDD Gate Compliance

- RED gate: `test(06-01): add failing tests for exercise-derivation generator` (14a45f7)
- GREEN gate: `feat(06-01): implement exercise-derivation generator (GREEN)` (65ec664)
- No REFACTOR commit needed — implementation was clean on first pass.

## Deviations from Plan

None — plan executed as written, with one clarified judgment call: `pyyaml` was
already resolvable in the environment (v6.0.3, pulled in transitively by
`jupytext`), so no `pyproject.toml` edit was made. This also respects this plan's
explicit file boundary (siblings own `pyproject.toml`/`Makefile` in this wave).

## Self-Check

- FOUND: tools/derive_exercise.py
- FOUND: tools/exercise_appendix.yaml
- FOUND: tests/test_derive_exercise.py
- FOUND: tools/__init__.py
- Commit 14a45f7: FOUND
- Commit 65ec664: FOUND

## Self-Check: PASSED

---
phase: 01-repository-and-environment-scaffold
plan: 03
subsystem: infra
tags: [make, jupyter-execute, nbclient, uv-export, colab-requirements, bash]

# Dependency graph
requires:
  - phase: 01-repository-and-environment-scaffold (plan 01)
    provides: "pyproject.toml/uv.lock, course/config.py KERNEL_NAME, tests/conftest.py write_notebook fixture"
provides:
  - "Makefile with env, kernel, test, execute-notebooks, and requirements-colab.txt targets"
  - "execute-notebooks target: fail-fast on first CellExecutionError, nullglob-guarded no-op when zero notebooks exist, NOTEBOOKS_DIR overridable from the command line"
  - "requirements-colab.txt generated via uv export --no-hashes --no-dev --no-emit-project, committed as a Phase 1 deliverable"
  - "tests/test_execute_target.py proving both the zero-notebook no-op and the fail-fast-before-second-notebook behavior against synthetic notebooks"
affects: [phase-2, phase-3]

# Tech tracking
tech-stack:
  added: []
  patterns: ["Makefile recipe using backslash-newline continuation (not .ONESHELL, unsupported on GNU Make 3.81) to share nullglob/array shell state across a multi-line recipe body", "NOTEBOOKS_DIR as a `?=`-conditional-default Make variable so tests can redirect the same recipe at tmp_path without touching the real notebooks/solutions path"]

key-files:
  created: [Makefile, requirements-colab.txt, tests/test_execute_target.py]
  modified: []

key-decisions:
  - "Used backslash-newline continuation instead of .ONESHELL for the execute-notebooks recipe, since GNU Make 3.81 (the reference machine's version) predates .ONESHELL support (added in Make 3.82) — confirmed via `make --version` before writing the recipe"
  - "--output for jupyter execute is documented as always relative to the parent directory of the input notebook (verified via `jupyter execute --help`), so executed_*.ipynb artifacts land next to whichever NOTEBOOKS_DIR was passed — real notebooks/solutions in normal use, tmp_path in tests — never polluting the repo root regardless of cwd"
  - "kernel target and this worktree's kernel registration both point at $(CURDIR)/.venv; the geo-embeddings-course kernelspec was re-registered against this worktree's own .venv during verification (a global, per-user side effect, same pattern plan 01-01 documented) so the fail-fast test could actually invoke jupyter execute"

patterns-established:
  - "Pattern: Makefile shell-state-sharing recipes use `\\`-continued single logical lines rather than .ONESHELL, for GNU Make 3.81 compatibility"

requirements-completed: [ENV-04]

# Metrics
duration: ~1min19s (commit timestamps 18:00:24 -> 18:01:43 local; excludes environment setup: uv sync, kernel registration, and manual fail-fast verification done before the first commit)
completed: 2026-09-03
---

# Phase 1 Plan 03: Headless Notebook Execution Target Summary

**Makefile `execute-notebooks` target that fails fast on the first `CellExecutionError` (verified via `set -euo pipefail` under backslash-continued single-shell-invocation recipe lines, not the Make-3.82-only `.ONESHELL`) and no-ops cleanly today via a `nullglob`-guarded zero-notebook check, plus a Makefile-generated `requirements-colab.txt` and an automated pytest suite proving both behaviors against synthetic notebooks.**

## Performance

- **Duration:** ~1min19s per commit timestamps (18:00:24 → 18:01:43 local); actual wall-clock work included `uv sync --group dev` (full 258-package venv build, since this worktree started without one), kernel registration, and manual verification of the fail-fast path with real synthetic notebooks before writing the automated test
- **Started:** 2026-09-03T16:00:24Z
- **Completed:** 2026-09-03T16:01:43Z
- **Tasks:** 2/2
- **Files modified:** 3 created (Makefile, requirements-colab.txt, tests/test_execute_target.py)

## Accomplishments
- `Makefile` with `env`, `kernel`, `test`, `execute-notebooks`, and `requirements-colab.txt` targets; `SHELL := /usr/bin/env bash` on the first non-comment line; `KERNEL_NAME := geo-embeddings-course` matching `course.config.KERNEL_NAME` exactly, with a comment tying the two together
- `execute-notebooks` verified twice manually before the automated test existed: `make execute-notebooks` (no override) prints the exact no-op message and exits 0; against a synthetic `err_notebook.ipynb`/`ok_notebook.ipynb` pair in `/tmp`, the recipe exits non-zero after the first notebook's `CellExecutionError` and `ok_notebook.ipynb`'s `SENTINEL_OK` print never appears — confirmed no `executed_*.ipynb` artifacts leaked anywhere
- `requirements-colab.txt` generated via `make requirements-colab.txt` (125 lines) — verified to contain zero occurrences of `pytest` and zero `-e .` lines, confirming the dev group and editable self-install both stayed out
- `tests/test_execute_target.py` — two tests, both invoking the real Makefile via `subprocess` against the repo root, using the shared `write_notebook` fixture from `tests/conftest.py` (not redefined); both pass, and the full suite (`uv run pytest tests/ -q`) is green at 8/8 (wave 1's 6 plus these 2)

## Task Commits

Each task was committed atomically:

1. **Task 1: Makefile with env, kernel, test, execute-notebooks, and requirements-colab.txt targets** - `ee8901a` (feat)
2. **Task 2: Automated proof of fail-fast and zero-notebook behavior** - `80be010` (test)

**Plan metadata:** committed with this SUMMARY.md (see below)

## Files Created/Modified
- `Makefile` - `env`/`kernel`/`test`/`execute-notebooks`/`requirements-colab.txt` targets; bash-continuation recipe for the nullglob/array fail-fast loop, portable to GNU Make 3.81
- `requirements-colab.txt` - generated Colab reference requirements (no hashes, no dev group, no `-e .`), committed as a Phase 1 deliverable
- `tests/test_execute_target.py` - `test_execute_notebooks_no_op_with_zero_notebooks`, `test_execute_notebooks_fails_fast_on_first_error`

## Decisions Made
- Confirmed GNU Make on this machine is 3.81 (pre-`.ONESHELL`, which landed in 3.82) before writing the `execute-notebooks` recipe, and used backslash-newline continuation instead — this is the "equivalent single-line-continuation block" the plan's Task 1 action explicitly allowed as an alternative to `.ONESHELL`
- Confirmed via `jupyter execute --help` that `--output` is always relative to the input notebook's parent directory (not cwd), which is why pointing `NOTEBOOKS_DIR` at `tmp_path` in tests guarantees no `executed_*.ipynb` artifacts land in the real repo tree regardless of where `make` itself is invoked from
- Ran `uv sync --group dev` and re-registered the `geo-embeddings-course` kernel against this worktree's own `.venv` before verification, since this parallel worktree started with no `.venv` — required for the fail-fast test to actually invoke a working kernel, matching plan 01-01's documented precedent that kernel registration is a global, per-user side effect re-pointed per active worktree/checkout

## Deviations from Plan

None - plan executed exactly as written. Both tasks' `<action>` and `<acceptance_criteria>` were implemented literally; the only extra step taken was environment setup (`uv sync`, kernel registration) required because this parallel worktree began without a `.venv`, which is expected worktree-execution overhead rather than a plan deviation.

## Issues Encountered
None - all verification commands (manual `make execute-notebooks` no-op check, manual synthetic fail-fast check, `make requirements-colab.txt` content check, `uv run pytest tests/test_execute_target.py -x -q`, and the full `uv run pytest tests/ -q`) passed on the first attempt.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- `make execute-notebooks` is provably correct today (no-op) and will be exercised for real starting Phase 3, when the first solution notebook lands in `notebooks/solutions/`
- `requirements-colab.txt` is a live Makefile target (`pyproject.toml`/`uv.lock` as prerequisites) — later phases that add dependencies should re-run `make requirements-colab.txt` rather than hand-editing the file
- No blockers for the next plan in this phase or for Phase 2/3.

---
*Phase: 01-repository-and-environment-scaffold*
*Completed: 2026-09-03*

## Self-Check: PASSED

All 3 created files verified present on disk (Makefile, requirements-colab.txt, tests/test_execute_target.py), plus this SUMMARY.md. Both task commits verified present in git history (ee8901a, 80be010).

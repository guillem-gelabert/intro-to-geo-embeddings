---
phase: 01-repository-and-environment-scaffold
plan: 04
subsystem: testing
tags: [pytest, subprocess, nbclient, nbformat, uv-extras, jupyter-kernel]

# Dependency graph
requires:
  - phase: 01-repository-and-environment-scaffold (plan 01)
    provides: "pyproject.toml with ee/providers extras, course/config.py (RANDOM_STATE, COURSE_RELEASE, KERNEL_NAME), tests/conftest.py's write_notebook fixture, and the registered geo-embeddings-course Jupyter kernel"
provides:
  - "tests/test_core_env_isolation.py — permanent, fast (<1s), network-free subprocess-based proof that `import course` succeeds and ee/geemap/geotessera/duckdb/torch all fail to import in the default (core+dev, no-extras) synced environment"
  - "A one-time, manually-run (not a permanent test) proof that `uv sync --group dev --extra ee` installs the ee extra cleanly and `uv sync --group dev` reverts it, with zero uv.lock drift either way"
  - "tests/test_bootstrap.py — proves the Colab Setup cell's control flow, its course.config contract, and kernel-to-project-venv resolution via a synthetic in-memory notebook, before any real notebook exists"
affects: [01-05, phase-2]

# Tech tracking
tech-stack:
  added: []
  patterns: ["subprocess-against-sys.executable for fast negative-import assertions (no `uv run` shell-out, since pytest already runs inside uv's venv)", "one-time manual extras-toggle proof kept out of the permanent test suite to protect the phase's sub-15s sampling budget", "synthetic in-memory notebook (nbformat + write_notebook fixture) executed via nbclient.NotebookClient to prove a Setup-cell pattern before any real notebook exists"]

key-files:
  created: [tests/test_core_env_isolation.py, tests/test_bootstrap.py]
  modified: []

key-decisions:
  - "Split ENV-05's proof into two halves per RESEARCH.md's Sampling-Rate Argument: a permanent, network-free subprocess test (committed) plus a one-time extras-toggle proof (run manually during this task, documented here, not encoded as a pytest test) — a permanent test that synced extras on every run would blow the 15s budget"
  - "test_bootstrap.py's assertion cell also checks `not IN_COLAB` in addition to the plan's required RANDOM_STATE/COURSE_RELEASE/.venv checks, as a belt-and-suspenders proof the pip-install branch was genuinely skipped locally rather than silently no-op'd for an unrelated reason"

patterns-established:
  - "Pattern: negative-import proofs (\"package X must NOT be importable\") run via `subprocess.run([sys.executable, \"-c\", ...])`, never `uv run python -c`, so they exercise the exact interpreter pytest is already running under"

requirements-completed: [ENV-02, ENV-05]

# Metrics
duration: ~1min (commit timestamps 18:01:20 -> 18:01:58; actual wall-clock work included two full `uv sync` package-set toggles of ~150 packages each)
completed: 2026-09-03
---

# Phase 1 Plan 04: Bootstrap and Isolation Tests Summary

**Two independently-failing claims proven with automated tests: `tests/test_core_env_isolation.py` (subprocess-based, network-free, proves ee/geemap/geotessera/duckdb/torch stay out of the default sync) and `tests/test_bootstrap.py` (synthetic in-memory notebook via nbclient, proves the Colab Setup cell's control flow and course.config contract before any real notebook exists).**

## Performance

- **Duration:** ~1 min per commit timestamps (18:01:20 -> 18:01:58, both +02:00); actual wall-clock work included two full `uv sync` extras-toggle passes (~150 packages installed then removed) between the two task commits
- **Started:** 2026-09-03T16:01:20Z
- **Completed:** 2026-09-03T16:01:58Z
- **Tasks:** 2/2
- **Files modified:** 2 created (tests/test_core_env_isolation.py, tests/test_bootstrap.py)

## Accomplishments
- `tests/test_core_env_isolation.py`: 6 parametrized/individual tests, all subprocess-based against `sys.executable`, running in 0.17-0.19s total — `import course` succeeds; `ee`, `geemap`, `geotessera`, `duckdb`, `torch` all fail to import in the default synced environment
- One-time extras-toggle proof performed as a task-level verification step (not a permanent test): `uv sync --group dev --extra ee` → `import ee` succeeds → `uv sync --group dev` → `import ee` fails again — `git status --short` showed zero drift to `uv.lock` or any tracked file at every step
- `tests/test_bootstrap.py`: builds a synthetic notebook via the `write_notebook` fixture reproducing RESEARCH.md's Colab Setup cell verbatim, executes it against the `geo-embeddings-course` kernel via `nbclient.NotebookClient`, and asserts `RANDOM_STATE == 42`, `COURSE_RELEASE == "2026.08"`, `not IN_COLAB`, and `.venv` in `sys.executable` — all in 0.93s
- Full suite (`tests/` — schema + isolation + bootstrap) is green: 13 tests passed in 0.91s
- Environment left in its default extras-free state: final `uv run python -c "import ee"` exits 1 (`ModuleNotFoundError`)

## Task Commits

Each task was committed atomically:

1. **Task 1: Core/extras isolation test and the extras-toggle proof** - `74f9230` (test)
2. **Task 2: Setup-cell bootstrap contract test** - `02edbc7` (test)

**Plan metadata:** committed with this SUMMARY.md (see below)

## Files Created/Modified
- `tests/test_core_env_isolation.py` - permanent isolation suite: `test_course_imports_in_default_environment` + parametrized `test_heavy_or_credentialed_packages_absent_by_default` over `["ee", "geemap", "geotessera", "duckdb", "torch"]`
- `tests/test_bootstrap.py` - `test_setup_cell_executes_and_matches_config_contract`: builds and executes a synthetic two-cell notebook (verbatim Setup cell + assertion cell) via `nbclient.NotebookClient(kernel_name=KERNEL_NAME)`

## Decisions Made
- Kept the extras-toggle proof out of the permanent pytest suite entirely, exactly as the plan instructed, since a per-run `uv sync --extra ee` would perform a large network install every time `pytest` runs — documented the manual transcript here instead
- Added a `not IN_COLAB` assertion to the bootstrap test's assertion cell beyond what the plan's acceptance criteria strictly required, to make explicit (not just implicit via a skipped install) that the Colab branch was correctly bypassed in this local execution

## Deviations from Plan

None - plan executed exactly as written. Both tasks matched their `<action>` blocks and `<acceptance_criteria>` without requiring any Rule 1-4 fixes.

## Issues Encountered

The globally-registered `geo-embeddings-course` Jupyter kernel (`~/Library/Jupyter/kernels/geo-embeddings-course/kernel.json`) was found pointing at a sibling worktree's `.venv` path (`agent-a6a4185f84560e4ee`, not this plan's own worktree `agent-aa446da3b74d4ad93`, nor the path noted in 01-01-SUMMARY.md) — an expected consequence of three wave-2 agents sharing one user-level kernel registry concurrently. Since `course/config.py` was not modified by any wave-2 plan and all three worktrees share the same base commit's `uv.lock`, this did not affect correctness: `tests/test_bootstrap.py` passed against whichever worktree's `.venv` the kernel currently resolved to. Per this plan's interfaces note ("the kernel is already registered globally by plan 01-01's Task 1... without registering it again"), no re-registration was performed here. As with 01-01-SUMMARY.md's equivalent note, the kernel will need one idempotent re-registration from the merged main-repo checkout once all worktrees are cleaned up.

## User Setup Required
None - no external service configuration required. (No Earth Engine or LGND credentials are touched; the `ee` extra was synced only transiently, during this plan's own extras-toggle proof, and fully reverted before the plan finished.)

## Next Phase Readiness
- Both permanent test files are green and merge-independent of the sibling wave-2 plans (01-02: README/jupytext/pre-commit/.gitignore; 01-03: Makefile/requirements-colab.txt/test_execute_target.py) — no shared files were touched beyond the two declared in this plan's frontmatter.
- ENV-02 and ENV-05 are now both test-covered; the only remaining phase-1 verification not automatable from this machine is the live Colab timing checkpoint, explicitly owned by plan 01-05.
- No blockers for the next plan in this phase.

---
*Phase: 01-repository-and-environment-scaffold*
*Completed: 2026-09-03*

## Self-Check: PASSED

Both created files verified present on disk (tests/test_core_env_isolation.py, tests/test_bootstrap.py). Both task commits verified present in git history (74f9230, 02edbc7).

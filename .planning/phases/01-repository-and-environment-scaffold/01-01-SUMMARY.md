---
phase: 01-repository-and-environment-scaffold
plan: 01
subsystem: infra
tags: [uv, pyproject, python3.12, geopandas, pytest, jupyter-kernel, uv_build]

# Dependency graph
requires: []
provides:
  - "pyproject.toml with uv_build flat-layout override (module-root='', module-name='course') making `import course` resolvable from the repo root"
  - "Committed, drift-free uv.lock (258 packages resolved) and .python-version pinned to 3.12"
  - "Core install includes rasterio and xarray per REQUIREMENTS.md ENV-01; ee and providers extras hold everything heavy/credentialed; torch/stackstac/claymodel excluded entirely"
  - "geo-embeddings-course Jupyter kernel registered against this repo's own .venv"
  - "course/config.py (RANDOM_STATE, COURSE_RELEASE, KERNEL_NAME) and course/schema.py (A_COLS, S2_COLS, REQUIRED, embedding_cols, validate, to_matrix) — the schema contract every later notebook and pipeline script imports"
  - "tests/conftest.py's make_gdf and write_notebook fixtures — the shared fixture contract plans 01-03 and 01-04 build on"
affects: [01-02, 01-03, 01-04, phase-2, phase-3]

# Tech tracking
tech-stack:
  added: [uv 0.12.9, uv_build, Python 3.12.13, numpy 2.5.2, pandas 3.0.5, geopandas 1.1.4, rasterio 1.5.1, xarray 2026.7.0, scikit-learn 1.9.0, matplotlib 3.11.1, folium/mapclassify, jupyterlab 4.6.3, pytest 9.1.1, nbclient 0.11.0, nbformat 5.11.1]
  patterns: ["Flat-layout package under uv_build via [tool.uv.build-backend] module-root/module-name override", "Heavy/credentialed deps split into pip-installable [project.optional-dependencies] extras (ee, providers), not PEP 735 groups", "course/schema.py as the single, numpy-only, zero-I/O validation contract for GeoDataFrames"]

key-files:
  created: [pyproject.toml, .python-version, uv.lock, README.md, course/__init__.py, course/config.py, course/schema.py, tests/conftest.py, tests/test_schema.py]
  modified: []

key-decisions:
  - "rasterio and xarray placed in core [project.dependencies], not the providers extra, per REQUIREMENTS.md ENV-01's explicit core-stack list (overrides RESEARCH.md's own grouping, per this plan's documented conflict resolution)"
  - "README.md created as a minimal placeholder (banner + one-line status) because uv_build refuses to resolve/build when the readme file declared in [project] doesn't exist yet — a hard blocking dependency discovered while running Task 1, not an optional nicety"
  - "nbclient explicitly pinned >=0.11.0,<0.12 in the dev group even though uv's resolver already landed on 0.11.0, per RESEARCH.md's guidance that the ambient, unlocked install (0.10.4) must not be trusted"

patterns-established:
  - "Pattern: course/schema.py imports numpy only at module scope — zero geopandas/pandas/cloud calls at import time, per ARCHITECTURE.md's 'zero cloud calls at import time' rule"
  - "Pattern: tests/conftest.py's make_gdf(n, n_dims, crs, unit_norm, missing_cols) factory is the canonical way to exercise every validate() failure mode without real data"

requirements-completed: [ENV-01, ENV-05]

# Metrics
duration: ~3min (session clock; see Issues Encountered for a note on this)
completed: 2026-09-03
---

# Phase 1 Plan 01: Repository and Environment Scaffold Summary

**uv-managed Python 3.12 project with a flat-layout `course` package importable via a `uv_build` module-root/module-name override, a committed 258-package `uv.lock` (core includes rasterio/xarray per ENV-01), a registered `geo-embeddings-course` Jupyter kernel, and a green `course.schema` contract (validate/embedding_cols/to_matrix) covering the happy path and every assertion failure mode.**

## Performance

- **Duration:** ~3 min per commit timestamps (17:49:43 → 17:51:16 local); actual wall-clock work included multiple `uv add` package resolution/download passes and a full clean-clone rebuild for phase-gate verification
- **Started:** 2026-09-03T15:49:43Z
- **Completed:** 2026-09-03T15:52:29Z
- **Tasks:** 3/3
- **Files modified:** 9 created (pyproject.toml, .python-version, uv.lock, README.md, course/__init__.py, course/config.py, course/schema.py, tests/conftest.py, tests/test_schema.py)

## Accomplishments
- `pyproject.toml` with the verified `[tool.uv.build-backend]` override — `uv run python -c "import course"` works from the repo root, not `geo_embeddings_course`
- Core dependency set matches REQUIREMENTS.md ENV-01 exactly, including rasterio and xarray in core (not the providers extra); `ee` and `providers` extras hold everything heavy/credentialed; `torch` appears nowhere in the lockfile
- `geo-embeddings-course` kernel registered and proven to resolve this repo's own `.venv` (kernel.json argv path verified)
- `course.schema` contract (A_COLS, S2_COLS, REQUIRED, embedding_cols, validate, to_matrix) green under pytest with 6 tests covering the happy path and every assertion failure mode
- `tests/conftest.py`'s `make_gdf`/`write_notebook` fixtures built to the exact signatures later plans (01-03, 01-04) will import by name
- Phase-gate verification passed in full: `rm -rf .venv && uv sync --group dev` clean rebuild, `uv lock --check` exit 0, `import rasterio, xarray` exit 0 in the default sync, `pytest tests/test_schema.py -x -q` green, `git diff --exit-code uv.lock` exit 0

## Task Commits

Each task was committed atomically:

1. **Task 1: pyproject.toml, uv-managed environment, and project kernel** - `217b6e7` (feat)
2. **Task 2: The course package and the schema contract** - `cf54d79` (feat)
3. **Task 3: Shared pytest fixtures and the schema test suite** - `8ae1b30` (test)

**Plan metadata:** committed with this SUMMARY.md (see below)

## Files Created/Modified
- `pyproject.toml` - project metadata, uv_build flat-layout override, core deps (incl. rasterio/xarray), dev group, ee/providers extras, pytest config
- `.python-version` - pins 3.12
- `uv.lock` - committed, reproducible resolution of 258 packages
- `README.md` - minimal placeholder banner (blocking-issue fix, see Deviations)
- `course/__init__.py` - `__version__ = "2026.8.0"`
- `course/config.py` - `RANDOM_STATE`, `COURSE_RELEASE`, `KERNEL_NAME`
- `course/schema.py` - `A_COLS`, `S2_COLS`, `REQUIRED`, `embedding_cols()`, `validate()`, `to_matrix()`
- `tests/conftest.py` - `make_gdf` and `write_notebook` fixtures
- `tests/test_schema.py` - 6 tests: happy path + 5 failure/edge cases

## Decisions Made
- Kept `rasterio`/`xarray` in core per REQUIREMENTS.md ENV-01, diverging from RESEARCH.md's own "Standard Stack" section grouping — this was pre-decided in the plan's Objective note, not a new call made during execution
- Created `README.md` as a minimal placeholder rather than a fully populated one, since Plan 01-02 owns the README's real content (banner, Colab-badge legend, license section) per the phase's Open Question 2 resolution

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Created a placeholder `course/__init__.py` before the first `uv add`**
- **Found during:** Task 1, Step 2 (`uv add numpy pandas ...`)
- **Issue:** `uv_build`'s flat-layout resolution builds the project package as part of every `uv add`/`uv sync`, not just `uv build`. With no `course/__init__.py` on disk yet, `uv add` failed with `Expected a Python module at: course/__init__.py` — a chicken-and-egg gap between Task 1 (writes `pyproject.toml`) and Task 2 (writes `course/__init__.py`) that the plan's step-by-step ordering didn't anticipate.
- **Fix:** Created an empty `course/__init__.py` placeholder immediately before running `uv add`, so the build backend had a module to find. Task 2 then overwrote it with the real `__version__` content and committed the final version as originally planned — the placeholder itself was never committed on its own.
- **Files modified:** `course/__init__.py` (placeholder, superseded by Task 2's commit)
- **Verification:** `uv add` succeeded after the placeholder was created; Task 2 re-verified `course.__version__ == "2026.8.0"` after overwriting it
- **Committed in:** superseded by `cf54d79` (Task 2 commit) — no standalone commit for the placeholder

**2. [Rule 3 - Blocking] Created a minimal `README.md` before the first `uv add`**
- **Found during:** Task 1, Step 2 (`uv add numpy pandas ...`), immediately after fixing deviation #1
- **Issue:** `pyproject.toml`'s `[project]` section (per the plan's own Task 1 instructions) sets `readme = "README.md"`. `uv_build` opens that file during every resolution, and it failed with `failed to open file ... README.md: No such file or directory` since no README existed yet in this greenfield repo.
- **Fix:** Wrote a minimal two-line placeholder README (banner + one-line status) so `uv add` could proceed. This is a genuinely new file not listed in this plan's `files_modified`, but was required to unblock the plan's own declared action.
- **Files modified:** `README.md`
- **Verification:** `uv add` succeeded after the file was created; no acceptance criteria in this plan depend on README content, so no further verification was needed here (Plan 01-02 owns the real README content)
- **Committed in:** `217b6e7` (Task 1 commit)

---

**Total deviations:** 2 auto-fixed (both Rule 3 - blocking, both chicken-and-egg gaps in the plan's exact step ordering vs. what `uv_build` actually needs on disk at resolution time)
**Impact on plan:** Both fixes were minimal, load-bearing, and fully superseded or absorbed by tasks the plan already specified (Task 2 overwrote the placeholder `__init__.py`; the README content itself is explicitly Plan 01-02's job per the phase's Open Question 2). No scope creep — no README sections beyond a two-line placeholder were written here.

## Issues Encountered
- Git commit timestamps for this session (`217b6e7` at 17:49:43 and `8ae1b30` at 17:51:16, both `+02:00`) show only ~3 minutes elapsed despite the actual work performed (four separate `uv add` invocations each resolving/downloading dozens of packages, a full `.venv` rebuild for phase-gate verification, and six pytest test cases). The reported "Duration" above reflects this timestamp delta as the best available objective signal, not a literal wall-clock measurement of effort.
- No other issues — all verification commands (Task 1's kernel/env checks, Task 2's import checks, Task 3's pytest run, and the plan's overall phase-gate sequence) passed on the first attempt after the two blocking-issue fixes above.

## User Setup Required
None - no external service configuration required. (No Earth Engine or LGND credentials are touched by this plan; `ee`/`providers` extras stay uninstalled by default, as designed.)

## Next Phase Readiness
- The `course` package, its schema contract, and the shared pytest fixtures (`make_gdf`, `write_notebook`) are in place and green — plans 01-02 (README/Makefile/pre-commit), 01-03, and 01-04 can now build on `import course` and reuse these fixtures without redefining them.
- One note for the orchestrator: the `geo-embeddings-course` kernel was registered with an `argv`/`VIRTUAL_ENV` pointing at this worktree's own path (`.claude/worktrees/agent-a7d5d22f582e74251/.venv`), since kernel registration is a global, per-user side effect (`~/Library/Jupyter/kernels/`) performed during verification, not a repo-tracked file. Once this worktree is merged and removed, that kernelspec will point at a path that no longer exists. Re-running `uv run ipython kernel install --user --env VIRTUAL_ENV "$(pwd)/.venv" --name=geo-embeddings-course` from the merged main repo checkout (a one-line, idempotent command) will re-point it correctly — this is expected worktree-execution behavior, not a defect in this plan's work, but is worth doing once before anyone opens the kernel interactively.
- No blockers for the next plan in this phase.

---
*Phase: 01-repository-and-environment-scaffold*
*Completed: 2026-09-03*

## Self-Check: PASSED

All 9 created files verified present on disk (pyproject.toml, .python-version, uv.lock, README.md, course/__init__.py, course/config.py, course/schema.py, tests/conftest.py, tests/test_schema.py). All 3 task commits verified present in git history (217b6e7, cf54d79, 8ae1b30).

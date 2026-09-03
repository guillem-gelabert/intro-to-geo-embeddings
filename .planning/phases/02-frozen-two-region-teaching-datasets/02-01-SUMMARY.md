---
phase: 02-frozen-two-region-teaching-datasets
plan: 01
subsystem: data
tags: [numpy, geopandas, pytest, dequantization, alphaearth]

# Dependency graph
requires:
  - phase: 01-course-scaffolding
    provides: course/schema.py validate() contract, course/config.py, pytest+ruff+uv scaffolding
provides:
  - course.embeddings.dequantize_aef — the single, tested AlphaEarth int8-to-unit-vector formula
  - course.schema.FROZEN_REQUIRED / validate_frozen — frozen-table schema contract
  - course.config.AREAS / ANCHOR_YEARS / BLOCK_SIZE_M / DATA_DIR / RELEASE_* — study-area registry
  - course.live.LiveSourceUnavailable — shared exception for live-source adapters
  - pytest `network` marker with `-m "not network"` as the default fast-suite filter
  - Makefile `test-network` target
affects: [02-02, 02-03, 02-04, 02-05, 02-06, 02-07, 02-08, 02-09, 02-10, 02-11, 02-12]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Single shared dequantization helper: no module re-implements the AlphaEarth (v/127.5)**2*sign(v) formula"
    - "validate_frozen() composes validate() rather than duplicating its checks"
    - "LiveSourceUnavailable(RuntimeError) as the one exception type every live-source adapter raises"
    - "Default pytest suite excludes network tests via addopts; opt in with -m network or make test-network"

key-files:
  created:
    - course/embeddings.py
    - course/live/__init__.py
    - tests/test_embeddings.py
    - tests/test_config.py
  modified:
    - course/schema.py
    - course/config.py
    - pyproject.toml
    - Makefile
    - tests/test_schema.py
    - uv.lock

key-decisions:
  - "Dequantization masks -128 nodata via np.any(raw == NODATA, axis=0, keepdims=True) before computing (v/127.5)**2*sign(v), then renormalizes — matches 02-RESEARCH.md's verified formula exactly, not the earlier single-pixel folklore figure"
  - "FROZEN_REQUIRED is REQUIRED + extras (list concatenation), never mutates REQUIRED, so Phase 1's validate() contract is byte-for-byte unchanged"
  - "requests added to core [project.dependencies] (not just the providers extra) because course/data.py (Plan 02-05) is core-tier"
  - "network pytest marker paired with addopts = [\"-m\", \"not network\"] so a bare `make test` stays fast (single-digit seconds) even though live AlphaEarth window reads measured 190-340s in research"

patterns-established:
  - "Pattern: TDD tasks land as paired test(...)/feat(...) commits so RED/GREEN gates are visible in git log"
  - "Pattern: config.py registries (AREAS, ANCHOR_YEARS, etc.) are the single source of truth other modules import rather than re-typing bboxes/years"

requirements-completed: [DATA-01, DATA-07, DATA-08]

# Metrics
duration: 4min
completed: 2026-09-03
---

# Phase 2 Plan 1: Foundational Contracts (Dequantization, Frozen Schema, Study-Area Registry) Summary

**Shared `dequantize_aef` (numpy-only, nodata-masking, renormalizing), `validate_frozen`/`FROZEN_REQUIRED` schema extension, `AREAS`/`ANCHOR_YEARS`/`BLOCK_SIZE_M` registry, `LiveSourceUnavailable` exception, and a `network` pytest marker excluded from the default suite by `addopts`.**

## Performance

- **Duration:** 4 min
- **Started:** 2026-09-03T19:23:36+02:00
- **Completed:** 2026-09-03T19:27:05+02:00
- **Tasks:** 3 completed
- **Files modified:** 10 (4 created, 6 modified)

## Accomplishments
- `course/embeddings.py::dequantize_aef` — the one place the AlphaEarth int8 dequantization formula lives; masks `-128` nodata across all 64 bands first, applies `(v/127.5)**2 * sign(v)`, then L2-renormalizes; pure numpy (no rasterio/requests import)
- `course/schema.py::validate_frozen`/`FROZEN_REQUIRED` extend Phase 1's `validate()` contract additively — every pre-existing Phase 1 schema test still passes unmodified
- `course/config.py::AREAS`/`ANCHOR_YEARS`/`BLOCK_SIZE_M`/`DATA_DIR`/`RELEASE_*` — Bern and Seville bboxes, EPSG codes, and the three anchor years now exist in one place other plans import instead of re-typing
- `course/live/__init__.py::LiveSourceUnavailable` — the shared exception every live-source adapter in Plans 02-02 through 02-04 will raise
- `network` pytest marker registered with `addopts = ["-m", "not network"]`, plus a `Makefile` `test-network` target, so the phase's default suite stays fast from the start

## Task Commits

Each task was committed atomically (Tasks 1 and 2 are TDD: test → feat pairs):

1. **Task 1: Shared AlphaEarth dequantization helper**
   - `48f3408` test(02-01): add failing test for dequantize_aef (RED)
   - `3621595` feat(02-01): implement shared AlphaEarth dequantization helper (GREEN)
2. **Task 2: Frozen-table schema extension**
   - `8d68a68` test(02-01): add failing tests for validate_frozen (RED)
   - `e83d139` feat(02-01): add FROZEN_REQUIRED and validate_frozen to course.schema (GREEN)
3. **Task 3: Study-area registry, live-source package init, network marker**
   - `9944b4a` feat(02-01): add study-area registry, live-source package, network marker

## Files Created/Modified
- `course/embeddings.py` - `dequantize_aef(raw)` and `NODATA = -128`, pure numpy
- `course/live/__init__.py` - `LiveSourceUnavailable(RuntimeError)`
- `tests/test_embeddings.py` - 4 behavior tests (unit norm, nodata NaN masking, sign preservation, batch independence)
- `tests/test_config.py` - AREAS/ANCHOR_YEARS/LiveSourceUnavailable assertions
- `course/schema.py` - added `FROZEN_REQUIRED` and `validate_frozen`, additive-only diff
- `course/config.py` - added `AREAS`, `ANCHOR_YEARS`, `BLOCK_SIZE_M`, `DATA_DIR`, `RELEASE_ORG`, `RELEASE_REPO`, `RELEASE_TAG`
- `pyproject.toml` - `requests` added to core `[project.dependencies]`; `markers` and `addopts` added to `[tool.pytest.ini_options]`
- `Makefile` - `test-network` phony target
- `tests/test_schema.py` - 4 new tests for `validate_frozen`, plus reformatted import line (ruff auto-fix, no test body changes)
- `uv.lock` - regenerated to reflect `requests` moving from providers-only to core dependency

## Decisions Made
- Kept the dequantization mask computation as `np.any(raw == NODATA, axis=0, keepdims=True)` exactly as specified in the plan and 02-RESEARCH.md, rather than a per-band mask, since a single `-128` in any band invalidates the whole spatial/point position.
- Put the new config-registry test in a new `tests/test_config.py` file rather than appending to `tests/test_schema.py`, since AREAS/ANCHOR_YEARS/LiveSourceUnavailable are a config-module concern, not a schema concern — the plan explicitly allowed either and asked for consistency.

## Deviations from Plan

None — plan executed exactly as written, including the three plan-checker-mandated additions to Task 3 (addopts, test-network Makefile target, requests in core dependencies).

## Issues Encountered

None. One environment quirk noted for the record: `uv run pytest --markers | grep -c "network: requires internet access"` returns `0` instead of `1` under this Bash tool's pseudo-tty (pytest's bold-marker ANSI codes split the substring across an escape sequence); `uv run pytest --markers --color=no | grep -c ...` returns `1` as expected. This is a terminal-detection artifact of the sandboxed shell, not a defect in the marker registration — verified the marker is registered exactly once via the `--color=no` form and via direct inspection of `pyproject.toml`.

## TDD Gate Compliance

Both TDD tasks (1 and 2) show the required RED → GREEN commit sequence in git log, verified above. No REFACTOR commits were needed (implementations were correct on first GREEN pass).

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- `dequantize_aef`, `validate_frozen`/`FROZEN_REQUIRED`, `AREAS`/`ANCHOR_YEARS`/`BLOCK_SIZE_M`, and `LiveSourceUnavailable` are now stable, unit-tested contracts. Plans 02-02 through 02-12 (live-source adapters, pipeline, loader, tests) can import them without further negotiation.
- The `network` marker and `test-network` Makefile target are in place before any network-dependent test exists, so later plans that add network-marked tests (Plans covering DATA-07, DATA-09's remote-fallback half) slot in without further pytest config changes.
- No blockers.

---
*Phase: 02-frozen-two-region-teaching-datasets*
*Completed: 2026-09-03*

## Self-Check: PASSED

All 11 claimed files found on disk; all 6 commit hashes (48f3408, 3621595, 8d68a68, e83d139, 9944b4a, 9c3f53d) found in git log.

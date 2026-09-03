---
phase: 02-frozen-two-region-teaching-datasets
plan: 02
subsystem: data
tags: [rasterio, duckdb, warpedvrt, alphaearth, geoparquet, point-sampling]

# Dependency graph
requires:
  - phase: 02-frozen-two-region-teaching-datasets
    plan: 01
    provides: course.embeddings.dequantize_aef, course.live.LiveSourceUnavailable, network pytest marker
provides:
  - course.live.aef_cog.find_tile — tile lookup against the public aef_index.parquet via DuckDB httpfs+spatial
  - course.live.aef_cog.read_window — bounded AOI window read with the WarpedVRT bottom-up-COG orientation fix
  - course.live.aef_cog.sample_points_from_window — array-index point extraction from an already-dequantized window
affects: [02-07, 02-09, 02-10]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Lazy in-function `import duckdb` inside find_tile() so course.live.aef_cog stays importable without the 'providers' extra (ENV-05/T-01-10) — only calling find_tile() itself requires duckdb"
    - "Missing duckdb is itself a LiveSourceUnavailable, not an ImportError leaking to callers — consistent with every other source-failure path in this module"
    - "One bounded window read per (region, year) via WarpedVRT, then array-index every sample point in memory — never loop .sample()/.read() per point against a remote COG (Pitfall 4)"
    - "Duckdb-dependent tests use @pytest.mark.skipif(not _HAS_DUCKDB, ...) at class/function scope (checked via importlib.util.find_spec, not a real import) so they skip gracefully instead of erroring when the 'providers' extra isn't synced"

key-files:
  created:
    - course/live/aef_cog.py
    - tests/test_aef_cog.py
  modified: []

key-decisions:
  - "find_tile() imports duckdb lazily inside the function body rather than at module top-level — a module-level `import duckdb` would make course.live.aef_cog (and read_window/sample_points_from_window, which don't need duckdb at all) fail to import whenever the 'providers' extra isn't synced, breaking tests/test_core_env_isolation.py's ENV-05/T-01-10 contract and the plan's own 'uv run pytest tests/ -q passes' success criterion in a fresh no-extras environment"
  - "read_window's dst_crs parameter (required by the plan's interface spec) is used as a defensive post-open CRS assertion, not as the WarpedVRT reprojection target — the actual orientation fix always reprojects into the tile's OWN native CRS via WarpedVRT(ds, crs=ds.crs) per 02-RESEARCH.md; dst_crs catches a tile unexpectedly served in the wrong CRS before it reaches downstream code (ASVS V5, same class of check as threat T-02-03's structural-response validation)"
  - "sample_points_from_window uses the non-deprecated `@` matmul operator for the Affine transform instead of `*` (PendingDeprecationWarning observed from rasterio itself during the live network test, confirming this was the right call)"
  - "duckdb-dependent tests are gated with @pytest.mark.skipif keyed off importlib.util.find_spec('duckdb'), not pytest.importorskip at module level — importorskip at the top of the file would have skipped the also-present, duckdb-independent sample_points_from_window tests too"

patterns-established:
  - "Pattern: optional-extra-gated live-source adapters keep their heavy import lazy and function-scoped; their tests self-skip via find_spec-based skipif rather than requiring the extra to be present for the fast suite to pass"

requirements-completed: [DATA-01, DATA-07]

# Metrics
duration: 3min
completed: 2026-09-03
---

# Phase 2 Plan 2: AlphaEarth COG Adapter (Tile Lookup, Windowed Read, Point Sampling) Summary

**`course/live/aef_cog.py` with `find_tile` (DuckDB tile-index lookup), `read_window` (WarpedVRT-fixed bounded AOI read), and `sample_points_from_window` (array-index point extraction) — the pipeline never downloads a full 3.68 GB tile or loops remote `.sample()` per point.**

## Performance

- **Duration:** 3 min (commit-to-commit; additional wall-clock time spent on one live network verification run, ~90s, run separately and not counted against task duration)
- **Started:** 2026-09-03T19:42:20+02:00
- **Completed:** 2026-09-03T19:44:56+02:00
- **Tasks:** 2 completed (Task 2 is TDD: RED → GREEN)
- **Files modified:** 2 (both created)

## Accomplishments
- `find_tile(lon, lat, year)` — DuckDB `httpfs`+`spatial` query against the public `aef_index.parquet`, returns `{"utm_zone", "crs", "url"}`; raises `LiveSourceUnavailable` on missing `duckdb`, query failure, or no match
- `read_window(url, bbox_4326, dst_crs)` — opens the remote COG via `/vsicurl/`, wraps in `WarpedVRT(ds, crs=ds.crs)` to fix Google's bottom-up (`transform.e = +10`) orientation, reprojects the AOI bbox into the tile's own CRS, rounds the window via `.round_offsets().round_lengths()`, and validates the tile's CRS against the caller's `dst_crs` before ever reading; returns `(raw, window_transform)`
- `sample_points_from_window(raw_unit, window_transform, points_xy)` — vectorized `~window_transform @ (x, y)` → rounded `(row, col)` → array index into the already-fetched, already-dequantized window; out-of-bounds points return an all-NaN row rather than raising
- Both `find_tile` and `read_window` stay independently importable without the `providers` extra installed — `course.live.aef_cog` never hard-requires `duckdb` at module load time
- One live network run confirmed end-to-end: `find_tile(7.4474, 46.9480, 2021)` resolved the real Bern tile (`32N`, `2021` in the URL) and `read_window` on a ~200m×200m sub-bbox returned a `(64, H, W)` int8 array

## Task Commits

Each task was committed atomically (Task 2 is TDD: test → feat):

1. **Task 1: Tile lookup and windowed read with the bottom-up-COG fix** - `2e503d1` (feat)
2. **Task 2: Array-index point sampling and tests**
   - `a60d943` test(02-02): add failing tests for sample_points_from_window (RED)
   - `baa481f` feat(02-02): implement sample_points_from_window (GREEN)

## Files Created/Modified
- `course/live/aef_cog.py` - `find_tile`, `read_window`, `sample_points_from_window`, `AEF_INDEX_URL`, `AEF_GCS_BASE`
- `tests/test_aef_cog.py` - `TestFindTile` (3 non-network tests, duckdb-gated), one `@pytest.mark.network` live integration test, `TestSamplePointsFromWindow` (3 non-network tests)

## Decisions Made
- Made `duckdb` a lazy, function-scoped import inside `find_tile()` instead of a module-level import (see key-decisions above) — this was necessary, not optional: a module-level import broke `tests/test_core_env_isolation.py`'s `ENV-05`/`T-01-10` contract and would have broken the plan's own "`uv run pytest tests/ -q` passes" success criterion in any environment that hadn't manually synced the `providers` extra (i.e. any fresh clone running the default `make test`).
- Used `dst_crs` as a defensive post-open assertion rather than a reprojection target, keeping `WarpedVRT(ds, crs=ds.crs)` exactly as specified in the plan and 02-RESEARCH.md, while still giving the parameter real behavior (catches a tile served in an unexpected CRS).
- Switched `sample_points_from_window`'s Affine multiplication from `*` to `@` after seeing rasterio's own `PendingDeprecationWarning` for the `*` operator during testing.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Made `duckdb` import lazy/function-scoped instead of module-level**
- **Found during:** Task 1, first full-suite verification run
- **Issue:** A straightforward module-level `import duckdb` (as a literal reading of the plan's code interface suggested) made `course.live.aef_cog` — and by extension `read_window`/`sample_points_from_window`, which don't use `duckdb` at all — fail to import whenever the `providers` extra wasn't synced. This broke two pre-existing Wave 1 tests (`tests/test_core_env_isolation.py::test_heavy_or_credentialed_packages_absent_by_default[duckdb]` and `[geotessera]`, which assert `duckdb` stays out of the default no-extras environment per ENV-05/T-01-10) and would have broken the plan's own "`uv run pytest tests/ -q` passes" success criterion for anyone running the standard `make test`/`uv sync --group dev` workflow without additionally syncing `providers`.
- **Fix:** Moved `import duckdb` inside `find_tile()`'s function body; on `ImportError`, raise `LiveSourceUnavailable` with an actionable message (`install the 'providers' extra`). Gated the corresponding tests with `@pytest.mark.skipif(not _HAS_DUCKDB, ...)` (checked via `importlib.util.find_spec`, not a real import) so they skip cleanly instead of erroring when `duckdb` isn't installed.
- **Files modified:** `course/live/aef_cog.py`, `tests/test_aef_cog.py`
- **Verification:** Ran `uv run pytest tests/ -q` in both states — with `providers` synced (all `TestFindTile` tests pass for real, `test_core_env_isolation.py` fails as expected since duckdb IS present) and after reverting to `uv sync --group dev` (30 passed, 3 skipped, full suite clean including `test_core_env_isolation.py`). Also ran the one live network test with `providers` temporarily synced, then reverted.
- **Committed in:** `2e503d1` (Task 1 commit)

---

**Total deviations:** 1 auto-fixed (1 blocking)
**Impact on plan:** Necessary for the module and its tests to coexist with the pre-existing ENV-05/T-01-10 isolation contract and for the plan's own fast-suite success criterion to hold outside this session's local environment. No scope creep — the public function signatures, the `WarpedVRT` fix, and the window-rounding logic match the plan exactly.

## Issues Encountered
- `uv run pytest tests/test_aef_cog.py -k "not network"` initially deselected all 3 Task 1 tests because the `-k "not network"` keyword filter matched the substring "Network" in the class name `TestFindTileNoNetwork` (case-insensitive substring match), not just the `network` marker. Renamed the class to `TestFindTile` to avoid the collision — a reusable lesson for naming test classes/functions in this project going forward (avoid the literal substring "network" anywhere in a non-network test's name).
- `.venv` (gitignored, not committed) was toggled between `uv sync --group dev` and `uv sync --extra providers` several times during this session to develop/verify duckdb-dependent code paths and the live network test, then reverted to `uv sync --group dev` as the final state, matching what a fresh clone's default sync produces.

## User Setup Required

None - no external service configuration required. `find_tile`/`read_window` use only anonymous, no-credential HTTPS access (public `aef_index.parquet` and the AlphaEarth GCS bucket), consistent with DATA-07.

## Next Phase Readiness
- `course.live.aef_cog.find_tile`, `read_window`, and `sample_points_from_window` are stable, independently tested, and ready for `pipeline/extract_aef.py` (Plan 02-07) to call as a thin wrapper: `find_tile` → `read_window` → `course.embeddings.dequantize_aef` (once, on the whole window) → `sample_points_from_window`.
- The lazy-duckdb-import + skipif-gated-test pattern established here is reusable for any other Phase 2 module that needs a `providers`-extra-only dependency (e.g. `pystac-client`/`odc-stac` in the Sentinel-2 adapter) while keeping the fast suite green without the extra synced.
- No blockers. The one live network test was run once this session (per the plan's acceptance criteria — "do not gate the plan's completion on repeated network runs") and passed against the real Bern 2021 tile.

---
*Phase: 02-frozen-two-region-teaching-datasets*
*Completed: 2026-09-03*

## Self-Check: PASSED

All 3 claimed files found on disk (`course/live/aef_cog.py`, `tests/test_aef_cog.py`, this SUMMARY.md); all 3 commit hashes (`2e503d1`, `a60d943`, `baa481f`) found in `git log`.

---
phase: 02-frozen-two-region-teaching-datasets
plan: 07
subsystem: data
tags: [rasterio, geopandas, pandas, alphaearth, worldcover, hrl-imperviousness, point-extraction]

# Dependency graph
requires:
  - phase: 02-frozen-two-region-teaching-datasets
    plan: 02
    provides: course.live.aef_cog.find_tile, read_window, sample_points_from_window
  - phase: 02-frozen-two-region-teaching-datasets
    plan: 03
    provides: course.live.labels.class_to_label, imd_2018_window
  - phase: 02-frozen-two-region-teaching-datasets
    plan: 06
    provides: pipeline.sample_design.generate_sample_points (sample_id, x, y, worldcover_class)
provides:
  - pipeline.extract_aef.extract_area_year(area, year, points) -> pd.DataFrame with sample_id + A00..A63
  - pipeline.attach_labels.attach_labels(area, points) -> gpd.GeoDataFrame with label, label_source, imd_2018, validation_source
affects: [02-09, 02-10, 02-12]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "extract_area_year calls find_tile/read_window exactly once per (area, year) and dequantize_aef exactly once on the whole window, then sample_points_from_window exactly once with the full point array -- never a per-point remote fetch"
    - "extract_area_year reuses sample_design's precomputed x/y columns only when their CRS (course.config.AREAS[area]['epsg']) matches the AlphaEarth tile's own CRS (tile['crs']), compared via rasterio.crs.CRS equality, not string equality; otherwise it explicitly reprojects lon/lat into the tile's CRS rather than silently reusing mismatched coordinates"
    - "extract_area_year accepts an optional bbox_4326 override (defaulting to AREAS[area]['bbox_4326']) so a live-network test can scope reads to a small sub-bbox instead of the full AOI"
    - "attach_labels keeps label_source and validation_source as separate, hardcoded module-level string constants, architecturally uncoupled from each other -- label comes from WorldCover via class_to_label, imd_2018 comes independently from imd_2018_window, and neither is derived from the other"
    - "_sample_single_band_window in pipeline/attach_labels.py mirrors course.live.aef_cog.sample_points_from_window's array-indexing logic, adapted for a 2-D single-band raster (HRL Imperviousness) instead of a (64, H, W) stack"

key-files:
  created:
    - pipeline/extract_aef.py
    - pipeline/attach_labels.py
    - tests/test_extract_aef.py
    - tests/test_attach_labels.py
  modified: []

key-decisions:
  - "extract_area_year's CRS-reuse check compares rasterio.crs.CRS.from_user_input(tile['crs']) against CRS.from_user_input(AREAS[area]['epsg']) rather than string equality (e.g. 'EPSG:32632' vs 32632 would otherwise never match) -- verified interactively that CRS equality holds across int/string EPSG representations of the same code"
  - "Added a 4th non-network test (beyond the plan's 3 required) asserting the reprojection fallback path actually produces UTM-magnitude coordinates rather than degrees, since a silent CRS mismatch here would corrupt every point's embedding without any other test catching it"
  - "attach_labels.py declares label_source/validation_source as lowercase module-level constants (not the more PEP8-conventional UPPER_CASE) specifically so the literal grep-checkable assignment 'label_source = \"esa_worldcover_2021\"' exists verbatim in the file, satisfying the plan's acceptance-criteria grep pattern while also giving both values a single canonical, testable definition point"
  - "Ran the network-marked extract_aef live test manually with the 'providers' extra temporarily synced (uv sync --extra providers), confirmed it passes end-to-end (real find_tile + read_window against a ~200m x 200m sub-bbox around Bern, unit-norm A00..A63 within atol=1e-3), then reverted to uv sync (no extras) so the default environment keeps duckdb absent per ENV-05/T-01-10 -- consistent with Plan 02-02's established pattern for this exact situation"

patterns-established: []

requirements-completed: [DATA-01, DATA-03, DATA-07, DATA-08]

# Metrics
duration: 2min
completed: 2026-09-03
---

# Phase 2 Plan 7: AlphaEarth Extraction and Label/Validation Attachment Summary

**`pipeline.extract_aef.extract_area_year` and `pipeline.attach_labels.attach_labels`: one windowed AlphaEarth read plus one HRL Imperviousness read per area/year, each indexed once for every sample point, with WorldCover-derived labels kept architecturally separate from the independent HRL validation reference.**

## Performance

- **Duration:** 2 min (commit-to-commit across both TDD task pairs; one live network verification of the network-marked test run separately with the `providers` extra temporarily synced, ~86s, not counted against task duration)
- **Started:** 2026-09-03T20:06:17+02:00
- **Completed:** 2026-09-03T20:08:20+02:00
- **Tasks:** 2 completed (both TDD: RED -> GREEN)
- **Files modified:** 4 (all created)

## Accomplishments

- `extract_area_year(area, year, points, bbox_4326=None)` calls `find_tile` + `read_window` exactly once per `(area, year)`, `dequantize_aef` exactly once on the whole window, then `sample_points_from_window` exactly once with the full point array -- regression-tested via call-count assertions at 5 and 50 points
- Reuses `sample_design`'s precomputed `x`/`y` columns only when their CRS genuinely matches the AlphaEarth tile's own CRS (compared via `rasterio.crs.CRS` equality); otherwise reprojects `lon`/`lat` into the tile's CRS explicitly -- verified with a dedicated test that the reprojected fallback path produces UTM-magnitude coordinates, not degrees
- Returns a `pd.DataFrame` with `sample_id` and `A00..A63` (`course.schema.A_COLS`) columns, one row per input point, in the input's original order
- Accepts an optional `bbox_4326` override so the network-marked live test scopes its read to a small ~200m x 200m sub-bbox around 5 real Bern points instead of the full AOI (02-RESEARCH.md measured 311-342s for a full-AOI window; that path is already exercised by Plans 02-09/02-10)
- `attach_labels(area, points)` maps `worldcover_class` -> `label` via `class_to_label` per row, sets a constant `label_source = "esa_worldcover_2021"`, calls `imd_2018_window` exactly once per area, and samples every point's `imd_2018` value by array-indexing that single fetched window via a new `_sample_single_band_window` helper (mirroring `sample_points_from_window`'s indexing logic for a single-band raster), setting a constant `validation_source = "eea_hrl_imperviousness_2018"`
- `label_source` and `validation_source` are hardcoded, distinct module-level constants -- directly asserted never-equal by a dedicated test, and the pipeline has no code path that could derive one from the other (T-02-14/Pitfall 6 mitigation)
- Live network verification (run manually, `providers` extra temporarily synced then reverted): `extract_area_year("bern", 2021, ...)` against 5 real points and a ~200m x 200m sub-bbox returned unit-norm `A00..A63` vectors (`atol=1e-3`) in 86s

## Task Commits

Each task was committed atomically (both TDD: test -> feat):

1. **Task 1: extract_area_year -- one window read, array-indexed per point**
   - `d50bde1` test(02-07): add failing tests for extract_area_year (RED)
   - `5088d0d` feat(02-07): implement extract_area_year (GREEN)
2. **Task 2: attach_labels -- course label plus independent validation reference**
   - `0e18c15` test(02-07): add failing tests for attach_labels wiring (RED)
   - `28acdd4` feat(02-07): implement attach_labels (GREEN)

## Files Created/Modified

- `pipeline/extract_aef.py` (91 lines) - `extract_area_year`
- `pipeline/attach_labels.py` (100 lines) - `attach_labels`, `_sample_single_band_window`, `label_source`, `validation_source`
- `tests/test_extract_aef.py` (171 lines) - call-count regression tests (5 and 50 points), column/order tests, CRS-reprojection-fallback test, one `@pytest.mark.network` live integration test scoped to a small sub-bbox
- `tests/test_attach_labels.py` (130 lines) - `TestSampleSingleBandWindow` (center-pixel, out-of-bounds, multi-point ordering, mirroring `test_aef_cog.py`'s existing pattern), `TestAttachLabelsWiring` (label correctness, `label_source != validation_source`, `imd_2018_window` called once at both 3 and 30 points)

## Decisions Made

- Compared CRS via `rasterio.crs.CRS.from_user_input(...)` equality rather than string equality, since `tile["crs"]` (e.g. `"EPSG:32632"`) and `AREAS[area]["epsg"]` (e.g. `32632`) are different Python types representing the same CRS -- verified interactively that `CRS.from_user_input(32632) == CRS.from_user_input("EPSG:32632")` before relying on it.
- Added a 4th non-network test for `extract_area_year`'s reprojection fallback (beyond the plan's 3 required tests) because a silently-wrong CRS reuse here would corrupt every point's embedding without any other test in this plan or 02-02/02-06 catching it.
- Named the two source constants in `attach_labels.py` as lowercase `label_source`/`validation_source` module-level variables specifically so the literal string `label_source = "esa_worldcover_2021"` (and its validation-source counterpart) appears verbatim in the file, satisfying the plan's grep-based acceptance criteria while giving both values one canonical definition site that tests import directly.
- Verified the network-marked `extract_aef` test manually with `uv sync --extra providers` (duckdb requires this extra for `find_tile`), then reverted with `uv sync` to restore the default no-`providers` environment -- `uv run pytest tests/ -q` confirmed clean (75 passed, 3 skipped, 6 deselected) both before and after.

## Deviations from Plan

None - plan executed exactly as written. The 4th (reprojection-fallback) test in `test_extract_aef.py` is an addition within the plan's own described behavior spec ("otherwise reproject explicitly and do not silently reuse a mismatched CRS"), not a behavior change.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required. The network-marked tests require the `providers` extra (`uv sync --extra providers`) and live internet access to run, but are excluded from the default `uv run pytest tests/` suite via the `network` marker (`addopts = ["-m", "not network"]` in `pyproject.toml`).

## Next Phase Readiness

- `pipeline.extract_aef.extract_area_year` and `pipeline.attach_labels.attach_labels` are ready for Plan 02-08 (which owns `pipeline/attach_s2.py`) and Plans 02-09/02-10 (full-AOI regeneration and real pipeline run) to compose into the per-area/year table build.
- Both functions' "exactly once per area/year" contracts are locked in by call-count tests, so a future accidental regression to per-point fetching will fail fast in CI rather than silently costing hours at build time.
- No blockers.

---
*Phase: 02-frozen-two-region-teaching-datasets*
*Completed: 2026-09-03*

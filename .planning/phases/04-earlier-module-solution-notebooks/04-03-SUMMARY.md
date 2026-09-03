---
phase: 04-earlier-module-solution-notebooks
plan: 03
subsystem: data
tags: [rasterio, cog, alphaearth, geotiff, dequantization]

requires:
  - phase: 02-frozen-teaching-dataset
    provides: course.live.aef_cog (find_tile, read_window), course.embeddings.dequantize_aef
provides:
  - "pipeline/extract_clip_raster.py: author-side, network-using script that (re)builds the clipped raster from the live GCS COG"
  - "data/bern_aef_2024_clip.tif: checked-in raw int8, 64-band, COG GeoTIFF, ~1.5km sub-AOI of Bern, year 2024"
  - "data/bern_aef_2024_clip.provenance.json: provenance record for the clip"
  - "tests/test_clip_raster.py: non-network raster-integrity tests + network-marked regeneration test"
affects: [04-05, 04-06, earlier-module-notebooks]

tech-stack:
  added: []
  patterns:
    - "Author-side-only extraction scripts write raw (non-dequantized) rasters when the pedagogy requires the student to run dequantization themselves"

key-files:
  created:
    - pipeline/extract_clip_raster.py
    - data/bern_aef_2024_clip.tif
    - data/bern_aef_2024_clip.provenance.json
    - tests/test_clip_raster.py

key-decisions:
  - "Sub-bbox (7.44, 46.94, 7.46, 46.96) yields a 157x225 pixel window with zero nodata pixels — visually interesting mixed Bern terrain, not an arbitrary corner"
  - "Shipped raw int8 (not dequantized float32) so the notebook demonstrates the dequantization formula on genuine raw values, per plan directive"
  - "License/attribution/dequantization formula/nodata value recorded as GeoTIFF tags via update_tags(), in addition to the sidecar provenance JSON, so the artifact is self-describing even if the JSON is lost"
  - "Ran uv sync --extra providers only transiently to execute the network-using script, then uv sync (no extras) to restore the default env — avoids breaking tests/test_core_env_isolation.py which asserts duckdb/geotessera are absent by default"

patterns-established: []

requirements-completed: [EARLY-04]

duration: 25min
completed: 2026-09-03
---

# Phase 04 Plan 03: Author-side AlphaEarth clip raster Summary

**Checked-in 2.0MB, 64-band int8 COG GeoTIFF of a Bern sub-AOI (2024), built via a reusable author-side script against the live anonymous GCS bucket, with provenance and dequantization tags for the offline notebook path.**

## Performance

- **Duration:** 25 min
- **Started:** 2026-09-03T23:09:00Z (approx)
- **Completed:** 2026-09-03T23:34:41Z
- **Tasks:** 2 completed
- **Files modified:** 4 created

## Accomplishments
- `pipeline/extract_clip_raster.py` reuses `course.live.aef_cog.find_tile`/`read_window` (no re-implementation) to clip a small, hardcoded 1.5km sub-AOI window from the live AlphaEarth GCS bucket, writing raw (undequantized) int8 to a COG GeoTIFF
- `data/bern_aef_2024_clip.tif` checked in: 64 bands, int8, nodata -128, 157x225px, 2.0MB (well under the 3MB budget), zero nodata pixels in the chosen window
- License, attribution, dequantization formula, and nodata value recorded verbatim in the GeoTIFF's own tags, plus a sidecar `data/bern_aef_2024_clip.provenance.json`
- `tests/test_clip_raster.py` proves the checked-in file dequantizes to unit-norm vectors via `course.embeddings.dequantize_aef` with no network access, and separately (network-marked) exercises the full regeneration path

## Task Commits

Each task was committed atomically:

1. **Task 1: Author-side clip script and checked-in COG** - `ec32da7` (feat)
2. **Task 2: Non-network raster-integrity test and network-marked regeneration test** - `c9dc24f` (test)

## Files Created/Modified
- `pipeline/extract_clip_raster.py` - `build_clip()`, the one author-side network-using script for this artifact
- `data/bern_aef_2024_clip.tif` - checked-in raw int8, 64-band, COG GeoTIFF
- `data/bern_aef_2024_clip.provenance.json` - provenance record (source tile URL, dataset version, sampling method, license, attribution)
- `tests/test_clip_raster.py` - integrity + regeneration tests

## Decisions Made
- Used the plan's suggested sub-bbox `(7.44, 46.94, 7.46, 46.96)` as-is; verified empirically it produces a 225x157 window with 0% nodata, so no adjustment was needed.
- Wrote both GeoTIFF tags and a JSON sidecar for provenance (belt-and-suspenders) since the plan explicitly required "self-describing" tags in the acceptance criteria while also asking for a separate provenance JSON artifact.
- Did not edit `data/DATA_CARD.md` — deferred to Plan 04-07 per the plan's explicit instruction.

## Deviations from Plan

None - plan executed exactly as written. One incidental note: executing the network-using script required temporarily installing the `providers` extra (`uv sync --extra providers`) since `find_tile` imports `duckdb` lazily; the environment was restored to the default (no extras) afterward with a plain `uv sync` so `tests/test_core_env_isolation.py` continues to pass, per this project's ENV-05/T-01-10 isolation contract (pre-existing, not a plan requirement, restored to keep the shared test suite green).

## Issues Encountered
None.

## User Setup Required
None - no external service configuration required. The script requires network access (anonymous, no credentials) only when regenerating the artifact; the checked-in file and its tests need neither.

## Next Phase Readiness
`data/bern_aef_2024_clip.tif` and its provenance are ready for Plans 04-05/04-06 (`01_alphaearth_access_visualize.ipynb` Path B) to read directly with `rasterio`, dequantize via `course.embeddings.dequantize_aef`, and demonstrate pseudo-RGB/PCA on real pixels with zero network access. No blockers.

---
*Phase: 04-earlier-module-solution-notebooks*
*Completed: 2026-09-03*

## Self-Check: PASSED

---
phase: 02-frozen-two-region-teaching-datasets
plan: 03
subsystem: data
tags: [rasterio, requests, worldcover, eea-hrl, labels, geospatial]

# Dependency graph
requires:
  - phase: 02-frozen-two-region-teaching-datasets
    plan: 01
    provides: course.config.AREAS, course.live.LiveSourceUnavailable
provides:
  - course.live.labels.worldcover_window — one bounded ESA WorldCover 2021 class-code window read per AOI
  - course.live.labels.class_to_label — WorldCover raw code -> course 5-class teaching label
  - course.live.labels.worldcover_tile_name — 3x3-degree lower-left-corner WorldCover tile naming
  - course.live.labels.imd_2018_window — one bounded EEA HRL Imperviousness 2018 window read per AOI (independent reference, never a label)
affects: [02-07]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "WorldCover label and HRL Imperviousness reference are architecturally separate functions (worldcover_window/class_to_label vs imd_2018_window) so label_source can never be derived from validation_source or vice versa"
    - "Both live-source readers do exactly one bounded rasterio/requests call per AOI, never a per-point loop, matching 02-01's LiveSourceUnavailable contract"
    - "HRL response bytes parsed via rasterio.io.MemoryFile, no disk write"

key-files:
  created:
    - course/live/labels.py
    - tests/test_labels.py

key-decisions:
  - "class_to_label raises KeyError (not LiveSourceUnavailable) for unrecognized codes — this is a programming/data-corruption error, not a live-source failure, so it should not be caught by the same fallback-to-frozen-data handling"
  - "Both worldcover_window and imd_2018_window catch a broad Exception around the rasterio/requests call and re-raise as LiveSourceUnavailable, per the plan's threat-model mitigation for T-02-06 (tampered/non-GeoTIFF remote bytes)"
  - "imd_2018_window's exportImage params use bboxSR=4326 always (input bbox is always EPSG:4326 per course.config.AREAS) with imageSR=dst_epsg for server-side reprojection, avoiding a client-side rasterio reproject step"
  - "A call-count test (test_worldcover_window_calls_rasterio_open_once_per_aoi) locks in the 'one window read per AOI, never per-point' contract from 02-RESEARCH.md Pitfall 4, using a monkeypatched fake rasterio.open so no real I/O occurs in the fast suite"

patterns-established: []

requirements-completed: [DATA-01, DATA-03, DATA-07]

# Metrics
duration: 12min
completed: 2026-09-03
---

# Phase 2 Plan 3: WorldCover Labels and Independent HRL Imperviousness Reference Summary

**`course/live/labels.py` with `worldcover_tile_name`/`worldcover_window`/`class_to_label` (ESA WorldCover 2021 v200 -> 5-class teaching label) and `imd_2018_window` (EEA HRL Imperviousness Density 2018, architecturally separate, an independent reference never used as a label), both doing one bounded window read per AOI.**

## Performance

- **Duration:** 12 min
- **Started:** 2026-09-03
- **Completed:** 2026-09-03
- **Tasks:** 2 completed
- **Files modified:** 2 created

## Accomplishments

- `worldcover_tile_name(lon, lat)` computes ESA WorldCover's 3x3-degree lower-left-corner tile name; verified exact match against both confirmed tile names (`N45E006` for Bern, `N36W006` for Seville)
- `worldcover_window(bbox_4326)` opens the tile via `/vsicurl/` and does exactly one bounded `rasterio` window read per AOI (locked in by a monkeypatched call-count test), returning `(arr, transform)`; raises `LiveSourceUnavailable` on any open/read failure
- `class_to_label(code)` maps all 11 official WorldCover v200 codes to the course's 5 teaching labels (`built`, `crop`, `vegetation`, `water`, `bare`), documented with the grouping rationale in the module docstring; raises `KeyError` naming the unrecognized code for anything outside the mapping
- `imd_2018_window(bbox_4326, dst_epsg, size)` calls the EEA `HRL_ImperviousnessDensity_2018` ImageServer `exportImage` endpoint once per AOI (`bboxSR=4326`, `imageSR=dst_epsg`, `format=tiff`), parses the response bytes via `rasterio.io.MemoryFile` (no disk write), and raises `LiveSourceUnavailable` on request failure or a non-GeoTIFF body
- `imd_2018_window` is architecturally separate from `worldcover_window`/`class_to_label` — no shared state or derivation between them — so a downstream `label_source` can never equal `validation_source` (Pitfall 6 mitigation, T-02-07)
- All four functions verified live against the real WorldCover S3 bucket and the real EEA ImageServer this session (`uv run pytest tests/test_labels.py -m network` — 2 passed), not just against mocks

## Task Commits

Each task was committed atomically (Task 2 is TDD: test -> feat):

1. **Task 1: WorldCover window read and course label mapping**
   - `9131965` feat(02-03): add WorldCover 2021 window read and class label mapping
2. **Task 2: EEA HRL Imperviousness 2018 independent reference and tests**
   - `7f76a76` test(02-03): add failing tests for imd_2018_window (RED)
   - `7ce88e8` feat(02-03): implement EEA HRL Imperviousness 2018 independent reference (GREEN)

## Files Created/Modified

- `course/live/labels.py` (166 lines) - `WORLDCOVER_BASE`, `EEA_IMD_BASE`, `WORLDCOVER_CLASS_TO_LABEL`, `worldcover_tile_name`, `worldcover_window`, `class_to_label`, `imd_2018_window`
- `tests/test_labels.py` (163 lines) - 9 fast (no-network) tests + 2 `@pytest.mark.network` tests covering tile naming, class mapping totality/values, the call-count contract, mocked `imd_2018_window` request/parse and bad-response handling, and live integration against both real sources

## Decisions Made

- Kept `class_to_label`'s failure mode as `KeyError`, not `LiveSourceUnavailable` — an unrecognized class code is a data/programming defect (e.g. a WorldCover legend revision), not a live-source outage, so it should propagate distinctly rather than trigger a frozen-data fallback.
- Used a broad `except Exception` around each reader's rasterio/requests call, per the plan's threat-model mitigation (T-02-06): both readers must fail loudly and uniformly on tampered/non-GeoTIFF remote bytes, regardless of whether the underlying failure is a network error, an HTTP status, or a GDAL parse error.
- Split Task 1 and Task 2 into separate, self-contained commits even though both land in the same `course/live/labels.py` file, so the TDD RED/GREEN gate for Task 2 (`imd_2018_window`) is visible independently of Task 1's already-passing WorldCover code in git log.

## Deviations from Plan

None — plan executed exactly as written. `imd_2018_window`'s per-source-failure catch uses a broad `except Exception` (as `worldcover_window` already does) rather than narrowing to `requests.RequestException`/`rasterio.errors.RasterioIOError` specifically; this is the same pattern Task 1 established and matches the plan's "Raise `LiveSourceUnavailable` if the response is not a valid GeoTIFF (catch the rasterio open failure)" instruction without introducing a second, narrower exception-handling convention in the same module.

## Issues Encountered

None. Live network access was available in this execution environment, so both `@pytest.mark.network` tests (`test_worldcover_window_live_bern`, `test_imd_2018_window_live_bern`) were run and passed against the real ESA WorldCover S3 bucket and the real EEA HRL ImageServer, confirming the implementation end to end rather than only against mocks.

## TDD Gate Compliance

Task 2 shows the required RED -> GREEN commit sequence in git log (`7f76a76` test commit, collection failed with `ImportError: cannot import name 'imd_2018_window'`, confirmed before the GREEN commit `7ce88e8`). No REFACTOR commit was needed.

## User Setup Required

None - no external service configuration required. Both sources (ESA WorldCover S3, EEA HRL ImageServer) are anonymously reachable with no credentials.

## Next Phase Readiness

- `worldcover_window`, `class_to_label`, and `imd_2018_window` are stable, unit-tested (and live-verified) contracts. Plan 02-07 (`pipeline/attach_labels.py`) can import them directly to set `label`/`label_source="esa_worldcover_2021"` and `imd_2018`/`validation_source="eea_hrl_imperviousness_2018"` as two distinct, never-derived-from-each-other columns.
- No blockers.

---
*Phase: 02-frozen-two-region-teaching-datasets*
*Completed: 2026-09-03*

## Self-Check: PASSED

Both claimed files found on disk (`course/live/labels.py`, `tests/test_labels.py`); all 3 commit hashes (9131965, 7f76a76, 7ce88e8) found in git log.

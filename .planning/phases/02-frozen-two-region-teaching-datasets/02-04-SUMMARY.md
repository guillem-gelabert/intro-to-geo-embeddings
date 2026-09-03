---
phase: 02-frozen-two-region-teaching-datasets
plan: 04
subsystem: data
tags: [sentinel-2, stac, earth-search, rasterio, requests, scl-masking]

# Dependency graph
requires:
  - phase: 02-frozen-two-region-teaching-datasets
    plan: 01
    provides: course.live.LiveSourceUnavailable, course.schema.S2_COLS, course.config.AREAS
provides:
  - course.live.s2_stac.search_scenes — Earth Search STAC POST search, LiveSourceUnavailable on failure/empty
  - course.live.s2_stac.select_scenes — deterministic same-date duplicate-item resolution (_0_ vs _1_ archive pairs)
  - course.live.s2_stac.sample_bands — SCL-masked, point-sampled reflectance with a defensive plausibility assertion, never subtracting the collection's contradictory offset metadata
affects: [02-08]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Never trust raster:bands.offset / earthsearch:boa_offset_applied literally for this collection — apply scale only, then assert mean reflectance lands in a plausible range and fail loudly otherwise"
    - "STAC duplicate-item dedup is a pure function over already-fetched item lists (select_scenes), independently unit-testable without network"
    - "Every remote-source read (STAC search, COG asset open) is wrapped to raise LiveSourceUnavailable, never a bare requests/rasterio exception"

key-files:
  created:
    - course/live/s2_stac.py
    - tests/test_s2_stac.py
  modified: []

key-decisions:
  - "Deviation (Rule 1 bug fix): the plan's literal datetime string (f\"{year}-{months[0]:02d}-01/{year}-{months[1]:02d}-31\") is rejected by the live Earth Search API (\"datetime value is invalid, does not match RFC3339 format\") and hardcodes an invalid day-31 for any end month with fewer than 31 days. Fixed by emitting full RFC3339 datetimes (T00:00:00Z/T23:59:59Z) with calendar.monthrange computing the end month's actual last day — verified live against the real endpoint."
  - "Earth Search asset keys are band common names (blue/green/red/nir/swir16/swir22/scl), not B02-style codes — verified live; BAND_ASSET_KEYS maps the course's B02..B12 vocabulary onto them."
  - "select_scenes groups purely by acquisition date, not by (date, MGRS tile) — matches the plan's literal spec and tested acceptance criteria exactly. Live search confirmed the Bern bbox can return items from two different MGRS 100km tiles (32TLS/32TLT) on the same date; date-only grouping could in principle drop one tile's coverage for that date, but points still accumulate contributions from other dates' scenes across the season, so this does not block the plan's correctness requirements. Documented here for Plan 02-08's awareness, not changed, since altering the grouping key is an architectural change outside this task's scope."
  - "sample_bands casts S2_B02..S2_B12 to float32 (not left as pandas' default float64) to match the frozen schema's stated float32 convention and the 02-RESEARCH.md row-budget design, even though not explicitly required by the plan's acceptance criteria."

patterns-established:
  - "Pattern: TDD tasks land as paired test(...)/feat(...) commits so RED/GREEN gates are visible in git log (Task 2 here)"

requirements-completed: [DATA-02, DATA-07]

# Metrics
duration: 15min
completed: 2026-09-03
---

# Phase 2 Plan 4: Sentinel-2 Raw-Band Adapter Summary

**`course/live/s2_stac.py` with `search_scenes`/`select_scenes`/`sample_bands` over Earth Search STAC — deterministic `_0_`/`_1_` duplicate-item resolution and SCL-masked band sampling that deliberately never subtracts the collection's contradictory offset metadata, instead asserting reflectance plausibility.**

## Performance

- **Duration:** 15 min
- **Started:** 2026-09-03T19:30:26+02:00
- **Completed:** 2026-09-03T19:44:26+02:00
- **Tasks:** 2 completed
- **Files modified:** 2 (2 created)

## Accomplishments
- `search_scenes(bbox_4326, year, months, cloud_lt)` — POSTs to Earth Search STAC (`sentinel-2-l2a`), raises `LiveSourceUnavailable` on request failure or zero results
- `select_scenes(items)` — resolves same-date duplicate archive items deterministically: prefers `_0_` (original processing) for dates before 2022-01-25, otherwise lowest `eo:cloud_cover`, ties broken by `id`; verified live against a real duplicate pair (`S2B_32TLS_20210812_0_L2A`/`_1_L2A`)
- `sample_bands(items, points_lonlat, bands)` — reads each band's COG asset at each point, applies `raster:bands.scale` with NO offset subtraction, masks SCL classes 3/8/9/10 before compositing, takes the per-point median across contributing scenes, returns `S2_B02..S2_B12` (float32, matching `course.schema.S2_COLS`) plus `s2_n_scenes`
- Defensive plausibility assertion (`-0.05 < mean < 0.6`) fires loudly on implausible reflectance regardless of which offset convention the scene metadata claims — verified this fires correctly on synthetic implausible data and passes on real live-fetched data (measured 0.06–0.24 reflectance at Bern, summer 2021, consistent with 02-RESEARCH.md's offset-free finding)
- Live-verified against the real Earth Search API: confirmed the exact duplicate-item and offset-metadata discrepancy the research documented (baseline 03.01 items carry `offset: 0`, baseline 05.xx items carry `offset: -0.1` and `boa_offset_applied: true`, at the same scene's reprocessed duplicate)

## Task Commits

Task 1 (non-TDD) and Task 2 (TDD) were each committed atomically:

1. **Task 1: STAC scene search and deterministic duplicate-item resolution**
   - `46d8367` feat(02-04): add Sentinel-2 STAC scene search and duplicate resolution
2. **Task 2: SCL-masked band sampling with the defensive plausibility assertion**
   - `a66e271` test(02-04): add failing tests for SCL-masked band sampling (RED)
   - `dad9f0a` feat(02-04): implement SCL-masked band sampling with plausibility assertion (GREEN)

## Files Created/Modified
- `course/live/s2_stac.py` - `search_scenes`, `select_scenes`, `sample_bands`, plus internal helpers `_apply_scale`, `_assert_plausible_reflectance`, `_asset_href`, `_asset_scale`, `_sample_at_points`
- `tests/test_s2_stac.py` - 7 dedup/search unit tests (no network), 3 sample_bands helper unit tests (no network), 1 `@pytest.mark.network` end-to-end test against Bern summer 2021

## Decisions Made
- Fixed the plan's literal datetime-string bug (Rule 1) after verifying live against Earth Search that date-only ranges are rejected and hardcoded day-31 is invalid for shorter months — see `key-decisions` above.
- Cast `sample_bands`' band columns to `float32` to match the frozen schema's documented dtype convention, even though the plan's acceptance criteria didn't explicitly require a dtype.
- Kept `select_scenes`' grouping key as date-only, exactly per the plan's literal spec and tested acceptance criteria, despite discovering live that a single AOI bbox can span two MGRS tiles on the same date — documented as a note for Plan 02-08 rather than an in-scope architectural change (Rule 4 territory, not applied since the plan's explicit tests only cover the date-only grouping and functional correctness is preserved via multi-date compositing).

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed the plan's literal STAC search datetime format**
- **Found during:** Task 1 (`search_scenes`)
- **Issue:** The plan specified `f"{year}-{months[0]:02d}-01/{year}-{months[1]:02d}-31"`. Verified live against `https://earth-search.aws.element84.com/v1/search`: this date-only format is rejected with `{"code":"BadRequest","description":"datetime value is invalid, does not match RFC3339 format"}`. It also hardcodes day 31 for the end month regardless of actual month length (e.g. June has 30 days), which would be an invalid calendar date for non-default `months` arguments.
- **Fix:** Emit full RFC3339 datetimes (`T00:00:00Z`/`T23:59:59Z`) and compute the end month's actual last day via `calendar.monthrange(year, end_month)`.
- **Files modified:** `course/live/s2_stac.py`
- **Verification:** Live curl and live pytest run against the real endpoint both confirmed the fix works; a regression test (`test_search_scenes_posts_valid_rfc3339_datetime_range`) asserts the exact emitted string.
- **Committed in:** `46d8367` (Task 1 commit)

---

**Total deviations:** 1 auto-fixed (1 bug fix)
**Impact on plan:** Necessary for `search_scenes` to function at all against the live API — without this fix, every call would fail with a 400 error. No scope creep.

## Issues Encountered
None beyond the datetime bug documented above. Live verification (multiple `curl` calls and two full `uv run pytest -m network` runs) confirmed both of the plan's headline empirical claims hold: the `_0_`/`_1_` duplicate-item pattern exists exactly as described, and the offset metadata is genuinely contradictory across processing baselines (03.01 → `offset: 0`; 05.xx → `offset: -0.1`, `boa_offset_applied: true`) at the same reprocessed scene.

## User Setup Required
None - no external service configuration required. Earth Search STAC and the Sentinel-2 COG assets on S3 are anonymously reachable with no credentials.

## Next Phase Readiness
- `search_scenes`, `select_scenes`, and `sample_bands` are stable, unit- and live-tested contracts ready for Plan 02-08 (`pipeline/attach_s2.py`) to consume.
- `select_scenes`' item-ID threading (for provenance, per the plan's threat model T-02-09) is available on every returned item's `id` field — Plan 02-08 should record it.
- Note for Plan 02-08: since `select_scenes` dedups by date only (not date+tile), an AOI whose bbox spans two MGRS grid squares can see one tile's date-item deprioritized in favor of the other tile's same-date item. This did not block this plan's tests or live verification, but Plan 02-08 should be aware that per-point `s2_n_scenes` may be lower near a tile boundary if the search window is narrow.
- No blockers.

---
*Phase: 02-frozen-two-region-teaching-datasets*
*Completed: 2026-09-03*

## Self-Check: PASSED

All 3 claimed files found on disk (`course/live/s2_stac.py`, `tests/test_s2_stac.py`, this SUMMARY.md); all 3 commit hashes (46d8367, a66e271, dad9f0a) found in git log.

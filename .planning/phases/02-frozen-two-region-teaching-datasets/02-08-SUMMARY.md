---
phase: 02-frozen-two-region-teaching-datasets
plan: 08
subsystem: data
tags: [sentinel-2, stac, provenance, pandas]

# Dependency graph
requires:
  - phase: 02-frozen-two-region-teaching-datasets
    plan: 04
    provides: course.live.s2_stac.search_scenes, .select_scenes, .sample_bands
  - phase: 02-frozen-two-region-teaching-datasets
    plan: 06
    provides: pipeline.sample_design.generate_sample_points (fixed sample_id/lon/lat point set)
provides:
  - pipeline.attach_s2.attach_s2(area, year, points) -> pd.DataFrame with sample_id + S2_B02..S2_B12 + s2_n_scenes, points' original row order, scene IDs at result.attrs["s2_item_ids"]
affects: [02-09]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "attach_s2 never talks to Earth Search directly -- it only calls course.live.s2_stac's already-hardened search_scenes/select_scenes/sample_bands, keeping the network trust boundary in one place (Plan 02-04)"
    - "One search_scenes + select_scenes + sample_bands call per (area, year) for the whole point set, never per point (T-02-16, same DoS trap as the other extractors)"
    - "Provenance passed via result.attrs['s2_item_ids'] rather than a tuple return, keeping attach_s2's signature a plain pd.DataFrame per the plan's stated interface -- documented in the module docstring for Plan 02-09's writer"

key-files:
  created:
    - pipeline/attach_s2.py
    - tests/test_attach_s2.py
  modified: []

key-decisions:
  - "Used df.attrs['s2_item_ids'] (not a tuple return) for scene-ID provenance, matching the plan's literal artifact contract 'attach_s2(area, year, points) -> pd.DataFrame' -- the plan offered both conventions as acceptable and asked for the choice to be documented in a one-line module docstring, which is done"
  - "attach_s2 raises LiveSourceUnavailable itself (checking `if not selected`) rather than relying solely on search_scenes's own empty-result guard, so the zero-scenes case is caught defensively regardless of whether the emptiness originates in search_scenes or select_scenes, and the message explicitly names area and year"
  - "Added a KeyError guard for an unknown `area` argument, matching the same defensive pattern already established in pipeline.sample_design.generate_sample_points -- minor consistency addition, not separately tested since it mirrors an existing, already-tested pattern"

patterns-established: []

requirements-completed: [DATA-02, DATA-07]

# Metrics
duration: ~12min
completed: 2026-09-03
---

# Phase 2 Plan 8: Sentinel-2 Raw-Band Attachment Summary

**`pipeline.attach_s2.attach_s2(area, year, points)` wires the fixed sample point set to Sentinel-2 raw reflectance bands via `course.live.s2_stac`, fetching once per (area, year) and never dropping a row even under partial scene coverage.**

## Performance

- **Duration:** ~12 min
- **Started:** 2026-09-03T20:04Z (first commit)
- **Completed:** 2026-09-03T20:10Z (last commit)
- **Tasks:** 2 completed
- **Files modified:** 2 (2 created)

## Accomplishments
- `attach_s2(area, year, points)` calls `search_scenes(AREAS[area]["bbox_4326"], year)` -> `select_scenes(...)` -> `sample_bands(selected, points[["lon","lat"]].to_numpy())` exactly once for the whole point set (verified by a call-count-asserting unit test with 5 points)
- Returns `sample_id` + `S2_B02..S2_B12` + `s2_n_scenes` in `points`' original row order (verified with a deliberately shuffled `sample_id` sequence to catch accidental resorting)
- Raises `course.live.LiveSourceUnavailable` naming the area/year when zero scenes are selected, instead of letting an empty item list propagate into `sample_bands` as an assertion/index error or silently returning an all-NaN table
- Never drops rows under partial scene coverage: points outside the returned scenes' actual coverage keep `s2_n_scenes == 0` and NaN band values, covered points keep their real values, and the row count always equals `len(points)`
- Selected scene IDs are exposed at `result.attrs["s2_item_ids"]` for `pipeline/write.py` (Plan 02-09) to record in the table's provenance metadata (T-02-17)
- Live-verified end to end: `test_attach_s2_end_to_end_bern_2021` (network-marked) ran against the real Earth Search STAC API and real Sentinel-2 COG assets for 3 points at Bern, summer 2021 -- passed in ~99s, confirming the module's wiring works against the live adapter, not just mocks

## Task Commits

Task 1 is TDD (test -> feat); Task 2 is test-only, committed atomically:

1. **Task 1: attach_s2 wiring and provenance**
   - `c0aa12b` test(02-08): add failing tests for attach_s2 wiring and provenance (RED)
   - `8113cdf` feat(02-08): implement attach_s2 wiring and scene provenance (GREEN)
2. **Task 2: Non-network edge case tests**
   - `5f8e3c1` test(02-08): add zero-scene and partial-coverage edge case tests

## Files Created/Modified
- `pipeline/attach_s2.py` (52 lines) - `attach_s2(area, year, points)`; reuses `course.live.s2_stac.search_scenes/select_scenes/sample_bands` without reimplementing any STAC or SCL logic
- `tests/test_attach_s2.py` (139 lines) - 4 non-network tests (call-count, order-preservation, zero-scenes error, partial-coverage passthrough) + 1 `@pytest.mark.network` end-to-end test against Bern summer 2021

## Decisions Made
- Chose `df.attrs["s2_item_ids"]` over a tuple return for scene provenance, per the plan's explicit choice-and-document instruction; documented in `pipeline/attach_s2.py`'s module docstring so Plan 02-09's writer knows which convention to read.
- Added attach_s2's own `if not selected: raise LiveSourceUnavailable(...)` check rather than depending only on `search_scenes`'s internal empty-result guard, so the error message reliably names the area and year regardless of where the empty scene list originates, and so a future change to `search_scenes`'s own error handling can't silently reintroduce an IndexError here.
- Added a minor `KeyError` guard for an unrecognized `area` argument, mirroring the existing pattern in `pipeline.sample_design.generate_sample_points` (Plan 02-06) -- a small consistency addition, not a plan-mandated behavior, so no dedicated test was added for it.

## Deviations from Plan

None - plan executed exactly as written. The `area` KeyError guard above is a minor, pattern-consistent addition (Rule 2 territory, but trivial) rather than a deviation from any specified behavior.

## Issues Encountered

None. The live network test (`test_attach_s2_end_to_end_bern_2021`, excluded from the default suite by `pyproject.toml`'s `addopts = -m "not network"`) was run manually in this session and passed against the real Earth Search STAC API, confirming the module's wiring end to end beyond the mocked unit tests.

## TDD Gate Compliance

Task 1 shows the required RED -> GREEN commit sequence in git log (`c0aa12b` test commit -- collection failed with `ImportError: cannot import name 'attach_s2' from 'pipeline'`, confirmed before the GREEN commit `8113cdf`). No REFACTOR commit was needed.

## User Setup Required

None - no external service configuration required. Earth Search STAC and the Sentinel-2 COG assets on S3 are anonymously reachable with no credentials (same as Plan 02-04's adapter).

## Next Phase Readiness

- `pipeline.attach_s2.attach_s2(area, year, points)` is a stable, unit- and live-tested contract ready for Plan 02-09 (`pipeline/write.py`) to consume: call it per (area, year) against `pipeline.sample_design.generate_sample_points(area)`'s fixed point set, join the result on `sample_id`, and read `result.attrs["s2_item_ids"]` for provenance.
- Note for Plan 02-09: per Plan 02-04's summary, `select_scenes` dedups by date only (not date+tile), so an AOI spanning two MGRS tiles can see per-point `s2_n_scenes` lower near a tile boundary -- this does not block correctness (median compositing across dates still applies) but is worth surfacing in the provenance record's scene count if the writer wants to flag low-coverage points.
- No blockers.

---
*Phase: 02-frozen-two-region-teaching-datasets*
*Completed: 2026-09-03*

## Self-Check: PASSED

All 3 claimed files found on disk (`pipeline/attach_s2.py`, `tests/test_attach_s2.py`, this SUMMARY.md); all 3 commit hashes (c0aa12b, 8113cdf, 5f8e3c1) found in git log.

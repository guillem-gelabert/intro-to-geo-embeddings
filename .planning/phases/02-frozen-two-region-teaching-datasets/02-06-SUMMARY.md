---
phase: 02-frozen-two-region-teaching-datasets
plan: 06
subsystem: data
tags: [numpy, geopandas, rasterio, pyyaml, worldcover, sampling, spatial-blocks]

# Dependency graph
requires:
  - phase: 02-frozen-two-region-teaching-datasets
    plan: 01
    provides: course.config.AREAS, course.config.BLOCK_SIZE_M, course.config.RANDOM_STATE
  - phase: 02-frozen-two-region-teaching-datasets
    plan: 03
    provides: course.live.labels.worldcover_window, course.live.labels.class_to_label
provides:
  - pipeline/areas.yaml — per-region sampling parameters (n_target, class_caps, min_spacing_m, seed)
  - pipeline.sample_design.generate_sample_points(area) — fixed, stratified, capped, seed-stable sample point set with sample_id, region, lon, lat, x, y, block_id, worldcover_class
  - pipeline.sample_design._block_id(x, y, block_size_m) — deterministic 1.5 km grid cell id in a projected CRS
affects: [02-07, 02-08, 02-12]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "pipeline/areas.yaml holds only pipeline-only sampling parameters (n_target, class_caps, min_spacing_m, seed) and references course.config.AREAS by region name for bbox/epsg rather than duplicating them"
    - "One bounded WorldCover window read per region (via course.live.labels.worldcover_window); all stratification, capping, and id/block assignment happens on the in-memory array — never a per-point network call"
    - "sample_id is assigned by sorting selected candidates on (label, row, col) before enumerating 0..N-1, not by draw order, so a re-run at the same seed reproduces an identical sample_id -> (lon, lat) mapping"
    - "worldcover_class carries the raw WorldCover code only; the code -> course-label mapping is deliberately deferred to Plan 02-07 so the one WorldCover fetch per region is never repeated"
    - "block_id is computed only after reprojecting a copy of the point geometry into the region's own UTM EPSG (course.config.AREAS[area]['epsg']); the returned GeoDataFrame's own geometry/CRS stays EPSG:4326, x/y are plain float columns"

key-files:
  created:
    - pipeline/__init__.py
    - pipeline/areas.yaml
    - pipeline/sample_design.py
    - tests/test_sample_design.py

key-decisions:
  - "Used PyYAML (already a transitive dependency via jupytext/pre-commit in the dev group, confirmed importable) for pipeline/areas.yaml rather than falling back to a plain Python dict literal — the plan's fallback trigger (yaml not importable) did not occur"
  - "Class caps set exactly as 02-RESEARCH.md's settled recommendation: crop/vegetation/built 500, water 400, bare 150 (below Bern's measured 219-candidate pool, so bare is genuinely cap-bound at Seville but pool-bound at Bern)"
  - "Split Task 2 (x/y/block_id) into a distinct test(RED) -> feat(GREEN) commit pair even though Task 1's block-agnostic sample_id/lon/lat/worldcover_class implementation already existed in the same file, per the plan's tdd=\"true\" flag on Task 2"
  - "_block_id extracted as a small, independently-unit-testable pure function (x, y, block_size_m) -> block id string, rather than inlining the floor-division into generate_sample_points — makes the same-cell/different-cell behavior directly testable without depending on random sample selection"

patterns-established: []

requirements-completed: [DATA-01, DATA-03, DATA-04, DATA-08]

# Metrics
duration: 20min
completed: 2026-09-03
---

# Phase 2 Plan 6: Sampling Design (Stratified WorldCover Points + Spatial Blocks) Summary

**`pipeline.sample_design.generate_sample_points(area)`: one bounded WorldCover window read per region, stratified-with-caps candidate draw (crop/vegetation/built capped at 500, water 400, bare 150, clamped to whatever pool actually exists), seed-stable `sample_id`, and `block_id` computed from a 1.5 km grid in the region's own projected UTM CRS.**

## Performance

- **Duration:** ~20 min
- **Started:** 2026-09-03
- **Completed:** 2026-09-03T17:59:08Z
- **Tasks:** 2 completed
- **Files modified:** 4 created

## Accomplishments

- `pipeline/areas.yaml` holds per-region sampling parameters (`n_target: 2000`, `class_caps`, `min_spacing_m: 50`, `seed: 42`) for both `bern` and `seville`, referencing `course.config.AREAS` by name rather than duplicating bbox/epsg
- `generate_sample_points(area)` reads one bounded WorldCover window via `course.live.labels.worldcover_window`, builds a stride-5 (50 m spacing at WorldCover's 10 m/px) candidate grid, maps codes to course labels via `class_to_label`, and draws up to each label's cap using `np.random.default_rng(seed)` — never unseeded — with caps clamped to the available pool per class (never raises or duplicates points to hit a cap)
- `sample_id` is assigned `0..N-1` by sorting the selected candidates on `(label, row, col)` before enumerating, not by draw order — proven seed-stable by a test asserting two independent calls produce identical `sample_id` -> `(lon, lat)` mappings
- `_block_id(x, y, block_size_m)` computes a deterministic `"{cell_x}_{cell_y}"` grid-cell id from projected-CRS coordinates; wired into `generate_sample_points` after reprojecting a copy of the point geometry to the region's own UTM EPSG (`course.config.AREAS[area]["epsg"]`) — never computed in degrees
- The returned GeoDataFrame keeps its own geometry/CRS at EPSG:4326 (matching `course.schema.validate`'s CRS==4326 requirement); `x`/`y` are plain float columns holding the projected coordinates, not a second geometry
- Verified manually against a full-AOI synthetic Bern sample: 1,916 points selected (500 crop, 500 vegetation, 500 built, 400 water, 16 bare — bare's synthetic pool was deliberately smaller than its cap), 250 distinct `block_id`s (well within 02-RESEARCH.md's measured 150–509 range, far above the DATA-08 floor of 5), and `x`/`y` in the expected EPSG:32632 easting/northing magnitude (370k–393k / 5,190k–5,212k), not degrees

## Task Commits

Each task was committed atomically (Task 2 is TDD: test -> feat):

1. **Task 1: areas.yaml and stratified min-spacing point sampling** - `a19da0c` (feat)
2. **Task 2: Projected x/y and block_id assignment**
   - `02a6362` (test — RED: `_block_id`/`x`/`y`/`block_id` tests added, collection fails on missing `_block_id` import)
   - `8fa4d14` (feat — GREEN: `_block_id` implemented and wired into `generate_sample_points`, all tests pass)

## Files Created/Modified

- `pipeline/__init__.py` - empty package marker for `python -m pipeline.build` (later plans)
- `pipeline/areas.yaml` - per-region sampling parameters (n_target, class_caps, min_spacing_m, seed), heavily commented with the research rationale for each cap
- `pipeline/sample_design.py` (149 lines) - `generate_sample_points`, `_candidate_grid`, `_labels_for_codes`, `_stratified_indices`, `_block_id`, `_load_pipeline_areas`
- `tests/test_sample_design.py` (233 lines) - 12 tests: areas.yaml structure, cap-respecting and pool-clamping stratification, seed-stability, dense sample_id range, CRS==4326, unknown-area error, `_block_id` same/different-cell behavior, block count well above 5, x/y in UTM range not degrees, block_id matches direct `_block_id` computation

## Decisions Made

- Used PyYAML directly (confirmed already a transitive dependency via jupytext/pre-commit in the `dev` dependency group, always installed by `uv sync`) rather than the plan's dict-literal fallback, since `yaml` imports cleanly in this environment.
- Deliberately did not resolve `worldcover_class` to a course label inside `generate_sample_points` — only the raw WorldCover code is carried through, so the one-per-region WorldCover fetch this module does is never repeated by Plan 02-07's label-attachment step, per the plan's `key_links` contract.
- Extracted `_block_id` as a standalone, directly-testable pure function rather than inlining the floor-division inside `generate_sample_points`, to satisfy Task 2's TDD requirement for same-cell/different-cell unit tests independent of the random sampling draw.

## Deviations from Plan

None - plan executed exactly as written. `_block_id` as a named private helper (vs. inlining the block computation) is a code-structure choice within the plan's own action text ("compute block_id as f"{int(x//BLOCK_SIZE_M)}_{int(y//BLOCK_SIZE_M)}""), not a behavior change.

## Issues Encountered

None. `uv run ruff format` reformatted one line-length wrap in `_stratified_indices`'s signature during Task 1 — applied before committing, no behavior change.

## TDD Gate Compliance

Task 2 shows the required RED -> GREEN commit sequence in git log (`02a6362` test commit — collection failed with `ImportError: cannot import name '_block_id' from 'pipeline.sample_design'`, confirmed before the GREEN commit `8fa4d14`). No REFACTOR commit was needed.

## User Setup Required

None - no external service configuration required. All tests run against a synthetic in-memory WorldCover array; no network access needed for this plan's test suite.

## Next Phase Readiness

- `pipeline.sample_design.generate_sample_points(area)` is a stable, unit-tested contract: `sample_id`, `region`, `lon`, `lat`, `x`, `y`, `block_id`, `worldcover_class`, `geometry` (EPSG:4326). Plan 02-07 (per-year AlphaEarth/label extraction) can call it once per region and index every year's extraction against the same fixed `sample_id` set.
- `block_id` is the reference answer Plan 02-12's dataset-aliveness guard and any future notebook's own block computation can check against — computed once, here, in the correct projected CRS.
- No blockers. `pipeline/areas.yaml`'s caps (2,050 max per region: 500×3 + 400 + 150) sit within 02-RESEARCH.md's ~1,900–2,200 recommendation; real-network runs against Bern/Seville will land slightly below that ceiling wherever a class's true pool (e.g., Bern's 219-candidate bare) is smaller than its cap.

---
*Phase: 02-frozen-two-region-teaching-datasets*
*Completed: 2026-09-03*

## Self-Check: PASSED

All 5 claimed files found on disk (`pipeline/__init__.py`, `pipeline/areas.yaml`, `pipeline/sample_design.py`, `tests/test_sample_design.py`, this SUMMARY.md); all 3 commit hashes (a19da0c, 02a6362, 8fa4d14) found in git log.

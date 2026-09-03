---
phase: 04-earlier-module-solution-notebooks
plan: 02
subsystem: data
tags: [duckdb, clay, lgnd, geoparquet, provenance, offline-first]

requires: []
provides:
  - "pipeline/fetch_clay_fixture.py: author-side, network-using script that (re)builds a tiny Clay embedding fixture; exports build_fixture"
  - "data/clay_sample_fixture.parquet: checked-in, 1-row Clay patch-embedding fixture for Bern (1024-D)"
  - "data/clay_sample_fixture.provenance.json: provenance sidecar (source path, license, attribution, extraction date)"
affects: [04-04]

tech-stack:
  added: []
  patterns:
    - "Author-side fetch script pattern: network-using script writes a frozen fixture + provenance JSON once; consuming notebook never imports the fetch module or touches the network"

key-files:
  created:
    - pipeline/fetch_clay_fixture.py
    - data/clay_sample_fixture.parquet
    - data/clay_sample_fixture.provenance.json
    - tests/test_clay_fixture.py
  modified: []

key-decisions:
  - "Pinned the corpus file to the single object the S3 ListObjectsV2 listing returned for geohash_l2=u0/year=2025/month=06 (data_01c1fab1-0004-5b1c-0009-b72e01d3104e_222_0_0.parquet) rather than a glob, because the HTTPS mirror rejects `*` in paths by default and the partition currently holds exactly one file"
  - "ST_Intersects on Bern's city-center point against this file returned exactly 1 row (not the requested 5) — acceptable per the plan's 1-5 row acceptance criteria; the fixture stays honestly small"

patterns-established:
  - "Author-side network fetch scripts live in pipeline/ and are excluded from the notebook's dependency graph; their tests split into non-network (default suite) and @pytest.mark.network (excluded by addopts) tiers"

requirements-completed: [EARLY-02]

duration: 25min
completed: 2026-09-04
---

# Phase 04 Plan 02: Author-side Clay/LGND fixture fetch Summary

**Author-side DuckDB script fetches one real Bern-area Clay v1.5 Sentinel-2 L2A patch embedding (1024-D) from the public LGND corpus over HTTPS and freezes it with provenance for offline notebook use.**

## Performance

- **Duration:** ~25 min
- **Tasks:** 2 completed
- **Files modified:** 4 created

## Accomplishments
- `pipeline/fetch_clay_fixture.py` regenerates the fixture anonymously over HTTPS against the pinned `clay/lgnd-clay-v1-5-sentinel-2-l2a` corpus (not the larger `lgnd-embeddings` product)
- `data/clay_sample_fixture.parquet` (14.6 KB, 1 row, `embedding` column of length 1024) committed for `00b_representation_inspection.ipynb` (Plan 04-04) to read with zero network access
- `data/clay_sample_fixture.provenance.json` records source path, query, extraction date, CC BY 4.0 license and the exact attribution sentence
- Default test suite (`uv run pytest tests/`, no `duckdb` installed) passes; a `@pytest.mark.network` regeneration test exercises `build_fixture()` against the live corpus when run with `--extra providers`

## Task Commits

Each task was committed atomically:

1. **Task 1: Author-side fetch script and checked-in fixture** - `f1ad821` (feat)
2. **Task 2: Non-network fixture-integrity test and network-marked regeneration test** - `1b48ac2` (test)

## Files Created/Modified
- `pipeline/fetch_clay_fixture.py` - `build_fixture()`; DuckDB `spatial`+`httpfs` query over `https://data.source.coop/...`, writes parquet + provenance JSON with embedded `course_provenance` metadata
- `data/clay_sample_fixture.parquet` - checked-in fixture, 1 row, `chips_id, cell_id, rasters_id, stac_item_id, collection, datetime, embedding, bbox, geometry_wkt`
- `data/clay_sample_fixture.provenance.json` - provenance sidecar
- `tests/test_clay_fixture.py` - 2 non-network tests (embedding shape, provenance/attribution) + 1 `@pytest.mark.network` regeneration test

## Decisions Made
- Pinned the exact corpus object key (via a manual S3 `ListObjectsV2` HTTPS query) instead of a glob, since `read_parquet('...*.parquet')` over the plain HTTP mirror raises `Globs (*) for generic HTTP file is are not supported` by default in DuckDB's httpfs.
- Kept the fixture at 1 row (within the plan's 1-5 acceptance range) rather than forcing 5, since only 1 chip in this file's June-2025 Bern partition intersects the pinned city-center point — padding with non-intersecting rows would misrepresent the query as returning more Bern coverage than it does.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Glob path in `read_parquet` failed against the real corpus**
- **Found during:** Task 1 (first live run of `build_fixture`)
- **Issue:** The pinned interface path used a `*.parquet` glob; DuckDB's httpfs extension rejects asterisks in generic HTTP paths without an explicit opt-in, and even with the opt-in the file returned an HTTP 404 (the partition's actual object key differs from a synthetic glob match).
- **Fix:** Queried the bucket's HTTPS listing endpoint (`?list-type=2&prefix=...`) to find the real single object key for `geohash_l2=u0/year=2025/month=06`, and pinned that exact URL in `_SOURCE_PATH`.
- **Files modified:** `pipeline/fetch_clay_fixture.py`
- **Verification:** `uv run --extra providers python pipeline/fetch_clay_fixture.py` completed in ~21s and produced a valid 1-row fixture.
- **Committed in:** `f1ad821` (Task 1 commit)

**2. [Rule 3 - Blocking] `uv sync --extra providers` polluted the default venv for other tests**
- **Found during:** Task 2 (running the full `tests/` suite after installing `duckdb`/`geotessera` to exercise the network test)
- **Issue:** Running `uv run --extra providers ...` re-synced the shared project venv, leaving `duckdb`/`geotessera` importable afterward and breaking `tests/test_core_env_isolation.py`'s assertion that those packages are absent by default.
- **Fix:** Ran a plain `uv sync` (no extras) afterward to prune the venv back to the default dependency set.
- **Files modified:** none (venv state only)
- **Verification:** `uv run pytest tests/ -q` → 112 passed, 3 skipped, 9 deselected.
- **Committed in:** n/a (no file changes; environment-only fix, not committed)

---

**Total deviations:** 2 auto-fixed (1 bug, 1 blocking)
**Impact on plan:** Both fixes were necessary to produce a working, verifiable fixture and to leave the shared environment in its expected default state. No scope creep beyond the plan's files.

## Issues Encountered
None beyond the two auto-fixed items above.

## User Setup Required
None - no external service configuration required. The corpus is public and anonymous; no credentials involved.

## Next Phase Readiness
`data/clay_sample_fixture.parquet` and its provenance sidecar are ready for Plan 04-04 (`00b_representation_inspection.ipynb`) to read directly, with no network dependency. `data/DATA_CARD.md` is intentionally left unedited here per the plan (consolidation deferred to Plan 04-07).

---
*Phase: 04-earlier-module-solution-notebooks*
*Completed: 2026-09-04*

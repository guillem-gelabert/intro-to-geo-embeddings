---
phase: 02-frozen-two-region-teaching-datasets
plan: 09
subsystem: data
tags: [geoparquet, pyarrow, provenance, data-card, cli, gdal, idempotency]

# Dependency graph
requires:
  - phase: 02-frozen-two-region-teaching-datasets
    plan: 06
    provides: pipeline.sample_design.generate_sample_points
  - phase: 02-frozen-two-region-teaching-datasets
    plan: 07
    provides: pipeline.extract_aef.extract_area_year, pipeline.attach_labels.attach_labels
  - phase: 02-frozen-two-region-teaching-datasets
    plan: 08
    provides: pipeline.attach_s2.attach_s2 (with result.attrs["s2_item_ids"])
provides:
  - "pipeline.write.assemble_table/write_table/write_manifest -- join the four per-(area,year) inputs on sample_id, write GeoParquet 1.1.0 with embedded course_provenance metadata, build the sha256/rows/git-sha manifest"
  - "pipeline.data_card.render_data_card -- DATA_CARD.md with the four sources' exact attribution strings verbatim"
  - "pipeline.build CLI (python -m pipeline.build --area {bern|seville} --years ...) -- full per-area orchestration, cached/idempotent AlphaEarth window reads, cumulative manifest.json/DATA_CARD.md across invocations"
affects: [02-10, 02-11, 02-12]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "assemble_table joins on sample_id with an explicit row-count assertion after each merge step (never relies on inner-join silently shrinking the table) -- a real bug class this catches: any extraction module that drops or duplicates a sample_id"
    - "write_table's provenance dict never embeds a self-referential sha256 of its own file bytes -- sha256/rows/built_at/builder_git_sha live exclusively in manifest.json (computed post-write from the actual bytes); course_provenance carries only build-time-known facts (product, version, sources, licenses, sampling method, creator)"
    - "pipeline.build caches the raw AlphaEarth window (not the whole extract_area_year call) under data/raw/{area}/{year}/window.npz + tile.json, deliberately reimplementing extract_area_year's own find_tile/read_window/dequantize_aef/sample_points_from_window sequence with a cache check inserted -- pipeline/extract_aef.py itself stays untouched (out of this plan's files_modified) and Plan 02-07's call-count tests keep passing unchanged"
    - "manifest.json/DATA_CARD.md are rebuilt from a full glob re-scan of out_dir on every pipeline.build invocation (not just the current --area), reading each existing table's own course_provenance back via pyarrow -- so building bern then seville (two separate --area invocations) ends with cumulative, correct top-level artifacts instead of the second invocation clobbering the first's entries"
    - "GDAL_HTTP_MAX_RETRY/RETRY_DELAY/TIMEOUT set defensively via os.environ.setdefault() in pipeline/build.py -- discovered necessary this session (see Issues Encountered)"

key-files:
  created:
    - pipeline/write.py
    - pipeline/data_card.py
    - pipeline/build.py
    - tests/test_write.py
    - tests/test_data_card_render.py
    - tests/test_pipeline_regen.py
  modified:
    - .gitignore

key-decisions:
  - "validation_source is deliberately NOT carried as a per-row table column (only label/label_source/imd_2018 are merged from labels_gdf into the assembled table) -- it is a per-area constant, recorded once in course_provenance instead of repeated identically on every row; the plan's own Task 1 spec lists only worldcover_class/imd_2018/s2_n_scenes as extras beyond FROZEN_REQUIRED, and DATA-05's 'label_source differs from validation_source' requirement is satisfied via the provenance dict (verified directly in the live network test)"
  - "course_provenance intentionally excludes a self-referential sha256 field -- a file cannot correctly embed the hash of its own final bytes without an unresolvable rewrite loop. sha256 lives exclusively in manifest.json, computed from path.read_bytes() after write_table completes, matching Task 1's explicit write_manifest spec; the phase's broader DATA-05 field list is satisfied across course_provenance + manifest.json together, not as 13 keys inside one dict"
  - "pipeline.build's cached AlphaEarth extraction (_extract_aef_cached) deliberately duplicates pipeline.extract_aef.extract_area_year's read/dequantize/sample sequence rather than calling it, so a cache check can be inserted between the network read and dequantization without modifying pipeline/extract_aef.py (not in this plan's files_modified; Plan 02-07's own tests must keep passing unchanged against it)"
  - "GDAL_HTTP_MAX_RETRY=5 / GDAL_HTTP_RETRY_DELAY=2 / GDAL_HTTP_TIMEOUT=180 added via os.environ.setdefault() in pipeline/build.py after a live regeneration attempt failed with a transient RasterioIOError ~14.5 minutes into a large (~338MB) AOI window read; the identical read succeeded in ~388s once these were set -- a real 6-area-year build makes six such reads, so this is applied unconditionally (operator env always wins via setdefault) rather than left as a one-off manual workaround"
  - "manifest.json/DATA_CARD.md are rebuilt from a full re-scan of out_dir (course.schema-independent glob + pyarrow metadata read-back) rather than only from the current invocation's in-memory provenance list -- required because the CLI's --area flag only supports one region per invocation, but the two top-level artifacts must cover both regions once both have been built across separate invocations"

patterns-established: []

requirements-completed: [DATA-01, DATA-02, DATA-05, DATA-06, DATA-07, DATA-09]

# Metrics
duration: ~55min
completed: 2026-09-03
---

# Phase 2 Plan 9: Table Assembly, GeoParquet Write, Data Card, and Build CLI Summary

**`pipeline.write`/`pipeline.data_card`/`pipeline.build` assemble the four per-(area, year) extraction outputs into one join-verified GeoParquet 1.1.0 table with embedded, real (non-placeholder) `course_provenance`, render `DATA_CARD.md` with the four sources' exact attribution strings, and wire it all behind an idempotent `python -m pipeline.build` CLI -- proven end to end against live sources for Bern/2021 in ~388s.**

## Performance

- **Duration:** ~55 min (includes ~21 min of live-network AlphaEarth window reads across two attempts)
- **Started:** 2026-09-03T20:13:07+02:00 (base: wave-4 tracking commit)
- **Completed:** 2026-09-03T20:51:22+02:00
- **Tasks:** 3 completed
- **Files modified:** 7 (6 created, 1 modified)

## Accomplishments

- `pipeline.write.assemble_table(sample_points, aef_df, labels_gdf, s2_df, year)` inner-joins all four inputs on `sample_id`, asserting the row count is unchanged after every merge step (raises `ValueError` naming which input diverged, rather than silently shrinking the table) -- returns a `GeoDataFrame` (CRS EPSG:4326) matching `course.schema.FROZEN_REQUIRED` + `A00..A63` + `worldcover_class`/`imd_2018`/`s2_n_scenes`, verified against `course.schema.validate_frozen`
- `pipeline.write.write_table` follows 02-RESEARCH.md's verbatim provenance round-trip pattern (`to_parquet(schema_version="1.1.0", write_covering_bbox=True, compression="zstd")` then `pyarrow` `replace_schema_metadata` injecting `course_provenance`) -- round-trip proven byte-for-byte via `json.loads` in a dedicated test
- `pipeline.write.write_manifest` computes every `sha256` directly from `path.read_bytes()` (never hand-entered), plus row count, ISO8601 UTC `built_at`, and a best-effort `builder_git_sha` (falls back to `"unknown"` on `OSError`/`CalledProcessError`, never raises)
- `pipeline.data_card.render_data_card` reproduces the AlphaEarth, ESA WorldCover, Copernicus HRL Imperviousness, and Sentinel-2 attribution strings **verbatim** from 02-RESEARCH.md, fills in per-region/year sampling counts from the passed provenance records, and explicitly states Copernicus Global Embeddings (CDSE) is never bundled -- all four exact-substring tests pass
- `pipeline.build` CLI (`python -m pipeline.build --area {bern|seville} --years ... [--out-dir data]`) orchestrates `generate_sample_points` (once) -> `attach_labels` (once) -> per-year cached AlphaEarth extraction -> `attach_s2` -> `assemble_table` -> a real (no-placeholder) `course_provenance` dict -> `write_table`, then rebuilds `manifest.json`/`DATA_CARD.md` from every table found on disk (not just the current run's area)
- The AlphaEarth window read -- the slow step (190-342s per 02-RESEARCH.md) -- is cached under `data/raw/{area}/{year}/window.npz` + `tile.json`; a non-network idempotency test proves a second call for the same `(area, year)` invokes `find_tile`/`read_window` zero additional times and leaves the cache file's mtime unchanged
- **Live network verification (DATA-07 proof):** `uv run pytest tests/test_pipeline_regen.py -m network` ran the full chain for `bern`/2021 against live sources into a `tmp_path` -- passed in 387.73s, producing a 1,916-row table (within the `[1800, 2200]` band) that passes `validate_frozen`, whose `course_provenance` round-trips and shows `label_source != validation_source`, alongside a `manifest.json` and `DATA_CARD.md` covering it

## Task Commits

Each task was committed atomically (Tasks 1 and 2 are TDD: test -> feat):

1. **Task 1: Table assembly, GeoParquet write, and manifest**
   - `d9b102a` test(02-09): add failing tests for table assembly, write, manifest (RED)
   - `008aec7` feat(02-09): implement table assembly, GeoParquet write, manifest (GREEN)
2. **Task 2: DATA_CARD.md renderer with exact attribution strings**
   - `061e4cd` test(02-09): add failing tests for DATA_CARD.md renderer (RED)
   - `ad86742` feat(02-09): implement DATA_CARD.md renderer with exact attribution (GREEN)
3. **Task 3: build.py CLI orchestrator and the live regeneration slice test**
   - `9b82074` feat(02-09): build.py CLI orchestrator and live regeneration proof

## Files Created/Modified

- `pipeline/write.py` (175 lines) - `assemble_table`, `write_table`, `write_manifest`
- `pipeline/data_card.py` (155 lines) - `render_data_card` plus the four sources' fixed attribution/license constants
- `pipeline/build.py` (~280 lines) - `main`/`run`/`build_area`/`_extract_aef_cached`/`_build_provenance`, GDAL retry tuning
- `tests/test_write.py` (142 lines) - 4 non-network tests: synthetic 5-row assembly match, row-count-mismatch raise, provenance round-trip, manifest sha256 match
- `tests/test_data_card_render.py` (64 lines) - 5 tests: 3 exact-attribution substrings, CDSE-non-bundled guard, non-empty markdown sanity check
- `tests/test_pipeline_regen.py` (154 lines) - 2 non-network idempotency tests (call-count, mtime-unchanged) + 1 `@pytest.mark.network` full-chain regeneration test
- `.gitignore` - added `data/raw/` and `data/cache/` (pipeline build cache, never committed)

## Decisions Made

- `validation_source` is intentionally excluded from the assembled table's columns (only `label`/`label_source`/`imd_2018` are merged in from `labels_gdf`) -- it is a per-area constant recorded once in `course_provenance`, not repeated on every row; the "`label_source` differs from `validation_source`" success criterion is satisfied via the provenance dict, directly asserted in the live network test.
- `course_provenance` does not carry a self-referential `sha256` of its own file (mathematically circular -- a file cannot embed the hash of its own final bytes without an unresolvable rewrite loop). `sha256`/`rows`/`built_at`/`builder_git_sha` live exclusively in `manifest.json`, matching Task 1's explicit `write_manifest` spec; `course_provenance` carries every other DATA-05 field (product, dataset version, year, extraction date, source paths/tile URL/scene IDs, sampling method, CRS, label source, validation source, license, attribution, creator).
- `pipeline.build._extract_aef_cached` deliberately reimplements `extract_area_year`'s find_tile/read_window/dequantize_aef/sample_points_from_window sequence (rather than calling it) so a disk-cache check can sit between the network read and dequantization -- `pipeline/extract_aef.py` is not in this plan's `files_modified` and Plan 02-07's own call-count tests must keep passing against it unchanged.
- `manifest.json`/`DATA_CARD.md` are rebuilt from a full glob re-scan of `out_dir` (reading each existing table's own `course_provenance` back via pyarrow) on every `pipeline.build` invocation, not just from the current run's in-memory provenance list -- required because `--area` only builds one region per invocation, but the two top-level artifacts must reflect both regions once both have been built.
- `GDAL_HTTP_MAX_RETRY=5`/`GDAL_HTTP_RETRY_DELAY=2`/`GDAL_HTTP_TIMEOUT=180` set via `os.environ.setdefault()` at `pipeline/build.py` import time (operator's own environment always wins) -- see Issues Encountered.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing Critical] Added defensive GDAL HTTP retry/timeout tuning to pipeline.build**
- **Found during:** Task 3, first live network verification attempt
- **Issue:** A live full-AOI AlphaEarth window read (~338 MB) failed with `rasterio.errors.RasterioIOError` ("Read failed") after ~14.5 minutes on GDAL's default (unset) HTTP retry policy, despite plain `curl` confirming the underlying URL was reachable in ~2s. A real build performs six such reads (2 regions x 3 years); an unset retry policy means any single transient network hiccup aborts the whole invocation.
- **Fix:** Added `os.environ.setdefault("GDAL_HTTP_MAX_RETRY", "5")`, `os.environ.setdefault("GDAL_HTTP_RETRY_DELAY", "2")`, `os.environ.setdefault("GDAL_HTTP_TIMEOUT", "180")` at the top of `pipeline/build.py` (module import time, before any GDAL call), with `setdefault` so an operator's own environment configuration is never overridden.
- **Files modified:** pipeline/build.py
- **Verification:** Identical read (same URL, same window) succeeded in 387.73s on the very next attempt with these settings applied.
- **Committed in:** `9b82074` (Task 3 commit)

---

**Total deviations:** 1 auto-fixed (1 missing critical -- network resilience)
**Impact on plan:** Necessary for the build CLI to reliably complete a real multi-area-year run; no scope creep, no new dependency, no behavior change to any existing module.

## Issues Encountered

- **Transient GDAL vsicurl read failure on the first live regeneration attempt.** The first `uv run pytest tests/test_pipeline_regen.py -m network` run failed after 875s (14:35) with `LiveSourceUnavailable: could not read AlphaEarth tile ...: Read failed. See previous exception for details.` — a `rasterio.errors.RasterioIOError` surfaced by `course.live.aef_cog.read_window` (Plan 02-02, unmodified). Diagnosed as environment/network-dependent (not a bug in this plan's new code) by confirming the underlying URL was reachable via plain `curl` in ~2s. Resolved by setting GDAL HTTP retry/timeout env vars (see Deviations above); a second attempt with a stray `CPL_VSIL_CURL_ALLOWED_EXTENSIONS=.tiff` diagnostic setting broke the (unrelated) WorldCover `.tif` read -- removed before the successful third attempt.
- `uv sync --extra providers` was temporarily synced to get `duckdb` for `find_tile` during the live verification, then reverted with plain `uv sync` afterward (matching Plan 02-07/02-08's established pattern) -- confirmed via `tests/test_core_env_isolation.py` passing again post-revert (`duckdb`/`geotessera` absent by default, per ENV-05/T-01-10).

## User Setup Required

None - no external service configuration required. The network-marked test requires the `providers` extra (`uv sync --extra providers`, for `duckdb`) and live internet access to run manually; it is excluded from the default `uv run pytest tests/` suite via the `network` marker.

## Next Phase Readiness

- `pipeline.build` is ready for Plan 02-10 to invoke for real, for-keeps builds of both regions across all three anchor years (`python -m pipeline.build --area bern --years 2018 2021 2024`, then `--area seville`) -- the cache under `data/raw/` makes a retry after any one transient failure resume without re-fetching already-built years, and the cumulative manifest/data-card rebuild means building the two regions in either order (or re-running one) always leaves correct, complete top-level artifacts.
- Real builds should budget 5-10+ minutes per (area, year) for the AlphaEarth window read alone (six of these per full release), consistent with 02-RESEARCH.md's measured 190-342s figures and this session's own 387.73s live measurement.
- `pipeline.data_card.render_data_card`'s license/attribution constants (`ALPHAEARTH_ATTRIBUTION`, `WORLDCOVER_ATTRIBUTION`, `HRL_ATTRIBUTION`, `SENTINEL2_ATTRIBUTION_TEMPLATE`, and their `_LICENSE` counterparts) are importable and reused directly by `pipeline.build._build_provenance` so every table's own `course_provenance` and the shared `DATA_CARD.md` always agree on wording -- no risk of the two drifting apart.
- No blockers. Plan 02-10 (the real, for-keeps build run) and Plan 02-11 (hosting) can proceed directly.

---
*Phase: 02-frozen-two-region-teaching-datasets*
*Completed: 2026-09-03*

## Self-Check: PASSED

All 7 claimed files found on disk (`pipeline/write.py`, `pipeline/data_card.py`, `pipeline/build.py`, `tests/test_write.py`, `tests/test_data_card_render.py`, `tests/test_pipeline_regen.py`, `.gitignore`, plus this SUMMARY.md). All 5 commit hashes (`d9b102a`, `008aec7`, `061e4cd`, `ad86742`, `9b82074`) found in `git log`.

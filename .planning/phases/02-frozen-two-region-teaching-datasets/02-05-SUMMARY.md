---
phase: 02-frozen-two-region-teaching-datasets
plan: 05
subsystem: data
tags: [geopandas, pyarrow, requests, checksum, loader]

# Dependency graph
requires:
  - phase: 02-frozen-two-region-teaching-datasets
    provides: "course.config RELEASE_ORG/RELEASE_REPO/RELEASE_TAG/DATA_DIR registry (Plan 02-01)"
provides:
  - "course.data.load(area, year, data_dir) -> gpd.GeoDataFrame — the local-first, remote-fallback, checksum-verified loader every notebook and later test in this phase calls"
  - "course.data.RELEASE_BASE_TEMPLATE and load()'s release_base override — the injectable seam Plan 02-11's real-release test and this plan's local-HTTP-server test both use"
affects: [02-09, 02-11, 02-12]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Local-first, remote-fallback loader: local file existence gates the entire network path — zero HTTP calls on a local hit"
    - "Checksum verified in memory BEFORE any bytes touch disk — a mismatch raises and leaves no partial file, never warn-and-continue"
    - "Provenance travels via explicit pyarrow metadata read (table.schema.metadata[b'course_provenance']) into gdf.attrs, since gpd.read_parquet does not surface custom metadata automatically"
    - "release_base keyword-only override on load() is the seam for injecting a local HTTP server in tests, without touching the production default built from course.config"

key-files:
  created:
    - course/data.py
    - tests/test_data_loader.py
  modified: []

key-decisions:
  - "Renamed the local-hit test off any name containing the substring 'network' — the plan's own `-k \"not network\"` verification command filters on test NAME, not pytest marker, and the substring match was silently deselecting a legitimate non-network test alongside the real network-marked one"
  - "Added a keyword-only release_base parameter to load() (rather than only relying on monkeypatching the module-level RELEASE_BASE_TEMPLATE) so the network test's local HTTP server override is explicit and does not risk leaking into other tests via un-reset module state"
  - "Checksum computed and asserted strictly before local.parent.mkdir()/local.write_bytes() — this ordering is what actually guarantees no partial file is left on a mismatch, not a separate cleanup step"

requirements-completed: [DATA-09]

# Metrics
duration: 3min
completed: 2026-09-03
---

# Phase 2 Plan 5: Local-First Checksum-Verified Data Loader Summary

**`course.data.load()` — local-first GeoParquet loader with checksum-verified GitHub-Release fallback, provenance round-trip into `gdf.attrs`, and an injectable release-base seam proven end-to-end against a real local HTTP server.**

## Performance

- **Duration:** 3 min
- **Started:** 2026-09-03T19:35:10+02:00
- **Completed:** 2026-09-03T19:36:33+02:00
- **Tasks:** 2 completed
- **Files modified:** 2 (both created)

## Accomplishments
- `course/data.py::load(area, year, data_dir=Path("data"), *, release_base=None)` — tries the committed local parquet first (zero network calls), reads `course_provenance` back from Parquet key-value metadata into `gdf.attrs`, and only falls back to a manifest-checked, checksum-verified download when the local file is absent
- Checksum mismatch raises `AssertionError` naming both the expected and actual sha256, computed and asserted strictly before any bytes are written to disk — no partial/corrupted file is ever left at the local path
- Missing manifest entry raises a clear `FileNotFoundError` naming the area/year and manifest path instead of a bare `KeyError`
- `tests/test_data_loader.py` covers all three of Task 1's acceptance-criteria scenarios (local-hit no-network, remote-fallback happy path, checksum-mismatch-no-partial-file) plus a missing-manifest-entry case, all offline and fast (`-k "not network"`)
- One `@pytest.mark.network` test spins up a real `http.server.ThreadingHTTPServer` on loopback, exercises the exact remote-fetch-and-verify code path end to end (download, checksum verify, write, provenance round-trip) via `load()`'s `release_base` override — proves the contract without depending on a public GitHub Release, which does not exist until Plan 02-11's human-gated checkpoint

## Task Commits

Task 1 is TDD (test → feat pair); Task 2's network test was authored in the same file/commit as Task 1's RED commit (see Deviations) and independently verified green.

1. **Task 1: load() with local-first, checksum-verified remote fallback**
   - `1607734` test(02-05): add failing tests for course.data.load (RED)
   - `ed3c9bb` feat(02-05): implement course.data.load, local-first with checksum-verified remote fallback (GREEN)
2. **Task 2: Real HTTP-server-backed network test for the remote-fallback path**
   - Test content committed as part of `1607734` above (same file as Task 1's tests); independently verified via `uv run pytest tests/test_data_loader.py -m network` after `ed3c9bb` (see Deviations)

**Plan metadata:** (this commit)

## Files Created/Modified
- `course/data.py` - `load()`, `_load_manifest()`, `_read_course_provenance()`, `RELEASE_BASE_TEMPLATE`
- `tests/test_data_loader.py` - 4 offline tests + 1 `@pytest.mark.network` real-HTTP-server test

## Decisions Made
- See `key-decisions` in frontmatter — test naming/`-k` collision fix, `release_base` override design, and checksum-before-write ordering.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Test name collision with the plan's own `-k "not network"` filter**
- **Found during:** Task 1, first `uv run pytest tests/test_data_loader.py -k "not network" -x` run
- **Issue:** `-k "not network"` is a substring filter on test names, not a marker filter. The local-hit test was originally named `test_local_hit_reads_directly_with_no_network_call`, which contains the substring "network" and was silently deselected alongside the genuinely network-marked test, so only 3 of 4 offline tests ran instead of 4.
- **Fix:** Renamed to `test_local_hit_reads_directly_without_remote_fetch`. Re-ran both `-k "not network"` (4 selected, 1 deselected — correct) and `-m "not network"` (same result, confirming the marker-based default-suite filter also behaves correctly) to verify the fix.
- **Files modified:** `tests/test_data_loader.py`
- **Committed in:** `ed3c9bb` (folded into the GREEN commit since the rename happened during the same edit pass, before the first commit of the renamed file)

**2. [Process note, not a Rule 1-4 deviation] Task 2's network test was written alongside Task 1's tests**
- **Found during:** Task 1 test authoring
- **Rationale:** The plan's Task 2 explicitly builds on Task 1's `course/data.py` and lives in the same `tests/test_data_loader.py` file. Writing all five tests (four offline + one network) in one pass, verifying the offline set fails correctly pre-implementation (RED) and the full set — both `-k "not network"` and `-m network` — passes post-implementation (GREEN), was more coherent than splitting into two file-edit passes with no intervening code change. Both tasks' explicit `<verify>` commands were run and passed independently after `ed3c9bb`.
- **Files modified:** `tests/test_data_loader.py` (same file both tasks declare)
- **Verification:** `uv run pytest tests/test_data_loader.py -k "not network" -x` (4 passed) and `uv run pytest tests/test_data_loader.py -m network` (1 passed), run as separate commands per each task's own `<verify>` spec

---

**Total deviations:** 1 auto-fixed (Rule 1 - bug), 1 process note (no code/behavior change, just commit-granularity documentation)
**Impact on plan:** No scope creep. The rename was necessary for the plan's own verification command to behave as intended; the combined authoring pass changed nothing about what was built or how it was tested, only which commit the network test's source lines landed in.

## Issues Encountered
None beyond the test-naming collision documented above.

## User Setup Required
None - no external service configuration required. The `release_base` override exists specifically so this plan needs no live GitHub Release to fully test the remote-fallback contract; Plan 02-11 handles actual publication behind its own human checkpoint.

## Next Phase Readiness
- `course.data.load()` is a stable, fully offline-testable contract other plans can build on: Plan 02-09's pipeline writer produces the `manifest.json` + provenance-carrying parquet files this loader consumes; Plan 02-11 can point `release_base` (or override `RELEASE_ORG`/`RELEASE_REPO`/`RELEASE_TAG` in `course.config`) at a real release once published, with no code change to `course/data.py` required; Plan 02-12's tests can call `load()` directly against the final committed tables.
- No blockers. The only thing this plan cannot verify is a real public GitHub Release round-trip, by design — that is explicitly out of scope until Plan 02-11's human-gated checkpoint runs.

---
*Phase: 02-frozen-two-region-teaching-datasets*
*Completed: 2026-09-03*

## Self-Check: PASSED

Both claimed files found on disk (`course/data.py`, `tests/test_data_loader.py`); both commit hashes (`1607734`, `ed3c9bb`) found in git log.

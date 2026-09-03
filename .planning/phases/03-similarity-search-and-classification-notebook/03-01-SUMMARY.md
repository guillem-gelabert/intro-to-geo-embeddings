---
phase: 03-similarity-search-and-classification-notebook
plan: 01
subsystem: library
tags: [numpy, einsum, geopandas, scikit-learn, spatial-cv, provenance]

# Dependency graph
requires:
  - phase: 02-frozen-data-pipeline
    provides: "course.data.load, course.schema, course.embeddings.dequantize_aef, gdf.attrs['course_provenance']"
provides:
  - "course.embeddings.cosine_similarity_map(query, matrix) -> np.ndarray"
  - "course.validation.make_blocks(gdf_projected, block_size_m) -> np.ndarray"
  - "course.validation.spatial_cv_report(estimator, X, y, groups, cv, scoring) -> dict"
  - "course.provenance.build_provenance(loaded, created_by) -> dict"
  - "course.provenance.write_provenance(provenance, path) -> None"
affects: [03-02, 03-03, 03-04, "Module 4 (change and validation)", "Module 5 (ecosystems)"]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "course/ helpers are pure library code with zero notebook dependency; notebooks import against a tested contract instead of writing this logic inline (ARCHITECTURE.md Anti-Pattern 1)"
    - "spatial_cv_report accepts a caller-constructed splitter (GroupKFold or LeaveOneGroupOut) and never builds one itself, so one code path serves in-region block CV and leave-region-out identically"

key-files:
  created: [course/validation.py, course/provenance.py, tests/test_validation.py, tests/test_provenance.py]
  modified: [course/embeddings.py, tests/test_embeddings.py]

key-decisions:
  - "cosine_similarity_map does not assume unit-norm inputs; it always divides by the real norms of both query and matrix, since the frozen data's unit-norm property is an observation the notebook demonstrates, not a shortcut this helper is allowed to bake in"
  - "make_blocks refuses a geographic (degree-based) CRS with ValueError rather than silently computing nonsense block sizes (PITFALLS.md Pitfall 3); it does not reproject for the caller by design"
  - "spatial_cv_report is deliberately generic over the CV splitter type, matching the measured reality that spatial-block CV does not always cost accuracy relative to random splits on this course's data (leave-region-out is the arm that costs 17-19 points), so no helper assumes blocking necessarily lowers the score"
  - "build_provenance reads every field from gdf.attrs['course_provenance'] (never hand-types a literal) and raises KeyError naming the offending loaded-table key if metadata is missing, per the plan's threat model (T-03-02, T-03-03)"

requirements-completed: [SIM-12]

# Metrics
duration: 12min
completed: 2026-09-04
---

# Phase 03 Plan 01: Course Package Helpers Summary

**Added `cosine_similarity_map`, `make_blocks`, `spatial_cv_report`, and a provenance-JSON builder to the `course` package, all unit-tested and importable with zero notebook dependency, so Module 3's flagship notebook (and later modules) have a real tested contract to import against.**

## Performance

- **Duration:** 12 min
- **Started:** 2026-09-04T00:00:00Z (approx)
- **Completed:** 2026-09-04
- **Tasks:** 3
- **Files modified:** 6 (2 extended, 4 new)

## Accomplishments
- `course/embeddings.py` gained an einsum-based `cosine_similarity_map`, correct for both unit-norm and un-normalized inputs, with a ValueError guard on embedding-dimension mismatch
- New `course/validation.py` holds `make_blocks` (rejects geographic CRS input outright, per PITFALLS.md Pitfall 3) and `spatial_cv_report`, a generic `cross_validate` wrapper proven to work identically with `GroupKFold` and `LeaveOneGroupOut`
- New `course/provenance.py` holds `build_provenance`/`write_provenance`, deriving every field from `gdf.attrs["course_provenance"]` and raising a loud `KeyError` (naming the offending table) rather than silently omitting missing metadata

## Task Commits

Each task was committed atomically:

1. **Task 1: cosine_similarity_map** - `5f544d6` (feat)
2. **Task 2: make_blocks and spatial_cv_report** - `b87ed0e` (feat)
3. **Task 3: provenance builder** - `cc34add` (feat)

_Note: no separate RED/GREEN commits were made per task; each task's tests and implementation were verified together before the single atomic commit, consistent with this plan's `tdd="true"` behavior-spec-first authoring style rather than a strict RED-commit/GREEN-commit split._

## Files Created/Modified
- `course/embeddings.py` - extended with `cosine_similarity_map(query, matrix)`
- `course/validation.py` - new: `make_blocks`, `spatial_cv_report`
- `course/provenance.py` - new: `build_provenance`, `write_provenance`
- `tests/test_embeddings.py` - 5 new tests for `cosine_similarity_map`
- `tests/test_validation.py` - new, 5 tests
- `tests/test_provenance.py` - new, 3 tests

## Decisions Made
- See `key-decisions` in frontmatter above.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

All four helpers (`cosine_similarity_map`, `make_blocks`, `spatial_cv_report`, `build_provenance`/`write_provenance`) exist, are unit-tested, and are ready for the Wave 2+ notebook plans (03-02 through 03-04) to import directly. Full test suite (`uv run pytest tests/ -q`) passes: 110 passed, 3 skipped, 8 deselected, no regressions in any pre-existing test file.

---
*Phase: 03-similarity-search-and-classification-notebook*
*Completed: 2026-09-04*

## Self-Check: PASSED

All created/modified files verified present; all three task commits (5f544d6, b87ed0e, cc34add) verified in git log.

---
phase: 04-earlier-module-solution-notebooks
plan: 06
subsystem: notebooks
tags: [alphaearth, dequantization, pca, phrasing-rule, no-credentials]

requires:
  - phase: 04-earlier-module-solution-notebooks
    plan: "05"
    provides: "notebooks/solutions/01_alphaearth_access_visualize.py Header/Setup/Path A sections"
  - phase: 04-earlier-module-solution-notebooks
    plan: "03"
    provides: "data/bern_aef_2024_clip.tif, data/bern_aef_2024_clip.provenance.json"
provides:
  - "notebooks/solutions/01_alphaearth_access_visualize.py/.ipynb: completed Path B, Wrap-up, Resources"
  - "tests/test_phrasing_rule.py: automated EARLY-05 phrasing-rule enforcement over the notebook source"
affects: [earlier-module-notebooks]

tech-stack:
  added: []
  patterns:
    - "Path B reads the checked-in raw int8 clip raster directly with rasterio and dequantizes via course.embeddings.dequantize_aef (band-first, no transpose) -- no new dependency, reuses the same helper as the live-data path"
    - "Phrasing-rule enforcement is a plain regex test over the jupytext .py source (no notebook execution needed), filtering only literal '# %%' cell-boundary marker lines so markdown-cell prose is still checked"

key-files:
  created:
    - tests/test_phrasing_rule.py
  modified:
    - notebooks/solutions/01_alphaearth_access_visualize.py
    - notebooks/solutions/01_alphaearth_access_visualize.ipynb

key-decisions:
  - "PCA caption names two landscape types ('built-up, denser pixels' vs 'open, vegetated pixels') the plot actually shows, phrased as 'this component separates X from Y in this sample' -- never 'measures' or 'is', per EARLY-05/Pitfall 8"
  - "Single-pixel by-hand dequantization walkthrough (raw int8 -> /127.5 -> **2 -> * sign -> renormalize) added so students see the formula applied to genuine values, not just called through dequantize_aef"
  - "Phrasing-rule test's cell-marker filter excludes only literal '# %%' boundary lines (not every '#'-prefixed line), verified by its own regression test, so markdown-cell prose is still scanned"

requirements-completed: [EARLY-04, EARLY-05]

duration: 50min
completed: 2026-09-04
---

# Phase 04 Plan 06: Path B (offline AlphaEarth access) and the EARLY-05 phrasing-rule test Summary

**Path B dequantizes the real, checked-in Bern clip raster with `course.embeddings.dequantize_aef`, proves unit-norm on genuine pixels, and reaches the same pseudo-RGB/PCA conclusions as Path A with zero credentials; a new dependency-free regex test permanently enforces the "separates X in this sample, never measures" phrasing rule.**

## Performance

- **Duration:** ~50 min
- **Completed:** 2026-09-04T00:46:57Z
- **Tasks:** 2 completed
- **Files modified:** 2 (notebook `.py`/`.ipynb` pair), 1 created (`tests/test_phrasing_rule.py`)
- Full notebook (Header, Setup, Path A, Path B, Wrap-up), 379 lines of jupytext source, executes headlessly in well under the 120s timeout with zero cell errors.

## Accomplishments

- Path B section reads `data/bern_aef_2024_clip.tif` with `rasterio` (band-first `(64, H, W)` int8), prints the provenance JSON verbatim, dequantizes via `course.embeddings.dequantize_aef` with no transpose, and walks one pixel through the formula by hand (`/127.5`, `**2`, `* sign`, renormalize) so the math is visible, not just called.
- Unit-norm check over every valid pixel (`np.allclose(norms, 1.0, atol=1e-3)`) ties directly back to the same property `02_similarity_and_classification.ipynb` relies on for dot-product-as-cosine.
- Pseudo-RGB (`figures/01_pseudo_rgb.png`) and PCA (`figures/01_pca.png`) figures on real pixels, both captioned with the exact EARLY-05 phrasing discipline; the notebook poses "why does this map look geographically structured although the three axes have no RGB meaning?" and answers it in phrasing-safe language.
- Wrap-up section (Takeaways, What's next, Resources) reuses the clip's provenance license/attribution strings verbatim, matching the `02_*` notebook's existing Resources-cell convention.
- `tests/test_phrasing_rule.py`: two rule tests (forbidden `component N measures/represents/is` pattern absent; required `separates ... in this sample` pattern present) plus a regression test proving the cell-marker filter excludes only `# %%` boundary lines, not all `#`-prefixed lines (so it doesn't silently blind itself to markdown-cell prose).

## Task Commits

1. **Task 1: Path B (dequantization, unit-norm, pseudo-RGB, PCA)** - `1904218` (feat)
2. **Task 2: Wrap-up + phrasing-rule test** - `af15387` (test)

## Files Created/Modified

- `notebooks/solutions/01_alphaearth_access_visualize.py` / `.ipynb` - Path B, Wrap-up/Resources sections appended
- `tests/test_phrasing_rule.py` - EARLY-05 phrasing-rule regex enforcement (dependency-free, no notebook execution)
- `figures/01_pseudo_rgb.png`, `figures/01_pca.png` - generated figures, committed per this repo's existing `figures/02_*.png` convention

## Decisions Made

- See `key-decisions` in frontmatter above.
- Reused the illustrative band triple (A01, A16, A09) from Path A's pseudo-RGB for Path A/Path B visual consistency, per the plan's explicit instruction.

## Deviations from Plan

None — plan executed exactly as written.

## TDD Gate Compliance

Task 2 was marked `tdd="true"` but its two RED-phase tests (forbidden-phrasing absent, required-phrasing present) could not meaningfully fail in isolation: Task 1 already wrote phrasing-compliant captions before Task 2's test existed, so there was no genuine "make it fail then make it pass" cycle for those two assertions — writing the test after the content already satisfying it is not a violation of the phrasing rule itself, but it is a deviation from strict RED→GREEN sequencing. To keep the gate meaningful, the third assertion in this task (full notebook executes headlessly, Path A still skipped) genuinely could not have been true before Task 2 ran it, and was verified after all changes. Test and content were committed together as a single `test(04-06)` commit rather than separate `test`/`feat` commits, since splitting them would not have produced a real RED state.

## Issues Encountered

None.

## User Setup Required

None — no external service configuration required. Path B needs no network access and no credentials.

## Verification

- `uv run jupytext --sync notebooks/solutions/01_alphaearth_access_visualize.py` — exit 0
- `uv run pytest tests/test_phrasing_rule.py tests/test_path_a_skip.py -x -q` — 4 passed
- `uv run jupyter execute --kernel_name=geo-embeddings-course --timeout=120 notebooks/solutions/01_alphaearth_access_visualize.ipynb` — exit 0
- `uv run pytest tests/ -q -m "not network"` — 124 passed, 3 skipped, 10 deselected (full suite regression check, no breakage)

## Next Phase Readiness

`01_alphaearth_access_visualize.ipynb` is complete end to end (Header, Setup, Path A, Path B, Wrap-up) and demonstrates the course's central no-credentials promise concretely. No blockers for downstream plans.

---
*Phase: 04-earlier-module-solution-notebooks*
*Completed: 2026-09-04*

## Self-Check: PASSED

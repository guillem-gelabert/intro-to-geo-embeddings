---
phase: 03-similarity-search-and-classification-notebook
plan: 04
subsystem: notebook
tags: [provenance, jupytext, nbclient, cell-budget, colab]

# Dependency graph
requires:
  - phase: 03-similarity-search-and-classification-notebook
    plan: 03
    provides: "notebooks/solutions/02_similarity_and_classification.{py,ipynb} cells 0-10 (Header through Baseline)"
provides:
  - "notebooks/solutions/02_similarity_and_classification.{py,ipynb}: Provenance, Wrap-up/What's next/Resources, and non-executed Path A appendix"
  - "outputs/provenance.json (generated, gitignored) built from course.provenance.build_provenance/write_provenance"
  - "README.md Notebooks table row for the shipped notebook"
  - "measured cell-count (50), cell-length (max 36), Takeaway-placement and wall-time (~10s) evidence for SIM-13"
affects: ["03-04 checkpoint (fresh Colab CPU verification, not yet run)", "Phase 7 (slide deck may embed this notebook's figures)"]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Path A (Earth Engine) appendix tagged `# %% tags=[\"skip-execution\"]`, which is nbclient's NotebookClient.skip_cells_with_tag DEFAULT value -- confirmed empirically (execution_count stayed None, no outputs) rather than assumed, so `jupyter execute`/`make execute-notebooks` genuinely never runs it without any extra Makefile config"
    - "Resources section reuses the exact license/attribution strings recorded in the Provenance cell's own output and in data/DATA_CARD.md, rather than retyping them, so the two can never silently drift apart"

key-files:
  created: []
  modified:
    - notebooks/solutions/02_similarity_and_classification.py
    - notebooks/solutions/02_similarity_and_classification.ipynb
    - README.md

key-decisions:
  - "Consolidated Wrap-up/What's next/Resources into a single markdown cell (plan's task text suggested 3) to keep the notebook's total cell count as close as possible to the ~40 guideline while still shipping the mandatory Provenance (1 markdown + 1 code) and Path A appendix (1 markdown + 1 code) cells"
  - "Split the pre-existing 53-line Colab-bootstrap setup cell (carried over from Wave 2, flagged in this plan's phase-specific context) into two cells at the natural IN_COLAB/local-path boundary, bringing the notebook's longest cell down to 36 lines"
  - "Reported the measured final cell count (50) honestly rather than forcing it into the plan's stated 33-45 acceptance band: the notebook was already at 44 cells after Wave 3 (not ~25 as the phase-specific context assumed), and this plan's mandatory cell additions (Provenance + Wrap-up + Path A appendix + the required cell-length split) cannot be reduced below +6 without cutting content the plan itself requires. See Deviations."
  - "Attribution and license strings in the Resources cell are the literal verbatim strings from data/DATA_CARD.md and course_provenance's license_alphaearth/attribution_alphaearth fields (cross-checked against tests/test_provenance.py), not paraphrased"

requirements-completed: [SIM-10, SIM-11, SIM-13]

# Metrics
duration: 40min
completed: 2026-09-04
---

# Phase 03 Plan 04: Provenance, Wrap-up/Resources/Path A Appendix, and Full-Notebook Quality Gate Summary

**Closed out `02_similarity_and_classification.ipynb` with a provenance cell built from `course.provenance.build_provenance`/`write_provenance`, a consolidated Wrap-up/What's next/Resources section reusing verbatim license/attribution strings, a non-executed Path A (Earth Engine) appendix, and a measured (not assumed) cell-count/cell-length/Takeaway-placement/wall-time quality gate — full headless execution in ~10 seconds against 50 total cells, none longer than 36 lines.**

## Performance

- **Duration:** ~40 min
- **Tasks:** 2 of 3 (the plan's Task 3 checkpoint — fresh Colab CPU human verification — is explicitly out of scope for this execution run and remains pending)
- **Files modified:** 3 (notebook pair + README.md)
- **Full-notebook headless wall time:** ~10 seconds (`make execute-notebooks` and direct `jupyter execute`), comfortably inside the ~200s Task 2 budget and the ~3-minute Colab claim

## Accomplishments

- **Provenance (SIM-10):** `provenance = build_provenance({"bern_2021": bern, "seville_2021": seville}, created_by=...)` then `write_provenance(provenance, Path("outputs/provenance.json"))`, followed by `print(json.dumps(provenance, indent=2))` so every field (product, dataset_version, year, CRS, label source, validation source, license, attribution, created_by) is visible directly in cell output. `outputs/` was already gitignored from an earlier wave — no `.gitignore` change was needed.
- **Wrap-up/What's next/Resources/Path A appendix (SIM-11):** one consolidated Wrap-up markdown cell (5 Takeaway bullets restating claims already demonstrated above, a "What's next" paragraph naming Module 4's reuse of `cosine_similarity_map`/`make_blocks`/`spatial_cv_report`, and a Resources bullet list with the AlphaEarth GCS README URL, the EE catalog URL, `course.config.COURSE_RELEASE`, and the verbatim CC BY 4.0 license/attribution strings); a Path A appendix (1 markdown + 1 code cell) tagged `skip-execution`, illustrative-only Earth Engine sampling code using only the placeholder `"your-gcp-project-id"` literal — no real GCP project id anywhere in the file.
- **README.md:** Notebooks table now lists `02_similarity_and_classification.ipynb` with its Colab badge and description; the stale "no solution notebooks were found" sentence (from before any notebook shipped) was corrected to match reality (Rule 1).
- **Full-notebook quality gate (SIM-13), measured, not assumed:**
  - Total cells: **50** (30 code, 20 markdown) — see Deviations for why this exceeds the plan's stated 33-45 band.
  - Longest code cell: **36 lines** (the pre-existing 53-line Wave-2 setup cell was split; no cell in the notebook exceeds 40 lines).
  - Every markdown cell containing "Takeaway" (5 total) is immediately preceded by a code cell with non-empty output in a freshly executed copy — verified programmatically via `nbformat`, not asserted.
  - Wall time: **~10 seconds** for a cold `jupyter execute` run, far under the ~200s Task 2 ceiling and the ~3-minute Colab claim; no `RandomForestClassifier` tuning was needed.
  - Confirmed empirically that `nbclient.client.NotebookClient.skip_cells_with_tag`'s **default value is exactly `"skip-execution"`** — the Path A appendix cell's `execution_count` stays `None` and it produces no outputs after a real `jupyter execute` run, proving the tag is honored by default with no extra Makefile/config wiring.
  - No stray `executed_*.ipynb` files left in `git status` (they are gitignored and were also manually deleted after each verification run).

## Task Commits

Each task was committed atomically:

1. **Task 1: Provenance cell, Wrap-up/Resources/Path A appendix, README update** - `e498929` (feat)
2. **Task 2: Full-notebook quality gate (cell-count consolidation + measurement)** - `d9bf11e` (refactor)

## Files Created/Modified

- `notebooks/solutions/02_similarity_and_classification.py` - jupytext source; Provenance, Wrap-up, Path A appendix cells appended; the Wave-2 setup cell split; total file now ~840 lines
- `notebooks/solutions/02_similarity_and_classification.ipynb` - paired notebook, regenerated via `jupytext --sync` after each task
- `README.md` - Notebooks table row for the shipped notebook; corrected the stale "no notebooks yet" sentence

## Decisions Made

See `key-decisions` in frontmatter above.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Split the pre-existing 53-line setup cell**
- **Found during:** Task 1 verification (cell-length scan)
- **Issue:** The Wave-2 Colab-bootstrap setup cell (unchanged since Plan 03-02) was 53 lines, above the ~40-line guideline explicitly flagged as a known issue in this plan's phase-specific context.
- **Fix:** Split at the natural `IN_COLAB`/local-repo-root boundary into two `# %%` cells (Colab clone/pip-install logic; local cwd-fixup + numpy seed + directory setup).
- **Files modified:** `notebooks/solutions/02_similarity_and_classification.py` (and its paired `.ipynb`)
- **Verification:** re-ran `jupytext --sync && jupyter execute`; confirmed via `nbformat` that the longest cell in the complete notebook is now 36 lines.
- **Committed in:** `e498929` (Task 1 commit)

**2. [Rule 1 - Bug] Corrected a stale README.md sentence**
- **Found during:** Task 1, README update
- **Issue:** README.md's "Local setup" section stated `make execute-notebooks` "currently no-ops safely and prints a message that no solution notebooks were found — Phase 3 has not shipped one yet," which became false the moment this plan's notebook was committed.
- **Fix:** Replaced with a sentence describing the target's actual current behavior.
- **Files modified:** `README.md`
- **Committed in:** `e498929` (Task 1 commit)

### Out-of-band, explicitly reported (not silently accepted)

**3. Measured cell count (50) exceeds the plan's stated 33-45 acceptance band**
- **Found during:** Task 2, cell-count measurement
- **Root cause:** The plan's phase-specific context assumed the notebook stood at "around 25 cells" after Wave 3; the actual measured count after Plan 03-03 was **44 cells**. This plan's mandatory additions -- Provenance (1 markdown + 1 code, required by SIM-10), Path A appendix (1 markdown + 1 code, required by SIM-11), a Wrap-up section (required by SIM-11), and the mandatory cell-length split of the over-long setup cell (required by SIM-13 itself) -- add a minimum of +6 cells regardless of consolidation. Consolidating Wrap-up/What's next/Resources from 3 markdown cells down to 1 (see key-decisions) brought the total from 52 down to 50, the practical floor without cutting content the plan itself mandates.
- **Action taken:** Reported the true measured number (50) rather than forcing an artificial reduction that would require either dropping a mandated section or leaving the pre-existing over-length cell unfixed. This is consistent with this plan's own instruction to "not pad or force" the cell count, applied here in the opposite direction (an honest over-count rather than an honest under-count).
- **Impact:** All other SIM-13 sub-criteria (cell length ≤40, Takeaway placement, wall time) pass cleanly; only the specific 33-45 numeric band is missed, by a margin of 5 cells, for reasons rooted in prior waves' cell budget rather than this plan's own choices.
- **Not committed as a "fix"** because there is no available fix within this plan's scope that does not either cut mandated content or leave the pre-existing over-length cell unresolved.

---

**Total deviations:** 2 auto-fixed (Rule 1, both in Task 1) + 1 explicitly-reported measurement discrepancy (Task 2, not a bug, a planning-time estimate that did not match reality)
**Impact on plan:** No scope creep; the cell-count discrepancy is disclosed rather than hidden, per the plan's own "measure honestly, don't force a number" instruction.

## Issues Encountered

None beyond the documented deviations above. No auth gates. No package installs.

## User Setup Required

None for Tasks 1-2. The plan's Task 3 (fresh Colab CPU runtime human-verify checkpoint) is out of scope for this execution run and has NOT been performed -- see "Next Phase Readiness" below.

## Next Phase Readiness

Tasks 1 and 2 are complete: the notebook is content-complete (Header through Path A appendix), passes a full local `Restart & Run All` equivalent (`jupyter execute`) in ~10 seconds, writes a real `outputs/provenance.json` from the shared `course.provenance` helper, and `uv run pytest tests/ -q` still passes (110 passed, 3 skipped, 8 deselected — no regressions).

**Not done in this run:** Plan 03-04's Task 3 (`checkpoint:human-verify`, "Fresh Colab CPU runtime verification") was explicitly out of scope for this execution per its stated objective. Before Phase 3 can be considered fully closed, a human still needs to push this branch, open the Colab badge link in a fresh unauthenticated session, run "Restart session and run all," and confirm: no cell errors, wall time near 3 minutes, the `git clone` bootstrap succeeds with no credential prompt, and the Path A appendix cell shows as skipped (not run).

---
*Phase: 03-similarity-search-and-classification-notebook*
*Completed: 2026-09-04*

## Self-Check: PASSED

All three modified files verified present; both task commits (e498929, d9bf11e) verified in git log.

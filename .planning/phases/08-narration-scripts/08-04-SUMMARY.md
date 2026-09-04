---
phase: 08-narration-scripts
plan: 04
subsystem: narration-scripts-module-03
tags: [narration, flagship, spatial-cv]
requires:
  - templates/NARRATION_SCRIPT_TEMPLATE.md
  - tools/verify_narration_scripts.py
provides:
  - scripts/03_similarity_classification_SCRIPT.md
affects:
  - 08-08 (grand-total/key-message check, once all 8 scripts exist)
tech-stack:
  added: []
  patterns:
    - "11 lectures covering all 14 notebook headings (title + What you will learn + Data merged into Lecture 03.1; Search-by-example + Why-this-is-wrong merged into the codealong Lecture 03.2; remaining 9 headings map 1:1)"
key-files:
  created:
    - scripts/03_similarity_classification_SCRIPT.md
  modified: []
decisions:
  - "Quoted the leave-region-out cost as '17-19 points' verbatim, matching both the notebook's own markdown takeaway text and the phase-constraint figure exactly -- no correction was needed since the notebook's prose already states this range (not a raw executed-notebook numeric read, since the solution .py's own markdown cell states the range directly and no numeric divergence was found)."
  - "Reported the Sentinel-2 baseline honestly per phase_specific_context: the script states the notebook measured no larger in-region block gap for Sentinel-2 than for embeddings, rather than asserting embeddings are more leakage-resistant."
metrics:
  duration: "~40 min"
  completed: "2026-09-04"
---

# Phase 8 Plan 4: Module 03 (flagship) narration script Summary

Wrote the 65-minute AV narration script for `02_similarity_and_classification.ipynb`, the course's core-value notebook, carrying both required verbatim key messages (unit-norm/dot-equals-cosine; leave-region-out costs 17-19 balanced-accuracy points) and framing the WRONG-conclusion trap cell and the honest leave-region-out gap as the module's center of gravity.

## What was built

`scripts/03_similarity_classification_SCRIPT.md` — 11 lectures (`03.1`–`03.11`), covering all 14 notebook headings in order: title/"What you will learn"/"Data" merged into Lecture 03.1 (unit-norm assertion cell, verbatim key message), "Search by example"/"Why this is wrong" merged into the codealong Lecture 03.2 (the WRONG-conclusion trap, narrated explicitly as a deliberate trap before the correction), then one lecture each for prototype queries, the optional positive-minus-negative prototype, the random-split trap, spatial-block CV, the codealong leave-region-out lecture (03.7, carrying the 17-19-point verbatim figure and the honest note that in-region blocking costs almost nothing), the Sentinel-2 baseline (reporting the measured, non-larger in-region gap rather than assuming embeddings win), provenance, wrap-up (naming both assessment files), and the illustrative-only Path A appendix. Lecture durations sum to exactly 65:00; Pronunciation Notes cover AlphaEarth, precision@k, EPSG:2056, balanced accuracy, GroupKFold, LeaveOneGroupOut.

## Deviations from Plan

None — Task 2's cross-check against the notebook's own leave-region-out markdown takeaway confirmed the "17-19 points" figure matches exactly as written in `notebooks/solutions/02_similarity_and_classification.py` (the notebook's markdown cell states the range directly rather than requiring a numeric read from `executed_02_similarity_and_classification.ipynb`), so no correction to the phase-constraint placeholder was needed.

## Known Stubs

None. This is a text-only narration script; no code was stubbed.

## Threat Flags

None. The only threat-model row (T-08-05, repudiation of the leave-region-out figure) was satisfied by the cross-check above; T-08-06 (Appendix Path A, accepted) is narrated explicitly as illustrative/non-executed in Lecture 03.11.

## Self-Check

- `scripts/03_similarity_classification_SCRIPT.md` exists — FOUND
- Commit `b8de861` (feat(08-04)) — FOUND
- `uv run python -m tools.verify_narration_scripts --scripts-glob "scripts/03_similarity_classification_SCRIPT.md" --strict` → `PASS 03_similarity_classification_SCRIPT.md` — FOUND
- `uv run pytest tests/ -q` → 184 passed, 3 skipped, 10 deselected — FOUND

## Self-Check: PASSED

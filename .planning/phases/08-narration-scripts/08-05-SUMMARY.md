---
phase: 08-narration-scripts
plan: 05
subsystem: narration-scripts
tags: [narration, change-detection, honesty]
requires:
  - templates/NARRATION_SCRIPT_TEMPLATE.md
  - tools/verify_narration_scripts.py
provides:
  - scripts/04_change_detection_SCRIPT.md
affects:
  - 08-08 (grand-total/key-message check completes once all 8 scripts exist)
tech-stack:
  added: []
  patterns:
    - "Ten lectures (60:00 total) rather than the template's typical eight-nine, to fit the module's honesty-heavy content (WRONG conclusion, proxy calibration, transition matrix, spatiotemporal CV) without exceeding the 7:00 per-lecture ceiling"
key-files:
  created:
    - scripts/04_change_detection_SCRIPT.md
  modified: []
decisions:
  - "Sourced the calibrated detector's measured precision/recall/F1 (0.023 / 0.065 / 0.933 / 0.121) from .planning/phases/05-later-module-solution-notebooks/05-02-SUMMARY.md, which records the executed notebook's actual printed output, rather than assuming the phase brief's suggested figure — confirmed it matches slides/03_change_detection.md's already-verified figure."
  - "Stated the proxy-reference limitation and the EU Login alternative in two separate lectures (04.5 calibration mechanics, 04.10 wrap-up) so it is not a single easily-skipped mention."
metrics:
  duration: "~25 min"
  completed: "2026-09-04"
---

# Phase 8 Plan 5: Module 04 change-detection narration script Summary

Wrote the 60-minute, ten-lecture narration script for Module 04 (change
detection and validation), carrying the "1 − cosine measures representation
movement" message verbatim, narrating the WRONG-conclusion threshold trap
as a deliberate error, and stating on camera — twice — that the calibrated
detector's honestly weak measured result (precision 0.065, recall 0.933, F1
0.121 at threshold 0.023) comes from validating against a proxy reference
rather than the true Copernicus HRL Imperviousness Change 2018-2021 product,
which requires a free EU Login the author has not created for this course.

## What was built

- `scripts/04_change_detection_SCRIPT.md` — ten lectures totaling exactly
  60:00, each anchored to real `[CELL]` headings from
  `notebooks/solutions/03_change_detection_and_validation.py` (re-verified
  live by the verifier, not a snapshot) and `[SLIDE]` positions in
  `slides/03_change_detection.md`. Covers: intro/objectives, the 2018-vs-2021
  data pairing rationale (Copernicus's 2015/2018 series break), the change
  score and its verbatim "representation movement, not semantic transition"
  framing, the WRONG-conclusion trap cell narrated verbatim, why it's wrong,
  the proxy-reference calibration disclosed explicitly (not implied), the
  measured 0.065-precision result stated plainly as an honest consequence of
  a weak reference rather than a failure, per-year classifiers and the
  predicted-not-true transition matrix, comparing the transition mask
  against the continuous change score, spatially- and temporally-grouped CV
  (the temporal-leakage trap), and a wrap-up that repeats the EU-Login
  limitation once more.

## Deviations from Plan

None (Rule 1-4). The plan's own behavior spec (verbatim message, proxy
disclosure, anchor/timing verification) was implementable directly from the
notebook, slide deck, and the already-verified `05-02-SUMMARY.md` figures.

## Known Stubs

None. This is a narration-script artifact with no code or data dependency.

## Threat Flags

None. This plan's threat model (T-08-07, overclaiming the calibration
reference) is the only registered threat and is directly mitigated by
Lectures 04.5/04.6/04.10 naming the proxy explicitly and the `grep -qi
proxy` verification gate.

## Self-Check

- `scripts/04_change_detection_SCRIPT.md` exists — FOUND
- `uv run python -m tools.verify_narration_scripts --strict --scripts-glob "scripts/04_change_detection_SCRIPT.md"` — PASS (anchors/timings; grand-total and key-messages checks report "skipped"/"incomplete" as expected until all 8 scripts exist)
- `grep -qi proxy scripts/04_change_detection_SCRIPT.md` — matched
- "1 − cosine measures representation movement" appears verbatim (2 occurrences)
- "0.065" appears (3 occurrences); "EU Login" appears (3 occurrences)

## Self-Check: PASSED

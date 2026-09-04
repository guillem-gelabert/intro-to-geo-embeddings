---
phase: 08-narration-scripts
plan: 03
subsystem: narration-scripts-content
tags: [narration, module-02, access-visualize]
requires:
  - templates/NARRATION_SCRIPT_TEMPLATE.md
  - tools/verify_narration_scripts.py
provides:
  - scripts/02_access_visualize_SCRIPT.md
affects: []
tech-stack:
  added: []
  patterns:
    - "Path A (live Earth Engine) narrated explicitly as shown-but-not-executed, cued [CUT] immediately before the EE_PROJECT credential per T-08-04"
    - "Forbidden physical-quantity phrasing ('measures vegetation') is quoted only inside the WRONG-conclusion trap row, never asserted as fact"
key-files:
  created:
    - scripts/02_access_visualize_SCRIPT.md
  modified: []
decisions:
  - "8 lectures (not 6-7): Path A codealong runs the full 12:00 ceiling to cover authenticate/inspect/display/sample/export without compressing any sub-step, leaving 7 remaining lectures at 4:00-7:00 each for the Path B walkthrough, dequantization, unit-norm, pseudo-RGB, PCA, and wrap-up."
  - "Quoted the unit-norm/cosine key message verbatim in Lecture 02.5 since it appears naturally in this module's own Unit-norm check section — not assigned to module 02 by any prior plan, but included because it fits without distortion."
metrics:
  duration: "~25 min"
  completed: "2026-09-04"
---

# Phase 8 Plan 3: Module 02 access/visualize narration script Summary

Wrote the 50-minute, 8-lecture recording script for `01_alphaearth_access_visualize.ipynb`, anchoring every VISUAL cell to a live notebook heading and every slide row to `slides/01_access_visualize.md`, with Path A (live Earth Engine) explicitly narrated as a shown-but-not-executed reference walkthrough and Path B as the actual recorded/tested default.

## What was built

- `scripts/02_access_visualize_SCRIPT.md` — header block (module/title/50 min/notebook/deck), 8 lectures (`02.1`–`02.8`) covering: the three-path decision flowchart, Path A's live-EE walkthrough (tagged `(codealong)`, 12:00, with a `[CUT]` cue immediately before the `EE_PROJECT` environment variable per the plan's threat model T-08-04), Path B's offline read, the int8 dequantization formula and its by-hand walkthrough, the unit-norm check (quoting the "AlphaEarth vectors are unit-norm, so dot product equals cosine" key message), static pseudo-RGB, PCA on the clip (quoting the notebook's own "separates ... in this sample, never 'measures vegetation'" caption verbatim), and wrap-up/attribution/quiz callback. Total sums to exactly 50:00.
- Every `[CELL]` anchor uses the exact heading text from `notebooks/solutions/01_alphaearth_access_visualize.py` (verified live by the verifier, not copied from a snapshot); every `[SLIDE]` anchor references one of the 9 sections in `slides/01_access_visualize.md`.

## Deviations from Plan

None (Rule 1-4). The plan's own behavior spec (segment 9 headings into 6-8 lectures, Path A illustrative framing, phrasing-rule enforcement, pronunciation notes, quiz callback) was implementable directly.

## Known Stubs

None.

## Threat Flags

None beyond what the plan's own threat model already covers (T-08-04: Path A's `[CUT]` cue before the `EE_PROJECT` credential, verified present in Lecture 02.2's third row).

## Verification

- `uv run python -m tools.verify_narration_scripts --strict` → `PASS 02_access_visualize_SCRIPT.md` (grand-total and key-messages checks report `skipped`/`incomplete` because only 1 of 8 expected scripts currently exists — expected until the remaining Wave-2 sibling plans land).
- `grep -qiv 'measures vegetation\|represents vegetation\|measures water\|measures built' scripts/02_access_visualize_SCRIPT.md` passes; the two lines containing "measures vegetation" are both quoted as the deliberate wrong-conclusion trap, not asserted as fact.
- `uv run pytest tests/ -q` → 184 passed, 3 skipped, 10 deselected.

## Self-Check

- `scripts/02_access_visualize_SCRIPT.md` exists — FOUND
- Commit `283c15f` (feat) — FOUND

## Self-Check: PASSED

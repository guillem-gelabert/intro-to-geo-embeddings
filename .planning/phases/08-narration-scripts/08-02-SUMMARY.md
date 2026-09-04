---
phase: 08-narration-scripts
plan: 02
subsystem: narration-scripts
tags: [narration, refresher, foundations]
requires:
  - templates/NARRATION_SCRIPT_TEMPLATE.md
  - tools/verify_narration_scripts.py
provides:
  - scripts/00_refresher_SCRIPT.md
  - scripts/01_foundations_SCRIPT.md
affects:
  - 08-09 (grand-total/key-message aggregation, once all 8 scripts exist)
tech-stack:
  added: []
  patterns:
    - "Two content-light modules (no provider credentials, no live network calls) narrated with [CELL] anchors verbatim-matched to notebook markdown headings and [SLIDE] anchors to the Marp decks"
key-files:
  created:
    - scripts/00_refresher_SCRIPT.md
    - scripts/01_foundations_SCRIPT.md
  modified: []
decisions:
  - "Neither script uses any of the five canonical KEY_MESSAGES substrings -- both modules are explicitly out of scope for those messages (unit-norm/cosine, A17-is-not-NDVI, leave-region-out cost, 1-minus-cosine, Dynamic-World-validation), stated explicitly in each Key Messages Used section so the eventual all-8 hard-fail check doesn't misfire against these two."
  - "01_foundations narration explicitly does not claim the SatCLIP branch executed a real forward pass even when torch happens to be installed -- the notebook's own comment marks that branch illustrative-only with a placeholder shape, and the script repeats that caveat rather than overselling it."
metrics:
  duration: "~25 min"
  completed: "2026-09-04"
---

# Phase 8 Plan 2: Narration scripts for Modules 00 and 01 Summary

Wrote the two lightest-weight module narration scripts (`00_refresher_SCRIPT.md`, 25:00; `01_foundations_SCRIPT.md`, 35:00) following the Wave-1 template, anchored every VISUAL row to real, currently-existing notebook markdown headings, and confirmed both pass `tools/verify_narration_scripts.py --strict`.

## What was built

- `scripts/00_refresher_SCRIPT.md` — 5 lectures covering `00_embedding_refresher.ipynb`'s seven content sections (intro/what-you'll-learn folded into Lecture 00.1; Vectors and L2 normalization; Cosine similarity; PCA on a toy embedding matrix; A tiny classifier + A CRS reprojection reminder combined into one lecture; Wrap-up), summing to exactly 25:00. Pronunciation Notes cover EPSG and AlphaEarth (mentioned only in the forward-pointer). Key Messages Used section states none of the five canonical messages apply. Exercise/Quiz Callback references `assessments/00_refresher_diagnostic.md`.
- `scripts/01_foundations_SCRIPT.md` — 6 lectures covering `00b_representation_inspection.ipynb`'s six content sections, summing to exactly 35:00. Honors the phrasing rule from the phase context ("this axis separates these landscape types in this sample", never "this axis measures X") in the Side-by-side comparison lecture, matching the deliberate trap slide in `slides/00b_representation_inspection.md`. The SatCLIP lecture explicitly states the reference environment has torch absent by default (so the cell prints a skip message) and that even a torch-enabled run of that branch is illustrative-only with a placeholder shape, not a real model checkpoint — no overselling of an unexecuted path. Pronunciation Notes cover AlphaEarth, Clay, SatCLIP, and EPSG. Exercise/Quiz Callback references `assessments/00b_representation_quiz.md`.

## Verification

- `uv run python tools/verify_narration_scripts.py --strict` (default glob `scripts/*_SCRIPT.md`, which currently matches only these two files): both scripts report `PASS` — zero anchor errors, zero timing errors. Grand-total check reports `status: skipped` (6 of 8 module scripts not yet written by sibling plans). Key-messages check reports `status: incomplete` (expected; this plan's two modules deliberately carry none of the five canonical messages).
- `uv run pytest tests/test_narration_scripts.py -q`: 16 passed.

Note: the plan's stated verification commands (`uv run python -m tools.verify_narration_scripts --strict --anchors-only scripts/00_refresher_SCRIPT.md scripts/01_foundations_SCRIPT.md` and the equivalent without `--anchors-only`) do not match the actual CLI signature — the tool takes no positional file arguments and no `--anchors-only` flag, only `--scripts-glob` (default `scripts/*_SCRIPT.md`) and `--strict`. Ran the tool with its real signature instead (see above); this is a Rule 3 blocking-issue fix (plan's verify command was wrong, not the tool), no code changes were needed since the default glob already covered exactly this plan's two files.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - blocking] Plan's verify command does not match the verifier's actual CLI**
- **Found during:** Task 1 verification
- **Issue:** Plan specifies `uv run python -m tools.verify_narration_scripts --strict --anchors-only scripts/00_refresher_SCRIPT.md scripts/01_foundations_SCRIPT.md`; the actual `tools/verify_narration_scripts.py` (built in 08-01) accepts only `--scripts-glob` and `--strict`, with no positional file arguments and no `--anchors-only` flag.
- **Fix:** Ran `uv run python tools/verify_narration_scripts.py --strict` (default glob), which matched exactly this plan's two files since no other `scripts/*_SCRIPT.md` exist yet.
- **Files modified:** none (verification-only)
- **Commit:** n/a (no code change)

None (Rule 1, 2, 4): no bugs, no missing critical functionality, no architectural changes.

## Known Stubs

None. Both scripts are complete, recording-ready narration for modules with no offline/fixture caveats to disclose (per the plan's own threat model and success criteria).

## Threat Flags

None. Both modules covered here (00_embedding_refresher, 00b_representation_inspection) touch no credentials, external APIs, or provider tokens — consistent with the plan's threat model (T-08-03, disposition: accept).

## Self-Check

- `scripts/00_refresher_SCRIPT.md` exists — FOUND
- `scripts/01_foundations_SCRIPT.md` exists — FOUND
- Commit `7c9fd48` (feat) — FOUND

## Self-Check: PASSED

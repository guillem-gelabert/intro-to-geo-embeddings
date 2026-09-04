---
phase: 08-narration-scripts
plan: 07
subsystem: narration-scripts
tags: [narration, provenance, licensing, capstone, marp, doc-anchor]
requires: ["08-01"]
provides:
  - scripts/06_production_provenance_SCRIPT.md
  - scripts/07_capstone_SCRIPT.md
  - "tools/verify_narration_scripts.py [DOC] anchor support"
affects:
  - "final grand-total/key-messages check in tools/verify_narration_scripts.py (now 2/8 scripts present)"
tech-stack:
  added: []
  patterns:
    - "[DOC] {file_path} § \"{heading}\" anchor syntax for modules with no source notebook, checked by the same extract-live-headings-at-check-time discipline as [CELL], but resolving the path directly (any repo file) instead of notebooks/solutions/{stem}.py"
key-files:
  created:
    - scripts/06_production_provenance_SCRIPT.md
    - scripts/07_capstone_SCRIPT.md
  modified:
    - tools/verify_narration_scripts.py
decisions:
  - "Used the real measured leave-region-out cost from notebooks/solutions/05_capstone_artificialization.py (\"roughly 17-19 balanced-accuracy points\") rather than the 23-point figure mentioned in the plan's phase-specific context, since the notebook's own printed takeaway and KEY_MESSAGES both say 17-19 -- narrating a number not actually in the notebook would break the anchor-truthfulness discipline this verifier exists to enforce."
  - "[DOC] anchors branch on file extension: .py files use the jupytext '# #' percent-comment heading form (reusing extract_notebook_headings' regex), .md files use bare '#'/'##'/'###' headers, via a new extract_doc_headings() function."
  - "Avoided anchoring into PROVENANCE_CHECKLIST.md's one heading that itself contains literal double-quote characters (the CDSE 'do not redistribute' worked example) since the [DOC]/[CELL] anchor syntax uses \" as its own delimiter; narrated that content under the adjacent, quote-free 'Reference table' heading instead."
metrics:
  duration: "~50 min"
  completed: "2026-09-04"
---

# Phase 8 Plan 7: Module 06/07 narration scripts Summary

Wrote the two remaining narration scripts -- Module 06 (production, provenance, licensing; 45 min, no dedicated notebook) and Module 07 (capstone launch; 25 min) -- completing the full eight-script set's content, and extended the shared verifier to support document-anchored rows for the one module with no notebook to point at.

## What was built

- **`tools/verify_narration_scripts.py`** -- added `MD_HEADING_RE`, `DOC_ANCHOR_RE`, `extract_doc_headings()` (branches `.py` jupytext percent-comment headings vs. bare `.md` markdown headings), extended the `Anchor` dataclass with a `doc_path` field and `"doc"` kind, extended `parse_script_anchors` to recognize `[DOC] {file} § "{heading}"` rows, and extended `check_anchors_exist` to resolve `[DOC]` anchors against `REPO_ROOT / {file}` directly (any repo path, not just `notebooks/solutions/*.py`) with the same live-re-derivation, fail-loud discipline as `[CELL]` anchors. All 16 pre-existing tests pass unchanged -- no regression.
- **`scripts/06_production_provenance_SCRIPT.md`** -- 7 lectures, 45:00 total. Anchors into `templates/MODEL_DATA_CARD_TEMPLATE.md` (Provenance, Representation Choice, Ethics Statement sections), `templates/PROVENANCE_CHECKLIST.md` (the eight-item checklist, Pitfall 6, the verbatim attribution reference table), `data/DATA_CARD.md`'s own Provenance section, plus `[CELL]` callback rows into three prior modules' own "Provenance" headings (Module 3's similarity/classification notebook, Module 4's change-detection notebook, Module 5's ecosystems notebook) to tie the checklist back to worked examples already run. States the TESSERA (unstated data license), Copernicus CDSE (explicit "do not redistribute" per portal terms), and Clay (four licenses across four artifact types) findings as real, reportable checklist outcomes, not gaps. Ethics content names the specific harmed party (a landowner facing regulatory/compliance consequences from a false "artificialized" flag) and the specific sensitivity gap (inferred label vs. underlying imagery), not a generic disclaimer.
- **`scripts/07_capstone_SCRIPT.md`** -- 6 lectures, 25:00 total, anchored to all 12 of `notebooks/solutions/05_capstone_artificialization.py`'s real headings (title through Wrap-up). Lecture 07.2 is tagged `(codealong)` at 8:00 (AOI -> Features -> Predictions). Lecture 07.3 states the measured "roughly 17-19 balanced-accuracy points" leave-region-out cost verbatim (matching `KEY_MESSAGES`). Lecture 07.4 explicitly ties the ranked-candidate-layer-not-binary-map design decision to that measured drop. The Wrap-up lecture states on camera, honestly, that every notebook in this course has been run locally end to end and a fresh Colab run is the one verification step still ahead -- never implying Colab has already been verified.

## Deviations from Plan

### 1. [Rule 1 -- factual correction] 17-19 points, not 23

- **Found during:** Task 1, reading `notebooks/solutions/05_capstone_artificialization.py`'s own printed takeaway and `KEY_MESSAGES` in `tools/verify_narration_scripts.py`.
- **Issue:** The plan's phase-specific context states "The capstone measured a 23-point leave-region-out drop." The actual notebook content (and the verifier's own canonical `KEY_MESSAGES` list, which every script must eventually quote) says "roughly 17-19 balanced-accuracy points."
- **Fix:** Narrated the real, verifiable 17-19 figure throughout, matching the notebook's own text and the verifier's `KEY_MESSAGES` substring check.
- **Files modified:** scripts/07_capstone_SCRIPT.md
- **Commit:** 7eafa45

### 2. [Rule 3 -- blocking anchor-syntax conflict] Avoided a heading with embedded quotes

- **Found during:** Task 1, drafting a `[DOC]` anchor into `templates/PROVENANCE_CHECKLIST.md`'s `## Worked "do not redistribute" example: Copernicus Global Embeddings (CDSE)` heading.
- **Issue:** The `[DOC]`/`[CELL]` anchor syntax delimits the heading text with `"`, but that heading itself contains literal `"` characters, which would truncate the regex match.
- **Fix:** Narrated the CDSE worked example's content under the adjacent, quote-free `## Reference table: exact verbatim attribution strings` heading instead, without altering the template file.
- **Files modified:** scripts/06_production_provenance_SCRIPT.md
- **Commit:** 7eafa45

## Known Stubs

None -- both scripts are complete, recording-ready content anchored to real, existing sources.

## Threat Flags

None. No new network endpoints, auth paths, or trust-boundary changes introduced; this plan only adds narration text and an anchor-checking code path.

## Verification

- `uv run pytest tests/test_narration_scripts.py -x` -- 16 passed, no regression.
- `uv run pytest tests/` (full suite) -- 184 passed, 3 skipped, 10 deselected.
- `uv run python -m tools.verify_narration_scripts --strict` -- `PASS 06_production_provenance_SCRIPT.md`, `PASS 07_capstone_SCRIPT.md`; grand-total/key-messages checks correctly report `skipped`/`incomplete` (2 of 8 scripts present; siblings write the remaining six).
- `grep -qi 'colab' scripts/07_capstone_SCRIPT.md` -- matches (Wrap-up lecture's Colab-verification-gap disclosure).

## Self-Check

- `scripts/06_production_provenance_SCRIPT.md` exists, `Total: 45:00` present -- FOUND
- `scripts/07_capstone_SCRIPT.md` exists, `Total: 25:00` present -- FOUND
- `tools/verify_narration_scripts.py` contains `DOC_ANCHOR_RE`/`extract_doc_headings` -- FOUND
- Commit `7eafa45` -- FOUND

## Self-Check: PASSED

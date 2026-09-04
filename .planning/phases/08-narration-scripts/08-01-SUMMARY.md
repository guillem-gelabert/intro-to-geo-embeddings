---
phase: 08-narration-scripts
plan: 01
subsystem: narration-scripts-tooling
tags: [tdd, verifier, template, marp]
requires: []
provides:
  - templates/NARRATION_SCRIPT_TEMPLATE.md
  - tools/verify_narration_scripts.py
affects:
  - 08-02..08-08 (all Wave-2 narration script plans write against this template and are checked by this verifier)
tech-stack:
  added: []
  patterns:
    - "Anchors re-derived from live notebook headings at check time (regex over jupytext py:percent markdown headings), never cached from a snapshot"
    - "Hard-fail gating deferred until all 8 expected artifacts exist (grand total, key messages), informational/skip status before that"
key-files:
  created:
    - templates/NARRATION_SCRIPT_TEMPLATE.md
    - tools/verify_narration_scripts.py
    - tests/test_narration_scripts.py
  modified: []
decisions:
  - "Adapted [SLIDE] anchor syntax to {deck_stem}.md (Marp), not {deck_stem}.qmd (Quarto) -- Phase 7 pivoted to Marp; slides/NN_*.md with HTML-comment speaker notes, matching the correction plan 07-05 already applied."
  - "Slide number in [SLIDE] anchors is the 1-indexed position of the deck's --- delimited sections, since Marp has no native slide-numbering directive to anchor against."
  - "Only [CELL] anchors are live-checked against notebook headings; [SLIDE] anchors are parsed and typed but not existence-checked, since no authoritative live index of deck section counts is maintained separately from the deck files themselves."
  - "KEY_MESSAGES defined as five literal substrings (unit-norm/cosine, A17-is-not-NDVI, 17-19 points, 1-minus-cosine, Dynamic-World-is-not-validation) checked via substring containment across all present scripts' text, not a stricter per-module assignment (assignment is a Wave-2-plan responsibility per the plan's own footer spec)."
metrics:
  duration: "~35 min"
  completed: "2026-09-04"
---

# Phase 8 Plan 1: Narration script template and anchor/timing verifier Summary

Built the shared two-column AV narration-script format contract and a standalone, TDD-proven verifier (`extract_notebook_headings`, `parse_script_anchors`, `check_anchors_exist`/`MissingAnchor`, `check_lecture_durations`, `check_module_total`, `check_grand_total`, `check_key_messages`) that re-derives notebook headings live and gates on the 360-minute syllabus, so all six sibling narration-script plans write against one unambiguous contract instead of drifting independently.

## What was built

- `templates/NARRATION_SCRIPT_TEMPLATE.md` — header block (module/title/minutes/notebook/deck path, with an explicit "deck not yet available" fallback instead of an invented path), per-lecture `### Lecture {m}.{n}` structure with the exact five-column table (`Duration | Cumulative | VISUAL | AUDIO | Cue`), both `[CELL] ... § "..."` and `[SLIDE] {stem}.md #{n}` anchor syntaxes, the five cue tokens, recap/end-state/target-length lines, and the module footer (totals line, Pronunciation Notes, Key Messages Used, Exercise/Quiz Callback), plus one fully worked module-03 example lecture using real notebook and deck content.
- `tools/verify_narration_scripts.py` — importable module + CLI (`argparse`, default glob `scripts/*_SCRIPT.md`, `--strict`). `MODULE_MINUTES` dict for the eight module slugs (sums to `GRAND_TOTAL_MINUTES = 360`, asserted at import time), `KEY_MESSAGES` list of five canonical substrings. Anchor parsing distinguishes cell vs. slide anchors; `check_anchors_exist` raises `MissingAnchor` (carrying script name, offending row, and heading) for any `[CELL]` anchor whose heading is absent from the live, re-derived notebook heading set. Duration/module/grand-total/key-message checks operate on markdown table rows and lecture blocks split on `### Lecture` headings.
- `tests/test_narration_scripts.py` — 16 tests, all passing, covering every function in the behavior spec plus the module-import-time `MODULE_MINUTES` sum assertion. One test runs `extract_notebook_headings` against the real `notebooks/solutions/02_similarity_and_classification.py` file (not a fixture) to prove the heading extraction works on live course content.

## TDD Gate Compliance

RED: `c4574e9 test(08-01): add failing tests for narration script verifier` — confirmed collection failure (`ModuleNotFoundError`) before any implementation existed.
GREEN: `d48e63a feat(08-01): implement narration script anchor/timing verifier` — all 16 tests pass; full repo suite (`uv run pytest tests/`) also passes (184 passed, 3 skipped, 10 deselected).
No REFACTOR commit was needed — implementation passed cleanly on first attempt.

## Deviations from Plan

### Auto-fixed / adapted (not a Rule 1-4 bug, but a documented correction per phase_specific_context instruction)

**1. Quarto → Marp anchor syntax correction**
- **Found during:** Task 1 (reading `slides/02_similarity_classification.md`, per files_to_read)
- **Issue:** Plan's interfaces/task text specifies `[SLIDE] {deck_stem}.qmd #{n}` and Quarto `::: {.notes}` conventions, but Phase 7 pivoted to Marp (`slides/NN_*.md`, plain HTML-comment speaker notes) — the same mismatch plan 07-05 hit and adapted for.
- **Fix:** Template and verifier both use `[SLIDE] {deck_stem}.md #{n}`; the verifier's regex accepts both `.md` and `.qmd` extensions for forward-compatibility but documents `.md` as canonical. Explicitly called out at the top of both the template and the verifier's module docstring.
- **Files modified:** templates/NARRATION_SCRIPT_TEMPLATE.md, tools/verify_narration_scripts.py
- **Commits:** bdcad18, d48e63a

### None (Rule 1-4)

No bugs, missing functionality, blockers, or architectural changes encountered — the plan's own behavior spec was implementable directly.

## Known Stubs

None. This plan produces tooling and a template only, no narration content; the `scripts/` directory intentionally does not exist yet (Wave 2's job).

## Threat Flags

None beyond what the plan's own threat model already covers (T-08-01 credential-cut convention documented in the template; T-08-02 constants accepted as low-risk, code-reviewed).

## Self-Check

- `templates/NARRATION_SCRIPT_TEMPLATE.md` exists, contains `VISUAL` (3 occurrences) — FOUND
- `tools/verify_narration_scripts.py` exists — FOUND
- `tests/test_narration_scripts.py` exists, 16/16 passing — FOUND
- Commit `c4574e9` (test) — FOUND
- Commit `d48e63a` (feat) — FOUND
- Commit `bdcad18` (docs/template) — FOUND
- Manual demonstration: a deliberately broken `[CELL]` anchor (`"Totally Made Up Heading"`) correctly raises `MissingAnchor` when run through `check_anchors_exist` — verified via ad hoc scratchpad script, not committed to the repo.

## Self-Check: PASSED

---
phase: 05-later-module-solution-notebooks
plan: 08
subsystem: templates
tags: [provenance, licensing, data-card, LATE-06]
requires: []
provides: [model-data-card-template, provenance-checklist, module3-worked-example]
affects: [notebooks/05_capstone_artificialization.ipynb (future reference)]
tech-stack:
  added: []
  patterns: [verbatim attribution copy-not-paraphrase, label_source != validation_source]
key-files:
  created:
    - templates/MODEL_DATA_CARD_TEMPLATE.md
    - templates/PROVENANCE_CHECKLIST.md
    - templates/model_card_worked_example_module3.md
  modified: []
decisions:
  - "Checklist items phrased as yes/no questions about a specific artifact, not vague prompts"
  - "TESSERA data license documented as unstated (software MIT only) rather than inventing a license"
  - "Copernicus CDSE Global Embeddings documented as the worked 'do not redistribute' example"
metrics:
  duration: "~15 min"
  completed: 2026-09-04
---

# Phase 05 Plan 08: Templates (model/data card, provenance checklist, Module 3 worked example) Summary

One-liner: A reusable model/data card template plus a yes/no provenance checklist with verbatim per-provider attribution strings, worked concretely against Module 3's actual shipped Bern/Seville AlphaEarth dataset.

## What was built

- `templates/MODEL_DATA_CARD_TEMPLATE.md` -- generic fillable card with `[PLACEHOLDER]` fields, mirroring `data/DATA_CARD.md`'s section structure (Description, Licenses and Attribution, Sampling Method/Model Details, Structure, Limitations, Citation, Provenance) plus a new "Representation Choice" section for capstone submissions that pick their own embedding backbone, and an Ethics Statement section.
- `templates/PROVENANCE_CHECKLIST.md` -- 8-item yes/no checklist (source documented, license identified, attribution verbatim, `label_source`/`validation_source` distinct per Pitfall 6, CRS recorded, version/checksum recorded, representation tradeoff stated, ethics statement present), followed by a reference table of verbatim attribution strings copied character-for-character from `data/DATA_CARD.md` for AlphaEarth, ESA WorldCover 2021, Copernicus HRL Imperviousness, Sentinel-2, and LGND Clay v1.5, plus TESSERA (documented as MIT software license with an explicitly unstated data license, per STACK.md's gap) and a worked "do not redistribute" example for Copernicus Global Embeddings (CDSE), whose portal terms prohibit redistribution.
- `templates/model_card_worked_example_module3.md` -- the template filled out for the actual shipped `02_similarity_and_classification.ipynb` dataset (Bern + Seville, 2018/2021/2024), with every field (license/attribution table, `label_source: esa_worldcover_2021`, `validation_source: eea_hrl_imperviousness_2018`, row counts, CRS, sampling method, `course_provenance` field names) copied from `data/DATA_CARD.md` rather than invented. Closes with a note pointing students at this file when the capstone (`05_capstone_artificialization.ipynb`) asks them to apply the template to a previous lab's outputs.

## Verification

- `grep -q "Google and Google DeepMind" templates/PROVENANCE_CHECKLIST.md` -- pass
- `grep -q "ESA WorldCover" templates/PROVENANCE_CHECKLIST.md` -- pass
- `grep -q "MIT" templates/PROVENANCE_CHECKLIST.md` -- pass
- `grep -q "esa_worldcover_2021" templates/model_card_worked_example_module3.md` -- pass
- `grep -q "eea_hrl_imperviousness_2018" templates/model_card_worked_example_module3.md` -- pass
- `uv run pytest tests/ -q` -- 129 passed, 3 skipped, 10 deselected (pre-existing, unrelated to this plan)

No test file was added for this plan; per the plan's own threat model ("templates/ files -> no code execution ... pure markdown, no trust boundary crossed") the deliverables are pure markdown verified structurally via the grep checks above, matching the guidance to keep any such test "structural... rather than trying to judge prose quality."

## Deviations from Plan

None -- plan executed exactly as written. All three files match the `<files_modified>` frontmatter list and satisfy each task's `<done>` criterion.

## Self-Check

- FOUND: templates/MODEL_DATA_CARD_TEMPLATE.md
- FOUND: templates/PROVENANCE_CHECKLIST.md
- FOUND: templates/model_card_worked_example_module3.md
- FOUND commit c5a2297 (Task 1)
- FOUND commit d826ee1 (Task 2)

## Self-Check: PASSED

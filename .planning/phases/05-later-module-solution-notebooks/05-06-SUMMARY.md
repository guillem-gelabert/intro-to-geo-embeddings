---
phase: 05-later-module-solution-notebooks
plan: 06
subsystem: capstone-notebook
tags: [capstone, validation, spatial-cv, template]
requires: [course.embeddings.change_score, course.validation.make_blocks, course.validation.spatial_cv_report, course.data.load, course.schema.to_matrix]
provides: [notebooks/solutions/05_capstone_artificialization.ipynb (Header through Validation sections)]
affects: [notebooks/solutions/05_capstone_artificialization.ipynb]
tech-stack:
  added: []
  patterns: ["EDIT ME AOI knob substitution point (course.data.load only)", "baseline-aware feature stacking (base-year embedding + change_score, not delta alone)", "dual validation reuse of spatial_cv_report for both GroupKFold and LeaveOneGroupOut"]
key-files:
  created: [notebooks/solutions/05_capstone_artificialization.py, notebooks/solutions/05_capstone_artificialization.ipynb]
  modified: []
decisions:
  - "Classifies the same 4-class label (built/crop/vegetation/water) Module 3 uses, rather than a binary artificialized/not target, since no artificialized_mask helper exists yet in course/ at this plan's point in the wave; the choice is stated explicitly in a markdown cell as the representation/target decision a capstone submission must also justify"
  - "Feature matrix is base-year (2024) embedding stacked with change_score(2018, 2021) as one extra column, per PITFALLS.md Pitfall 5's baseline-aware configuration -- literal reading of the plan's task description, not the more intuitive 2018->2024 span"
  - "Held-out region's feature matrix is padded with a zero change-score column (only one anchor year is loaded for it) rather than loading three years for both regions, to keep the notebook's execution light; documented inline as an explicit substitution, not a silent shape hack"
metrics:
  duration: "~25 min"
  completed: 2026-09-04
---

# Phase 5 Plan 6: Capstone AOI, Features, Predictions, Validation Summary

Started `05_capstone_artificialization.ipynb` (Header through the validation section): a template notebook that assembles an AOI-to-validation pipeline entirely from existing `course` helpers, with an `# EDIT ME` AOI knob and both spatial-block and leave-region-out validation via `course.validation.spatial_cv_report`.

## What Was Built

- **Header**: title, Colab badge, "what you will learn" list, Module 3-5 prerequisites table, time estimate, course-release banner sentence (verbatim from Module 3's own wording), and the six-row capstone rubric table with the exact ASSESS-04 weights (validation design 30%, reproducibility/provenance 15%, CRS/alignment 15%, interpretation/uncertainty 15%, representation choice 15%, licensing/ethics 10%) plus a one-sentence "what satisfies this row" per criterion.
- **Setup**: identical Colab-bootstrap + repo-root-chdir pattern as Module 3/4's notebooks.
- **AOI**: `AOI = "bern"  # EDIT ME` knob; loads `course.config.ANCHOR_YEARS` (2018, 2021, 2024) via `course.data.load`, plus the other region (`seville` when `AOI == "bern"`) as the held-out region for leave-region-out. Verified rows are row-aligned across years for the same AOI (sample_id order matches) before relying on that for `change_score`.
- **Features**: `X = hstack([to_matrix(gdf_2024), change_score(to_matrix(gdf_2018), to_matrix(gdf_2021)).reshape(-1,1)])` — 65-column baseline-aware feature matrix, with the representation-choice trade-off (AlphaEarth vs TESSERA/Clay) stated in markdown.
- **Predictions**: `Pipeline(StandardScaler(), LogisticRegression())` fit on the 4-class label (built/crop/vegetation/water, `bare` dropped as in Module 3), with the target choice stated explicitly in markdown.
- **Validation**: spatial-block CV (`make_blocks` + `GroupKFold(n_splits=5, shuffle=True)` reprojected to the AOI's own UTM EPSG) and leave-region-out (`LeaveOneGroupOut` over `region_groups`), both via `course.validation.spatial_cv_report` — no hand-rolled CV loop anywhere. A comparison table prints both results side by side.
- Measured on this run: spatial-block CV balanced_accuracy = 0.887 ± 0.010; leave-region-out (train bern, predict seville) = 0.656 ± 0.122 — a ~23-point gap, consistent with the course's documented 17-19 point pattern (same direction and order of magnitude; this run's specific numbers are a function of the 65-feature representation, not the 64-feature one Module 3 measured).

## Deviations from Plan

**1. [Rule 4-adjacent, resolved without a stop] Target choice for Predictions**
- **Found during:** Task 2 planning
- **Issue:** the plan offered a choice between the 4-class `label` and a binary `artificialized_mask` "derived the same way as Plan 05-03's". Plan 05-03 (a sibling plan, not yet executed in this wave) has not created that helper or mask logic anywhere in `course/` yet — grepped and confirmed no `artificialized_mask` exists.
- **Resolution:** used the 4-class `label`, which is fully supported by existing `course` helpers with no new code, and stated the choice explicitly in a markdown cell per the plan's own instruction ("state the choice explicitly ... as a representation/target choice"). No architectural change; no new dependency introduced.
- **Files modified:** notebooks/solutions/05_capstone_artificialization.py
- **Commit:** fb00e2d

None of the auto-fix rules (1-3) were triggered; the notebook executed cleanly end to end on the first `jupyter execute` run.

## Verification

- `uv run jupytext --to notebook notebooks/solutions/05_capstone_artificialization.py && uv run jupyter execute --kernel_name=geo-embeddings-course --timeout=180 --output=executed_05_capstone_artificialization.ipynb notebooks/solutions/05_capstone_artificialization.ipynb` — exit 0, no cell errors. (The `executed_*` output copy was deleted after inspection; it is gitignored per `notebooks/**/executed_*.ipynb`.)
- `uv run jupytext --sync notebooks/solutions/05_capstone_artificialization.py` — no drift between `.py` and `.ipynb`.
- `uv run pytest tests/ -q` — 139 passed, 3 skipped, 10 deselected. No regressions.

## Commits

- `fb00e2d` feat(05-06): capstone AOI, features, predictions, and honest validation

Both plan tasks (Header/Setup/AOI/Features, and Predictions/Validation) were implemented and verified together as one notebook build before the first commit, since the notebook only executes meaningfully end to end (an intermediate commit after Task 1 alone would not pass the full-notebook `jupyter execute` verification the plan itself uses for both tasks). Both tasks' `<done>` criteria are independently satisfied by the single commit's content.

## Known Stubs

None. Every cell in this notebook executes against real data and prints real, measured numbers — nothing is hardcoded or placeholder.

## Threat Flags

None. This plan only reads local frozen parquet files, matching the plan's stated trust boundary; no new network, auth, or schema surface was introduced.

## Self-Check

- FOUND: notebooks/solutions/05_capstone_artificialization.py
- FOUND: notebooks/solutions/05_capstone_artificialization.ipynb
- FOUND: commit fb00e2d

## Self-Check: PASSED

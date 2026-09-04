---
phase: 06-exercise-notebooks-and-assessments
plan: 04
subsystem: assessments
tags: [assessments, quizzes, diagnostic, pedagogy]
requires: []
provides: [assessments/00_refresher_diagnostic.md, assessments/00b_representation_quiz.md, assessments/01_access_visualize_quiz.md, assessments/02_similarity_classification_quiz.md]
affects: []
tech-stack:
  added: []
  patterns: [conceptual-error MCQ with per-option cell-quoting explanations]
key-files:
  created:
    - assessments/00_refresher_diagnostic.md
    - assessments/00b_representation_quiz.md
    - assessments/01_access_visualize_quiz.md
    - assessments/02_similarity_classification_quiz.md
  modified: []
decisions:
  - "Quiz explanations quote the notebook's own Takeaway/Caption/heading text verbatim where possible, rather than paraphrasing, to keep them auditable against the frozen solution notebooks"
  - "Used the notebook's own '17-19 points' figure (02_similarity_and_classification.py line 598) rather than the plan's paraphrase '17-23 points', since the notebook is the ground truth being quoted"
metrics:
  duration: "~25 min"
  completed: "2026-09-04"
---

# Phase 6 Plan 4: Refresher Diagnostic and Module Quizzes Summary

Wrote four prose assessment files (one ungraded diagnostic, three conceptual-error quizzes) derived directly from the frozen solution notebooks for modules 00 (refresher), 00b (representation inspection), 01 (access/visualize), and 02 (similarity/classification).

## What Was Built

- **`assessments/00_refresher_diagnostic.md`** — 5 ungraded MCQ questions labeled "Ungraded — for your own calibration before starting Module 1," covering L2 normalization, cosine similarity, PCA on a toy matrix, train/test split purpose, and CRS reprojection. Sourced from `notebooks/solutions/00_embedding_refresher.py`'s section headings and Takeaway cells.
- **`assessments/00b_representation_quiz.md`** — 6 conceptual-error questions on pixel (AlphaEarth, 64-D, 10m, annual) vs patch (Clay, 1024-D, 2560m MajorTOM cell, single scene) vs location (SatCLIP, ~few-hundred-D, no observation date) embedding granularity, including a "bigger vector = smaller area" trap and a torch-optional-dependency question.
- **`assessments/01_access_visualize_quiz.md`** — 5 conceptual-error questions on the "PC1 measures vegetation" trap (EARLY-05), the pseudo-RGB display-stretch trap, why unit-norm/dequantization matters for later similarity math, and why Path A and Path B reach the same conclusions about the data.
- **`assessments/02_similarity_classification_quiz.md`** — 8 conceptual-error questions (largest, flagship module): two "spot the leakage" questions (random split mixing regions; in-region spatial-block CV vs leave-region-out), the WRONG-conclusion cell (arbitrary similarity threshold), why leave-region-out costs 17-19 points while in-region blocking costs only 1-4, the Sentinel-2 baseline's purpose, prototype-renormalization requirement, and a synthesis question on which number to report for cross-region generalization.

Every option in every file carries an explanation naming the specific notebook heading, Takeaway/Caption text, or print output that proves the answer, per ASSESS-01/ASSESS-02.

## Verification

```
grep -c '^#### Q' assessments/*.md
# 00_refresher_diagnostic.md: 5
# 00b_representation_quiz.md: 6
# 01_access_visualize_quiz.md: 5
# 02_similarity_classification_quiz.md: 8
```

All counts within spec (diagnostic exactly 5; quizzes 5-8). `02_similarity_classification_quiz.md` includes Q2/Q3 as "spot the leakage" questions and Q4 referencing the WRONG-conclusion cell by name.

`uv run pytest tests/ -q` — 141 passed, 3 skipped, 10 deselected (pre-existing suite; unaffected by this plan, which touched only new markdown files under `assessments/`).

## Deviations from Plan

None — plan executed exactly as written. One clarification: the plan's `<phase_specific_context>` paraphrased the leave-region-out gap as "17-23 balanced-accuracy points," but `02_similarity_and_classification.py` line 598 states "17-19 points for logistic regression and random forest." The quiz quotes the notebook's own figure (17-19) since the notebook is the source of truth these explanations must trace to.

## Self-Check: PASSED

- FOUND: assessments/00_refresher_diagnostic.md
- FOUND: assessments/00b_representation_quiz.md
- FOUND: assessments/01_access_visualize_quiz.md
- FOUND: assessments/02_similarity_classification_quiz.md
- FOUND commit: 235698c

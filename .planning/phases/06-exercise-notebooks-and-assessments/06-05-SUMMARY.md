---
phase: 06-exercise-notebooks-and-assessments
plan: 05
subsystem: testing
tags: [assessment, quiz, rubric, markdown, capstone]

# Dependency graph
requires:
  - phase: 05-capstone-and-provenance
    provides: frozen solution notebooks 03/04/05 and templates/PROVENANCE_CHECKLIST.md
provides:
  - Change-detection and ecosystems module quizzes (ASSESS-02)
  - Similarity/classification, change-detection, and ecosystems assignment texts (ASSESS-03)
  - Capstone rubric and proposal template (ASSESS-04)
affects: [06-06 exercise-notebook derivation, assessment-review]

# Tech tracking
tech-stack:
  added: []
  patterns: ["cell-quoting quiz explanations (every option cites the exact notebook cell/heading/Takeaway)", "verbatim-weight assignment headers (published module weights repeated identically across all three assignment files)"]

key-files:
  created:
    - assessments/03_change_detection_quiz.md
    - assessments/04_ecosystems_quiz.md
    - assessments/02_similarity_classification_assignment.md
    - assessments/03_change_detection_assignment.md
    - assessments/04_ecosystems_assignment.md
    - assessments/05_capstone_rubric.md
    - assessments/05_capstone_proposal_template.md
  modified: []

key-decisions:
  - "Each quiz question uses 4 options with a full explanation on every option (not just the correct one), each explanation quoting a specific notebook cell/heading/Takeaway verbatim"
  - "Assignment weight line kept on a single unwrapped markdown line in all three files so the verification grep matches (soft-wrapped prose broke the initial grep check)"
  - "Ecosystems assignment states the 20% core and 10% portability components as two separate rubric rows, never summed into 30%"

requirements-completed: [ASSESS-02, ASSESS-03, ASSESS-04]

# Metrics
duration: 25min
completed: 2026-09-04
---

# Phase 06 Plan 05: Assessments (Quizzes, Assignments, Capstone Rubric) Summary

**Seven assessment markdown files: two conceptual-error quizzes, three graded-lab assignments with verbatim published weights, and a capstone rubric plus self-checkable proposal template.**

## Performance

- **Duration:** 25 min
- **Started:** 2026-09-04T00:00:00Z (approx.)
- **Completed:** 2026-09-04
- **Tasks:** 3
- **Files modified:** 7 created

## Accomplishments
- `03_change_detection_quiz.md` and `04_ecosystems_quiz.md`: 7 questions each, every option's explanation quotes a specific notebook cell/heading/Takeaway (WRONG-conclusion 0.25 threshold, precision_recall_curve calibration, proxy-reference weakness, transition-matrix predicted-vs-true axes, temporal leakage for 03; provider norm checking, graceful `LGND_TOKEN` degradation, TESSERA-vs-Clay access patterns, cross-provider non-comparability, unstated TESSERA data license for 04)
- Three graded-lab assignments (`02_similarity_classification_assignment.md` 15%, `03_change_detection_assignment.md` 20%, `04_ecosystems_assignment.md` 20%+10% portability) each state the full published weight set verbatim and define gradable, observable submission criteria rather than aspirational ones
- `05_capstone_rubric.md` publishes the six weighted criteria verbatim (validation design 30%, reproducibility/provenance 15%, CRS/alignment 15%, interpretation/uncertainty 15%, representation choice 15%, licensing/ethics 10%), summing to 100%
- `05_capstone_proposal_template.md` provides a 12-key provenance dict skeleton matching `data/DATA_CARD.md`'s schema and a six-item rubric self-check checklist, referencing `templates/PROVENANCE_CHECKLIST.md`

## Task Commits

1. **Task 1: Write the change-detection and ecosystems quizzes** - `a6e6b55` (feat)
2. **Task 2: Write the three graded-lab assignments** - `aa1f835` (feat)
3. **Task 3: Write the capstone rubric and proposal template** - `5ee0251` (feat)

## Files Created/Modified
- `assessments/03_change_detection_quiz.md` - 7 conceptual-error questions on cosine-threshold traps, calibration, proxy-reference weakness, transition matrix, temporal leakage
- `assessments/04_ecosystems_quiz.md` - 7 conceptual-error questions on provider norm checks, graceful degradation, TESSERA/Clay access patterns, non-comparability, license gaps
- `assessments/02_similarity_classification_assignment.md` - 15% assignment: search-by-example + random-vs-spatial-CV interpretation
- `assessments/03_change_detection_assignment.md` - 20% assignment: threshold calibration + precision/recall/F1 table + transition matrix
- `assessments/04_ecosystems_assignment.md` - 20%+10% assignment: TESSERA/Clay norm and behavior comparison, portability kept as a separate figure
- `assessments/05_capstone_rubric.md` - six weighted rubric criteria, verbatim percentages
- `assessments/05_capstone_proposal_template.md` - provenance dict skeleton + rubric self-check checklist

## Decisions Made
- Quiz format: `#### Q<n>.` headings with four lettered options, each carrying its own explanation line quoting the notebook — chosen so the verification grep (`^#### Q`) and the acceptance criterion ("every option's explanation names a specific notebook cell/heading") are both satisfied unambiguously.
- Fixed a soft-wrap bug in the first draft of the assignment weight line (markdown line-wrapped across two source lines broke the single-line grep check); rewrote as one unwrapped line in all three assignment files.
- Capstone rubric text expands each of the six rows with 2-3 sentences of "what full marks looks like," drawn directly from the capstone notebook's own rubric table and rubric self-check section, rather than inventing new criteria language.

## Deviations from Plan

None - plan executed exactly as written, with one self-corrected authoring mistake (see below).

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed line-wrap breaking the verification grep in assignment files**
- **Found during:** Task 2 (verification step)
- **Issue:** The "Published module weights: ..." line was authored as soft-wrapped markdown prose across two lines; `grep -l "15%, change detection 20%, ecosystems 20%, portability 10%"` returned 0 matches instead of 3 because grep matches single lines.
- **Fix:** Rewrote the weights line as a single unwrapped line in all three assignment files.
- **Files modified:** `assessments/02_similarity_classification_assignment.md`, `assessments/03_change_detection_assignment.md`, `assessments/04_ecosystems_assignment.md`
- **Verification:** Re-ran the grep; returned 3 as required.
- **Committed in:** `aa1f835` (Task 2 commit, fixed before commit)

---

**Total deviations:** 1 auto-fixed (1 bug fix, self-caught during verification, no separate commit needed since it was fixed before the task commit was made)
**Impact on plan:** No scope creep; the fix was purely a markdown authoring correction to satisfy the plan's own verification command.

## Issues Encountered
None.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- ASSESS-02, ASSESS-03, ASSESS-04 complete alongside sibling plan 06-04's ASSESS-01/ASSESS-02 (00b/01/02 quizzes).
- `assessments/02_similarity_classification_assignment.md` references
  `notebooks/exercises/02_similarity_and_classification.ipynb`, which
  06-06 is expected to produce via exercise derivation — no blocker, but
  that link should be spot-checked once 06-06 lands.
- `uv run pytest tests/ -q` passes (141 passed, 3 skipped, 10 deselected)
  confirming no regression from these markdown-only additions.

---
*Phase: 06-exercise-notebooks-and-assessments*
*Completed: 2026-09-04*

## Self-Check: PASSED

All 7 created files verified present (`assessments/03_change_detection_quiz.md`,
`assessments/04_ecosystems_quiz.md`,
`assessments/02_similarity_classification_assignment.md`,
`assessments/03_change_detection_assignment.md`,
`assessments/04_ecosystems_assignment.md`,
`assessments/05_capstone_rubric.md`,
`assessments/05_capstone_proposal_template.md`). All 3 task commits
(`a6e6b55`, `aa1f835`, `5ee0251`) verified present in `git log`.

Module: 07 — capstone
Title: Capstone Launch — Artificialization Pipeline Template
Syllabus minutes: 25 (see MODULE_MINUTES in tools/verify_narration_scripts.py)
Source notebook: notebooks/solutions/05_capstone_artificialization.py
Slide deck: slides/05_capstone.md

---

### Lecture 07.1 — What this capstone is, and how it's graded

Objective: describe the capstone as a reusable pipeline template built
entirely from Modules 3-5's own helpers, and preview the six rubric
criteria it is graded against.

| Duration | Cumulative | VISUAL | AUDIO | Cue |
|----------|------------|--------|-------|-----|
| 01:00 | 01:00 | [CELL] 05_capstone_artificialization.ipynb § "Module 6: Capstone — Artificialization Pipeline Template" | "This is a template, not a finished analysis: similarity, classification, change detection, and spatially honest validation, assembled end to end from course helpers you've already used in Modules 3 through 5. Every 'EDIT ME' cell is where your own capstone substitutes in." | [NONE] |
| 01:00 | 02:00 | [CELL] 05_capstone_artificialization.ipynb § "What you will learn" | "By the end you'll be able to assemble a full AOI-to-provenance pipeline from reusable helpers without reimplementing any of them, know exactly what the rubric grades, and understand why validation design outweighs every other criterion. Prerequisites are Modules 3 and 4; Module 5 is recommended, not required." | [NONE] |
| 02:00 | 04:00 | [CELL] 05_capstone_artificialization.ipynb § "Capstone rubric" | "Six weighted rows, summing to 100%: validation design at 30 -- more than any other single criterion -- reproducibility and provenance at 15, CRS and alignment correctness at 15, interpretation and uncertainty at 15, representation choice at 15, and licensing and ethics at 10. That 30% weight is deliberate: an impressive-looking classifier with a dishonest validation still fails this rubric." | [ZOOM] |

Recap: the capstone reuses Modules 3-5's own helpers unmodified, and its
rubric weights validation design above every other row on purpose.
End-state: the six-row rubric weight table is fully visible on screen.
Target length: 2:00-7:00 (not a codealong).

---

### Lecture 07.2 — AOI, Features, Predictions (codealong)

Objective: walk the AOI-to-predictions path live, reusing `course.data.load`,
`course.schema.to_matrix`, and `course.embeddings.change_score` exactly as
seen in Modules 3-5.

| Duration | Cumulative | VISUAL | AUDIO | Cue |
|----------|------------|--------|-------|-----|
| 02:30 | 06:30 | [CELL] 05_capstone_artificialization.ipynb § "AOI" | "First, pick the AOI -- Bern or Seville, the same frozen regions from every earlier module -- and load it with `course.data.load`, the identical helper you've been calling since Module 3. No new loading code exists for the capstone; that's the point." | [RUN CELL] |
| 03:00 | 09:30 | [CELL] 05_capstone_artificialization.ipynb § "Features" | "Features come from `course.schema.to_matrix`, and this is where you state your representation choice explicitly -- here, AlphaEarth's 64-dimensional annual composite, plus a change-score feature from `course.embeddings.change_score` across anchor years. State the trade-off against TESSERA or Clay here too; the rubric's representation-choice row grades exactly this statement." | [RUN CELL] |
| 02:30 | 12:00 | [CELL] 05_capstone_artificialization.ipynb § "Predictions" | "Fit the classifier in-region and generate predictions -- same `sklearn` classifier pattern from Module 3, no new modeling code. On its own, a prediction map like this invites a reader to treat it as settled fact. It isn't, yet -- the next section is why." | [RUN CELL] |

Recap: nothing in the AOI-to-predictions path is new code -- it's Modules
3-5's own helpers, called in sequence, with the representation choice made
explicit along the way.
End-state: the prediction array and its shape are printed on screen.
Target length: 2:00-12:00 (codealong).

---

### Lecture 07.3 — Validation: spatial-block CV and leave-region-out

Objective: report both required validations side by side and name which
one is the honest generalization estimate.

| Duration | Cumulative | VISUAL | AUDIO | Cue |
|----------|------------|--------|-------|-----|
| 02:00 | 14:00 | [CELL] 05_capstone_artificialization.ipynb § "Validation: spatial-block CV and leave-region-out" | "Validation design is the single largest rubric weight, and both validations below reuse the exact same `spatial_cv_report` call shape from Module 3, changing only `groups` and `cv`. Spatial-block CV first -- `GroupKFold` on 10 km blocks, projected to the local UTM zone before any distance calculation, never in EPSG:4326." | [RUN CELL] |
| 02:00 | 16:00 | [CELL] 05_capstone_artificialization.ipynb § "Validation: spatial-block CV and leave-region-out" | "Then leave-region-out, training on this AOI and predicting an entirely held-out region with `LeaveOneGroupOut`. On this course's measured data, leave-region-out costs roughly 17-19 balanced-accuracy points relative to in-region spatial-block CV -- while spatial-block CV itself costs almost nothing relative to a random split. The honest cross-region number is where this pipeline's real generalization test lives, not the in-region one." | [ZOOM] |

Recap: a capstone submission must report both spatial-block CV and
leave-region-out side by side -- never either one alone, and never a
random split standing in for either.
End-state: the two-row `comparison` DataFrame -- spatial-block CV and
leave-region-out, each with mean and std -- is visible on screen.
Target length: 2:00-7:00 (not a codealong).

---

### Lecture 07.4 — Why a ranked layer, not a binary map

Objective: connect the measured leave-region-out gap directly to the
decision to present a ranked candidate layer for human review, never a
finished binary classification.

| Duration | Cumulative | VISUAL | AUDIO | Cue |
|----------|------------|--------|-------|-----|
| 02:00 | 18:00 | [CELL] 05_capstone_artificialization.ipynb § "Map: predictions over the AOI" | "Here's the prediction map -- deliberately paired with the uncertainty view that follows it, never left standing alone. A model that loses 17 to 19 balanced-accuracy points the moment it leaves its training region is exactly the kind of model that should never ship as a crisp, final map." | [ZOOM] |
| 02:00 | 20:00 | [CELL] 05_capstone_artificialization.ipynb § "Uncertainty: model-level and validation-level" | "Two distinct uncertainty signals, never conflated: model-level, the top-1-minus-top-2 probability margin per point, and validation-level, the fold-to-fold `std_balanced_accuracy` spread. The takeaway printed by the notebook says it directly -- read this map as a ranked candidate layer a human verifies, ordered by margin, low-margin points reviewed first, never as a finished classification." | [ZOOM] |

Recap: the ranked-layer-not-binary-map decision is a direct consequence of
the measured 17-19 point leave-region-out drop -- a model that sensitive to
region does not get to present its output as settled fact.
End-state: the prediction map and the uncertainty-margin histogram are
both visible, side by side.
Target length: 2:00-7:00 (not a codealong).

---

### Lecture 07.5 — Provenance and the rubric self-check

Objective: show the capstone's own provenance write-out and rubric
self-check as the worked example a submission should imitate.

| Duration | Cumulative | VISUAL | AUDIO | Cue |
|----------|------------|--------|-------|-----|
| 01:00 | 21:00 | [CELL] 05_capstone_artificialization.ipynb § "Provenance" | "Every number and figure above traces back to a dataset version, CRS, label source, and license -- summarized here with `build_provenance`/`write_provenance`, never hand-typed. This notebook holds its own output to the same `PROVENANCE_CHECKLIST.md` standard demonstrated all through Module 6." | [RUN CELL] |
| 01:00 | 22:00 | [CELL] 05_capstone_artificialization.ipynb § "Rubric self-check" | "And the rubric self-check revisits each of the six criteria with this run's own evidence named -- the validation-design row pointing at the comparison table you just saw, the ethics row naming the false-positive cost directly. Imitate this table's structure in your own submission; it's the worked example, not a formality." | [ZOOM] |

Recap: provenance and rubric self-check are not afterthoughts -- they're
built from the same run's actual evidence, cited explicitly.
End-state: the rubric self-check table with per-row evidence is visible.
Target length: 2:00-7:00 (not a codealong).

---

### Lecture 07.6 — Wrap-up and the one verification step still ahead

Objective: close the capstone and disclose, honestly, that no notebook in
this course has been run on a live Colab runtime as part of authoring it.

| Duration | Cumulative | VISUAL | AUDIO | Cue |
|----------|------------|--------|-------|-----|
| 02:00 | 24:00 | [CELL] 05_capstone_artificialization.ipynb § "Wrap-up" | "This capstone assembles an AOI-to-provenance pipeline entirely from course helpers reused, unmodified, from Modules 3 through 5. Validation design carries the largest rubric weight for a reason: the leave-region-out gap is the single largest source of overconfidence this pipeline could produce if only the in-region number were reported. A prediction map is only honest alongside both uncertainty measures -- neither substitutes for the other." | [NONE] |
| 01:00 | 25:00 | [SLIDE] 05_capstone.md #2 | "One honest disclosure before you record your own capstone: every notebook in this course, including this one, has been run locally end to end -- a fresh Colab run is the one verification step still ahead. Treat any printed numbers here as illustrative of the pattern this pipeline produces, not as a guarantee of the exact figures a live Colab re-run will reproduce." | [NONE] |

Recap: the capstone closes on the same honesty standard it teaches --
reporting a real gap (17-19 points) and a real unverified step (Colab)
rather than implying more confidence than the evidence supports.
End-state: the Colab-disclosure sentence is on screen as the final frame.
Target length: 2:00-7:00 (not a codealong).

---

Total: 25:00 (syllabus: 25 minutes)

## Pronunciation Notes

- AlphaEarth — "AL-fuh urth"
- TESSERA — "teh-SAIR-uh"
- GeoTessera — "JEE-oh teh-SAIR-uh"
- Guadalquivir — "gwah-dahl-kee-VEER"
- EPSG — spelled out, "E-P-S-G"
- precision@k — "precision at k"
- balanced_accuracy — "balanced accuracy", spoken as two words

## Key Messages Used

- "17-19 points" (Lecture 07.3, leave-region-out cost)

## Exercise/Quiz Callback

See `assessments/05_capstone_proposal_template.md` (the proposal a student
fills in before starting their own capstone) and
`assessments/05_capstone_rubric.md` (the six-criterion grading rubric this
module's Lecture 07.1 and 07.5 walk through).

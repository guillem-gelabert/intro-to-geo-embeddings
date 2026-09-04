Module: 04 — change_detection
Title: Change Detection and Validation
Syllabus minutes: 60 (see MODULE_MINUTES in tools/verify_narration_scripts.py)
Source notebook: notebooks/solutions/03_change_detection_and_validation.py
Slide deck: slides/03_change_detection.md

---

### Lecture 04.1 — Introduction and what you will learn

Objective: state the module's central risk up front so the student watches
the rest of this module already primed to separate "the embedding moved"
from "the land changed."

| Duration | Cumulative | VISUAL | AUDIO | Cue |
|----------|------------|--------|-------|-----|
| 01:15 | 01:15 | [SLIDE] 03_change_detection.md #1 | "This module takes the same AlphaEarth embeddings you already used for search and classification and asks a harder question: did the land at a point actually change between two years? A single cosine-based change score is easy to compute and easy to misread. We're going to build it, show exactly how it misleads you, and then calibrate a threshold honestly against an independent reference instead of eyeballing one." | [NONE] |
| 01:30 | 02:45 | [SLIDE] 03_change_detection.md #2 | "Three things by the end of this module: a cosine-based change score between two years of the same point's embedding; why a fixed change-score threshold is not itself a semantic-change decision — that's the trap the middle of this module is built around; and calibrating a threshold against an independent reference with precision_recall_curve, so the number you end up with comes with a known precision and recall instead of a guess." | [NONE] |
| 01:15 | 04:00 | [CELL] 03_change_detection_and_validation.ipynb § "Module 4: Change Detection and Validation" | "No Earth Engine account is needed here — everything runs against the frozen tables, in about three minutes of execution on free Colab CPU. Course reference environment: 2026-08 release. Provider APIs may change, and every cloud notebook in this course has a local, offline fallback — this one included." | [RUN CELL] |

Recap: this module's job is to build a change score, show how it lies if
read naively, and then measure — not assume — how much to trust it.
End-state: the "What you will learn" slide is on screen with all three
learning points visible.

---

### Lecture 04.2 — Data: 2018 vs 2021, row-aligned by sample_id

Objective: explain why this module compares 2018 against 2021 specifically,
and why the row-alignment check matters before any change score is computed.

| Duration | Cumulative | VISUAL | AUDIO | Cue |
|----------|------------|--------|-------|-----|
| 02:00 | 06:00 | [CELL] 03_change_detection_and_validation.ipynb § "Data: 2018 vs 2021, row-aligned by `sample_id`" | "This module compares 2018 against 2021, not 2020 against 2024 — and that pair isn't arbitrary. Copernicus imperviousness has a series break between its 2015 and 2018 products, and the corresponding change product covers exactly 2018 to 2021. The frozen tables carry 2018, 2021, and 2024 for the same sample_ids across both study areas, so this pair joins directly without extra sampling." | [RUN CELL] |
| 03:00 | 09:00 | [CELL] 03_change_detection_and_validation.ipynb § "Data: 2018 vs 2021, row-aligned by `sample_id`" | "Before computing anything, the notebook asserts an exact sample_id match between the two years for each region — watch this assertion run. If it failed, that would mean a partial join, and a partial join here would silently compare unrelated points and call the result a 'change score.' The same sample_id has to name the same real-world point in both years, or subtracting one year's embedding from another is comparing noise, not measuring anything." | [RUN CELL] |
| 02:00 | 11:00 | [CELL] 03_change_detection_and_validation.ipynb § "Data: 2018 vs 2021, row-aligned by `sample_id`" | "That row-alignment stability is what makes a paired change score meaningful at all. Without it, this whole module would be building a number that looks precise and means nothing." | [ZOOM] |

Recap: a change score is only as trustworthy as the row alignment underneath
it — the notebook checks that alignment explicitly rather than assuming it.
End-state: the printed "N row-aligned points" summary for both Bern and
Seville is visible on screen.

---

### Lecture 04.3 — Change score: representation movement, not semantic transition

Objective: compute the cosine-based change score and state, verbatim, what
it does and does not measure.

| Duration | Cumulative | VISUAL | AUDIO | Cue |
|----------|------------|--------|-------|-----|
| 01:30 | 12:30 | [CELL] 03_change_detection_and_validation.ipynb § "Change score: `1 - cosine_similarity` per point" | "course.embeddings.change_score takes two row-aligned 64-dimensional matrices and returns one number per point: how far that point's embedding moved between the two years." | [RUN CELL] |
| 02:00 | 14:30 | [SLIDE] 03_change_detection.md #3 | "Here is the message to hold onto for the rest of this module: 1 − cosine measures representation movement, not a semantic transition. It reports that something moved in embedding space. It does not know, and does not claim to know, why a point moved." | [NONE] |
| 02:00 | 16:30 | [CELL] 03_change_detection_and_validation.ipynb § "Change score: `1 - cosine_similarity` per point" | "Here's the change-score histogram for both regions, split out — most points show a small representation shift, a minority show a large one. That long tail is exactly what's about to tempt us into the trap." | [RUN CELL] |
| 01:30 | 18:00 | [CELL] 03_change_detection_and_validation.ipynb § "Change score: `1 - cosine_similarity` per point" | "And here's the same change score plotted in geographic space, colored by magnitude. Notice the spatial structure — high-change points aren't randomly scattered. That real structure is exactly what makes a naive eyeballed threshold feel trustworthy, right before we show you it isn't." | [ZOOM] |

Recap: the change score is a real, cheap signal of embedding movement — and
by itself it is never a semantic-change verdict.
End-state: the change-score map figure is on screen with the colorbar
visible.

---

### Lecture 04.4 — The WRONG conclusion

Objective: watch the deliberate threshold trap run and see the flagged
counts it produces, before it gets corrected in the next lecture.

| Duration | Cumulative | VISUAL | AUDIO | Cue |
|----------|------------|--------|-------|-----|
| 02:00 | 20:00 | [SLIDE] 03_change_detection.md #6 | "It is tempting to pick a threshold by eye and call every point above it 'artificialized.' Watch this next cell do exactly that." | [NONE] |
| 03:00 | 23:00 | [CELL] 03_change_detection_and_validation.ipynb § "The WRONG conclusion" | "artificialized equals change_score greater than 0.25 — and it is wrong. There's no hedging in that heading, no softer framing. This cell is tagged wrong-conclusion in the source on purpose: it's the deliberate error the rest of this module exists to correct. Watch the flagged counts print for Bern and Seville — those numbers look decisive. They are not." | [RUN CELL] |

Recap: an eyeballed cutoff that flags points by construction still has zero
precision, recall, or F1 behind it.
End-state: the printed "WRONG: bern=N of N points flagged, seville=N of N
points flagged" line is visible on screen.

---

### Lecture 04.5 — Why this is wrong, and calibrating against a proxy reference

Objective: explain why 0.25 was never a safe cutoff, and state on camera
exactly what independent reference the calibrated threshold is validated
against — and what it is not.

| Duration | Cumulative | VISUAL | AUDIO | Cue |
|----------|------------|--------|-------|-----|
| 02:00 | 25:00 | [CELL] 03_change_detection_and_validation.ipynb § "Why this is wrong" | "1 minus cosine_similarity collapses the full 64-dimensional embedding into one number, and 0.25 was picked by eye with no reference data behind it. Google's own analysis of change scores derived this way found, quote, widespread speckling, scattered false positives — harvest cycles, a drought year, early snow cover, even a swath-boundary artifact in the underlying imagery can move a point's embedding by as much as genuine land-cover change does." | [ZOOM] |
| 02:00 | 27:00 | [CELL] 03_change_detection_and_validation.ipynb § "Calibrating a threshold against a proxy independent reference" | "So here's the honest fix: the true Copernicus HRL Imperviousness Change 2018-2021 product would be the right reference here — but it requires a free EU Login the author has not created for this course. If you have that login, you should substitute the real product and redo this calibration yourself. Rather than skip validation, or quietly reuse the label column as if it were an independent change product, this notebook builds an explicitly labeled proxy instead." | [NONE] |
| 02:00 | 29:00 | [CELL] 03_change_detection_and_validation.ipynb § "Calibrating a threshold against a proxy independent reference" | "That proxy is weaker than a real two-epoch change product for a specific, stated reason: the label column is a single 2021 snapshot, not a genuine 2018-versus-2021 label pair. So known_change here really means 'was clearly non-built in 2018 and is built in the one epoch we have a label for' — consistent with a transition to built, but not directly observed as one." | [RUN CELL] |
| 01:00 | 30:00 | [CELL] 03_change_detection_and_validation.ipynb § "Calibrating a threshold against a proxy independent reference" | "precision_recall_curve runs against those proxy controls, and the threshold that maximizes F1 gets picked." | [RUN CELL] |

Recap: the calibration is honest about what it validates against — a
labeled proxy, not the true Copernicus change product — and says so before
a single number is trusted.
End-state: the "controls: N/M rows kept" print line is visible on screen.

---

### Lecture 04.6 — The measured result: precision 0.065

Objective: report the calibrated detector's actual measured precision,
recall, and F1 without softening or spinning the weak number.

| Duration | Cumulative | VISUAL | AUDIO | Cue |
|----------|------------|--------|-------|-----|
| 02:00 | 32:00 | [SLIDE] 03_change_detection.md #7 | "Here's what that calibration actually measured: calibrated threshold 0.023, precision 0.065, recall 0.933, F1 0.121. Say that precision number out loud, because it's low — and it is low on purpose, in the sense that we are reporting it honestly rather than hiding it." | [NONE] |
| 03:00 | 35:00 | [SLIDE] 03_change_detection.md #7 | "This is not a broken pipeline. It is the direct, honest consequence of calibrating against a weak reference: only 208 positive controls, and a single-year label snapshot standing in for a genuine two-epoch change label. Recall of 0.933 shows the change score itself is catching almost every known change in the proxy — it's just also catching a lot else, which is exactly why the eyeballed 0.25 threshold was never a safe conclusion in the first place. A weak, honestly-measured detector is more useful than a confident, unvalidated one, because it tells you precisely how much to trust its output — and a student with the free EU Login should swap in the true HRL 2018-2021 change product and recalibrate for a stronger number." | [NONE] |
| 02:00 | 37:00 | [CELL] 03_change_detection_and_validation.ipynb § "Calibrating a threshold against a proxy independent reference" | "Watch the notebook print the WRONG-threshold flag count next to the calibrated-threshold flag count, side by side, without asserting which one should be larger — that direction depends on the run, not on a guarantee baked into the method." | [RUN CELL] |

Recap: precision 0.065 is the honest cost of a weak proxy reference, not a
failure of the calibration method — and the notebook says so explicitly.
End-state: the printed threshold-comparison line (WRONG vs calibrated flag
counts) is visible alongside the precision/recall/F1 numbers.

---

### Lecture 04.7 — Per-year classifiers and the class-transition matrix

Objective: build a second, independent way to ask "what changed" — a
transition matrix between two per-year classifiers' predictions.

| Duration | Cumulative | VISUAL | AUDIO | Cue |
|----------|------------|--------|-------|-----|
| 02:00 | 39:00 | [CELL] 03_change_detection_and_validation.ipynb § "Per-year classifiers and a class-transition matrix" | "The change score above answers 'how far did the embedding move' — it can't answer 'moved from what, to what.' A transition matrix can. Important caveat before this code runs: label doesn't itself vary by year, WorldCover 2021 is the only labeled epoch here. So 'per-year classifier' does not mean trained against a year-specific ground truth — it means the identical model architecture, fit separately on each year's own embedding distribution, still supervised by that same 2021 label column." | [ZOOM] |
| 02:30 | 41:30 | [CELL] 03_change_detection_and_validation.ipynb § "Per-year classifiers and a class-transition matrix" | "The interesting signal is where clf_2018's prediction and clf_2021's prediction disagree for the same point — something a single continuous change score can never show, because it never assigns a class at all." | [RUN CELL] |
| 02:30 | 44:00 | [SLIDE] 03_change_detection.md #8 | "Here's the transition matrix, and notice the axis labels say predicted, never true. Every cell here comes from two classifier predictions, not from any real 2018-versus-2021 ground-truth transition label — none exists in this dataset. Reading this as observed truth would silently overstate how much is actually validated. Vegetation-to-built transitions dominate among the flagged points — that's the semantically meaningful signal a raw threshold on 1-cosine can't distinguish from noise on its own." | [ZOOM] |

Recap: predicted-class transitions and a continuous change score are two
different, complementary measurements — neither replaces the other.
End-state: the transition-matrix figure is on screen with both axes
labeled "predicted," not "true."

---

### Lecture 04.8 — Comparing the transition mask against the change score

Objective: quantify how much the transition-matrix mask and the continuous
change score actually agree, and explain why partial disagreement is itself
the teaching point.

| Duration | Cumulative | VISUAL | AUDIO | Cue |
|----------|------------|--------|-------|-----|
| 02:30 | 46:30 | [CELL] 03_change_detection_and_validation.ipynb § "Comparing the transition-matrix mask against the continuous change score" | "The pooled table drops the bare class that the change-score table still carries, so these two can't be compared by row position — they're joined on sample_id and region instead, and the notebook asserts that join doesn't silently drop any points." | [RUN CELL] |
| 02:30 | 49:00 | [CELL] 03_change_detection_and_validation.ipynb § "Comparing the transition-matrix mask against the continuous change score" | "Here's the disagreement table for both the WRONG 0.25 threshold and the calibrated threshold, against the transition-matrix mask. They only partly agree, and that disagreement is itself the teaching point: a point can move a lot in embedding space without crossing the vegetation-to-built class boundary — phenology, a dry year — and a point can cross that boundary with only a modest cosine movement if the two classes' embedding centroids are already close. Neither number alone tells the whole story." | [RUN CELL] |

Recap: cosine measures how far the embedding moved; the transition matrix
measures what class it moved between — they agree only partly, by design.
End-state: the disagreement table (transition-mask-only, cosine-only, both)
is visible for both thresholds.

---

### Lecture 04.9 — Validating with spatial- and temporally-grouped CV

Objective: apply grouped cross-validation to the artificialization mask
itself, grouping by both space and year so neither dimension leaks across
the split.

| Duration | Cumulative | VISUAL | AUDIO | Cue |
|----------|------------|--------|-------|-----|
| 02:00 | 51:00 | [CELL] 03_change_detection_and_validation.ipynb § "Validating the artificialization mask: spatially- and temporally-grouped CV" | "artificialized_mask is itself the output of two classifiers — before trusting it, this notebook validates it the same honest way Module 3 validated the land-cover classifier: grouped CV, never a random split. But there's a second trap here Module 3 didn't have: temporal leakage. The pooled 2018-plus-2021 table contains the SAME real-world locations twice, once per year." | [ZOOM] |
| 02:00 | 53:00 | [CELL] 03_change_detection_and_validation.ipynb § "Validating the artificialization mask: spatially- and temporally-grouped CV" | "A random split, or even a spatial split that ignores year, can put a point's 2018 row in the training fold and its 2021 row in the test fold. The model would then partly recognize the site — soil color, terrain, whatever's stable across both years — rather than learn a signal that transfers to genuinely new locations or new years. Group by the thing that must not leak: spatial blocks there, year here." | [RUN CELL] |
| 02:00 | 55:00 | [CELL] 03_change_detection_and_validation.ipynb § "Validating the artificialization mask: spatially- and temporally-grouped CV" | "GroupKFold on spatial blocks, LeaveOneGroupOut on the year label — watch both balanced-accuracy numbers print." | [RUN CELL] |
| 01:00 | 56:00 | [SLIDE] 03_change_detection.md #9 | "The numbers printed are the honest, measured comparison, not an assumed direction. If leave-one-year-out scores lower, that supports year-specific artifacts — Sentinel swath differences, a different phenological state — making the model partly overfit to a year's own signature. If the two land close together, that's reported just as plainly. Either way: grouping by the dimension that must not leak is what makes the number trustworthy at all." | [NONE] |

Recap: validating a change-detection mask needs two separate groupings —
space and year — because both can leak independently.
End-state: the spatiotemporal CV comparison bar chart is on screen with
both scenarios' balanced accuracy visible.

---

### Lecture 04.10 — Provenance and wrap-up

Objective: close the module by restating, one more time, the exact
limitation a student should carry forward: this validates against a proxy,
not the true Copernicus product.

| Duration | Cumulative | VISUAL | AUDIO | Cue |
|----------|------------|--------|-------|-----|
| 01:30 | 57:30 | [CELL] 03_change_detection_and_validation.ipynb § "Provenance" | "Every table this module loaded gets its provenance written out — dataset version, source license, sampling method, label source, validation source — so nothing in this module's conclusions is untraceable back to its source." | [RUN CELL] |
| 01:30 | 59:00 | [CELL] 03_change_detection_and_validation.ipynb § "Wrap-up" | "A cosine-based change score reports how far a point's embedding moved between two years — a real, cheap signal, but not by itself a semantic change decision. Calibrating a threshold against an independent proxy reference turns it into one with a known precision, recall, and F1, unlike an eyeballed cutoff." | [NONE] |
| 01:00 | 60:00 | [SLIDE] 03_change_detection.md #12 | "One limitation, repeated once more for anyone skimming only this section: the true Copernicus HRL Imperviousness change product for 2018-2021 needs a free EU Login the author has not created for this course. Both correction paths in this module — the calibrated threshold and the transition-matrix mask — validate against the best currently-available proxy, and this course says so rather than presenting the proxy as equivalent to the real product." | [NONE] |

Recap: this module's two corrections — a calibrated threshold and a
transition-matrix mask — are both honestly validated against a proxy, and
both stay explicit about that limitation rather than implying otherwise.
End-state: the attribution slide (AlphaEarth CC BY 4.0, Copernicus HRL
Imperviousness) is on screen as the module closes.

Total: 60:00 (syllabus: 60 minutes)

## Pronunciation Notes

Shares pronunciation notes with Module 03 (AlphaEarth, EPSG, precision@k);
no new terms introduced in this module beyond those already covered there.

- AlphaEarth — "AL-fuh urth"
- EPSG — spelled out, "E-P-S-G"

## Key Messages Used

- "1 − cosine measures representation movement" (Lecture 04.3)

## Exercise/Quiz Callback

See assessments/03_change_detection_quiz.md, questions 1-3 and 7 (the
WRONG-conclusion threshold trap and the honest low-precision result), and
assessments/03_change_detection_assignment.md for the hands-on calibration
exercise.

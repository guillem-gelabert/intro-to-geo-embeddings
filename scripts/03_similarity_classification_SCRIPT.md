Module: 03 — similarity_classification
Title: Similarity Search and Classification
Syllabus minutes: 65
Source notebook: notebooks/solutions/02_similarity_and_classification.py
Slide deck: slides/02_similarity_classification.md

---

### Lecture 03.1 — Two regions, one embedding table

Objective: load the frozen Bern and Seville AlphaEarth tables and confirm, by assertion, that every embedding row is unit-norm.

| Duration | Cumulative | VISUAL | AUDIO | Cue |
|----------|------------|--------|-------|-----|
| 01:00 | 01:00 | [SLIDE] 02_similarity_classification.md #1 | "This is the flagship notebook of the course. By the end of today you will have run a similarity search, trained a classifier three different ways, and seen exactly how much a careless validation split lies to you." | [NONE] |
| 01:30 | 02:30 | [CELL] 02_similarity_and_classification.ipynb § "Data" | "Two regions ground this whole notebook: Bern, on the Swiss Plateau, and Seville, in Andalusia — chosen to be geographically and climatically distinct. Everything computed on Bern alone will look great; whether it generalizes to Seville is the question this module keeps coming back to." | [RUN CELL] |
| 01:30 | 04:00 | [CELL] 02_similarity_and_classification.ipynb § "Data" | "This checkpoint cell asserts that both regions have exactly 64 embedding dimensions and unit norm — and it passes. AlphaEarth vectors are unit-norm, so dot product equals cosine. That's an observation this assertion just proved about the data, not an assumption baked into the similarity helper — the helper always divides by the real norms, so it stays correct even for embeddings that are not unit-norm." | [RUN CELL] |
| 01:00 | 05:00 | [SLIDE] 02_similarity_classification.md #2 | "Keep that in mind: dot product and cosine similarity are the same number here, for this specific dataset." | [NONE] |

Recap: both regions are loaded and confirmed unit-norm, which is why the similarity helper's dot product equals cosine similarity for this data.
End-state: the "Both regions confirmed: 64 embedding dimensions, unit norm" checkpoint output is on screen.
Target length: 2:00–7:00 (not a codealong).

---

### Lecture 03.2 — Search by example, and why a threshold lies (codealong)

Objective: run a cosine-similarity search over one region's embedding table, then watch a fixed-threshold conclusion fall apart under a different threshold.

| Duration | Cumulative | VISUAL | AUDIO | Cue |
|----------|------------|--------|-------|-----|
| 02:00 | 07:00 | [CELL] 02_similarity_and_classification.ipynb § "Similarity 1: Search by example" | "Pick a single query point in Bern and rank every other point in the region by cosine similarity to it. No training, no labels needed at query time — just 'find me more of this.' We compute the dot product against every other embedding, and because we just proved these vectors are unit-norm, that dot product is the cosine similarity directly." | [RUN CELL] |
| 02:00 | 09:00 | [CELL] 02_similarity_and_classification.ipynb § "Similarity 1: Search by example" | "Here's the top-10 map and the similarity histogram. Most of the mass sits well below 1.0, with a tail above 0.90 we're about to probe — and here's the trap cell: watch what happens if we assume similarity above 0.90 means same land cover." | [RUN CELL] |
| 02:00 | 11:00 | [CELL] 02_similarity_and_classification.ipynb § "Why this is wrong" | "The 0.90 cutoff is arbitrary — nothing about the embedding's geometry singles it out as a meaningful boundary. Pick 0.85 or 0.95 instead and the apparent agreement rate changes, even though nothing about the underlying data changed. A fixed threshold answers 'how many points cross an arbitrary line,' not 'how good is this query.'" | [ZOOM] |
| 02:00 | 13:00 | [SLIDE] 02_similarity_classification.md #3 | "Ranking, plus precision at k, is the honest alternative — it asks how good the top-K matches are, which is exactly the question a search-by-example workflow needs answered." | [NONE] |

Recap: cosine similarity ranks candidates well; a fixed threshold like 0.90 is an arbitrary line that changes the story if you move it.
End-state: the similarity histogram and the "Why this is wrong" markdown cell are both visible.
Target length: 2:00–12:00 (codealong).

---

### Lecture 03.3 — Prototype queries

Objective: define a class by averaging labeled examples into a prototype vector instead of hand-picking one query point.

| Duration | Cumulative | VISUAL | AUDIO | Cue |
|----------|------------|--------|-------|-----|
| 02:30 | 15:30 | [CELL] 02_similarity_and_classification.ipynb § "Similarity 2: Prototype queries" | "Instead of one query point, average the embeddings of several labeled examples into a single prototype vector, then rank the whole region against that prototype. This is more robust than a single point because it's less sensitive to any one sample's noise." | [RUN CELL] |
| 02:30 | 18:00 | [CELL] 02_similarity_and_classification.ipynb § "Similarity 2: Prototype queries" | "Notice the ranked results now cluster around the prototype's class, not around one arbitrary example — this is the pattern you'll reuse for the assignment's own prototype query." | [RUN CELL] |

Recap: a prototype vector, built from several labeled examples, is a more robust query than any single point.
End-state: the prototype-ranked results table is on screen.
Target length: 2:00–7:00 (not a codealong).

---

### Lecture 03.4 — Positive-minus-negative prototype (optional)

Objective: build a directional prototype from positive and negative examples to isolate what one class has that another does not.

| Duration | Cumulative | VISUAL | AUDIO | Cue |
|----------|------------|--------|-------|-----|
| 02:00 | 20:00 | [CELL] 02_similarity_and_classification.ipynb § "Similarity 3: Positive-minus-negative prototype (optional)" | "This one is optional, but worth showing: subtract a negative-example prototype from a positive-example prototype, and you get a directional vector — 'more like this, less like that' — rather than a single class centroid." | [RUN CELL] |
| 02:00 | 22:00 | [CELL] 02_similarity_and_classification.ipynb § "Similarity 3: Positive-minus-negative prototype (optional)" | "Ranking by similarity to this difference vector surfaces points that lean toward the positive class and away from the negative one — a technique worth knowing even though we won't lean on it for the rest of the module." | [RUN CELL] |

Recap: a positive-minus-negative prototype captures direction, not just class membership.
End-state: the difference-vector ranked results are visible.
Target length: 2:00–7:00 (not a codealong).

---

### Lecture 03.5 — Classification: the random-split trap

Objective: train two classifiers on a random train/test split of Bern and see an accuracy number that looks convincing but has not yet been tested honestly.

| Duration | Cumulative | VISUAL | AUDIO | Cue |
|----------|------------|--------|-------|-----|
| 02:00 | 24:00 | [CELL] 02_similarity_and_classification.ipynb § "Classification: the random-split trap" | "Search-by-example needs no labels. A classifier does — and once labels are in play, how you split the data into train and test sets stops being a formality and becomes the single most consequential methodological choice in this notebook. We drop the sparse 'bare' class and keep built, crop, vegetation, and water — a stated, deliberate filter, not a silent one." | [RUN CELL] |
| 02:00 | 26:00 | [CELL] 02_similarity_and_classification.ipynb § "Classification: the random-split trap" | "We train a logistic regression and a random forest on a plain 70/30 random split of Bern. Look at these balanced-accuracy numbers — they look great. That's exactly the trap: a random split lets points that are metres apart land on opposite sides of train and test." | [RUN CELL] |
| 02:00 | 28:00 | [SLIDE] 02_similarity_classification.md #5 | "Hold onto this random-split number. We're about to test it two different, more honest ways." | [NONE] |

Recap: a random split reports an optimistic accuracy because nearby points leak between train and test.
End-state: the random-split confusion matrix, titled "looks great, proves little," is on screen.
Target length: 2:00–7:00 (not a codealong).

---

### Lecture 03.6 — Spatial CV: project first, then grid

Objective: reproject to a metre-based CRS, build spatial blocks, and re-run the same classifiers with grouped cross-validation.

| Duration | Cumulative | VISUAL | AUDIO | Cue |
|----------|------------|--------|-------|-----|
| 02:30 | 30:30 | [CELL] 02_similarity_and_classification.ipynb § "Spatial CV: project first, then grid" | "AlphaEarth embeddings make the leakage problem worse, not better, than raw pixels — a full year of spatial and temporal context is baked into every embedding, so neighbouring points are more similar than raw spectra would be. `make_blocks` refuses a geographic CRS outright, so we reproject Bern to E-P-S-G twenty fifty-six, Swiss LV95, a metre-based projection, before gridding — never the other way around." | [RUN CELL] |
| 02:30 | 33:00 | [CELL] 02_similarity_and_classification.ipynb § "Spatial CV: project first, then grid" | "Same models, same data, but now grouped by spatial block with GroupKFold instead of a random shuffle. Measured so far: the random-split and spatial-block numbers sit within a few points of each other, not tens of points apart. That gap is real and worth teaching, but it is not yet the dramatic effect we're building toward." | [RUN CELL] |

Recap: in-region spatial-block CV costs almost nothing on this data compared to the random split.
End-state: the printed BLOCK CV balanced-accuracy line, alongside the random-split number, is on screen.
Target length: 2:00–7:00 (not a codealong).

---

### Lecture 03.7 — Leave-region-out: the dramatic, honest gap (codealong)

Objective: train on Bern only, predict Seville only, and read the honest, generalization-relevant accuracy gap that a random split hides.

| Duration | Cumulative | VISUAL | AUDIO | Cue |
|----------|------------|--------|-------|-----|
| 03:00 | 36:00 | [CELL] 02_similarity_and_classification.ipynb § "Leave-region-out: the dramatic, honest gap" | "Now the real test: train on Bern only, predict Seville only — a climatically and geographically distinct region the model never saw. Same `spatial_cv_report` call shape as the block CV, just swapping in region labels and LeaveOneGroupOut, because the helper is genuinely generic, not two different code paths dressed up to look similar." | [RUN CELL] |
| 04:00 | 40:00 | [CELL] 02_similarity_and_classification.ipynb § "Leave-region-out: the dramatic, honest gap" | "Here is the headline result. Leave-region-out costs 17-19 points of balanced accuracy for both logistic regression and random forest, trained on Bern and evaluated on Seville — a large, double-digit drop. In-region spatial blocking, by contrast, costs almost nothing on this data. Leave-region-out is the primary evidence that a random split lies here; the in-region block-versus-random comparison is a real, smaller, second lesson about interpolation versus extrapolation, not the dramatic effect." | [RUN CELL] |
| 03:00 | 43:00 | [CELL] 02_similarity_and_classification.ipynb § "Leave-region-out: the dramatic, honest gap" | "This bar chart puts all three numbers side by side: random split, spatial-block CV, leave-region-out. The story is in the height of that third bar relative to the first two." | [RUN CELL] |
| 02:00 | 45:00 | [CELL] 02_similarity_and_classification.ipynb § "Leave-region-out: the dramatic, honest gap" | "And here's where those errors land geographically in Seville — a model that looks excellent on Bern alone loses a large fraction of its accuracy the moment it has to extrapolate to a different climate and land-cover mix." | [RUN CELL] |

Recap: leave-region-out costs 17-19 balanced-accuracy points on this data, while in-region spatial blocking costs almost nothing — the random split hides exactly the gap that matters for generalization.
End-state: the three-scenario bar chart and the Seville error map are both visible.
Target length: 2:00–12:00 (codealong).

---

### Lecture 03.8 — Baseline: the identical pipeline on raw Sentinel-2 bands

Objective: re-run the identical classification pipeline on raw Sentinel-2 reflectance bands to isolate representation as the only variable that changed.

| Duration | Cumulative | VISUAL | AUDIO | Cue |
|----------|------------|--------|-------|-----|
| 03:00 | 48:00 | [CELL] 02_similarity_and_classification.ipynb § "Baseline: the identical pipeline on raw Sentinel-2 bands" | "Everything above ran on 64-dimensional AlphaEarth embeddings. Now we re-run the identical pipeline — same classifiers, same split, same block CV, same leave-region-out — on the frozen table's raw Sentinel-2 reflectance bands, changing nothing except the feature matrix. This isolates the feature representation as the only variable." | [RUN CELL] |
| 04:00 | 52:00 | [CELL] 02_similarity_and_classification.ipynb § "Baseline: the identical pipeline on raw Sentinel-2 bands" | "The table reports what this run actually measured, not an assumed direction. On this sample, the Sentinel-2 raw-band baseline did not show a larger in-region block-CV gap than the embeddings did — so we can't claim embeddings are more leakage-resistant here; we simply report the number as measured. Either way, the leave-region-out gap, for both feature representations, remains the larger, more consequential effect in this notebook." | [RUN CELL] |

Recap: swapping in raw Sentinel-2 bands, with every other step held identical, tests but does not confirm the leakage-resistance hypothesis on this sample — the honest number is the lesson.
End-state: the AlphaEarth-vs-Sentinel-2 comparison table is on screen.
Target length: 2:00–7:00 (not a codealong).

---

### Lecture 03.9 — Provenance

Objective: trace every number and figure in this module back to its dataset version, CRS, label source, and license.

| Duration | Cumulative | VISUAL | AUDIO | Cue |
|----------|------------|--------|-------|-----|
| 01:30 | 53:30 | [CELL] 02_similarity_and_classification.ipynb § "Provenance" | "Every table you saw today was loaded once, with its provenance recorded automatically — dataset version, CRS, label source, license. `build_provenance` and `write_provenance` summarize that here; nothing in this record is hand-typed." | [RUN CELL] |
| 01:30 | 55:00 | [CELL] 02_similarity_and_classification.ipynb § "Provenance" | "This JSON is the single source of truth for 'what exactly did this run use' — the same discipline you'll see again in the capstone." | [RUN CELL] |

Recap: provenance for every table used in this module is recorded automatically, not hand-typed.
End-state: the printed provenance JSON is on screen.
Target length: 2:00–7:00 (not a codealong).

Note: this lecture runs 3:00, below the template's 2:00 floor guidance for richness but still within the 2:00–7:00 allowed range.

---

### Lecture 03.10 — Wrap-up

Objective: recap the module's five takeaways and connect them to the quiz and assignment.

| Duration | Cumulative | VISUAL | AUDIO | Cue |
|----------|------------|--------|-------|-----|
| 02:30 | 57:30 | [CELL] 02_similarity_and_classification.ipynb § "Wrap-up" | "Cosine similarity search over AlphaEarth's 64-dimensional embedding finds visually and semantically similar locations without any training loop. Prototype queries let you define a class by example rather than by hand-picking a threshold. A classifier trained and evaluated with a random split reports an accuracy that a spatial-block or leave-region-out split shows is optimistic — the gap is small in-region here but large across regions." | [RUN CELL] |
| 02:30 | 1:00:00 | [CELL] 02_similarity_and_classification.ipynb § "Wrap-up" | "The honest, leave-region-out estimate is the number that predicts how the classifier will actually perform somewhere it has not seen. Before you move on, work through the quiz in assessments/02_similarity_classification_quiz.md and the assignment in assessments/02_similarity_classification_assignment.md — both test exactly this random-split-versus-leave-region-out distinction, not terminology." | [RUN CELL] |

Recap: search, prototypes, and honest validation are the three tools this module hands you; the quiz and assignment test the validation trap specifically.
End-state: the "Takeaways" and "What's next" markdown cell is on screen.
Target length: 2:00–7:00 (not a codealong).

---

### Lecture 03.11 — Appendix: Path A (illustrative only)

Objective: show the Earth Engine code path for reference without executing it.

| Duration | Cumulative | VISUAL | AUDIO | Cue |
|----------|------------|--------|-------|-----|
| 02:00 | 1:02:00 | [CELL] 02_similarity_and_classification.ipynb § "Appendix: Path A (Earth Engine) -- illustrative only, not executed" | "This appendix shows what the equivalent Earth Engine access code looks like, for reference — it is illustrative only. We are not running it in this recording; everything you saw today came from the frozen, credential-free tables." | [ZOOM] |
| 02:00 | 1:04:00 | [CELL] 02_similarity_and_classification.ipynb § "Appendix: Path A (Earth Engine) -- illustrative only, not executed" | "If you do have an Earth Engine project configured, this is the shape of the call you'd make instead of `course.data.load` — same schema, same downstream code." | [ZOOM] |
| 01:00 | 1:05:00 | [SLIDE] 02_similarity_classification.md #6 | "That's Module 3. Next up: change detection." | [NONE] |

Recap: Path A is shown for completeness only; nothing in this appendix was executed on screen.
End-state: the appendix markdown cell, not a running Earth Engine call, is the last frame.
Target length: 2:00–7:00 (not a codealong).

---

Total: 65:00 (syllabus: 65 minutes)

## Pronunciation Notes

- AlphaEarth — "AL-fuh urth"
- precision@k — "precision at k"
- EPSG — spelled out, "E-P-S-G"
- EPSG:2056 — "E-P-S-G twenty fifty-six"
- balanced accuracy — "balanced accuracy" (not "accuracy")
- GroupKFold — "Group K-Fold"
- LeaveOneGroupOut — "Leave One Group Out"

## Key Messages Used

- "AlphaEarth vectors are unit-norm, so dot product equals cosine" (Lecture 03.1)
- "17-19 points" (Lecture 03.7, leave-region-out cost)

## Exercise/Quiz Callback

See assessments/02_similarity_classification_quiz.md and
assessments/02_similarity_classification_assignment.md (Lecture 03.10),
both testing the random-split-versus-leave-region-out distinction.

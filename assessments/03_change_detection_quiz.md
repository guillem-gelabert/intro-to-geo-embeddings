# Module 4 Quiz: Change Detection and Validation

This quiz tests conceptual errors, not terminology. Every option below is
explained by quoting the specific cell, heading, or Takeaway in
`notebooks/solutions/03_change_detection_and_validation.py` that
demonstrates the correct reasoning.

---

#### Q1. In the notebook, `change_score > 0.25` is used to flag points as
"artificialized." What is wrong with this specific threshold?

- A) 0.25 is too low a value; it should be closer to 1.0.
  **Incorrect.** The cell is explicitly tagged `wrong-conclusion` and
  headed "The WRONG conclusion" — the problem is not the numeric value
  chosen, it is that any unvalidated cutoff picked by eye is being
  treated as a semantic-change decision. Raising the number would not
  fix that.
- B) A fixed, eyeballed threshold has no precision/recall/F1 behind it,
  so a large change score means the *representation* moved, not that
  the *land cover* changed.
  **Correct.** The "Why this is wrong" section states directly: "A large
  change score means the *representation* moved; it does not by itself
  mean the *land cover* changed, let alone that it became
  'artificialized' specifically. Treating an unvalidated cutoff as a
  semantic-change decision is Pitfall 5 of this course."
- C) `1 - cosine_similarity` cannot be computed for embeddings from
  different years.
  **Incorrect.** The notebook computes exactly this ("Change score:
  `1 - cosine_similarity` per point" section) — the computation itself is
  fine; the trap is in how the number is interpreted afterward.
- D) The threshold should be calculated separately for Bern and Seville.
  **Incorrect.** The notebook's fix is calibration against a labeled
  reference (`precision_recall_curve`), not regional re-splitting of the
  same unvalidated eyeball cutoff — see "Calibrating a threshold against
  a proxy independent reference."

---

#### Q2. What does calibrating the threshold with
`precision_recall_curve` on the `controls` table actually buy you, that
the 0.25 cutoff did not have?

- A) A threshold with a known precision, recall, and F1 measured against
  a labeled reference, so you know how much to trust a flag it produces.
  **Correct.** The Takeaway after the calibration cells states: "the
  calibrated threshold above is not just 'a different number' than 0.25
  -- it comes with a precision, a recall, and an F1 score measured
  against a labeled reference, so you know how much to trust a flag it
  produces. The 0.25 threshold ... came with none of that."
- B) Proof that the calibrated threshold is the true HRL Imperviousness
  Change 2018-2021 product.
  **Incorrect.** The same section states the proxy "is weaker than a
  real two-epoch change product" and that "the true Copernicus HRL
  Imperviousness Change 2018-2021 product would be the right reference
  here -- but it requires a free EU Login the author has not created."
- C) A guarantee that the calibrated threshold will flag fewer points
  than 0.25 did.
  **Incorrect.** The notebook prints both counts side by side ("WRONG
  threshold ... flagged" vs "calibrated threshold ... flagged") without
  asserting a direction; which one flags more depends on the run, not on
  a guarantee.
- D) A way to avoid needing any independent reference at all.
  **Incorrect.** Calibration requires the `controls` table built from
  `known_change`/`known_unchanged` — an independent reference is exactly
  what makes calibration possible, not what it avoids.

---

#### Q3. A point's change score is large. What can you conclude?

- A) The point's embedding moved a large distance between the two years
  in representation space -- nothing more, without further validation.
  **Correct.** "Why this is wrong" is explicit: cosine "collapses the
  full 64-dimensional embedding into one number" and reports movement
  only; per the Module wrap-up Takeaway, "A cosine-based change score
  reports how far a point's embedding moved between two years -- a real,
  cheap signal, but not by itself a semantic change decision."
- B) The land cover at that point definitely changed.
  **Incorrect.** Same Takeaway: reports of movement are "not by itself a
  semantic change decision" — the notebook explicitly lists non-change
  causes ("harvest cycles, a drought year, early snow cover, or a
  swath-boundary artifact") that can move a score just as much as real
  change.
- C) The point was necessarily artificialized (became built).
  **Incorrect.** The wrong-conclusion cell is the demonstration of
  exactly this error — asserting "artificialized" from the raw score
  alone is the deliberate trap the notebook exists to correct.
- D) The classifier's prediction for that point is unreliable.
  **Incorrect.** Change score and classifier confidence are two
  different, separately-computed signals in this notebook; a large
  change score says nothing about classifier confidence on its own.

---

#### Q4. The notebook validates its calibrated threshold against a
"proxy" reference built from `imd_2018` and `label` rather than the true
Copernicus HRL Imperviousness Change 2018-2021 product. Why is this proxy
explicitly described as weaker than a true two-epoch change product?

- A) Because `label` is a single 2021 snapshot, not a genuine
  2018-vs-2021 label pair, so "known_change" really means "was clearly
  non-built in 2018 and is built in the one epoch we have a label for" —
  consistent with a transition, but not directly observed as one.
  **Correct.** Quoted verbatim from "Calibrating a threshold against a
  proxy independent reference": "This proxy is weaker than a real
  two-epoch change product for a specific reason: `label` is a single
  2021 snapshot, not a genuine 2018-vs-2021 label pair."
- B) Because `imd_2018` values are unreliable measurements.
  **Incorrect.** The notebook never questions `imd_2018`'s measurement
  quality; the stated weakness is about the label's single-epoch nature,
  not measurement error.
- C) Because the proxy only covers the Bern study area.
  **Incorrect.** `known_change`/`known_unchanged` are computed on
  `change_df`, which is built from both `bern` and `seville` in the
  "Change score" section above.
- D) Because the frozen tables do not contain enough rows to calibrate a
  threshold.
  **Incorrect.** The notebook prints "controls: N/M rows kept" and
  proceeds with calibration; row count is never cited as the limitation.

---

#### Q5. The transition matrix built from `clf_2018` and `clf_2021`
labels its axes "predicted 2018 class" / "predicted 2021 class," never
"true." Why does this distinction matter?

- A) Because every cell in the matrix comes from two classifier
  predictions, not from any 2018-vs-2021 ground-truth transition label —
  reading it as observed truth would silently overstate how much is
  actually validated.
  **Correct.** Quoted verbatim: "Why the axis labels say 'predicted,'
  never 'true': every cell in this matrix comes from two classifier
  predictions, not from any 2018-vs-2021 ground-truth transition label
  (none exists in this dataset). Reading it as observed truth would
  silently overstate how much is actually validated here."
- B) Because the classifiers were trained on unlabeled data.
  **Incorrect.** Both `clf_2018` and `clf_2021` are `LogisticRegression`
  fit on the pooled 2021 `label` column — supervised training, just
  applied to each year's own embedding distribution.
- C) Because "predicted" and "true" mean the same thing in this context.
  **Incorrect.** The whole point of the caveat is that they do not mean
  the same thing here — no 2018-2021 ground-truth transition label
  exists in this dataset.
- D) Because the matplotlib `ConfusionMatrixDisplay` widget cannot render
  a "true" axis label.
  **Incorrect.** This is a labeling/interpretation choice made
  deliberately in the code, not a plotting-library limitation.

---

#### Q6. Why does validating the artificialization mask require grouping
by year (`LeaveOneGroupOut` on `year_array`) in addition to grouping by
spatial block?

- A) Because the pooled 2018+2021 table contains the SAME real-world
  locations twice, and a split that ignores year could let a point's
  2018 row train the model that then predicts its own 2021 row —
  "recognising the site" rather than learning a transferable signal.
  **Correct.** Quoted from "Validating the artificialization mask":
  "The pooled 2018+2021 table contains the SAME real-world locations
  twice (once per year). A random split -- or even a spatial split that
  ignores year -- can put a point's 2018 row in the training fold and
  its 2021 row in the test fold. The model would then partly 'recognise
  the site' ... rather than learn a signal that transfers."
- B) Because `GroupKFold` cannot be used with fewer than 10 splits.
  **Incorrect.** The notebook uses `GroupKFold(n_splits=5, ...)` for the
  spatial-block validation; split count is not the reason year-grouping
  is needed.
- C) Because 2018 and 2021 use different embedding dimensionalities.
  **Incorrect.** Both years use the same 64-D AlphaEarth embeddings;
  `X_pooled_all` is a single matrix built from both years identically.
- D) Because spatial blocks and years are mathematically the same
  grouping variable.
  **Incorrect.** The notebook explicitly treats them as two distinct
  things that must each independently not leak: "grouping by TWO
  different things that must not leak across a CV split: space ... and
  year."

---

#### Q7. The notebook reports the calibrated detector's measured
precision and F1 against the proxy reference honestly, even when those
numbers are weak (e.g., a low precision/F1 rather than a strong one).
What is the correct takeaway from a weak measured score here?

- A) The weak number invalidates calibration entirely, so the 0.25
  eyeballed threshold should be trusted instead.
  **Incorrect.** The wrap-up Takeaway is unambiguous that the calibrated
  path, even with a modest score, "comes with a precision, a recall, and
  an F1 score measured against a labeled reference" while the 0.25
  threshold "came with none of that" — a known-weak number is still more
  trustworthy than an unmeasured one.
- B) A weak, honestly-measured score reflects a weak reference (a
  single-year label snapshot standing in for a true two-epoch change
  product), not necessarily a failure of the calibration method itself.
  **Correct.** This is the notebook's own framing: the proxy "is weaker
  than a real two-epoch change product" by construction (Q4), so a
  modest precision/F1 against it is an honest reflection of the proxy's
  own limits, exactly the point the "proxy" section and its Takeaway make
  — swap in the true HRL product and recalibrate for a stronger number.
- C) A weak score means the change-score computation itself
  (`1 - cosine_similarity`) is implemented incorrectly.
  **Incorrect.** The `checkpoint`-tagged cells validate the computation
  elsewhere in the course (e.g., Module 3's unit-norm assertion); a weak
  precision/F1 here is about reference quality, not arithmetic
  correctness.
- D) Weak calibration numbers should be omitted from the notebook so
  students only see favorable results.
  **Incorrect.** The notebook's whole design — printing both threshold
  counts, both CV scenarios, and stating the proxy's weakness explicitly
  — is built around reporting honestly measured numbers rather than
  curating only favorable ones.

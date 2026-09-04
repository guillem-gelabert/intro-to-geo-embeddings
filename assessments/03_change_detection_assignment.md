# Assignment: Change Detection and Validation (Module 4)

**Weight: 20% of course grade.**

Published module weights: similarity/classification 15%, change detection 20%, ecosystems 20%, portability 10%.

## Instructions

1. Open your derived exercise notebook,
   `notebooks/exercises/03_change_detection_and_validation.ipynb`, and
   complete every cell marked `# TODO:` with
   `raise NotImplementedError(...)`.
2. Reproduce the 2018-vs-2021 change score for both study areas
   (`bern`, `seville`), including the WRONG-conclusion cell run
   verbatim (do not delete or edit the 0.25 threshold demonstration —
   the pedagogy requires it to run and print its flagged-point counts).
3. Calibrate your own threshold using `precision_recall_curve` against
   the `controls` proxy reference, exactly as the solution notebook
   does, and report the resulting precision, recall, and F1.
4. Build the per-year classifiers and the class-transition matrix, and
   compute the disagreement table between the transition-matrix mask and
   the calibrated cosine threshold.

## What to Submit

- Your completed exercise notebook (`.ipynb`, with outputs), executed
  top to bottom without errors.
- A precision/recall/F1 table comparing the WRONG (0.25) threshold
  against your calibrated threshold, on the `controls` proxy reference.
- The class-transition matrix figure (axes labeled "predicted," never
  "true," matching the solution notebook's convention).
- 3-5 sentences stating: (a) your calibrated threshold value, (b) whether
  it flags more or fewer points than the 0.25 threshold, and (c) why the
  proxy reference used here (a single 2021 label snapshot) is weaker than
  a true two-epoch change product would be.

## Rubric

| Criterion | What earns full marks |
|---|---|
| WRONG-conclusion cell present and run | The 0.25-threshold cell executes verbatim and its flagged-point counts are visible in the submission. |
| Calibration correctness | Threshold is selected via `precision_recall_curve`/max-F1 on the `controls` table, not by eye; precision/recall/F1 are reported as numbers, not adjectives. |
| Transition matrix and disagreement table | Both are produced with the axis-labeling convention ("predicted," not "true") and the disagreement table between the mask and the calibrated cosine flag is reported. |
| Proxy-reference limitation stated (graded, not aspirational) | Submission names the specific weakness (single-year label snapshot, not a genuine two-epoch pair) rather than asserting the proxy is equivalent to the true HRL product — "the model works well" is not gradable; "reports precision X, recall Y, F1 Z against a proxy reference known to understate a true two-epoch product, because label is a single 2021 snapshot" is. |

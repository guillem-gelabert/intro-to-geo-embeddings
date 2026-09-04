# Assignment: Similarity and Classification (Module 3)

**Weight: 15% of course grade.**

Published module weights: similarity/classification 15%, change detection 20%, ecosystems 20%, portability 10%.

## Instructions

1. Open your derived exercise notebook,
   `notebooks/exercises/02_similarity_and_classification.ipynb` (produced
   in the exercise-derivation step of this phase), and complete every
   cell marked `# TODO:` with `raise NotImplementedError(...)`.
2. In the "Similarity 1: Search by example" section, pick one query point
   of your own choosing from the bundled candidate polygons (not
   necessarily the default query used in the solution notebook) and run
   the search-by-example ranking against it.
3. Complete the "Classification: the random-split trap" and "Spatial CV:
   project first, then grid" sections on the same frozen AlphaEarth data,
   reproducing both the random-split classifier score and the
   spatial-block-CV score.
4. Do not skip the `wrong-conclusion`-tagged cell — it must run and print
   its output, not be deleted or commented out.

## What to Submit

- Your completed exercise notebook (`.ipynb`, with outputs), executed
  top to bottom without errors (`jupyter execute` or an equivalent
  interactive run).
- The comparison bar chart showing random-split accuracy vs
  spatial-block-CV accuracy for your chosen query/classifier run
  (the figure produced by the "Spatial CV" section, saved under
  `figures/`).
- 3-5 sentences interpreting the random-vs-spatial-CV gap: state which
  score is higher, by roughly how much, and explain in your own words why
  a random split overstates performance relative to the spatial-block
  split on this data.

## Rubric

| Criterion | What earns full marks |
|---|---|
| Search-by-example correctness | The ranked similarity table is produced for your chosen query point and the top-ranked results are plausible under visual/label inspection. |
| Random-split vs spatial-CV reproduction | Both accuracy numbers are computed with the exact helper calls from the solution notebook (`GroupKFold`/plain split), not a hand-rolled alternative. |
| Gap interpretation (graded, not aspirational) | Submission states the numeric direction and size of the gap and explains it in terms of spatial autocorrelation/leakage — "shows good understanding" is not gradable; "reports balanced accuracy under both splits and states which score is inflated by nearby train/test points" is. |
| Wrong-conclusion cell present and run | The `wrong-conclusion`-tagged cell executes and its printed output is visible in the submitted notebook. |

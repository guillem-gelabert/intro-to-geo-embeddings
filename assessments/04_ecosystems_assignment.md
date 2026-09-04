# Assignment: Embedding Ecosystems and Portability (Module 5)

**Weight: 20% for the core exercise, plus a separate 10% portability
component** (running the same operation on both TESSERA and Clay and
comparing norms and behavior). These are stated as two separate figures
and are never merged into one number.

Published module weights: similarity/classification 15%, change detection 20%, ecosystems 20%, portability 10%.

## Instructions

**Core exercise (20%):**

1. Open your derived exercise notebook,
   `notebooks/exercises/04_embedding_ecosystems.ipynb`, and complete
   every cell marked `# TODO:` with `raise NotImplementedError(...)`.
2. Run the TESSERA section (`geotessera`, pinned
   `dataset_version="v1.1"`, `dataset_variant="cambridge"`), falling back
   to the bundled fixture if the live path or the optional `providers`
   extra is unavailable — either path is acceptable, as long as the
   source actually used is printed (`tessera_source`).
3. Compute `norm_diagnostics` on the TESSERA vectors and report the
   result as a printed diagnostic, not a hard assertion (matching the
   solution notebook's treatment of an undocumented provider property).

**Portability component (10%, separate from the core exercise):**

4. Run the Clay section (DuckDB over the LGND GeoParquet corpus,
   `geohash_l2=u0`) or its bundled fixture fallback, and compute its own
   `norm_diagnostics`.
5. Compare TESSERA's and Clay's norm diagnostics and similarity behavior
   side by side, and state explicitly that the raw similarity numbers
   from TESSERA (128-D), Clay (1024-D), and AlphaEarth (64-D) are not
   directly comparable to one another without a shared projection.

## What to Submit

- Your completed exercise notebook (`.ipynb`, with outputs), executed
  top to bottom without errors.
- A table of `norm_diagnostics` output for both TESSERA and Clay vectors
  (mean, n, and any other fields the helper reports), with the source
  used for each (live call or fixture) printed alongside.
- 3-5 sentences for the portability component specifically: what each
  provider's norm diagnostic showed, whether it was close to unit norm,
  and confirmation that you did not assume unit-norm behavior for either
  provider before checking.

## Rubric

| Criterion | Weight | What earns full marks |
|---|---|---|
| Core exercise: TESSERA section and norm check | 20% | TESSERA vectors are obtained (live or fixture) and `norm_diagnostics` is computed and printed as a report, not a hard assert; source used is stated explicitly. |
| Portability: Clay comparison | 10% | Clay vectors are obtained (live or fixture), `norm_diagnostics` is computed for Clay independently of TESSERA, and the two are compared side by side without conflating their numbers with AlphaEarth's. |
| Non-comparability statement (graded, not aspirational) | Included in the 10% above | Submission states plainly that TESSERA/Clay/AlphaEarth similarity scores are not directly comparable without a shared projection — "the embeddings are similar across providers" is not gradable; "TESSERA (128-D) and Clay (1024-D) norm means were X and Y respectively; neither is compared numerically to AlphaEarth's 64-D cosine scores because no shared projection exists between them" is. |
| Graceful degradation | Both figures above | Submission runs to completion whether or not the optional `providers` extras or `LGND_TOKEN` are present, using the documented fixture fallback rather than failing the notebook. |

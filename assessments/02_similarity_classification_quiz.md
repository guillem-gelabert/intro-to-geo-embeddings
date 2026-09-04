# Module 3 Quiz: Similarity Search and Classification

Conceptual-error quiz for `02_similarity_and_classification.ipynb`, the flagship module. Every
option's explanation names the specific notebook cell/heading/Takeaway that proves it.

---

#### Q1. The notebook computes similarity as a plain dot product between AlphaEarth vectors, without dividing by their norms. Why is this valid here specifically?

- A. Dot product always equals cosine similarity, for any embedding provider.
  *Incorrect — this is only true when vectors are unit-norm, a property of AlphaEarth verified in this notebook and in `01_alphaearth_access_visualize.ipynb`'s "Unit-norm check," not a universal fact about all embeddings (Clay's 1024-D vectors in Module 1's quiz are not asserted to be unit-norm the same way).*
- B. Because every AlphaEarth vector used here is already unit-norm, so dividing by norms (both equal to 1) is a no-op — the notebook's own Takeaway states dot product equals cosine similarity here specifically because of this property.
  *Correct — the Data section's Takeaway states directly: "dot product equals cosine similarity here because every [AlphaEarth vector is unit-norm]," matching the "Unit-norm check" verified in Module 2's access notebook.*
- C. Because the classifier results are the same either way, so the distinction doesn't matter.
  *Incorrect — the notebook never justifies the dot-product shortcut by classifier outcomes; it justifies it by the geometric fact of unit-norm vectors, stated in the Data section's Takeaway.*
- D. Because cosine similarity cannot be computed on embeddings with more than 32 dimensions.
  *Incorrect — there is no such dimensionality restriction anywhere in the notebook or the underlying math; cosine similarity is well-defined for any dimensionality.*

---

#### Q2. **Spot the leakage.** A colleague proposes: "I'll take all points from both Bern and Seville, shuffle them together, and do a random 70/30 train/test split (`train_test_split` with `stratify` on label)." Is this split valid for estimating how well the classifier will generalize to a genuinely new region it has not seen?

- A. Yes — as long as the split is stratified by label, it doesn't matter how the points are distributed spatially.
  *Incorrect — this describes exactly the "Classification: the random-split trap" section's `train_test_split(..., stratify=y_bern)` call, which the notebook explicitly labels a "TRAP ACCURACY" in its printed output and whose confusion-matrix figure is titled "looks great, proves little."*
- B. No — a random split lets spatially adjacent points land on opposite sides of train/test, and if both regions are mixed into one random split, that is a *worse* version of the same leakage the "Spatial CV" section warns about, not a genuine test of cross-region generalization.
  *Correct — the "Spatial CV: project first, then grid" section states plainly: "A random split lets adjacent points — potentially metres apart — land on opposite sides of train/test," and the notebook's own "Classification: the random-split trap" section demonstrates and labels this exact random-split pattern as a trap.*
- C. Yes, because AlphaEarth embeddings are annual composites and therefore immune to spatial leakage.
  *Incorrect — the "Spatial CV" section states the opposite: annual embeddings make leakage "worse than raw pixels, not better: a full year of spatial/temporal context is baked into every embedding, so neighbouring points are *more* similar than raw spectra would be."*
- D. No, but only because Bern and Seville use different coordinate reference systems.
  *Incorrect — this identifies a real but separate technical detail (Bern is reprojected to EPSG:2056 for block gridding); it is not the reason the random split is invalid for generalization testing, which is about spatial adjacency leakage regardless of CRS.*

---

#### Q3. **Spot the leakage.** Another colleague proposes: "I'll use `GroupKFold` with `groups` set to spatial blocks computed within Bern only (never mixing regions), to estimate generalization." Compared to leave-region-out (train Bern, predict Seville), what does this in-region spatial-block CV actually measure, and is it the dramatic gap the module highlights?

- A. It measures the same thing as leave-region-out, and the notebook shows an equally large accuracy drop from both approaches.
  *Incorrect — the "Leave-region-out" section states in-region spatial-block CV "showed only a 1-4 point gap above," in explicit contrast to the double-digit balanced-accuracy drop from leave-region-out, so the two are not equivalent.*
- B. In-region spatial-block CV measures interpolation within a region already seen during training (a smaller, real effect, ~1-4 points here); it is not the dramatic gap — leave-region-out (extrapolating to a climatically distinct, unseen region) is explicitly called "the primary evidence that a random split lies here."
  *Correct — the "Leave-region-out" section states directly: "In-region spatial-block CV, by contrast, showed only a 1-4 point gap above. **Leave-region-out is the primary evidence that a random split lies here**," and separately: "the in-region block-vs-random comparison is a real, smaller, second lesson about interpolation vs. extrapolation, not the dramatic effect."*
- C. In-region spatial-block CV is invalid and should never be used; only leave-region-out is a legitimate spatial validation strategy.
  *Incorrect — the notebook presents in-region block CV as a valid, real lesson worth teaching in its own right ("worth teaching in its own right" per the final Takeaway), just one with a much smaller effect size on this data, not an invalid technique.*
- D. It's not possible to do spatial-block CV within a single region; `groups` must always span multiple regions.
  *Incorrect — the "Spatial CV: project first, then grid" section does exactly this, using `make_blocks`/`GroupKFold` gridded within a single reprojected region (Bern), with region-spanning `LeaveOneGroupOut` introduced as a distinct, later step.*

---

#### Q4. The notebook's `wrong-conclusion`-tagged cell prints: "WRONG: X% of points with similarity > 0.90 share the query's label, so a similarity above 0.90 must mean 'same land cover.'" What specifically makes this conclusion wrong, per the notebook's own explanation?

- A. The 0.90 threshold is arbitrary — changing it to 0.85 or 0.95 changes the "agreement rate" even though nothing about the underlying data changed, so a fixed-threshold rate answers "how many points cross an arbitrary line," not "how good is this query."
  *Correct — this is the exact text under "### Why this is wrong": "The 0.90 cutoff is arbitrary... Pick 0.85 or 0.95 instead and the apparent 'agreement rate' above changes with it, even though nothing about the underlying data changed... Ranking, plus precision@k... is the honest alternative."*
- B. The label data used to compute the agreement rate is corrupted.
  *Incorrect — nothing in the "Why this is wrong" explanation questions label data quality; the critique is purely about the arbitrariness of the fixed similarity threshold, not data integrity.*
- C. Cosine similarity cannot be validly computed between AlphaEarth vectors at all.
  *Incorrect — the notebook relies on cosine/dot-product similarity throughout as valid (see Q1); the wrong-conclusion cell critiques drawing a categorical same/different-class conclusion from an arbitrary threshold, not the validity of similarity computation itself.*
- D. The similarity search was run on the wrong region.
  *Incorrect — the trap is conceptual (threshold arbitrariness), not a region-selection bug; the "Why this is wrong" text never mentions region choice.*

---

#### Q5. The notebook reports that leave-region-out causes a "double-digit balanced-accuracy drop" (17-19 points, per the cited prior measurement) for models trained on Bern and evaluated on Seville, while in-region spatial-block CV shows only a 1-4 point gap. What is the notebook's stated explanation for why the gap is so much larger across regions than within one region?

- A. AlphaEarth embeddings aggregate a full year of multi-modal satellite signal, which plausibly makes them more resistant to *adjacent-pixel* leakage within a region than raw spectral bands — but that aggregation does nothing to help a model trained only on Bern recognize Seville's genuinely different climate, soil, and crop-calendar signal; that is an extrapolation problem, not an interpolation one.
  *Correct — this is the "Leave-region-out" section's stated reasoning verbatim: the annual aggregation is "a within-region effect," while the region gap is "a genuinely different climate, soil, and crop-calendar signal — an extrapolation problem, not an interpolation one."*
- B. The Seville dataset has fewer labeled points than Bern, so its test-set accuracy is statistically noisier.
  *Incorrect — the notebook's explanation is about extrapolation to a different climate/land-cover signal, not sample-size noise; no such sample-size argument appears in the "Leave-region-out" section's reasoning.*
- C. The random forest and logistic regression models were configured differently for the leave-region-out experiment than for the spatial-block experiment.
  *Incorrect — the same `MODELS` dict (`logreg`, `random_forest`) is reused unchanged across the random-split trap, spatial-block CV, and leave-region-out sections; the notebook's stated point is that reusing `spatial_cv_report` with only `groups`/`cv` changed "is itself the point: the helper is genuinely generic."*
- D. Bern and Seville use incompatible AlphaEarth band ordering, causing the model to misinterpret features.
  *Incorrect — no such band-ordering incompatibility is mentioned anywhere in the notebook; both regions draw from `course.schema.to_matrix`, the same schema, and the explanation given is about climate/land-cover distribution shift, not a data-format bug.*

---

#### Q6. The "Baseline: the identical pipeline on raw Sentinel-2 bands" section runs the exact same classification pipeline on raw spectral bands instead of AlphaEarth embeddings. What is the purpose of this baseline, per the notebook's Takeaway?

- A. To prove that raw Sentinel-2 bands always outperform AlphaEarth embeddings.
  *Incorrect — the Takeaway states "the table above reports what this run actually measured," a neutral, measured framing, not a categorical claim that one modality always wins.*
- B. To directly test the hypothesis (raised in the "Leave-region-out" section) that AlphaEarth's yearly aggregation helps with within-region adjacent-pixel leakage but not necessarily with cross-region generalization, by running the identical pipeline on a modality without that yearly aggregation.
  *Correct — the "Leave-region-out" section explicitly sets this up: "The Sentinel-2 baseline in the next section tests this hypothesis directly," referring to its own claim about AlphaEarth's aggregation being a within-region, not cross-region, benefit.*
- C. To demonstrate that Sentinel-2 bands require no dequantization, unlike AlphaEarth.
  *Incorrect — dequantization is a property specific to AlphaEarth's int8 encoding covered in Module 2; the baseline section's stated purpose (per the Leave-region-out section's forward reference) is about testing the aggregation-vs-leakage hypothesis, not encoding format.*
- D. To show that random forests are unsuitable for classifying raw spectral data.
  *Incorrect — the baseline reuses both `logreg` and `random_forest` models from `MODELS`, the same as every earlier section; there is no claim in the notebook that either model type is unsuitable for raw bands.*

---

#### Q7. In "Similarity 3: Positive-minus-negative prototype," the notebook computes `pos_minus_neg = (positive_centroid - negative_centroid_raw)` and then renormalizes it. Why is renormalizing to unit length a required step here, not an optional cleanup?

- A. Because averaging (and subtracting) unit-norm vectors does not generally produce a unit-norm result, and this notebook's cosine/dot-product similarity machinery (see Q1) requires unit-norm query vectors to remain valid.
  *Correct — the "Similarity 2: Prototype queries" section states this directly: "The raw mean of several unit-norm embedding vectors is **not itself unit-norm**... Renormalizing... is required, not optional, to get back a valid query vector that `cosine_similarity_map` can compare on equal footing," and the same logic is applied again in "Similarity 3" via `pos_minus_neg = pos_minus_neg_raw / np.linalg.norm(pos_minus_neg_raw)`.*
- B. Because scikit-learn raises an error if you pass a non-unit-norm vector to a similarity function.
  *Incorrect — no such library-level enforcement is mentioned; the notebook implements the unit-norm requirement itself via `cosine_similarity_map`'s reliance on the "dot product equals cosine similarity" property from the Data section's Takeaway, not a scikit-learn exception.*
- C. Because renormalization improves classifier accuracy, as measured in the "Classification" section.
  *Incorrect — renormalization here is about keeping the similarity-search machinery mathematically valid (Similarity sections), not about the separate classification pipeline (Classification sections), which use `course.schema.to_matrix` directly, not the prototype vectors.*
- D. Because negative numbers are not allowed in the embedding matrix.
  *Incorrect — the embedding matrix and prototype vectors contain signed float32 values throughout (e.g., the dequantization formula itself uses `np.sign`); negative values are expected and normal, not disallowed.*

---

#### Q8. Considering the module's overall arc — random-split trap, spatial-block CV, leave-region-out, and the Sentinel-2 baseline — which single number should a practitioner report as "the" accuracy of this classifier if asked how well it will perform on a genuinely new, unseen region?

- A. The random-split "TRAP ACCURACY" number, since it's the simplest and highest.
  *Incorrect — this is precisely the number the notebook's own print statement labels "TRAP ACCURACY," and whose confusion-matrix figure title reads "looks great, proves little" — the module's central point is that this number is misleading for the generalization question.*
- B. The in-region spatial-block CV number, since it at least accounts for some spatial leakage.
  *Incorrect — while more honest than the random split, the "Leave-region-out" section states this only showed "a 1-4 point gap," and explicitly frames it as a smaller, different (interpolation) lesson, not the number that answers a cross-region generalization question.*
- C. The leave-region-out balanced accuracy (train Bern, predict Seville), since that scenario is the one that actually withholds an entire unseen region during training and is explicitly called "the primary evidence" for how the model performs on genuinely new geography.
  *Correct — the "Leave-region-out" section states this is "the primary evidence that a random split lies here" and its Takeaway names it as "where the dramatic, generalization-relevant gap lives for this modality... the moment it has to extrapolate to a different climate and land-cover mix" — this is the scenario structurally matching "a genuinely new, unseen region."*
- D. The average of all three numbers (random split, spatial-block CV, leave-region-out), since averaging is always the safest summary statistic.
  *Incorrect — the notebook never recommends averaging across scenarios that test fundamentally different questions (memorization vs. interpolation vs. extrapolation); doing so would blend a misleading number with a meaningful one, contradicting the module's entire methodological argument.*

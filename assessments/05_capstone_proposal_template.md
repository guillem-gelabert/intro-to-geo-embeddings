# Capstone Proposal Template

Copy this file, fill in every bracketed field, and submit it alongside
your capstone notebook. It is designed to make the rubric
(`assessments/05_capstone_rubric.md`) self-checkable before you submit:
if you cannot fill in a field honestly, that is a signal the
corresponding rubric row is not yet satisfied.

Before filling this in, read `templates/PROVENANCE_CHECKLIST.md` in
full — the provenance dict below mirrors its required fields, and its
worked "do not redistribute" example (Copernicus Global Embeddings via
CDSE) is the pattern to follow if your own source turns out to be
license-restricted.

## 1. Area of Interest and Question

- **AOI (name, bounding box or polygon):** `[EDIT ME]`
- **Question this capstone answers:** `[EDIT ME — e.g. "did built-up
  area increase in this AOI between year X and year Y?"]`
- **Target/classes used (state and justify, per rubric row
  "Representation choice"):** `[EDIT ME — e.g. binary
  artificialized/not, or the same four-class built/crop/vegetation/water
  scheme Module 3 used]`

## 2. Representation Choice

- **Embedding product used:** `[EDIT ME — AlphaEarth / TESSERA / Clay /
  other]`
- **Dataset version pinned:** `[EDIT ME — e.g. AlphaEarth
  DATASET_VERSION, or GeoTessera dataset_version/dataset_variant]`
- **One-sentence trade-off against at least one alternative:**
  `[EDIT ME]`

## 3. Provenance Dict (fill in every key; leave none blank)

```json
{
  "embedding_product": "[EDIT ME]",
  "dataset_version": "[EDIT ME]",
  "year": "[EDIT ME]",
  "source_license": "[EDIT ME]",
  "attribution": "[EDIT ME -- copy verbatim from the source's own wording, see templates/PROVENANCE_CHECKLIST.md reference table]",
  "crs": "[EDIT ME -- EPSG code]",
  "sampling_method": "[EDIT ME]",
  "label_source": "[EDIT ME]",
  "validation_source": "[EDIT ME -- must be a DIFFERENT product from label_source, see Pitfall 6]",
  "created_by": "[EDIT ME -- your name / notebook filename]",
  "created_at": "[EDIT ME -- ISO 8601 timestamp]",
  "course_release": "[EDIT ME -- e.g. 2026.08]"
}
```

## 4. Validation Plan (Validation design, 30% of rubric)

- **Spatial-block CV configuration:** `[EDIT ME — block size in metres,
  n_splits, CRS used for blocking]`
- **Leave-region-out / leave-one-AOI-out configuration:** `[EDIT ME —
  which region(s) held out]`
- **Both will be reported side by side, never either alone:** `[EDIT ME
  — confirm yes/no]`

## 5. Uncertainty Plan (Interpretation and uncertainty, 15% of rubric)

- **Model-level uncertainty measure:** `[EDIT ME — e.g. top-1/top-2
  probability margin]`
- **Validation-level uncertainty measure:** `[EDIT ME — e.g.
  std_balanced_accuracy across CV folds]`

## 6. Ethics Statement (Licensing and ethics, 10% of rubric)

- **Who bears the cost of a false positive from this pipeline's
  output:** `[EDIT ME]`
- **Is the inferred label more sensitive than the underlying imagery?**
  `[EDIT ME — yes/no and why]`

## Rubric Self-Check (complete before submitting)

- [ ] **Validation design (30%):** Both spatial-block CV and
  leave-region-out (or leave-one-AOI-out) are planned and will be
  reported side by side, not either/or.
- [ ] **Reproducibility and provenance (15%):** The provenance dict above
  is fully filled in and will be written via `write_provenance` (or
  hand-built to the same schema) and committed alongside the notebook.
- [ ] **CRS and alignment correctness (15%):** Every metre-based
  operation (blocking, buffers, distances) will run in a projected CRS,
  never geographic EPSG:4326.
- [ ] **Interpretation and uncertainty (15%):** Both a model-level and a
  validation-level uncertainty measure will be reported, kept distinct.
- [ ] **Representation choice (15%):** The embedding product is named
  above with an explicit one-sentence trade-off against an alternative.
- [ ] **Licensing and ethics (10%):** Every input's license/attribution
  is recorded verbatim, and the false-positive-cost/sensitivity statement
  above is filled in.

If any box above cannot be checked honestly, do not submit yet — return
to the corresponding section of this template and the matching row in
`assessments/05_capstone_rubric.md`.

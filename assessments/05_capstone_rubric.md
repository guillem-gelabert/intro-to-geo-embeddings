# Capstone Rubric: Artificialization Pipeline

Your capstone submission (a new AOI, your own labels, your own question)
is graded against the six weighted criteria below. They sum to 100%.
Validation design carries the largest single weight, deliberately: the
most damaging mistake in applied geospatial ML is impressive metrics on
an invalid split, not a poorly chosen classifier.

## Rubric

### Validation design: 30%

Full marks requires **both** spatial-block cross-validation (`GroupKFold`
on 10 km blocks or the course's `make_blocks` helper) **and**
leave-region-out (or leave-one-AOI-out) validation, reported side by
side — never either one alone, and never a random `train_test_split` in
place of either. The submission must state, in its own words, which
number is the honest generalization estimate and why (per the capstone
notebook's own worked example: leave-region-out costs roughly 17-19
balanced-accuracy points relative to in-region spatial-block CV on this
course's measured data — your own numbers may differ, but both must be
reported and compared, not cherry-picked).

### Reproducibility and provenance: 15%

Full marks requires a `course.provenance.build_provenance`/
`write_provenance` output (or an equivalent hand-built, JSON-serializable
provenance dict for non-frozen-table sources) committed alongside the
notebook, with every dataset version pinned explicitly (e.g. AlphaEarth
`DATASET_VERSION`, GeoTessera `dataset_version`/`dataset_variant`) rather
than left to whatever the live API happens to return that day.

### CRS and alignment correctness: 15%

Full marks requires reprojection to a projected CRS (e.g. EPSG:2056 or
the correct local UTM zone) before any metre-based operation —
`make_blocks`, buffers, or distance calculations. No geographic-CRS
(EPSG:4326) distance or area computation may appear anywhere in the
submission.

### Interpretation and uncertainty: 15%

Full marks requires reported metrics to carry the CV fold spread (mean ±
std), never a single point estimate, and requires both a model-level
uncertainty measure (e.g. top-1/top-2 probability margin) and a
validation-level uncertainty measure (fold-to-fold CV std) to be reported
as two distinct signals, not conflated into one number. Claims must be
scoped to what was actually measured — a prediction map presented without
either uncertainty measure alongside it does not satisfy this row.

### Representation choice: 15%

Full marks requires the embedding product used (AlphaEarth, TESSERA,
Clay, or another) to be stated explicitly, with a one-sentence trade-off
against at least one alternative (e.g. AlphaEarth's global 10 m/annual
coverage vs TESSERA's finer spatial resolution or Clay's
Sentinel-2-derived embedding and different license terms).

### Licensing and ethics: 10%

Full marks requires the attribution and license of every input to be
recorded verbatim (per `templates/PROVENANCE_CHECKLIST.md`'s reference
table — copy the strings exactly, never paraphrase), and requires an
explicit statement of who bears the cost of a false positive from this
pipeline's output (e.g. a false "artificialized" flag on someone's land
can trigger real regulatory or compliance consequences), including
whether the inferred label is more sensitive than the underlying imagery
itself.

## Weights sum check

30% + 15% + 15% + 15% + 15% + 10% = 100%

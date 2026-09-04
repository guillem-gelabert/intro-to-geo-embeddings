Module: 00 — refresher
Title: Embedding Refresher
Syllabus minutes: 25 (see MODULE_MINUTES in tools/verify_narration_scripts.py)
Source notebook: notebooks/solutions/00_embedding_refresher.py
Slide deck: slides/00_refresher.md

---

### Lecture 00.1 — Welcome and vectors as embeddings

Objective: state what an embedding is (a fixed-length vector) and show that L2-normalizing a vector turns a dot product into a cosine similarity.

| Duration | Cumulative | VISUAL | AUDIO | Cue |
|----------|------------|--------|-------|-----|
| 01:00 | 01:00 | [SLIDE] 00_refresher.md #1 | "Welcome to the embedding refresher. This module is optional background — if you already know vectors, cosine similarity, PCA, train/test splits, and CRS reprojection, skip ahead to Module 1 proper. Everything here uses tiny synthetic data, not any real dataset or provider, on purpose: the point is vocabulary, not results." | [NONE] |
| 01:00 | 02:00 | [SLIDE] 00_refresher.md #2 | "Five things by the end: NumPy vectors and L2 normalization, cosine similarity, PCA on a toy matrix, a tiny classifier with a train/test split, and CRS reprojection. No linear algebra and no GIS background required going in." | [NONE] |
| 03:00 | 05:00 | [CELL] 00_embedding_refresher.ipynb § "Vectors and L2 normalization" | "A geospatial embedding is just a vector — a fixed-length list of numbers describing a location. Here are six synthetic 8-dimensional vectors, three drawn tightly around one center and three around another. Their raw norms differ, which is the problem: L2-normalizing every row to unit length is what makes the dot product between two vectors equal their cosine similarity. That single fact is the same one real AlphaEarth vectors rely on later in the course." | [RUN CELL] |

Recap: an embedding is a vector, and unit-normalizing it is what turns a dot product into a cosine similarity.
End-state: the printed raw norms and the printed unit norms (all 1.0) are both visible on screen.
Target length: 2:00–7:00 (not a codealong).

---

### Lecture 00.2 — Cosine similarity

Objective: read a pairwise cosine similarity matrix and connect it to the AlphaEarth similarity-search notebook the course builds toward.

| Duration | Cumulative | VISUAL | AUDIO | Cue |
|----------|------------|--------|-------|-----|
| 01:00 | 01:00 | [SLIDE] 00_refresher.md #3 | "With every row unit-norm, the full pairwise dot-product matrix IS the pairwise cosine similarity matrix — no extra division step needed. That's the whole trick." | [NONE] |
| 03:00 | 04:00 | [CELL] 00_embedding_refresher.ipynb § "Cosine similarity" | "Here's that matrix computed and plotted. Vectors within the same synthetic cluster score high cosine similarity, close to 1; vectors across clusters score low. This is exactly the signal the real similarity-search notebook computes at scale over AlphaEarth embeddings — same math, more dimensions." | [RUN CELL] |

Recap: cosine similarity is high within a cluster and low across clusters — the same signal used later at scale.
End-state: the cosine similarity heatmap figure is visible on screen with its colorbar.
Target length: 2:00–7:00 (not a codealong).

---

### Lecture 00.3 — PCA on a toy embedding matrix

Objective: use PCA to compress a high-dimensional toy embedding to two plottable axes, and state precisely what those axes do and do not mean.

| Duration | Cumulative | VISUAL | AUDIO | Cue |
|----------|------------|--------|-------|-----|
| 01:00 | 01:00 | [SLIDE] 00_refresher.md #4 | "Real embeddings have far more dimensions than we can plot directly. PCA finds the two directions of greatest variance in the toy matrix, so it fits on a page — at the cost of throwing away everything else." | [NONE] |
| 04:00 | 05:00 | [CELL] 00_embedding_refresher.ipynb § "PCA on a toy embedding matrix" | "Here's PC1 and PC2 for our six toy vectors, colored by cluster. Say this precisely: these two components separate the two synthetic clusters in this toy sample — they do not correspond to a named physical variable. That phrasing matters. A component is not 'the vegetation axis' or 'the moisture axis'; it's a direction that happens to separate this data, in this sample." | [RUN CELL] |

Recap: PCA axes separate this sample's clusters; they are not named physical quantities.
End-state: the PC1/PC2 scatter plot with both cluster labels in the legend is visible on screen.
Target length: 2:00–7:00 (not a codealong).

---

### Lecture 00.4 — A tiny classifier and a CRS reprojection reminder

Objective: fit a linear classifier on unit-normalized vectors with a train/test split, then reproject toy points from EPSG:4326 to a projected CRS before any distance measurement.

| Duration | Cumulative | VISUAL | AUDIO | Cue |
|----------|------------|--------|-------|-----|
| 03:00 | 03:00 | [CELL] 00_embedding_refresher.ipynb § "A tiny classifier" | "With unit-normalized vectors and known cluster labels, can a simple linear model recover the clusters? We split into train and test, stratifying on the label so both splits keep the class balance, fit a logistic regression, and read off test-set accuracy. This is the smallest possible version of the classification workflow the AlphaEarth notebook runs on real data." | [RUN CELL] |
| 03:00 | 06:00 | [CELL] 00_embedding_refresher.ipynb § "A CRS reprojection reminder" | "One more piece of vocabulary before we're done: coordinates in EPSG, spelled out E-P-S-G, colon 4326 — longitude and latitude in degrees — are not metres. Here are three tiny points near Bern, the same study area the real notebooks use. Before reprojection they're in degrees; after reprojecting to EPSG:2056, a projected CRS for Switzerland, the coordinates are in metres and distance calculations become meaningful. Every later notebook in this course does this reprojection step before measuring anything in metres." | [RUN CELL] |

Recap: a linear classifier can recover known clusters from unit-normalized vectors; EPSG:4326 degrees must be reprojected before measuring distance.
End-state: the printed test-set accuracy and the reprojected point coordinates in EPSG:2056 are both visible on screen.
Target length: 2:00–7:00 (not a codealong).

---

### Lecture 00.5 — Wrap-up

Objective: recap the five vocabulary items this module built and point to the diagnostic for self-check.

| Duration | Cumulative | VISUAL | AUDIO | Cue |
|----------|------------|--------|-------|-----|
| 02:00 | 02:00 | [CELL] 00_embedding_refresher.ipynb § "Wrap-up" | "Five takeaways: L2-normalizing makes dot product equal cosine similarity; cosine similarity separates clusters and scales to real 64-D AlphaEarth embeddings; PCA compresses a high-dimensional embedding to two plottable axes at the cost of everything those axes don't capture; a simple linear classifier can recover known clusters from unit-normalized vectors; and EPSG:4326 degrees must be reprojected to a projected CRS, like EPSG:2056, before any metre-based distance calculation." | [NONE] |
| 01:00 | 03:00 | [SLIDE] 00_refresher.md #6 | "One housekeeping note that applies to every module in this course: dataset and library versions are pinned, because this field moves fast enough that unpinned material rots. You'll see the same reference-environment banner in every notebook." | [NONE] |
| 02:00 | 05:00 | [SLIDE] 00_refresher.md #7 | "This module only touched synthetic toy vectors — no real provider data, so there's no attribution to give here. Next up: `00b_representation_inspection.ipynb` and `01_alphaearth_access_visualize.ipynb` build directly on these ideas using real AlphaEarth data. If you want to check your understanding first, work through the refresher diagnostic." | [NONE] |

Recap: five vocabulary items — normalization, cosine similarity, PCA, classification, CRS reprojection — carry forward into every later module.
End-state: the wrap-up takeaway list and the forward pointer to the next two notebooks are visible on screen.
Target length: 2:00–7:00 (not a codealong).

---

Total: 25:00 (syllabus: 25 minutes)

## Pronunciation Notes

- EPSG — spelled out, "E-P-S-G"
- AlphaEarth — "AL-fuh urth" (mentioned only in the forward-looking wrap-up pointer; this module's own content uses only synthetic toy vectors)

## Key Messages Used

None of the five canonical messages apply to this module — it works entirely on synthetic toy data and does not touch AlphaEarth vectors, patch embeddings, leave-region-out costs, or Dynamic World validation.

## Exercise/Quiz Callback

See assessments/00_refresher_diagnostic.md.

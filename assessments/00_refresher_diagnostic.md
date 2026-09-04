# Module 1 Refresher: Ungraded Diagnostic

**Ungraded — for your own calibration before starting Module 1.** There is no
pass/fail threshold. Use it to see which refresher sections (from
`00_embedding_refresher.ipynb`) are worth a second look before you move on.

---

#### Q1. In the "Vectors and L2 normalization" section, why does L2-normalizing two vectors make their dot product equal to their cosine similarity?

- A. Because L2 normalization removes negative values from the vectors.
  *Incorrect — normalization rescales a vector's length, it does not touch the sign of any component. See the "Vectors and L2 normalization" section: the raw (non-unit) norms printed are not all positive-only vectors to begin with.*
- B. Because dividing each vector by its own norm sets every vector's length to 1, and cosine similarity is defined as the dot product divided by the product of the two norms — which becomes 1 once both norms are 1.
  *Correct — this is exactly the Takeaway of that section: "unit-length vectors turn the dot product into cosine similarity." Once `‖a‖ = ‖b‖ = 1`, `cos(a,b) = a·b / (‖a‖‖b‖) = a·b`.*
- C. Because cosine similarity and dot product are mathematically identical for any two vectors, regardless of normalization.
  *Incorrect — this is only true after normalization. The section explicitly prints "raw (non-unit) norms" before normalizing to show they are not already unit vectors.*
- D. Because L2 normalization is only meaningful for embeddings, not for arbitrary vectors.
  *Incorrect — the section demonstrates this on a toy synthetic matrix that has nothing to do with embeddings specifically; it's a general linear-algebra fact.*

---

#### Q2. In the "Cosine similarity" section, the notebook shows vectors within the same synthetic cluster scoring high cosine similarity. What does a high cosine similarity between two vectors tell you?

- A. That the two vectors point in a similar direction in the embedding space.
  *Correct — this is what the "Cosine similarity" section's Takeaway demonstrates: same-cluster vectors, which were constructed to point in similar directions, score high.*
- B. That the two underlying real-world objects are physically close to each other geographically.
  *Incorrect — the toy matrix in this section has no geography at all; cosine similarity is purely a statement about vector direction, not spatial proximity. Later notebooks (Module 3) test whether that direction similarity correlates with land-cover label agreement, and show it is not a guarantee.*
- C. That the two vectors have identical magnitude.
  *Incorrect — cosine similarity is magnitude-independent by construction (see Q1); two vectors can have wildly different lengths and identical cosine similarity if they point the same way.*
- D. That the two vectors were sampled from the same probability distribution.
  *Incorrect — the section never claims a statistical-distribution interpretation; it only shows within-cluster vs across-cluster cosine scores on a synthetic, deterministically constructed matrix.*

---

#### Q3. In "PCA on a toy embedding matrix," the notebook prints `explained_variance_ratio_` for the first components. What is the correct interpretation of this output?

- A. It tells you what real-world attribute (e.g. brightness, wetness) each component measures.
  *Incorrect — PCA components are directions of maximum variance in the data as given; the section's Takeaway is that they "separate the two synthetic clusters," not that they measure a named physical property. (This exact trap is revisited more explicitly in Module 2's "Caption" on the AlphaEarth PCA map.)*
- B. It tells you what fraction of the total variance in the toy matrix is captured by each component.
  *Correct — `explained_variance_ratio_` is exactly that: the proportion of variance along each principal axis. The section's Takeaway is that "the first two components separate the two synthetic clusters," which is a variance/separability claim, not a labeled-meaning claim.*
- C. It tells you the classification accuracy you should expect from a downstream classifier.
  *Incorrect — variance explained by PCA components has no direct arithmetic relationship to classifier accuracy; the "A tiny classifier" section trains and evaluates a separate model to get an accuracy number.*
- D. It is only meaningful once you have at least 64 dimensions, as in AlphaEarth.
  *Incorrect — the refresher deliberately uses a small toy matrix, not 64-D AlphaEarth vectors, to demonstrate PCA at all; the concept generalizes regardless of dimensionality.*

---

#### Q4. In "A tiny classifier," why does the notebook print a held-out **test-set** accuracy rather than reporting accuracy on the data the model was trained on?

- A. Because scikit-learn requires you to always split your data before calling `.fit()`.
  *Incorrect — scikit-learn does not enforce this; nothing prevents calling `.score()` on the training set. The section's point is methodological, not a library constraint.*
- B. Because a model can score well on data it has already memorized, so accuracy on unseen (test) data is the only number that tells you whether it generalizes.
  *Correct — this is the purpose of the train/test split shown in "A tiny classifier": the printed `test-set accuracy` is deliberately measured on data excluded from fitting, precisely so the score reflects generalization rather than memorization. Module 3 escalates this same idea into the random-split-vs-spatial-CV comparison.*
- C. Because training-set accuracy is always exactly 100% and therefore uninformative.
  *Incorrect — training accuracy is not guaranteed to be 100% (that depends on model capacity and data separability); the reason to prefer test accuracy is about generalization, not a guaranteed ceiling.*
- D. Because the toy classifier in this section is too simple to be evaluated on training data at all.
  *Incorrect — any model can technically be scored on its own training data; the section's message is that doing so is misleading, not impossible.*

---

#### Q5. In "A CRS reprojection reminder," the toy points are reprojected before their coordinates are printed. Why does the notebook insist on a projected CRS (e.g. EPSG:2056) rather than staying in geographic coordinates (EPSG:4326, lon/lat degrees)?

- A. Because geographic-CRS coordinates cannot be stored in a GeoDataFrame.
  *Incorrect — geopandas stores geometries in whatever CRS you assign, including EPSG:4326; the notebook explicitly prints `toy_points.crs` (geographic) before reprojecting, proving it's a valid starting state.*
- B. Because distances and areas computed in degrees do not correspond to consistent metre-based units, so any later step that needs real distances (like spatial blocking in Module 3) requires a projected, metre-based CRS first.
  *Correct — this is exactly the section's Takeaway: "every later notebook reprojects to a projected CRS" before doing anything distance-based. Module 3's spatial-CV section states the same rule explicitly for `make_blocks`, which "refuses a geographic CRS outright."*
- C. Because EPSG:2056 is the only CRS matplotlib can plot.
  *Incorrect — matplotlib has no CRS awareness at all; reprojection has nothing to do with plotting capability.*
- D. Because AlphaEarth embeddings are only defined in EPSG:2056.
  *Incorrect — AlphaEarth data is delivered per UTM zone (EPSG:327xx) per the access notebook; EPSG:2056 is simply the Swiss projected CRS chosen for Bern-region distance calculations in this course.*

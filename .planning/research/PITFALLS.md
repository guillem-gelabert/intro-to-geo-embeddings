# Pitfalls Research

**Domain:** Developer-oriented Udemy course on geospatial embeddings (AlphaEarth / Satellite Embedding backbone; TESSERA, Clay/LGND, OlmoEarth, Copernicus for portability), delivered as solution + exercise notebooks, slides, narration scripts and small frozen teaching datasets
**Researched:** 2026-09-03
**Confidence:** HIGH overall. Every AlphaEarth, Earth Engine, GeoTessera, licensing and environment claim below was checked against official documentation, PyPI metadata, Context7 (scikit-learn) or a live `uv pip compile` on this machine today. Items marked [LOW] rest on a single or non-official source.

**Phase labels used below** (from PROJECT.md build order):

| Label | Scope |
|-------|-------|
| **Phase 1** | `02_similarity_and_classification.ipynb` solution notebook + the frozen dataset(s) and `uv` environment it needs |
| **Phase 2** | Earlier modules: `00_embedding_refresher`, Module 1 inspection notebook, `01_alphaearth_access_visualize` |
| **Phase 3** | Later modules: `03_change_detection_and_validation`, `04_embedding_ecosystems`, `05_capstone_artificialization`, Module 6 provenance/licensing checklist |
| **Phase 4** | Exercise notebooks derived from solutions |
| **Phase 5** | Slide decks |
| **Phase 6** | Narration scripts |
| **Cross-cutting** | Repository layout, CI, data hosting, LICENSE/ATTRIBUTION files |

---

## Corrections to the research brief

Four premises in the brief or in `docs/research/course-design-research-2026-08.md` are out of date or imprecise. Fix them before they propagate into slides and scripts.

| Brief / report says | Verified state (2026-09-03) | Source |
|---|---|---|
| GCS bucket is requester-pays; budget for egress costs | The GCS README now states: "As of July 2026, this bucket is set up as 'provider pays'." Google's Medium post confirms users "will no longer incur any costs." Teach it as "currently provider-pays; policy can change; the frozen dataset is your insurance," not as a cost trap. | [HIGH] aef_on_gcs_readme; Medium "Now Available on GCS" |
| LGND open Clay corpus: 15.2 B embeddings, monthly Jan 2017–Apr 2026, CC BY 4.0 | True, but only for the product `source.coop/clay/lgnd-embeddings` (1,280 m/256D and 2,560 m/1024D, monthly aggregated; scene-level "forthcoming"). The similarly named `clay/lgnd-clay-v1-5-sentinel-2-l2a` (also in the AWS Open Data registry) has only **two time steps: June 2024 and June 2025**, 2,560 m/1024D, ~49.7 M aggregated rows / 182 GB. Notebook must pin the exact product path and partition. | [HIGH] both Source Coop pages; awslabs/open-data-registry yaml |
| System Python 3.14 "likely too new for the geo stack" | The full course stack (`geopandas, rasterio 1.5.1, rioxarray 0.23, geemap 0.38.4, earthengine-api 1.7.42, geotessera 0.10.1, stackstac, duckdb 1.5.5, scikit-learn 1.9.0 …`) **resolves on both 3.12 and 3.14** with `uv pip compile --python-platform aarch64-apple-darwin`; rasterio, duckdb, faiss-cpu and torch 2.14.0 all ship cp314 macOS-arm64 wheels. Standardise on **3.12 anyway** because Colab's current runtime is Python **3.12.13** (runtime 2026.07) and `geotessera`, `geemap`, `rasterio ≥1.5` and `rioxarray` all declare `>=3.12` — 3.12 is the intersection that matches Colab exactly. | [HIGH] PyPI JSON; Colab runtime FAQ; local `uv` resolve |
| Earth Engine catalog shows through 2024, GCS 2017–2025 | Confirmed. Catalog: availability ends 2025-01-01 (i.e., 2024 layer); GCS README: "2017 to 2025, inclusive." Also: catalog notes **dataset version 1.1 (2025-11-17) regenerated the 2017 layer** with additional Sentinel-1 acquisitions. | [HIGH] both official pages |

---

## Critical Pitfalls

Mistakes that cause a rewrite of a notebook, invalidate the course's core teaching claim, or expose the course legally.

### Pitfall 1: Treating raw int8 AlphaEarth COG values as the embedding

**What goes wrong:**
Reading `gs://alphaearth_foundations/...` COGs (or the Source Coop mirror) with rasterio and feeding the int8 band values straight into cosine similarity, PCA or a classifier; or averaging int8 values to make a prototype / coarser pixel; or leaving `-128` in the array so masked pixels become a legitimate-looking vector.

**Why it happens:**
Earth Engine serves the same dataset already de-quantized as floats in [-1, 1], so code written against Earth Engine "just works" and authors assume the COGs are the same numbers. They are not: the GCS README specifies a **square-root quantisation** that must be inverted, then a unit-length renormalisation.

**How to avoid:**
One shared, tested helper, used everywhere a COG is touched:

```python
import numpy as np

NODATA = -128  # present in ALL channels when a pixel is masked

def dequantize_aef(q: np.ndarray) -> np.ndarray:
    """int8 (…, 64) -> float32 unit vectors; masked pixels -> NaN."""
    q = np.asarray(q)
    mask = np.any(q == NODATA, axis=-1, keepdims=True)
    x = ((q.astype(np.float32) / 127.5) ** 2) * np.sign(q)
    x /= np.linalg.norm(x, axis=-1, keepdims=True) + 1e-12
    return np.where(mask, np.nan, x)
```

Aggregate only *after* de-quantising: sum the float vectors, then renormalise (this is exactly how Google builds the COG overviews). Never average int8. Store frozen course data as float32 parquet (a few thousand rows × 64 is trivially small), so students never see int8 unless the lesson is explicitly about it.

**Warning signs:**
- Vector norms ≠ 1.0 (add `assert np.allclose(np.linalg.norm(X, axis=1), 1, atol=1e-3)` to every notebook that loads embeddings).
- Values outside [-1, 1] after de-quantisation → `-128` leaked through (`(128/127.5)² ≈ 1.008`).
- Similarity histograms clustered near 0 or with a suspicious spike at exactly the same value.
- Colours in pseudo-RGB visualisation look posterised.

**Phase to address:** Phase 1 (frozen data must be produced with this helper; helper lives in the Module 3 notebook and is re-used), re-taught explicitly in Phase 2 (`01_alphaearth_access_visualize`, COG path) and Phase 3 (Module 6 provenance).

---

### Pitfall 2: Random `train_test_split` on neighbouring pixels (spatial leakage)

**What goes wrong:**
`train_test_split(X, y, random_state=42)` on pixel samples puts adjacent 10 m pixels of the same field or roof on opposite sides of the split. Reported accuracy of 95–99 % measures interpolation between near-duplicates, not generalisation. The course's own quiz question ("98 % random vs 82 % spatial") loses its bite if the solution notebook does not actually reproduce a gap.

**Why it happens:**
Every scikit-learn tutorial does it; Google's own Satellite Embedding supervised-classification tutorial collects ~10 points per class, uses kNN and reports **no** train/test split and no accuracy at all — students arriving from that tutorial have never seen a spatial split. Embeddings make this *worse* than raw spectra: AlphaEarth integrates spatial context, so neighbours are even more similar than raw pixels.

**How to avoid:**
- Sample the frozen dataset from **polygons/blocks**, not scattered points, and store a `block_id` (and a `region` label) column *in the parquet*, so the block structure is a first-class part of the data, not something computed ad hoc.
- Make the leakage visible: compute nearest-neighbour distance from each test point to the training set for the random split (median will be tens of metres) vs the block split (kilometres), and plot both. This is the single most convincing cell in the notebook.
- Temporal variant: the same location in 2020 and 2024 must share a group. Group by `location_id`, never by row.

**Warning signs:**
- Random-split score within 1–2 points of block-CV score → your blocks are probably too small or your classes are trivially separable (see Pitfall 3).
- Random-split accuracy > 97 % on a 3–4 class problem.
- Confusion matrix nearly diagonal but error map shows errors clustered at block edges.

**Phase to address:** Phase 1 (this is the core value; both splits must be in `02_similarity_and_classification.ipynb` with the gap reproduced on frozen data). Phase 3 extends it to spatial + temporal groups. Phase 4 exercise must not let students "fix" the leak by accident.

---

### Pitfall 3: Building spatial blocks wrongly

**What goes wrong:**
Several distinct bugs that all look like "spatial CV" but are not:
1. Blocks computed in EPSG:4326 (degrees) → rectangles ~7 km × 11 km at 47° N, and any distance/area printed is nonsense.
2. Blocks too large for the AOI → fewer groups than `n_splits`, or folds missing an entire class → `GroupKFold` raises or scores are NaN/degenerate.
3. Blocks too small (≈ autocorrelation range or less) → no better than random.
4. `groups=` forgotten in `cross_validate` → silently falls back to ordinary KFold.
5. No second region in the data → "leave-region-out" cannot be demonstrated.

**Why it happens:**
The report's snippet (`gdf.to_crs("EPSG:2056")`, 10 km blocks) is correct but assumes an AOI many times larger than 10 km. A "5 km buffer around Bern" AOI is ~10 km across → one to four blocks.

**How to avoid:**
- Always project first (Switzerland: EPSG:2056; the second region: its own projected CRS or the UTM zone from the COG's `UTM_ZONE`), then grid.
- Decide block size from data, not folklore: compute an empirical variogram / autocorrelation range of a few embedding dimensions (or of classifier residuals) and set block ≥ that range (blockCV's documented approach, Roberts et al. 2017). For a Swiss Plateau frozen dataset, expect 2–5 km blocks over a ≥ 30 × 30 km AOI; verify.
- Sanity checks in the notebook: `n_groups >= n_splits`; every fold's test set contains every class (or use `StratifiedGroupKFold`, which preserves class proportions with non-overlapping groups — verified in current scikit-learn docs).
- Ship the frozen dataset with **two regions** so leave-region-out is one `groups=region` call.

**Warning signs:**
- `ValueError: Cannot have number of splits n_splits=5 greater than the number of groups`.
- Block CV F1 varies wildly between folds (one fold has no positives).
- Printed block size in "metres" but the GeoDataFrame CRS is 4326.

**Phase to address:** Phase 1 (frozen dataset design: AOI extent, two regions, precomputed `block_id`). Phase 4 exercises can ask students to change block size and watch the gap.

---

### Pitfall 4: Over-correcting into "random splits are always wrong"

**What goes wrong:**
The course teaches spatial CV as the only valid evaluation. A sharp student (or reviewer) cites Wadoux et al. 2021, *"Spatial cross-validation is not the right way to evaluate map accuracy"*, which shows spatial CV can be **pessimistically** biased and that design-based estimation on a probability sample needs no autocorrelation adjustment. The course looks naive.

**Why it happens:**
The literature really is split: Ploton 2020 / Roberts 2017 / Kattenborn 2022 (random splits inflate up to ~28 %) vs Wadoux 2021 (spatial CV lacks theoretical underpinning for map accuracy). The 2026 "prediction-domain adaptive evaluation" line (kNNDM/NNDM) reconciles them: the right CV geometry depends on whether you predict *inside* the sampled area (interpolation) or *into new regions* (extrapolation).

**How to avoid:**
Teach the metric as an answer to a question, in one slide and one markdown cell:
- "How accurate is *this map* over *this AOI*?" → a probability sample of independent reference points + design-based estimate (random-ish is fine, spatial CV is not the tool).
- "How well will this model work *in a place I have no labels*?" → spatial block / leave-region-out.
- The course's running question (deploy to nearby unseen areas; transfer to a second region) is the second case — say so explicitly.

**Warning signs:**
Slides or scripts containing "random split is invalid" without a qualifier.

**Phase to address:** Phase 1 (one nuance cell), Phase 5/6 (slide wording, script wording), Module 6 checklist in Phase 3.

---

### Pitfall 5: Treating `1 − cosine` as "artificialisation happened" and picking a threshold by eye

**What goes wrong:**
`change = 1 - (e_2020 · e_2024)`; `artificialized = change > 0.25`. The map lights up on harvested fields, drought years, snow-cover differences, Sentinel swath boundaries and genuinely new buildings alike. Google's own April 2026 analysis ("Rethinking Change Detection and Attribution") found dot-product-only comparison "collapses the full 64-dimensional embedding space into a single similarity score" and produced "widespread speckling, scattered false positives," because the embeddings integrate "climate variability and structural context."

**Why it happens:**
The catalog page legitimately suggests dot product / angle to "reveal changes in conditions," and the number is easy to compute. The word "change" gets read as "land-cover change."

**How to avoid:**
- Keep the report's deliberate `# WRONG conclusion` cell, and follow it with three *correct* alternatives in ascending strength: (a) threshold **calibrated** with `precision_recall_curve` against independent change labels, reported on changed **and unchanged** controls; (b) per-year classifier → transition matrix (`vegetation → built`); (c) **baseline-aware** features — stack the base-year embedding with the delta or with the dot product (Google's best-performing configuration, 65 or 128 features) and train a change classifier on ~200 stable + ~200 change points per class.
- Show the disagreement map between (a) and (b): they answer different questions.
- Mention the catalog's own caveat: "some large scale swath and data availability artifacts remain… minor vector offsets."

**Warning signs:**
- Change map with linear boundaries following Sentinel-2 swath edges.
- Threshold chosen by looking at the histogram, no reference data used.
- Precision reported without unchanged controls.

**Phase to address:** Phase 3 (`03_change_detection_and_validation.ipynb`); classifier and CV code re-used from Phase 1.

---

### Pitfall 6: Validating one learned product against another, and misaligned reference years

**What goes wrong:**
Dynamic World "built" agrees with the AEF classifier "built" → declared validated. Dynamic World is single-image, near-real-time model output from the *same* Sentinel-2 imagery; its built/bare classes show low consistency across global 10 m products. Agreement is correlation of two models' errors, not accuracy. Separately, the Copernicus HRL Imperviousness reference chosen for the change lab has years **2006/2009/2012/2015/2018/2021** and change layers **2015–2018 (broken by the 20 m → 10 m resolution switch; ETC/ULS says the series "is broken")** and **2018–2021 (10 m status, 20 m/100 m change, EPSG:3035, released June 2025, status "validation pending")**. Comparing AEF 2020→2024 with HRL 2018→2021 is a silent year mismatch.

**Why it happens:**
Dynamic World is convenient (CC BY 4.0, in Earth Engine, same grid). HRL year cadence is not on anyone's mental map.

**How to avoid:**
- Use Dynamic World only to *bootstrap exploratory labels*, with a cell that says so, and never as the validation column.
- Align years: change lab = **AEF 2018 vs 2021** validated against **HRL Imperviousness Change 2018–2021**; note "validation pending" in provenance. Do not straddle 2015→2018.
- For Switzerland add an authoritative, independent, redistributable label source: **Arealstatistik** (BFS, 100 m hectare points, EPSG:2056, licence "OPEN BY — must provide the source", visually interpreted from aerial photographs, not a satellite model). It is the strongest reference in the report's hierarchy that is actually downloadable.
- Store `label_source` and `validation_source` in the provenance dict and require them to differ.

**Warning signs:**
- `validation_source == label_source`.
- Reference-year pair ≠ embedding-year pair anywhere in the notebook.
- Reference raster in EPSG:3035 sampled without reprojecting the points.

**Phase to address:** Phase 1 (label provenance columns in the frozen dataset; Dynamic World disclaimer cell), Phase 3 (change lab year choice, HRL/Arealstatistik as validation), Phase 5/6 (quiz answer wording).

---

### Pitfall 7: CRS, scale and grid-alignment errors specific to AlphaEarth

**What goes wrong:**
- `ee.ImageCollection(...).filterDate(...).mosaic()` **drops the native UTM projection**; the mosaic's default projection is WGS84 at 1° scale. Any `sample()`/`reduceRegion` without an explicit `scale=10` (and ideally `crs`) samples garbage, and `Export.image` without `crs`/`scale` produces a 1°-pixel raster. Google's own tutorial flags this.
- `.first()` instead of `.mosaic()` returns one 163,840 m × 163,840 m UTM tile — fine for Bern (single tile) until the AOI crosses a tile/zone boundary and half the map is empty.
- Distances/areas/block sizes in degrees (see Pitfall 3).
- Differencing two years read from COGs without asserting identical `transform`, `shape` and `crs` → off-by-one-pixel "change" everywhere.
- Source Coop mirror (`tge-labs/aef`) COGs are **bottom-up** (positive y-resolution); open them via the provided `.vrt` or many tools flip them.
- Resampling the embedding raster (bilinear) to another CRS, then computing cosine → norms drift; re-normalise or, better, reproject the **points** onto the raster's native UTM grid and sample there.

**Why it happens:**
Earth Engine hides projection; students' mental model is "10 m pixels everywhere."

**How to avoid:**
- Notebook pattern: `img.mosaic().setDefaultProjection(...)` or sample with explicit `scale=10, crs=...`; always print `img.projection().getInfo()` once.
- Frozen rasters for the change lab: keep native UTM (EPSG:32632 for Bern), identical grid for both years, and an `assert a.transform == b.transform and a.crs == b.crs` cell.
- Vector work in EPSG:2056 (Swiss) / the second region's projected CRS; raster work in the COG's UTM; never mix in one cell without an explicit `to_crs`.

**Warning signs:**
- Exported GeoTIFF with 1 pixel or a few hundred pixels.
- Half-empty maps at tile edges.
- Change score histogram not near zero for known-stable water/forest.

**Phase to address:** Phase 2 (`01_alphaearth_access_visualize`: mosaic/scale/projection cells), Phase 1 (frozen data extracted with explicit scale/CRS; CRS recorded), Phase 3 (raster alignment assert before differencing).

---

### Pitfall 8: Interpreting embedding axes or PCA components as physical variables

**What goes wrong:**
"A17 correlates with NDVI, so A17 is vegetation." "PC3 is urban density." Pseudo-RGB of `A01/A16/A09` narrated as if the colours were spectral. The catalog is explicit: the bands "collectively refer to a 64D coordinate in the embedding space and are not independently interpretable."

**How to avoid:**
- Fixed phrasing rule for scripts and slides: "this component *separates* X from Y *in this sample*" — never "measures."
- Keep the exercise question "why does the map look geographically structured even though the axes have no RGB meaning?"
- If you show a correlation between an axis and NDVI, show that it changes between regions/years to make the point that it is not a calibrated variable.
- Visualisation min/max (`-0.3..0.3`) is a display stretch, not a physical range; say so.

**Warning signs:**
Any slide caption with "vegetation axis," "water band," "urban dimension."

**Phase to address:** Phase 2 (visualisation notebook), Phase 5/6 (caption and script review against the phrasing rule).

---

### Pitfall 9: Notebooks that hard-depend on live credentials, and Earth Engine auth gotchas

**What goes wrong:**
A paid course whose Module 2 notebook dies at `ee.Initialize()`. Specific, verified failure modes:
- `ee.Initialize()` **without** `project=` fails since earthengine-api 0.1.383; the project must have the EE API enabled **and be registered** (noncommercial or commercial). Default Colab/Cloud projects are not.
- Noncommercial projects must pass **verification**; since 27 April 2026 they have monthly quotas: **Community 150 EECU-h**, Contributor 1,000 EECU-h (billing account required, not charged), Partner 100,000. Exhaustion puts the project in **restricted mode** (reduced concurrency/workers), not a hard stop, so notebooks "get slow" mysteriously.
- The old "paste a token" auth mode is **gone**. In local JupyterLab **without gcloud** (the author's situation) the default is `auth_mode='localhost'`, which only works when the browser runs on the same machine; `notebook` mode works remotely but requires choosing an "authentication project."
- Interactive limits: `getInfo()` on > 5,000 elements aborts ("Collection query aborted after accumulating over 5000 elements"); `sampleRegions` on large regions → "User memory limit exceeded"; for point collections use `reduceRegions`, or export a table.
- LGND requires `LGND_TOKEN`; trial credits are finite.
- Licensing edge: Google's noncommercial terms say "You may charge for your training services, but you cannot charge for use of Earth Engine," and internal R&D toward a commercial product is commercial. Producing frozen datasets for a paid course through a *noncommercial* project is a grey zone; the GCS bucket (no EE, provider-pays, CC BY 4.0) avoids it entirely.

**How to avoid:**
- **Path B first**: every notebook loads frozen data from a public URL (Hugging Face dataset repo or GitHub release asset, as the ISPRS 2026 tutorial does) *before* any optional live cell. Live cells are wrapped: `if LIVE and ee_ok(): ... else: load_frozen()`.
- Auth cell template that reads `EE_PROJECT` from env/`getpass`, catches `ee.EEException`, and prints the registration URL and the "check current eligibility and quotas" sentence.
- Produce the frozen AEF samples from the **GCS COGs** (rasterio + `GS_NO_SIGN_REQUEST=YES`, `/vsigs/alphaearth_foundations/...`) rather than through Earth Engine, so the course's data provenance does not depend on an EE project at all.
- Never a service-account JSON in the repo; CI that needs EE uses a secret and `ee.ServiceAccountCredentials`, and the README says so.

**Warning signs:**
- Any notebook whose first data-bearing cell imports `ee`.
- `ee.Initialize()` with no `project`.
- A `.json` key or `LGND_TOKEN=` literal anywhere in git history.

**Phase to address:** Phase 1 (frozen-data-first loader pattern is established here), Phase 2 (`01_alphaearth_access_visualize` auth cell + fallback), Phase 3 (LGND/TESSERA fallbacks), Cross-cutting (secrets, CI).

---

### Pitfall 10: Version rot — libraries, dataset versions, product paths

**What goes wrong:**
- `pip install geemap rasterio ...` unpinned: geemap released 0.38.4 on 2026-08-27, earthengine-api 1.7.42 on 2026-08-31, geotessera 0.10.1 on 2026-08-27 — this stack moves weekly. `stackstac`'s last release is **0.5.1 from August 2024** (it resolved as 0.5.0 today); it is the most likely package to break under a future xarray/numpy.
- AlphaEarth: dataset **v1.1 regenerated 2017** (2025-11-17). A 2017-based exercise recorded before that date gives different numbers today. Each EE image carries `DATASET_VERSION`, `MODEL_VERSION`, `PROCESSING_SOFTWARE_VERSION`, `UTM_ZONE` — record all four.
- GeoTessera: default `dataset_version="v1", year=2024`; v1.1 and v2 (beta) exist; docs warn **"Do not mix embeddings from different (version, variant) pairs"** — they are independently learned 128-D spaces. Tiles processed before 2025-08-20 may show tile-boundary discontinuities. Cached manifests are revalidated with `If-Modified-Since`, so results can change between runs without code changes. Global coverage exists only for 2024/v1; other years are partial.
- TESSERA de-quantisation is **different** from AlphaEarth (`int8 * per-tile float32 scales`, QAT-trained, unit length not documented). Applying the AEF square formula to TESSERA, or assuming dot = cosine, is wrong.
- LGND: two Source Coop products with different coverage (see corrections).

**How to avoid:**
- `uv lock` committed; `requirements.txt` exported for Colab with `==` pins; a repo banner "Course reference environment: 2026-08 release"; a CI job that re-executes all notebooks monthly against the lock and, separately, against latest to surface drift early.
- Provenance dict fields: `dataset_version`, `model_version`, `processing_software_version` (AEF), `tessera_dataset_version` + `tessera_dataset_variant`, `lgnd_product_path`, `retrieved_on`. GeoTessera stamps these into exported GeoTIFF tags — read them rather than typing them.
- One `normalize_rows()` helper applied to *every* provider before cosine; an assert on norms right after loading each provider's data.
- Consider `odc-stac` as the Sentinel-2 stacking fallback if `stackstac` breaks. [LOW — judgement, not verified breakage]

**Warning signs:**
- Notebook output cells show different accuracy than the recorded video.
- `pip install` line without `==`.
- `geotessera` call without `dataset_version=`.

**Phase to address:** Phase 1 (lockfile, banner, provenance dict), Phase 3 (per-provider version fields in `04_embedding_ecosystems`), Cross-cutting (CI).

---

### Pitfall 11: Hidden state, author-only paths and Colab/local divergence

**What goes wrong:**
Cells run out of order during authoring; the saved notebook "works" but a clean `Restart & Run All` fails (studies put non-reproducible public notebooks at the vast majority). Paths like `/Users/guillem/...` or `~/vault/...`; `sys.path.append("../src")` that does not exist on Colab; `!pip install` cells that run on Colab but pollute the local `uv` env; files written to `/content/` that vanish.

**How to avoid:**
- Pre-commit hook (or CI) that runs `jupyter nbconvert --execute` / `papermill` on every solution notebook from a clean kernel; treat failure as blocking. `nbval` for cells with deterministic outputs.
- Single environment-detection cell used verbatim in all notebooks:

```python
import os, pathlib, sys
IN_COLAB = "google.colab" in sys.modules
DATA_DIR = pathlib.Path(os.environ.get("COURSE_DATA", "/content/course-data" if IN_COLAB else "./course-data"))
DATA_DIR.mkdir(parents=True, exist_ok=True)
if IN_COLAB:
    %pip install -q -r https://raw.githubusercontent.com/<org>/<repo>/<tag>/requirements-colab.txt
```

- Data always fetched by URL into `DATA_DIR` (idempotent download with checksum), never assumed present; no `sys.path` hacks — either inline helpers per notebook or `pip install git+https://github.com/<org>/<repo>@<tag>`.
- Seed everything (`random_state=42` in every estimator and splitter).
- Keep outputs *in* solution notebooks (students read them on GitHub/Udemy); strip outputs from exercise notebooks; use `nbstripout` selectively or `nbdime` for diffs.

**Warning signs:**
- Execution counts in a committed notebook not monotonically increasing.
- Any absolute path or `~` in a code cell.
- A notebook that imports a module not in the lockfile.

**Phase to address:** Phase 1 (establish the template and CI gate on the first notebook), enforced for every later phase.

---

### Pitfall 12: Exercise notebooks drift from solutions

**What goes wrong:**
Exercises are hand-copied from solutions, then a bug fix or a dataset change lands in the solution only. Students hit an exercise whose checkpoint asserts no longer match. Hidden solutions in the exercise (collapsed cells) leak the answer or go stale.

**How to avoid:**
Generate, do not copy. Mark solution regions in the *solution* notebook with nbgrader-style markers (`### BEGIN SOLUTION` / `### END SOLUTION`, `### BEGIN HIDDEN TESTS`) plus cell metadata, and produce `exercises/*.ipynb` with a script (nbgrader `generate_assignment` or a 40-line `nbformat` script) that replaces solution regions with `# YOUR CODE HERE\nraise NotImplementedError()` and keeps checkpoint asserts. CI regenerates exercises and fails if the committed exercise differs from the regenerated one; CI also executes the solution notebook to prove the checkpoints pass.

**Warning signs:**
- `diff` between exercise and solution shows changes outside marked regions.
- Exercise checkpoint compares against a hard-coded number that the solution no longer produces.

**Phase to address:** Phase 4 (tooling), but the markers must be adopted in Phase 1 so the first solution notebook is already exercise-ready.

---

### Pitfall 13: Licensing and attribution mistakes in bundled frozen datasets

**What goes wrong:**
A paid course redistributes derived samples without the exact notices each source requires, or bundles data whose licence was never stated.

Verified requirements:

| Source | Licence | Required wording / condition |
|---|---|---|
| AlphaEarth / Satellite Embedding (EE and GCS) | CC BY 4.0 | "The AlphaEarth Foundations Satellite Embedding dataset is produced by Google and Google DeepMind." |
| Dynamic World | CC BY 4.0 | "This dataset is produced for the Dynamic World Project by Google in partnership with National Geographic Society and the World Resources Institute." |
| Sentinel-2 (any derived pixel values, incl. via `S2_SR_HARMONIZED`) | EU legal notice (Reg. 1159/2013) | Distribution of modified data: **"Contains modified Copernicus Sentinel data [Year]"** |
| Copernicus Land Monitoring Service (HRL Imperviousness) | Free/open, commercial use allowed | Derivatives: **"Generated using European Union's Copernicus Land Monitoring Service information; <DOI>"**; EU Login needed to download |
| Swiss Arealstatistik (BFS) | OPEN BY | "Open use. Must provide the source." |
| TESSERA precomputed embeddings | CC BY 4.0 per the TESSERA paper; GeoTessera software MIT; **not stated in GeoTessera docs** | Cite paper + record `(version, variant)`; re-check before bundling [MEDIUM] |
| LGND `clay/lgnd-embeddings` and `lgnd-clay-v1-5-sentinel-2-l2a` | CC BY 4.0 | Attribute LGND/Clay; note product path |
| Clay model | Code/weights Apache-2.0; docs CC BY; released embeddings ODC-BY | Three different licences; cite each |
| **Copernicus Global Embeddings (CDSE)** | **No explicit licence on the dataset page**; CDSE portal terms prohibit redistribution of portal material | **Do not bundle samples.** Stream from EODATA S3 in a live-only optional cell, cite Czerkawski et al. 2024 |
| Earth Engine as *access path* | Noncommercial terms | "You may charge for your training services, but you cannot charge for use of Earth Engine"; prefer GCS for producing course data |

**How to avoid:**
- `data/ATTRIBUTION.md` generated from the provenance dicts; every parquet carries `source_dataset_license` and `attribution` columns or file metadata.
- One licensing slide in Module 6 that shows these exact strings (students copy them).
- Anything with an unresolved licence (CDSE embeddings, Custom Satellite Embeddings preview) is live-only or a slide.

**Warning signs:**
- Frozen file with a `sentinel2_*` column and no "Contains modified Copernicus Sentinel data" notice.
- A single course-wide "CC BY 4.0" statement covering all sources.

**Phase to address:** Phase 1 (attribution embedded in the first frozen dataset), Phase 3 (Module 6 checklist and `04_embedding_ecosystems` per-provider notices), Cross-cutting (`LICENSE`, `ATTRIBUTION.md`).

---

### Pitfall 14: Scope drift

**What goes wrong:**
Module 1 grows a transformer/MAE explainer; Module 2 shows Code Editor JavaScript "because the tutorials are in JS"; Module 5 becomes a nine-provider catalogue with a shallow lab each; a Clay fine-tuning demo eats the time budget and needs a GPU.

**Why it happens:**
Google's Satellite Embedding tutorials are JavaScript; the Spatial Thoughts deep-dive is Code Editor; the provider table is long and interesting.

**How to avoid:**
- Time budget per module from the report (360 min total) is a hard constraint in each script; scripts carry a word count (~130 wpm).
- Rule: one workflow (search → classify → change → validate) taught in full on AlphaEarth; each other provider gets **one** repeated operation on the *same* labels and folds. Portability is the lesson, not coverage.
- Clay encoder demo is optional, separate `uv` environment, CPU-only, ≤ 10 min; OlmoEarth and Custom Satellite Embeddings are slides.
- JavaScript appears only as "the tutorial you may have seen; here is the Python equivalent."

**Warning signs:**
- Any notebook with `torch` in the core environment.
- A module's script exceeding its minute budget by > 15 %.

**Phase to address:** Phase 2 (Module 1 kept conceptual), Phase 3 (`04_embedding_ecosystems` one-operation rule), Phase 5/6 (budgets).

---

## Moderate Pitfalls

### Sentinel-2 raw-pixel baseline built on inconsistent reflectances
**What goes wrong:** Scenes after 2022-01-25 (processing baseline 04.00) have DN shifted by +1000. A raw-pixel baseline mixing 2020 and 2024 values learns the offset, not land cover, and compares unfairly with AEF.
**Prevention:** Use `COPERNICUS/S2_SR_HARMONIZED` (or apply the offset yourself), scale by 0.0001, document in provenance; store the baseline features in the same frozen parquet as the embeddings so the comparison is apples-to-apples. Phase 1.

### Single-pixel query vectors and un-normalised prototypes
**What goes wrong:** Search-by-example from one noisy pixel; or a polygon-mean prototype not renormalised → dot product no longer equals cosine, scores biased low.
**Prevention:** Prototype = normalised mean of several positives (optionally minus negatives); show the instability of a one-pixel query as a teaching cell. Phase 1.

### Assuming every provider's vectors are unit length
**What goes wrong:** Dot-product shortcut applied to TESSERA (normalisation undocumented), Clay (1024-D float32, not normalised), LGND. Cross-provider similarity numbers become incomparable.
**Prevention:** `normalize_rows()` before any cosine, `assert` on norms after load, per provider. Phase 3.

### Reporting a single accuracy number
**What goes wrong:** Imbalanced classes (built vs vegetation) → 90 % accuracy with zero built recall.
**Prevention:** Always per-class precision/recall, macro F1 or balanced accuracy, confusion matrix, and an **error map**. Phase 1; retrieval uses precision@k. Phase 3 adds IoU / commission-omission for change.

### "10 m pixel" read as "10 m object resolving power"; mixing spatial units
**What goes wrong:** Students expect individual buildings; or compare AEF 10 m pixels with LGND 2,560 m chips as if equivalent.
**Prevention:** Module 1 pixel/patch/location taxonomy slide with concrete footprints; in `04_embedding_ecosystems`, aggregate AEF to the chip footprint (mean + renormalise) before comparing. Phase 2/3.

### Year-to-year classifier transfer assumed free
**What goes wrong:** Train on 2020 labels, predict 2024, call differences "change." The Swiss LCZ study with AEF and TESSERA notes "the transfer of embedding-based models from one year to another remains an open challenge."
**Prevention:** Change lab trains per-year models or validates the transferred model on 2024 stable controls first; report the temporal transfer gap alongside the spatial gap. Phase 3.

### Frozen dataset too clean or too small to show the lesson
**What goes wrong:** Three trivially separable classes → random and block CV both ≈ 99 %, the leakage lesson evaporates; or a few hundred rows → CV variance swamps the gap.
**Prevention:** A few thousand rows, ≥ 2 regions, 3–4 classes including a confusable pair (grass vs crops, bare vs built), hard negatives from block edges; verify the random-vs-block gap on the frozen data *before* freezing it. Phase 1.

### Swath / data-availability artifacts read as change or as class boundaries
**Prevention:** Show one example, cite the catalog caveat, and use stable controls (water, old forest) to estimate the noise floor of the change score. Phase 3.

### Earth Engine interactive limits in the live path
**What goes wrong:** `sampleRegions(...).getInfo()` on thousands of points × 64 bands → memory/5,000-element errors mid-lecture.
**Prevention:** `reduceRegions` for points, `.limit()`, or `Export.table.toDrive`; sample ≤ 2–3 k points live; note quota tier. Phase 2.

### Kernel/Python mismatch between Colab and local
**What goes wrong:** Local env on 3.13/3.14, Colab on 3.12.13 → different wheels, different numerics, "works locally" bugs.
**Prevention:** `uv python pin 3.12`; `requires-python = ">=3.12,<3.13"` in `pyproject.toml`; CI matrix = 3.12 only. Phase 1.

---

## Minor Pitfalls

- **Broken "Open in Colab" badges:** URL must be `https://colab.research.google.com/github/{user}/{repo}/blob/{branch}/{path}.ipynb`; badges pointing at `main` break when notebooks move — point at a release tag once recorded. Phase 4/Cross-cutting.
- **Large binaries in git:** rasters and parquet in the repo bloat clones and Colab fetches; LFS adds bandwidth cost. Host data on a Hugging Face dataset repo or GitHub release assets (ISPRS pattern), keep the repo < 50 MB. Cross-cutting.
- **Hard-coded visualisation stretch** (`min=-0.3, max=0.3`) presented as meaningful; say "display stretch." Phase 2.
- **`geemap` not preinstalled on Colab** (only `ee` is); the Colab install cell must include it. Phase 2. [MEDIUM]
- **Duplicated helper code drifting across notebooks:** if helpers are inlined, CI should assert the inlined `dequantize_aef` / `normalize_rows` text is identical across notebooks (or install one tagged package). Phase 1.
- **Recording before pinning:** re-executed notebooks produce different numbers than the video; pin, freeze, then record. Phase 6.

---

## Technical Debt Patterns

| Shortcut | Immediate Benefit | Long-term Cost | When Acceptable |
|----------|-------------------|----------------|-----------------|
| Extract frozen data through Earth Engine instead of GCS COGs | Familiar API, quick | Provenance tied to an EE project/quota; noncommercial-terms grey zone for a paid course | Only if GCS access fails; record `DATASET_VERSION` etc. from image properties |
| Dynamic World as the only labels | Instant labels, same grid | Circular validation; low built/bare consistency | Exploratory labelling only, disclosed; never as validation |
| `train_test_split` shown "for comparison" without a block split beside it | Fewer cells | Students copy the wrong pattern | Never |
| Hand-copied exercise notebooks | No tooling | Drift within weeks | Never after Phase 1 |
| Unpinned `pip install` in Colab cell | Always latest | Notebook breaks on any upstream release | Never; pin to `requirements-colab.txt` at a tag |
| Skip `assert` on norms/CRS/transform | Cleaner cells | Silent wrong numbers | Never in solution notebooks; may be hidden tests in exercises |
| Single region in frozen data | Smaller file | Leave-region-out impossible | Never for the course dataset |
| Inline helpers duplicated per notebook | Self-contained notebooks | Drift between copies | Acceptable if CI checks copies are identical |
| Bundle CDSE embeddings samples | Complete offline lab | Redistribution licence unknown | Never until CDSE states a licence |

## Integration Gotchas

| Integration | Common Mistake | Correct Approach |
|-------------|----------------|------------------|
| Earth Engine auth | `ee.Initialize()` without `project`; unregistered project; assuming "free for everyone" | `ee.Authenticate(); ee.Initialize(project=EE_PROJECT)`; project registered + API enabled; say "check current eligibility and quotas"; Community tier = 150 EECU-h/month |
| Earth Engine local JupyterLab (no gcloud) | Expecting the old paste-token flow | Default `auth_mode='localhost'` (browser on same machine) or `'notebook'` (choose an auth project); credentials cached in `~/.config/earthengine/credentials` |
| Earth Engine CI | Committing a service-account key | Secret → `ee.ServiceAccountCredentials(email, key_path)`; project registered |
| Satellite Embedding collection | `.first()` or `.mosaic()` then sampling without `scale=10` | `filterDate(...).filterBounds(...).mosaic()` + explicit `scale=10`/`crs`; record `DATASET_VERSION`, `MODEL_VERSION`, `UTM_ZONE` |
| GCS COGs | Reading int8 as embeddings; forgetting `-128` | `GS_NO_SIGN_REQUEST=YES`, `/vsigs/alphaearth_foundations/...`, `dequantize_aef` |
| Source Coop AEF mirror | Opening `.tif` directly (bottom-up rasters) | Open the provided `.vrt`; note "unofficial mirror" in provenance |
| GeoTessera | No `dataset_version`, mixing versions/variants, AEF dequant formula | `GeoTessera(dataset_version="v1")`, `year=2024`, `int8 * scales`, read GeoTIFF tags |
| LGND open corpus | Pointing at `lgnd-clay-v1-5-sentinel-2-l2a` expecting monthly 2017–2026 | Use `clay/lgnd-embeddings` for monthly; pin `s3://us-west-2.opendata.source.coop/...` path + partition in provenance |
| LGND API | Inventing an SDK; hard-coding token | `requests`/`httpx` against the OpenAPI reference; `os.environ["LGND_TOKEN"]`; live-only cell |
| Sentinel-2 via EE | `COPERNICUS/S2_SR` across the 2022 baseline shift | `COPERNICUS/S2_SR_HARMONIZED`, scale 0.0001 |
| HRL Imperviousness | Comparing to AEF 2020–2024; using 2015→2018 | AEF 2018 vs 2021 against Change 2018–2021 (EPSG:3035, 20 m); reproject points |
| CDSE embeddings | Bundling parquet samples | Stream from EODATA S3 live-only; cite Czerkawski et al. 2024 |

## Performance Traps

| Trap | Symptoms | Prevention | When It Breaks |
|------|----------|------------|----------------|
| `sampleRegions(...).getInfo()` in the live path | "User memory limit exceeded" / 5,000-element abort | `reduceRegions`, `.limit()`, or table export | > ~5 k points × 64 bands interactively |
| Reading whole 8192² × 64 int8 COG tiles | 4 GB+ per tile in RAM after float conversion | Windowed reads by AOI; keep int8 until needed; use overviews for display | Any full-tile read |
| Brute-force cosine over a full AOI raster in Colab | Kernel OOM | Flatten only the AOI, float32, `np.einsum`; `sklearn.neighbors`/`faiss-cpu` only if demonstrating scale | > ~10–20 M pixels × 64 on free Colab |
| Random Forest with `n_estimators=300` on tens of thousands of rows in 5-fold × 3 split schemes | Minutes per cell in a 65-min module | Few thousand rows in frozen data; `n_jobs=-1`; cache results with `joblib` | Frozen data > ~20 k rows |
| GeoTessera downloading many 0.1° tiles live | Slow, coverage gaps, manifest revalidation | Pre-fetch a small exported GeoTIFF for Path B | Any live tile fetch in lecture |
| Earth Engine noncommercial "restricted mode" | Everything slow, no error | Keep live cells light; explain restricted mode | Project past 150 EECU-h in a month |

## Security Mistakes

| Mistake | Risk | Prevention |
|---------|------|------------|
| Service-account JSON or `LGND_TOKEN` committed | Credential abuse against the author's GCP/LGND accounts | `.gitignore`, `getpass`/env, secret scanning in CI, revoke on leak |
| Students told to paste tokens into shared Colabs | Token leakage | Colab Secrets / `getpass`; never print tokens |
| Notebooks that write to the author's GCS/Drive by default | Accidental writes, cost | Path B writes only to `DATA_DIR`; exports opt-in |
| Treating inferred maps as innocuous because imagery is public | Sensitive inference (activity, locations) | Module 6 rule: "is the inferred information more sensitive than the underlying public imagery?" |

## UX Pitfalls (student experience)

| Pitfall | User Impact | Better Approach |
|---------|-------------|-----------------|
| First cell requires Earth Engine | Paid course blocked at minute 1 | Frozen data first; live path clearly optional |
| Exercise checkpoints without expected shapes/ranges | Students cannot tell whether they are right | Checkpoint asserts with messages; hidden tests in generated exercises |
| Long silent cells | Students think Colab hung | Progress prints/`tqdm`; pre-fetched small data |
| Only a scalar metric | No intuition about failure | Error maps, nearest-neighbour distance plots, random-vs-block bar chart |
| Different numbers in video vs notebook | Loss of trust | Pin, freeze, seed, then record |
| Mixed JavaScript/Python | Cognitive load, wrong copy-paste | Python only; JS mentioned as "the tutorial you may have seen" |

## "Looks Done But Isn't" Checklist

- [ ] **Frozen dataset:** often missing `block_id`, `region`, `year`, `label_source`, `validation_source`, `dataset_version`, `attribution` columns — verify schema and that random-vs-block gap reproduces
- [ ] **Norm assert:** often missing after every load (`np.allclose(norms, 1)`) — verify present in every notebook that touches embeddings
- [ ] **CRS discipline:** often missing `assert transform/crs equal` before differencing; block sizes in degrees — verify projected CRS printed
- [ ] **Change lab:** often missing unchanged controls and calibrated threshold; year pair mismatched with reference — verify AEF 2018/2021 vs HRL 2018–2021
- [ ] **Validation independence:** often `validation_source == label_source` (Dynamic World) — verify they differ
- [ ] **Auth cell:** often missing `project=`, missing fallback — verify notebook completes with `LIVE=False`
- [ ] **Colab parity:** often missing `requirements-colab.txt` pin and `IN_COLAB` branch — verify a fresh Colab run
- [ ] **Exercises:** often hand-edited — verify regenerated from markers and byte-identical
- [ ] **Attribution:** often one blanket CC BY line — verify per-source strings present (AEF, DW, Sentinel "Contains modified…", CLMS "Generated using…", BFS)
- [ ] **Provenance:** often "record-from-source" placeholder left in the dict — verify real `DATASET_VERSION`/`MODEL_VERSION` values
- [ ] **Scripts:** often over budget — verify word count vs module minutes
- [ ] **Slides:** often "vegetation axis" wording — verify against the phrasing rule

## Recovery Strategies

| Pitfall | Recovery Cost | Recovery Steps |
|---------|---------------|----------------|
| Frozen data built from raw int8 | HIGH (re-extract, re-run, re-record) | Re-extract with `dequantize_aef`; regenerate all notebooks; check norms |
| Leakage discovered after recording | HIGH | Re-cut dataset with blocks/regions; re-execute; re-record the affected module |
| Wrong reference years in change lab | MEDIUM | Swap to 2018/2021 + HRL Change 2018–2021; re-execute Module 4 only |
| Upstream library break | LOW–MEDIUM | Lockfile pins protect students; fix in a new tag; badges point at tags |
| AEF dataset re-versioned (like v1.1/2017) | LOW | Provenance shows the version; add a "why numbers differ" note; re-freeze at the next release |
| Licence issue found in a bundled file | MEDIUM | Remove file, force-push is not enough — publish a new release, add notice, move source to live-only |
| Exercise/solution divergence | LOW | Regenerate exercises from markers; CI gate |
| EE eligibility/quota change | LOW | Path B already works; update one slide |

## Pitfall-to-Phase Mapping

| Pitfall | Prevention Phase | Verification |
|---------|------------------|--------------|
| 1 int8/dequantisation | Phase 1 (helper + frozen data), Phase 2 (COG lesson) | Norm assert passes; no values outside [-1, 1]; `-128` masked |
| 2 Random-split leakage | Phase 1 | Random vs block gap reproduced on frozen data; NN-distance plot |
| 3 Blocks built wrongly | Phase 1 (dataset design) | Projected CRS; `n_groups ≥ n_splits`; all classes per fold; two regions |
| 4 Over-correction (Wadoux) | Phase 1 cell, Phase 5/6 wording | Slides/scripts state which question each metric answers |
| 5 `1 − cosine` ≠ transition | Phase 3 | WRONG cell + calibrated threshold + transition matrix + baseline-aware features |
| 6 Model-vs-model validation; year misalignment | Phase 1 (label provenance), Phase 3 | `validation_source ≠ label_source`; AEF 2018/2021 vs HRL 2018–2021; Arealstatistik used |
| 7 CRS/scale/alignment | Phase 2, Phase 1, Phase 3 | `scale=10` everywhere in EE; transform/crs assert before differencing |
| 8 Axes as physical variables | Phase 2, Phase 5/6 | Caption/script grep for "measures", "vegetation axis" |
| 9 Credential hard-dependence; EE auth | Phase 1 pattern, Phase 2 auth cell, Cross-cutting | Every notebook runs with `LIVE=False`; no secrets in git |
| 10 Version rot | Phase 1 (lock, banner), Phase 3, Cross-cutting | `uv lock` committed; monthly CI re-execution; provenance versions real |
| 11 Hidden state / paths / Colab divergence | Phase 1 template, all phases | CI `Restart & Run All`; fresh Colab run; no absolute paths |
| 12 Exercise drift | Phase 1 markers, Phase 4 tooling | Regenerated == committed; solution passes hidden tests |
| 13 Licensing | Phase 1, Phase 3 (Module 6), Cross-cutting | `ATTRIBUTION.md` per source; CDSE not bundled |
| 14 Scope drift | Phase 2, Phase 3, Phase 5/6 | No `torch` in core env; script minutes within budget; Python only |

## Sources

**Official documentation (HIGH)**
- AlphaEarth Foundations GCS data README — quantisation formula, `-128` nodata, unit norm, overview construction, provider-pays (July 2026), 2017–2025, UTM tiling, attribution: https://developers.google.com/earth-engine/guides/aef_on_gcs_readme
- Earth Engine Satellite Embedding catalog — 2017–2024 availability, v1.1 (2025-11-17) regenerated 2017, swath artifacts, bands not independently interpretable, image properties (`DATASET_VERSION`, `MODEL_VERSION`, `PROCESSING_SOFTWARE_VERSION`, `UTM_ZONE`), local UTM per image: https://developers.google.com/earth-engine/datasets/catalog/GOOGLE_SATELLITE_EMBEDDING_V1_ANNUAL
- Satellite Embedding tutorial 01 (mosaic loses UTM projection; `scale: 10`; unit length): https://developers.google.com/earth-engine/tutorials/community/satellite-embedding-01-introduction
- Satellite Embedding tutorial 03 (kNN, ~10 points/class, no split or accuracy reported): https://developers.google.com/earth-engine/tutorials/community/satellite-embedding-03-supervised-classification
- Earth Engine auth guide (modes table, project requirement, paste mode removed): https://developers.google.com/earth-engine/guides/auth
- Earth Engine access/registration and noncommercial verification: https://developers.google.com/earth-engine/guides/access
- Earth Engine noncommercial tiers (150 / 1,000 / 100,000 EECU-h; restricted mode; from 2026-04-27): https://developers.google.com/earth-engine/guides/noncommercial_tiers
- Earth Engine quotas (concurrency, 429 backoff, memory limits): https://developers.google.com/earth-engine/guides/usage
- Earth Engine service accounts: https://developers.google.com/earth-engine/guides/service_account
- Earth Engine noncommercial eligibility ("may charge for training services, not for use of Earth Engine"): https://earthengine.google.com/noncommercial/
- Earth Engine best practices (5,000-element limit, `limit()`/`filter()`): https://developers.google.com/earth-engine/guides/best_practices
- Dynamic World catalog (CC BY 4.0 attribution, single-image NRT model output): https://developers.google.com/earth-engine/datasets/catalog/GOOGLE_DYNAMICWORLD_V1
- Sentinel-2 SR Harmonized (baseline 04.00 shift, scale 0.0001): https://developers.google.com/earth-engine/datasets/catalog/COPERNICUS_S2_SR_HARMONIZED
- GeoTessera README and docs (Python ≥3.12, `dataset_version`/`variant`, `int8 * scales`, do-not-mix warning, 2025-08-20 tiling fix, manifest revalidation): https://github.com/ucam-eo/geotessera , https://geotessera.readthedocs.io/en/latest/
- TESSERA paper (128-D, QAT int8, CC BY 4.0 embeddings, spatial CV): https://arxiv.org/html/2506.20380v5
- Clay documentation (Apache-2.0 / CC BY / ODC-BY): https://clay-foundation.github.io/model/index.html
- LGND products on Source Coop: https://source.coop/clay/lgnd-embeddings , https://source.coop/clay/lgnd-clay-v1-5-sentinel-2-l2a ; AWS registry yaml: https://github.com/awslabs/open-data-registry/blob/main/datasets/lgnd-clay-v1-5-sentinel2.yaml
- Source Coop AEF mirror (bottom-up COGs, `.vrt`): https://source.coop/tge-labs/aef
- Copernicus Sentinel Data Legal Notice ("Contains modified Copernicus Sentinel data [Year]"): https://sentinels.copernicus.eu/documents/247904/690755/Sentinel_Data_Legal_Notice
- CDSE terms and conditions; CDSE Global Embeddings docs (no explicit licence): https://dataspace.copernicus.eu/terms-and-conditions , https://documentation.dataspace.copernicus.eu/Data/ComplementaryData/Embeddings.html
- Copernicus Land Monitoring Service FAQ (attribution wording; open use): https://land.copernicus.eu/en/faq
- HRL Imperviousness 2021 / Change 2018–2021 (10 m status, 20 m change, EPSG:3035, "validation pending"): https://land.copernicus.eu/en/products/high-resolution-layer-imperviousness/imperviousness-density-change-2018-2021 , https://land.copernicus.eu/en/news/product-update-high-resolution-layer-imperviousness-2021
- ETC/ULS report on HRL Imperviousness 2015–2018 time-series break: https://www.eionet.europa.eu/etcs/etc-di/products/etc-di-products/etc-uls-technical-report-01-2021-time-series-inconsistency-in-the-copernicus-hrl-imperviousness-analysis-of-the-2015-2018-changes-implications-and-conclusions
- Swiss Arealstatistik (OPEN BY, EPSG:2056, 100 m points): https://www.geocat.ch/geonetwork/srv/api/records/f0b56783-613d-4664-9216-98442ce1994d?language=eng
- GDAL `/vsigs/` (`GS_NO_SIGN_REQUEST`, `GS_USER_PROJECT`): https://gdal.org/en/stable/user/virtual_file_systems.html
- Colab runtime FAQ (Python 3.12.13, runtime 2026.07): https://research.google.com/colaboratory/runtime-version-faq.html
- scikit-learn `GroupKFold` / `StratifiedGroupKFold` (Context7 `/websites/scikit-learn_stable`)
- nbgrader assignment generation (solution markers): https://nbgrader.readthedocs.io/en/stable/user_guide/creating_and_grading_assignments.html
- PyPI metadata checked 2026-09-03: rasterio 1.5.1 (>=3.12, cp312–cp315 macOS arm64), rioxarray 0.23.0 (>=3.12), geemap 0.38.4 (>=3.12), earthengine-api 1.7.42, geotessera 0.10.1 (>=3.12), torch 2.14.0 (cp310–cp314/cp314t macOS arm64), duckdb 1.5.5, faiss-cpu 1.15.0, stackstac 0.5.1 (2024-08-10); local `uv pip compile` on 3.12 and 3.14 both resolve.

**Google/industry analyses (MEDIUM–HIGH)**
- Google Earth, "Rethinking Change Detection and Attribution: How You Compare Satellite Embeddings Matters" (2026-04-13) — dot-product-only false positives, baseline-aware features, 200+200 samples: https://medium.com/google-earth/rethinking-change-detection-and-attribution-how-you-compare-satellite-embeddings-matters-858f17f577d7
- Google Earth, "AlphaEarth Foundations Satellite Embeddings: Now Available on GCS" (provider-pays): https://medium.com/google-earth/alphaearth-foundations-satellite-embeddings-now-available-on-google-cloud-storage-f9ab0f7252d6
- Isaac Corley, "The Technical Debt of Earth Embedding Products" (CNG, 2026-02-28) — metadata, quantisation, format fragmentation: https://cloudnativegeo.org/blog/2026/02/the-technical-debt-of-earth-embedding-products/
- A. Zuspan, "Efficiently Exporting AlphaEarth Embeddings from GEE" (2025-08-14) — re-quantisation, storage: https://www.aazuspan.dev/blog/efficiently-exporting-alphaearth-embeddings-from-gee/
- ISPRS 2026 embeddings tutorial (Hugging Face-hosted frozen data, Colab badges, continent holdout): https://github.com/konstantinklemmer/isprs26-embeddings-tutorial

**Peer-reviewed literature on validation (HIGH for the claims cited)**
- Ploton et al. 2020, spatial autocorrelation leakage: https://link.springer.com/article/10.1007/s10994-021-05972-1 (Springer ML, related), and Kattenborn et al. 2022 (CNN inflation up to ~28 %): https://www.sciencedirect.com/science/article/pii/S2667393222000072
- Roberts et al. 2017 / Valavi et al. 2019 blockCV — block size from autocorrelation range: https://besjournals.onlinelibrary.wiley.com/doi/10.1111/2041-210X.13107
- Wadoux et al. 2021, "Spatial cross-validation is not the right way to evaluate map accuracy": https://alexandrewadoux.github.io/assets/pdf/Wadoux_et_al_2021.pdf
- "Moving beyond spatial and random cross-validation… prediction-domain adaptive evaluation" (2026; kNNDM): https://arxiv.org/abs/2605.13689
- AlphaEarth vs TESSERA for LCZ mapping in five Swiss cities (year-to-year transfer open challenge): https://arxiv.org/abs/2606.20034
- Dynamic World built/bare consistency vs other 10 m products: https://www.mdpi.com/2072-4292/14/16/4101

**Community / single-source (LOW, flagged inline)**
- Colab `geemap` not preinstalled; `odc-stac` as `stackstac` fallback — author judgement, not verified today.

---
*Pitfalls research for: Introduction to Geospatial Embeddings (Udemy course materials)*
*Researched: 2026-09-03*

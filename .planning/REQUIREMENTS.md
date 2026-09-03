# Requirements: Introduction to Geospatial Embeddings

**Defined:** 2026-09-03
**Core Value:** A student can take a precomputed geospatial embedding field, run similarity search and a lightweight classifier on it, and evaluate the result with a spatially honest validation — and that entire workflow runs from a notebook without needing an Earth Engine account.

**Build order (fixed by the author):** solution notebook for Module 3 (similarity + classification) first, then the earlier modules' solution notebooks, then the later modules' solution notebooks, then exercise notebooks, slides and scripts derived from them. Working notebook first, solution before exercise, always.

## v1 Requirements

Requirements for the first complete course release. Each maps to roadmap phases.

### Environment & Repository

- [ ] **ENV-01**: Author can run `uv sync` on the repo and get a working JupyterLab kernel on Python 3.12 (`requires-python >=3.12,<3.14`) with the pinned core stack (numpy, pandas, pyarrow, geopandas, shapely, pyproj, scikit-learn, matplotlib, rasterio, xarray) and a committed `uv.lock`
- [ ] **ENV-02**: Every notebook opens with one Setup cell that detects Colab, pip-installs pinned dependencies only on Colab, imports everything, and sets `RANDOM_STATE` and dataset-version constants
- [ ] **ENV-03**: Repo README lists every notebook with an "Open in Colab" badge, local run instructions, all data sources with licenses, and the banner "Course reference environment: 2026-08 release. Provider APIs may change. Every cloud notebook has a local/offline fallback."
- [ ] **ENV-04**: Author can run one make/task target that executes every solution notebook headlessly against the frozen data and fails on any cell error
- [ ] **ENV-05**: Heavy or credentialed dependencies (earthengine-api, geemap, geotessera, duckdb, torch/Clay) are optional extras or a separate uv project so the core environment stays light and Colab-installable in under two minutes

### Frozen Teaching Datasets

- [ ] **DATA-01**: Point tables exist for two geographically distinct regions (Region A: Bern/Swiss Plateau; Region B: a distinct transfer region) sharing one schema: `A00..A63` float32 dequantized unit-norm, `lon`, `lat`, projected `x`/`y` (or GeoParquet geometry), `year`, `label`, `label_source`, `region`, `block_id`
- [ ] **DATA-02**: Each point row also carries Sentinel-2 bands (`B2..B12`) so a raw-band baseline runs on the same points
- [ ] **DATA-03**: Tables cover at least two years for the same points, aligned with an independent change reference (e.g. 2018 and 2021 to match Copernicus HRL Imperviousness change), so the change lab reuses them
- [ ] **DATA-04**: Each table is a few thousand rows and about 1 MB or less; the entire course data bundle stays under 100 MB
- [ ] **DATA-05**: Data ships with a provenance JSON per table: `embedding_product`, `dataset_version`, `year`, `extraction_date`, source path, `sampling_method`, `crs`, `label_source`, `validation_source`, `license`, exact attribution sentence, `created_by`, `sha256`
- [ ] **DATA-06**: Data ships with a dataset card (description, license, sources, structure, creation, limitations, citation) carrying the exact AlphaEarth attribution ("The AlphaEarth Foundations Satellite Embedding dataset is produced by Google and Google DeepMind", CC BY 4.0) and per-source licenses; sources without redistribution rights (Copernicus Global Embeddings) are never bundled
- [ ] **DATA-07**: Author can regenerate every table with committed prep scripts from no-login sources: AlphaEarth GCS COGs (anonymous read, documented int8 square-root dequantization then renormalization, `-128` nodata), an open label raster, and STAC Sentinel-2; Earth Engine is an optional alternative path, never a prerequisite
- [ ] **DATA-08**: Dataset tests assert unit norms within 1e-3 of 1, no NaN, the expected column set, minimum class counts per region, CRS present, and at least five spatial blocks per region
- [ ] **DATA-09**: Data is hosted publicly with no login (GitHub release assets or a public Hugging Face dataset) at a pinned release/revision with checksums, and notebooks fetch local-first with remote fallback
- [ ] **DATA-10**: A small GeoJSON of candidate query polygons (e.g. solar farm, quarry, new development) ships with the data so search-by-example works without a live map

### Similarity Search & Classification Notebook (Module 3 flagship, `02_similarity_and_classification.ipynb`)

- [ ] **SIM-01**: Notebook header states title, Colab badge, overview, numbered learning objectives, prerequisites table, time to complete, and "runs on free Colab CPU, no Earth Engine account"
- [ ] **SIM-02**: Student loads both region tables, sees the schema, class counts and a map of points coloured by label, and an assertion cell proves 64 dimensions and unit norm with a Takeaway that dot product equals cosine on this data
- [ ] **SIM-03**: Student runs search-by-example from a single-pixel query using an einsum-based `cosine_similarity_map`, and sees a top-k table, a map of matches, and a histogram of similarities
- [ ] **SIM-04**: A "WRONG conclusion" cell asserts "similarity > 0.90 means same land cover", followed by markdown explaining why a fixed threshold is arbitrary and ranking plus precision@k is the honest alternative
- [ ] **SIM-05**: Student builds a renormalized polygon-mean prototype and a positive-minus-negative prototype, compares the three query designs by precision@k against labels, and can change `QUERY_ID` and `K` through marked "EDIT ME" knobs
- [ ] **SIM-06**: Student trains a 2–4 class `Pipeline(StandardScaler, LogisticRegression)` and a `RandomForestClassifier(class_weight="balanced")` with a random split and sees accuracy plus a rendered confusion matrix explicitly labelled as the trap number
- [ ] **SIM-07**: Student reprojects to EPSG:2056, builds spatial blocks with `make_blocks`, runs `GroupKFold` `cross_validate` with `balanced_accuracy` and `f1_macro`, and runs leave-region-out on Region B
- [ ] **SIM-08**: One bar chart compares random split vs spatial-block CV vs leave-region-out for the same model, accompanied by per-class precision/recall and a map of where errors occur
- [ ] **SIM-09**: The identical pipeline and CV run on Sentinel-2 raw bands, with a comparison table and Takeaway contrasting embeddings vs raw bands under honest validation
- [ ] **SIM-10**: A provenance cell writes `outputs/provenance.json` with product, `dataset_version`, year, CRS, label source, validation source, license, attribution sentence and `created_by`
- [ ] **SIM-11**: Every experiment ends with a Takeaway cell; the notebook closes with a Wrap-up (3–5 bullets), What's next, Resources with URLs/versions/licenses, and a non-executed Path A appendix showing illustrative Earth Engine sampling code
- [ ] **SIM-12**: Reusable helpers (`cosine_similarity_map`, `make_blocks`, `spatial_cv_report`, provenance builder) live in an importable course utility module with unit tests, and the notebook imports them so later notebooks reuse the same code
- [ ] **SIM-13**: Notebook passes Restart & Run All locally and on a fresh Colab CPU runtime in about three minutes, has roughly 40 cells none longer than about 40 lines, every Takeaway claim is visible in the output above it, and figures are saved to `figures/02_*.png`

### Earlier Module Notebooks

- [ ] **EARLY-01**: `00_embedding_refresher.ipynb` covers NumPy vectors, L2 normalization, cosine similarity, PCA on a toy embedding matrix, a tiny classifier with a train/test split, and a CRS reminder reprojecting a GeoDataFrame, in about 25 minutes
- [ ] **EARLY-02**: The foundations module has a short hands-on notebook inspecting several representations of the same location — an AlphaEarth 64-D pixel vector, a Clay patch embedding from the open LGND GeoParquet corpus, and (optional, if torch is available) a SatCLIP location embedding — comparing shape, spatial unit, temporal support and metadata
- [ ] **EARLY-03**: `01_alphaearth_access_visualize.ipynb` Path A lets a student with Earth Engine access authenticate with a project ID, load `GOOGLE/SATELLITE_EMBEDDING/V1/ANNUAL` for an AOI near Bern for 2024, inspect the 64 bands, display three axes as pseudo-RGB with geemap, and sample/export an embedding table
- [ ] **EARLY-04**: The same notebook's Path B runs identical downstream cells from a small clipped AlphaEarth GeoTIFF/parquet bundled with the course data, including the int8 dequantization formula, unit-norm check, and static pseudo-RGB and PCA plots
- [ ] **EARLY-05**: The visualization notebook poses "why does this map look geographically structured although the three axes have no RGB meaning?" and states the phrasing rule "this component separates these landscape types in this sample", never "component 3 measures vegetation"

### Later Module Notebooks

- [ ] **LATE-01**: `03_change_detection_and_validation.ipynb` pairs year-aligned AlphaEarth tables, computes the cosine change score, shows the "WRONG: artificialized = change_score > 0.25" cell, calibrates a threshold with `precision_recall_curve` against independent change labels, and reports precision/recall/F1 on changed and unchanged controls
- [ ] **LATE-02**: The same notebook trains per-year classifiers, produces a class-transition matrix and a vegetation-to-built artificialization mask, compares it with the continuous change score, and validates with spatially and temporally grouped CV
- [ ] **LATE-03**: `04_embedding_ecosystems.ipynb` repeats one similarity or classification operation on TESSERA embeddings via geotessera and on open Clay GeoParquet via DuckDB using the same course helpers, and inspects/asserts vector norms per provider before reuse
- [ ] **LATE-04**: The same notebook contains LGND REST cells guarded by token presence with a recorded response fixture as fallback, an optional local Clay encoder section pointing to the isolated environment, and an OlmoEarth comparison (custom temporal windows vs annual fields) in markdown
- [ ] **LATE-05**: `05_capstone_artificialization.ipynb` is an end-to-end template (AOI → features → predictions → validation → map → uncertainty and provenance) with the capstone rubric checklist and provenance dict pre-filled
- [ ] **LATE-06**: The production/provenance module provides a model/data card template and a provenance checklist students apply to a previous lab's outputs, with exact attribution strings and license notes for every provider used in the course

### Exercise Notebooks

- [ ] **EXER-01**: A unit-tested generator script derives an exercise notebook from a tagged solution notebook (cell tags such as `solution`, `stub`, `hidden-test`), replacing solution code with a consistent stub, runnable via a make target
- [ ] **EXER-02**: Every solution notebook has a derived exercise notebook with the same narrative, data and headings, where roughly 30–40% of code cells targeting the learning code (not I/O boilerplate) become tasks
- [ ] **EXER-03**: Every task has a checkpoint assert with a friendly message and an expected-output hint, with at least one visible test per task
- [ ] **EXER-04**: Solutions are available on demand via collapsible details or a link to the solution notebook, and running all cells never spoils them
- [ ] **EXER-05**: Each exercise notebook executes cleanly up to the first stub, and ends with reflection prompts and stretch tasks

### Slide Decks

- [ ] **SLIDE-01**: One markdown-sourced 16:9 deck per module (eight including the refresher) is generated to PDF/HTML from the repo, with objectives and recap slides mirroring the notebook's objectives
- [ ] **SLIDE-02**: Decks embed figures exported from the solution notebooks (never manual screenshots) and the concept diagrams: pixel/patch/location taxonomy, provider decision flowchart, analytical chain, and "1 − cosine measures representation movement"
- [ ] **SLIDE-03**: Decks contain WRONG-conclusion slides mirroring the notebook trap cells, an attribution/license slide, and a version-banner slide
- [ ] **SLIDE-04**: Every slide carries speaker notes that serve as the first draft of the narration
- [ ] **SLIDE-05**: The ecosystems deck includes the provider comparison table; the foundations deck includes the "Custom Satellite Embeddings: private preview, watch this space" slide

### Narration Scripts

- [ ] **SCRIPT-01**: One recording-ready script per module in two-column AV format (VISUAL | AUDIO) with per-row duration and cumulative timing marks
- [ ] **SCRIPT-02**: Each module is segmented into lectures of 2–7 minutes (codealongs up to 12), each with an objective line, a recap line and an end-state line, and module totals match the syllabus (360 minutes overall)
- [ ] **SCRIPT-03**: Every row anchors to a notebook cell heading or slide number and uses explicit cue tokens ([RUN CELL], [ZOOM], [PAUSE], [CUT])
- [ ] **SCRIPT-04**: The key teaching messages appear verbatim (unit-length so dot equals cosine; A17 is not NDVI; random splits leak spatially; Dynamic World is a model output; 1 − cosine is not a semantic transition) and pronunciation notes are included
- [ ] **SCRIPT-05**: Each script references the module's exercise tasks and quiz so video, notebook and assessment tie together

### Assessments

- [ ] **ASSESS-01**: The refresher has an ungraded 5-question diagnostic
- [ ] **ASSESS-02**: Each module has a 5–8 question conceptual-error multiple-choice quiz with per-option explanations that quote the notebook cell demonstrating the answer
- [ ] **ASSESS-03**: The similarity/classification, change-detection and ecosystems modules each have an assignment text (instructions, what to submit, rubric) matching the report's weights (15%, 20%, 20%, 10% portability)
- [ ] **ASSESS-04**: The capstone rubric is published (validation design 30%, reproducibility/provenance 15%, CRS/alignment 15%, interpretation/uncertainty 15%, representation choice 15%, licensing/ethics 10%) alongside a proposal template

## v2 Requirements

Deferred to a later release. Tracked but not in the current roadmap.

### Notebook Enhancements

- **SIM-14**: Few-shot curve (accuracy vs 5/10/25/100 samples per class under spatial CV) testing the "10 samples is enough" claim
- **DATA-11**: Dense grid table per region for offline classified-map rendering
- **DATA-12**: Two label sources side by side (`label_dw`, `label_copernicus`) so "Dynamic World is not independent ground truth" is demonstrable, not just stated (Dynamic World requires Earth Engine)
- **EXER-06**: Checker self-tests (hidden cells asserting each checkpoint fails on a wrong answer and passes on the right one), stripped by the generator
- **EXER-07**: Prose-stripped `clean/` notebooks for recall practice

### Delivery & Automation

- **ENV-06**: GitHub Actions CI executing every solution notebook and the dataset tests on a CPU runner on each push
- **ENV-07**: Per-lecture downloadable zips (notebook pair, data pointer, slides PDF) generated from a git tag for Udemy upload
- **ASSESS-05**: Udemy in-platform coding exercises for pure-NumPy steps, only after verifying the runner supports numpy
- **EARLY-06**: Interactive geemap Path A recordings as bonus lectures, after Earth Engine eligibility and quota are confirmed for the author

## Out of Scope

Explicitly excluded. Documented to prevent scope creep.

| Feature | Reason |
|---------|--------|
| Foundation-model pretraining, transformer/MAE mathematics, distributed GPU training | Six hours is insufficient; obscures the developer skills the course exists to teach |
| Full semantic-segmentation fine-tuning | Sequel-course material |
| Vector-database infrastructure (FAISS/UMAP demos as core content) | `sklearn.neighbors` and NumPy suffice; report excludes vector-DB engineering |
| Earth Engine JavaScript | Python only; one language |
| Lengthy GIS introduction | 25-minute optional refresher is the ceiling |
| Google Custom Satellite Embeddings lab | Private preview as of July 2026; one "watch this space" slide only |
| Inventing an LGND Python SDK dependency | Use `requests`/`httpx` against the OpenAPI reference |
| Live Earth Engine / geemap as the default execution path | Requires GCP project and eligibility; widgets do not render in review; breaks on quota; Path B is the default |
| Bundling raw AlphaEarth COG tiles, Sentinel-2 scenes, TESSERA tiles or Copernicus Global Embeddings | Size, provider egress and unverified redistribution terms; sampled tables plus one tiny clipped GeoTIFF only |
| Shipping raw int8 embedding values | Students would average int8 and break unit norm; ship dequantized float32 |
| Full nbgrader/JupyterHub autograding | Needs a server; Udemy students are anonymous; self-check asserts and rubrics instead |
| Video recording, editing, Udemy upload/publishing | Materials only; recording is the author's manual step after scripts exist |

## Traceability

Which phases cover which requirements. Populated by the roadmapper during roadmap creation.

| Requirement | Phase | Status |
|-------------|-------|--------|
| ENV-01 | Phase 1 | Pending |
| ENV-02 | Phase 1 | Pending |
| ENV-03 | Phase 1 | Pending |
| ENV-04 | Phase 1 | Pending |
| ENV-05 | Phase 1 | Pending |
| DATA-01 | Phase 2 | Pending |
| DATA-02 | Phase 2 | Pending |
| DATA-03 | Phase 2 | Pending |
| DATA-04 | Phase 2 | Pending |
| DATA-05 | Phase 2 | Pending |
| DATA-06 | Phase 2 | Pending |
| DATA-07 | Phase 2 | Pending |
| DATA-08 | Phase 2 | Pending |
| DATA-09 | Phase 2 | Pending |
| DATA-10 | Phase 2 | Pending |
| SIM-01 | Phase 3 | Pending |
| SIM-02 | Phase 3 | Pending |
| SIM-03 | Phase 3 | Pending |
| SIM-04 | Phase 3 | Pending |
| SIM-05 | Phase 3 | Pending |
| SIM-06 | Phase 3 | Pending |
| SIM-07 | Phase 3 | Pending |
| SIM-08 | Phase 3 | Pending |
| SIM-09 | Phase 3 | Pending |
| SIM-10 | Phase 3 | Pending |
| SIM-11 | Phase 3 | Pending |
| SIM-12 | Phase 3 | Pending |
| SIM-13 | Phase 3 | Pending |
| EARLY-01 | Phase 4 | Pending |
| EARLY-02 | Phase 4 | Pending |
| EARLY-03 | Phase 4 | Pending |
| EARLY-04 | Phase 4 | Pending |
| EARLY-05 | Phase 4 | Pending |
| LATE-01 | Phase 5 | Pending |
| LATE-02 | Phase 5 | Pending |
| LATE-03 | Phase 5 | Pending |
| LATE-04 | Phase 5 | Pending |
| LATE-05 | Phase 5 | Pending |
| LATE-06 | Phase 5 | Pending |
| EXER-01 | Phase 6 | Pending |
| EXER-02 | Phase 6 | Pending |
| EXER-03 | Phase 6 | Pending |
| EXER-04 | Phase 6 | Pending |
| EXER-05 | Phase 6 | Pending |
| ASSESS-01 | Phase 6 | Pending |
| ASSESS-02 | Phase 6 | Pending |
| ASSESS-03 | Phase 6 | Pending |
| ASSESS-04 | Phase 6 | Pending |
| SLIDE-01 | Phase 7 | Pending |
| SLIDE-02 | Phase 7 | Pending |
| SLIDE-03 | Phase 7 | Pending |
| SLIDE-04 | Phase 7 | Pending |
| SLIDE-05 | Phase 7 | Pending |
| SCRIPT-01 | Phase 8 | Pending |
| SCRIPT-02 | Phase 8 | Pending |
| SCRIPT-03 | Phase 8 | Pending |
| SCRIPT-04 | Phase 8 | Pending |
| SCRIPT-05 | Phase 8 | Pending |

**Coverage:**
- v1 requirements: 58 total
- Mapped to phases: 58
- Unmapped: 0 ✓

**By phase:**

| Phase | Name | Requirements |
|-------|------|--------------|
| 1 | Repository and Environment Scaffold | ENV-01..05 (5) |
| 2 | Frozen Two-Region Teaching Datasets | DATA-01..10 (10) |
| 3 | Similarity Search and Classification Notebook | SIM-01..13 (13) |
| 4 | Earlier Module Solution Notebooks | EARLY-01..05 (5) |
| 5 | Later Module Solution Notebooks | LATE-01..06 (6) |
| 6 | Exercise Notebooks and Assessments | EXER-01..05, ASSESS-01..04 (9) |
| 7 | Slide Decks | SLIDE-01..05 (5) |
| 8 | Narration Scripts | SCRIPT-01..05 (5) |

---
*Requirements defined: 2026-09-03*
*Last updated: 2026-09-03 after roadmap creation (traceability populated)*

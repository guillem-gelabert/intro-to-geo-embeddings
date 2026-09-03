# Introduction to Geospatial Embeddings

## What This Is

A roughly six-hour, developer-oriented Udemy course that teaches how to use geospatial embeddings (AlphaEarth / Google Satellite Embedding as the backbone, with TESSERA, Clay, LGND, OlmoEarth, Copernicus and SatCLIP for portability) as practical data products: visualize, search, classify, detect change, and validate rigorously with spatial cross-validation. It is not a course on training Earth-observation foundation models.

The deliverables are course materials: solution notebooks, exercise notebooks derived from them, slide decks, and narration scripts for each module, plus small frozen teaching datasets so every notebook runs without cloud credentials.

## Core Value

A student can take a precomputed geospatial embedding field, run similarity search and a lightweight classifier on it, and evaluate the result with a spatially honest validation — and that entire workflow runs from a notebook without needing an Earth Engine account.

## Requirements

### Validated

(None yet — ship to validate)

### Active

- [ ] Working solution notebook for **similarity search and lightweight classification** on AlphaEarth embeddings (cosine search-by-example, 2–4 class RF/logistic classifier, confusion matrix, spatial-block CV vs random split, Sentinel-2 raw-pixel baseline)
- [ ] Frozen course datasets (embeddings + coordinates + year + labels, a few thousand rows) for the study areas, with provenance and license metadata, so notebooks run offline
- [ ] Solution notebooks for the earlier modules: embedding refresher (vectors, cosine, PCA, CRS), embedding foundations (pixel vs patch vs location embeddings), AlphaEarth access and visualization (Earth Engine + geemap, 64-band inspection, pseudo-RGB axes, sampling/export)
- [ ] Solution notebooks for the later modules: change detection and validation (cosine change score, threshold calibration, class-transition model, spatial+temporal CV), embedding ecosystems (TESSERA via GeoTessera, open Clay GeoParquet via DuckDB, LGND REST, optional local Clay encoder), capstone artificialization pipeline with provenance
- [ ] Exercise notebooks backtracked from each solution notebook (blanks, TODOs, checkpoints, hidden solutions)
- [ ] Slide decks for each module
- [ ] Narration scripts for each module (recording-ready)
- [ ] Every cloud-dependent notebook has a local/offline fallback path (Path A live, Path B guaranteed)
- [ ] Quizzes and assessment rubric (per the report's assessment weights, capstone criteria)
- [ ] Reproducible Python environment (Python 3.12, uv) with the pinned course stack; optional separate environment for Clay model demo

### Out of Scope

- Foundation-model pretraining, transformer mathematics, distributed GPU training — six hours is insufficient and these obscure the developer skills that matter
- Full semantic-segmentation fine-tuning — sequel-course material
- Vector-database infrastructure engineering — `sklearn.neighbors` / optional `faiss-cpu` suffice for teaching
- Earth Engine JavaScript — Python only, one language
- Lengthy GIS introductions — a 25-minute optional refresher is the ceiling
- Google Custom Satellite Embeddings — private preview as of July 2026; "watch this space" slide only, no lab
- Inventing an LGND Python SDK dependency — use `requests`/`httpx` against the OpenAPI reference
- Video recording and Udemy publishing/upload — materials only; recording is the author's manual step after scripts exist

## Context

**Source document:** `docs/research/course-design-research-2026-08.md` (identical copy of the deep-research report dated 2026-08-29). It is the authoritative design reference: provider landscape, reading list, notebook blueprints, code patterns, syllabus with timings, assessment weights, and risks.

**Course structure (from the report, 360 min total):**

| # | Module | Min | Notebook |
|---|--------|----:|----------|
| 0 | Optional refresher: vectors, ML, geospatial Python | 25 | `00_embedding_refresher.ipynb` |
| 1 | Earth observations become embeddings | 35 | (conceptual; small inspection notebook) |
| 2 | Access and visualize AlphaEarth | 50 | `01_alphaearth_access_visualize.ipynb` |
| 3 | Similarity search and lightweight classification | 65 | `02_similarity_and_classification.ipynb` |
| 4 | Change detection and rigorous evaluation | 60 | `03_change_detection_and_validation.ipynb` |
| 5 | Same problem, different embedding ecosystems | 55 | `04_embedding_ecosystems.ipynb` |
| 6 | Production, provenance, licensing, responsible use | 45 | (checklist/model card; extends prior labs) |
| 7 | Final assessment and capstone launch | 25 | `05_capstone_artificialization.ipynb` |

**Running problem:** "Where has vegetated/open land become artificial surface, and how confident are we?" Study areas: Bern/Swiss Plateau (visualization, artificialization), a compact European area with clear Copernicus imperviousness change (change lab), and a geographically distinct second region (transfer evaluation).

**Key teaching messages the materials must carry:**
- An embedding is a learned representation, not a land-cover class or physical measurement; dimension `A17` is not NDVI.
- AlphaEarth vectors are unit-length, so dot product equals cosine similarity.
- `1 − cosine` measures representation movement, not semantic transition; artificialization needs classified transitions or calibrated change labels.
- Random pixel splits leak spatially; use spatial blocks / leave-region-out.
- Dynamic World is a model output, not independent ground truth.
- Record dataset version, year, CRS, label and validation source in a provenance dictionary.

**Build order (author's decision, drives the roadmap):**
1. **First deliverable: the working solution notebook for similarity search and lightweight classification** (Module 3, `02_similarity_and_classification.ipynb`), including whatever frozen data and environment scaffolding it needs to run end-to-end.
2. Then backtrack to the earlier modules' solution notebooks (refresher, foundations, AlphaEarth access/visualize).
3. Then the later modules' solution notebooks (change detection, ecosystems, capstone).
4. Then, per module, derive exercise notebooks from the solution notebooks, then slides, then narration scripts.

Working notebook first, solution before exercise, always.

**Local environment findings (2026-09-03):**
- macOS, `uv` 0.12.9 installed; CPython 3.12.13 available via uv (GeoTessera requires 3.12+). System Python is 3.14.
- JupyterLab installed globally.
- **No Earth Engine credentials and no gcloud CLI present.** No `LGND_TOKEN`. Any live-path data extraction needs the author to authenticate Earth Engine with a GCP project first; frozen datasets are the guaranteed path.
- Earth Engine catalog metadata shows AlphaEarth through 2024 while the GCS distribution has 2017–2025. Use 2023–2024 for Earth Engine exercises.

**Reference resources to work through before building (from the report):** Earth Embeddings survey (Stewart et al. 2026), Google AEF GCS dataset guide, Earth Engine Satellite Embedding catalog + community tutorials (intro, supervised classification, regression, similarity), Spatial Thoughts Satellite Embedding Deep Dive, ISPRS 2026 embeddings tutorial (MIT, Colab CPU, no EE account — the best pedagogical model for frozen data), Clay Quick Start + wall-to-wall tutorial, LGND docs + OpenAPI, GeoTessera, OlmoEarth embedding docs, Copernicus Global Embeddings notebook.

## Constraints

- **Tech stack**: Python 3.12 via uv; JupyterLab/Colab; numpy, pandas, scikit-learn, matplotlib, geopandas, shapely, pyproj, rasterio, xarray, pyarrow, duckdb, fsspec, s3fs, pystac-client, stackstac, earthengine-api, geemap; `geotessera` for TESSERA; `requests`/`httpx` for LGND; torch/lightning/torchgeo optional and isolated — the report's recommended stack, Colab-first with a reproducible local env, not Docker-first
- **Data**: Frozen teaching datasets must be small (a few thousand rows), carry source provenance and license, and be redistributable (AlphaEarth CC BY 4.0 with Google/DeepMind attribution; Clay corpus CC BY 4.0; check Copernicus terms before bundling) — a paid course must survive auth failures, quota changes and disappearing API versions
- **Credentials**: Earth Engine access is the author's to arrange (GCP project, current eligibility/quota); LGND requires a token (trial tier exists) — notebooks must never hard-depend on either
- **Pedagogy**: Every notebook includes the conceptual traps as explicit cells (the "WRONG conclusion" cell, random vs spatial split comparison) — the report's quizzes test conceptual errors, not terminology
- **Runtime**: Core path ~5 h 35 min; total 360 min with the optional refresher — Udemy positioning
- **Versioning**: Pin dataset versions (AlphaEarth `DATASET_VERSION`, GeoTessera version) and library versions; repository banner "Course reference environment: 2026-08 release" — the field moves fast enough that unpinned material rots
- **Ethics**: Concrete, not generic — where evaluated, what counts as error, who bears false-positive cost, sensitivity of inferred information vs underlying imagery

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| AlphaEarth as primary backbone, portability to TESSERA/Clay/LGND/OlmoEarth taught deliberately | Global, analysis-ready, 10 m / 64D, CC BY 4.0, no model to run; report's strongest recommendation | — Pending |
| Build Module 3 (similarity + classification) solution notebook first, then backtrack | Author's decision; it is the core value and the most reusable code (all later modules reuse its search/classify/CV patterns) | — Pending |
| Solution notebook → exercise notebook → slides → script, per module | Author's decision; working code grounds the exercises and narration | — Pending |
| Two paths everywhere: Path A live (EE/GCS/API), Path B guaranteed (frozen parquet/tif) | Course durability against auth, quota, pricing and API drift | — Pending |
| Land artificialization as running problem | Coherent storyline across visualize → search → classify → change; Copernicus HRL Imperviousness gives independent European reference | — Pending |
| Spatial-block / leave-region-out CV taught as first-class, random split shown as the trap | Most damaging practical geospatial ML mistake is impressive metrics on an invalid split | — Pending |
| Python 3.12 via uv | GeoTessera requires 3.12+; system 3.14 likely too new for the geo stack | — Pending |
| GSD config: yolo, standard granularity, parallel, balanced models, research/plan-check/verifier on | Chosen autonomously under the /goal directive; adjust with `/gsd:settings` | — Pending |

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition** (via `/gsd-transition`):
1. Requirements invalidated? → Move to Out of Scope with reason
2. Requirements validated? → Move to Validated with phase reference
3. New requirements emerged? → Add to Active
4. Decisions to log? → Add to Key Decisions
5. "What This Is" still accurate? → Update if drifted

**After each milestone** (via `/gsd:complete-milestone`):
1. Full review of all sections
2. Core Value check — still the right priority?
3. Audit Out of Scope — reasons still valid?
4. Update Context with current state

---
*Last updated: 2026-09-03 after initialization*

# Roadmap: Introduction to Geospatial Embeddings

## Overview

The course is assembled in the order the author fixed: the working notebook first, everything else derived from it. Two scaffolding phases come first only because the flagship notebook provably cannot run without them — a pinned repo carrying the `course` package schema contract (Phase 1), and the frozen two-region dataset every notebook loads (Phase 2). Phase 3 delivers the core value: `02_similarity_and_classification.ipynb` running on free Colab CPU with no Earth Engine account. The course then fills in around it — backtrack to the earlier modules (Phase 4), forward to the later ones (Phase 5) — before the student-facing layer is derived from frozen solution notebooks: exercises and assessments (Phase 6), slide decks (Phase 7), narration scripts (Phase 8). Nothing derived is built before the artifact it derives from.

Research verified on 2026-09-03 that the entire frozen-data pipeline reads from anonymous public sources — AlphaEarth COGs on GCS, ESA WorldCover, EEA imperviousness, Earth Search STAC. Earth Engine is off the critical path entirely; it is optional and touches only the Path A branch of the access module in Phase 4.

**Decisions to surface early (research flags):**

- Phase 2: transfer-region and change-AOI bounds (HRL coverage, WorldCover class balance); whether to create a free EU Login for the 2021 Copernicus products.
- Phase 4: whether to register an Earth Engine noncommercial project for the Path A live cells.
- Phase 5: verify TESSERA v1.1 coverage over the study areas and the actual Clay/LGND corpus partitions before committing the ecosystems module.

Public data hosting at a pinned release with checksums is folded into Phase 2 (DATA-09); per-lecture zips and CI re-execution are v2 requirements, so there is no separate release phase in this milestone.

## Phases

**Phase Numbering:**

- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [ ] **Phase 1: Repository and Environment Scaffold** - Pinned Python 3.12 env, `course` package contract, headless runner, README banner
- [ ] **Phase 2: Frozen Two-Region Teaching Datasets** - Credential-free multi-year labelled embedding tables with provenance, card and integrity tests
- [x] **Phase 3: Similarity Search and Classification Notebook** - The flagship solution notebook and the reusable helpers every later module imports (completed 2026-09-03)
- [x] **Phase 4: Earlier Module Solution Notebooks** - Refresher, representation foundations, AlphaEarth access and visualization with its live/offline tiers (completed 2026-09-04)
- [x] **Phase 5: Later Module Solution Notebooks** - Change detection and validation, embedding ecosystems, capstone, provenance checklist (completed 2026-09-04)
- [ ] **Phase 6: Exercise Notebooks and Assessments** - Generated exercises with checkpoints, plus quizzes, assignments and the capstone rubric
- [ ] **Phase 7: Slide Decks** - One repo-built 16:9 deck per module with notebook figures, trap slides and speaker notes
- [ ] **Phase 8: Narration Scripts** - Recording-ready two-column AV scripts timed to the 360-minute syllabus

## Phase Details

### Phase 1: Repository and Environment Scaffold

**Goal**: The author can clone the repo, run one command, and get a working pinned Python 3.12 kernel with the shared `course` package contract in place — and every notebook written afterwards behaves identically locally and on Colab.
**Depends on**: Nothing (first phase)
**Requirements**: ENV-01, ENV-02, ENV-03, ENV-04, ENV-05
**Success Criteria** (what must be TRUE):

  1. Author runs `uv sync` on a clean clone and launches a JupyterLab kernel on Python 3.12 with the pinned core stack (numpy, pandas, pyarrow, geopandas, shapely, pyproj, scikit-learn, matplotlib, rasterio, xarray) against a committed `uv.lock`.
  2. A notebook's single Setup cell runs unchanged locally and on a fresh Colab CPU runtime, pip-installing pinned dependencies only on Colab in under two minutes, and sets `RANDOM_STATE` and the dataset-version constants.
  3. `import course` works from the synced environment while earthengine-api, geemap, geotessera, duckdb and torch/Clay stay out of the core install as optional extras or a separate uv project.
  4. Author runs one make/task target that executes every solution notebook headlessly against the frozen data and exits non-zero on the first cell error.
  5. The README lists every notebook with an Open-in-Colab badge, local run instructions, every data source with its license, and the banner "Course reference environment: 2026-08 release. Provider APIs may change. Every cloud notebook has a local/offline fallback."

**Plans**: 5 plans

Plans:
**Wave 1**

- [x] 01-01-PLAN.md — pyproject.toml, uv-managed environment, project kernel, `course` package, schema contract, shared pytest fixtures

**Wave 2** *(blocked on Wave 1 completion)*

- [x] 01-02-PLAN.md — README (banner, license, notebook table), jupytext/pre-commit/.gitignore hygiene
- [x] 01-03-PLAN.md — Makefile (env/kernel/test/execute-notebooks/requirements-colab.txt), fail-fast headless execution test
- [x] 01-04-PLAN.md — core/extras isolation test, Setup-cell bootstrap contract test

**Wave 3** *(blocked on Wave 2 completion)*

- [ ] 01-05-PLAN.md — manual Colab bootstrap timing checkpoint

### Phase 2: Frozen Two-Region Teaching Datasets

**Goal**: Every notebook in the course can load a labelled, multi-year, two-region embedding table from disk with a public remote fallback, carrying its own provenance and license — with no credentials of any kind.
**Depends on**: Phase 1
**Requirements**: DATA-01, DATA-02, DATA-03, DATA-04, DATA-05, DATA-06, DATA-07, DATA-08, DATA-09, DATA-10
**Success Criteria** (what must be TRUE):

  1. A caller loads Region A (Bern/Swiss Plateau) and Region B (a geographically distinct transfer region) point tables sharing one schema — `A00..A63` float32 dequantized unit-norm, `lon`, `lat`, projected `x`/`y`, `year`, `label`, `label_source`, `region`, `block_id` — with Sentinel-2 `B2..B12` on the same rows and at least two years covering the same points, aligned to an independent change reference.
  2. Author regenerates every table end to end with the committed prep scripts from anonymous no-login sources only (AlphaEarth GCS COGs with documented int8 square-root dequantization, `-128` nodata and renormalization; an open label raster; STAC Sentinel-2), with Earth Engine available only as an optional alternative path.
  3. The dataset test suite passes: unit norms within 1e-3 of 1, no NaN, the expected column set, minimum class counts per region, CRS present, and at least five spatial blocks per region.
  4. Each table ships a provenance JSON (product, version, year, extraction date, source path, sampling method, CRS, label source, validation source, license, exact attribution sentence, creator, sha256) and the bundle ships a dataset card with per-source licenses and the exact AlphaEarth attribution; no source lacking redistribution rights is bundled.
  5. A fresh Colab runtime with no local data fetches every table and the candidate query-polygon GeoJSON from a pinned public release, verifies checksums, and finds each table around 1 MB or less with the whole bundle under 100 MB.

**Plans**: 12 plans

Plans:
**Wave 1**

- [x] 02-01-PLAN.md — dequantize_aef helper, frozen-table schema extension, study-area/version registry, network pytest marker

**Wave 2** *(blocked on Wave 1 completion)*

- [x] 02-02-PLAN.md — AlphaEarth COG adapter: tile lookup, windowed read, array-index point sampling
- [x] 02-03-PLAN.md — WorldCover label adapter and independent HRL Imperviousness 2018 reference
- [x] 02-04-PLAN.md — Sentinel-2 STAC adapter: scene search, dedup, SCL-masked band sampling
- [x] 02-05-PLAN.md — course.data local-first loader with checksum-verified remote fallback

**Wave 3** *(blocked on Wave 2 completion)*

- [x] 02-06-PLAN.md — stratified sample design: WorldCover-based strata, min-spacing, block_id, stable sample_id

**Wave 4** *(blocked on Wave 3 completion)*

- [x] 02-07-PLAN.md — extract_aef.py and attach_labels.py wiring
- [x] 02-08-PLAN.md — attach_s2.py wiring

**Wave 5** *(blocked on Wave 4 completion)*

- [x] 02-09-PLAN.md — write.py (GeoParquet + provenance + manifest), data_card.py, build.py CLI, network regen test

**Wave 6** *(blocked on Wave 5 completion)*

- [ ] 02-10-PLAN.md — run the real pipeline for both regions/all years, DATA-10 query polygons, human checkpoint

**Wave 7** *(blocked on Wave 6 completion)*

- [ ] 02-11-PLAN.md — publish decision (checkpoint) and GitHub Release hosting
- [ ] 02-12-PLAN.md — final integrity, provenance, licensing and dataset-aliveness test suite

### Phase 3: Similarity Search and Classification Notebook

**Goal**: A student opens `02_similarity_and_classification.ipynb` on free Colab CPU with no Earth Engine account, searches an embedding field by example, trains a small classifier, and sees for themselves that a random split lies about accuracy while spatial-block and leave-region-out CV tell the truth.
**Depends on**: Phase 1, Phase 2
**Requirements**: SIM-01, SIM-02, SIM-03, SIM-04, SIM-05, SIM-06, SIM-07, SIM-08, SIM-09, SIM-10, SIM-11, SIM-12, SIM-13
**Success Criteria** (what must be TRUE):

  1. Student runs Restart & Run All on a fresh Colab CPU runtime in about three minutes with no credentials, starting from a header stating objectives, prerequisites and time, and the notebook loads both regions, shows the schema, class counts and a labelled point map, and asserts 64 dimensions and unit norm with the "dot product equals cosine" Takeaway.
  2. Student runs search-by-example from a single-pixel query and sees a top-k table, match map and similarity histogram, then compares single-pixel, renormalized polygon-mean and positive-minus-negative prototypes by precision@k, changing `QUERY_ID` and `K` through marked EDIT ME knobs.
  3. Student sees the trap accuracy and confusion matrix from a random split on logistic regression and random forest, then the same models scored by spatial-block `GroupKFold` in EPSG:2056 and by leave-region-out on Region B, compared in one bar chart with per-class precision/recall and a map of where errors occur.
  4. Student encounters the "similarity > 0.90 means same land cover" WRONG-conclusion cell with its ranking-and-precision@k correction, and every experiment ends with a Takeaway whose claim is visible in the output directly above it, closing with Wrap-up, What's next, Resources and a non-executed Path A Earth Engine appendix.
  5. The identical pipeline and CV run on Sentinel-2 raw bands with a comparison table, the notebook writes `outputs/provenance.json` and `figures/02_*.png`, and the helpers it uses (`cosine_similarity_map`, `make_blocks`, `spatial_cv_report`, provenance builder) are imported from the `course` package with green unit tests rather than defined inline.

**Plans**: 4 plans

Plans:
**Wave 1**

- [x] 03-01-PLAN.md — course helpers: cosine_similarity_map, make_blocks, spatial_cv_report, provenance builder, all unit-tested

**Wave 2** *(blocked on Wave 1 completion)*

- [x] 03-02-PLAN.md — notebook: Header, Setup, Data, Similarity 1/2/3 (search-by-example, WRONG-conclusion trap, prototype ladder + precision@k)

**Wave 3** *(blocked on Wave 2 completion)*

- [x] 03-03-PLAN.md — notebook: classification trap, spatial-block CV, leave-region-out, comparison chart, Sentinel-2 baseline

**Wave 4** *(blocked on Wave 3 completion)*

- [x] 03-04-PLAN.md — notebook: provenance cell, Wrap-up/Resources/Path A appendix, full-notebook timing/cell-budget verification, Colab checkpoint

### Phase 4: Earlier Module Solution Notebooks

**Goal**: A student arriving without linear-algebra or Earth Engine background can work the refresher, tell pixel, patch and location embeddings apart, and access and visualize AlphaEarth — with a guaranteed offline path that reaches the same conclusions as the live one.
**Depends on**: Phase 3
**Requirements**: EARLY-01, EARLY-02, EARLY-03, EARLY-04, EARLY-05
**Success Criteria** (what must be TRUE):

  1. Student completes `00_embedding_refresher.ipynb` in about 25 minutes covering NumPy vectors, L2 normalization, cosine similarity, PCA on a toy embedding matrix, a tiny classifier with a train/test split, and a GeoDataFrame reprojection.
  2. Student inspects several representations of the same location side by side — an AlphaEarth 64-D pixel vector, a Clay patch embedding from the open LGND GeoParquet corpus, and optionally a SatCLIP location embedding when torch is available — and reads off shape, spatial unit, temporal support and metadata for each.
  3. A student with Earth Engine access runs Path A of `01_alphaearth_access_visualize.ipynb`: authenticate with a project ID, load `GOOGLE/SATELLITE_EMBEDDING/V1/ANNUAL` over a Bern AOI for 2024, inspect the 64 bands, display three axes as pseudo-RGB with geemap, and sample and export an embedding table.
  4. A student with no credentials runs the same notebook's downstream cells from the bundled clipped AlphaEarth GeoTIFF/parquet — int8 dequantization formula, unit-norm check, static pseudo-RGB and PCA plots — and reaches the same conclusions as Path A.
  5. The visualization notebook poses "why does this map look geographically structured although the three axes have no RGB meaning?" and every caption and Takeaway uses the phrasing "this component separates these landscape types in this sample", never "component 3 measures vegetation".

**Plans**: 7 plans

Plans:
**Wave 1**

- [x] 04-01-PLAN.md — 00_embedding_refresher.ipynb (NumPy/cosine/PCA/classifier/CRS, toy data, no network)
- [x] 04-02-PLAN.md — Clay (LGND) fixture data prep: pipeline/fetch_clay_fixture.py, checked-in fixture + provenance
- [x] 04-03-PLAN.md — clipped AlphaEarth raster data prep: pipeline/extract_clip_raster.py, checked-in COG + provenance

**Wave 2** *(blocked on Wave 1 completion)*

- [x] 04-04-PLAN.md — 00b_representation_inspection.ipynb (AlphaEarth pixel vs Clay patch vs optional SatCLIP)
- [x] 04-05-PLAN.md — 01_alphaearth_access_visualize.ipynb: Header, Setup, Path A (Earth Engine, skip-execution)

**Wave 3** *(blocked on Wave 2 completion)*

- [x] 04-06-PLAN.md — 01_alphaearth_access_visualize.ipynb: Path B (offline, dequantization/pseudo-RGB/PCA), EARLY-05 phrasing-rule test

**Wave 4** *(blocked on Wave 3 completion)*

- [x] 04-07-PLAN.md — DATA_CARD.md/README.md consolidation, repo-wide headless-execution smoke test

### Phase 5: Later Module Solution Notebooks

**Goal**: A student can detect and validate change without mistaking representation movement for semantic transition, repeat the same operation on a different embedding provider, and run a provenance-complete artificialization pipeline end to end.
**Depends on**: Phase 3, Phase 4
**Requirements**: LATE-01, LATE-02, LATE-03, LATE-04, LATE-05, LATE-06
**Success Criteria** (what must be TRUE):

  1. Student computes a cosine change score on year-aligned AlphaEarth tables in `03_change_detection_and_validation.ipynb`, meets the "WRONG: artificialized = change_score > 0.25" cell, calibrates a threshold with `precision_recall_curve` against independent change labels, and reads precision, recall and F1 on both changed and unchanged controls.
  2. Student trains per-year classifiers in the same notebook, produces a class-transition matrix and a vegetation-to-built artificialization mask, compares it against the continuous change score, and validates it with spatially and temporally grouped CV.
  3. Student repeats one similarity or classification operation on TESSERA embeddings via geotessera and on the open Clay GeoParquet corpus via DuckDB in `04_embedding_ecosystems.ipynb`, using the same `course` helpers and asserting each provider's vector norms before reuse.
  4. A student with no `LGND_TOKEN` still runs the ecosystems notebook to completion: the LGND REST cells skip cleanly to a recorded response fixture, the optional local Clay encoder section points at the isolated environment, and the OlmoEarth comparison of custom temporal windows against annual fields is present in markdown.
  5. Student runs `05_capstone_artificialization.ipynb` as an end-to-end template (AOI → features → predictions → validation → map → uncertainty and provenance) with the rubric checklist and provenance dict pre-filled, and applies the model/data card template and provenance checklist — with exact attribution strings and license notes for every provider used — to a previous lab's outputs.

**Plans**: 9 plans

Plans:
**Wave 1**

- [x] 05-01-PLAN.md — course.embeddings change_score + norm_diagnostics helpers
- [x] 05-08-PLAN.md — model/data card template, provenance checklist, Module 3 worked example

**Wave 2** *(blocked on Wave 1 completion)*

- [x] 05-02-PLAN.md — notebook 03: Header/Setup/Data, change score, WRONG-conclusion trap, calibrated threshold
- [x] 05-04-PLAN.md — notebook 04: Header/Setup, provider fixtures, TESSERA section
- [x] 05-06-PLAN.md — notebook 05: Header/Setup/AOI/features, predictions, spatial + leave-region-out validation

**Wave 3** *(blocked on Wave 2 completion)*

- [x] 05-03-PLAN.md — notebook 03: transition matrix, artificialization mask, spatiotemporal CV, provenance, wrap-up
- [x] 05-05-PLAN.md — notebook 04: Clay section, LGND-guarded section, Clay-encoder pointer, OlmoEarth markdown, provenance, wrap-up
- [x] 05-07-PLAN.md — notebook 05: prediction map, uncertainty, provenance, rubric self-check, wrap-up

**Wave 4** *(blocked on Wave 3 completion)*

- [x] 05-09-PLAN.md — README Notebooks table, templates link, full four-notebook headless verification gate

### Phase 6: Exercise Notebooks and Assessments

**Goal**: Every module has a derived exercise notebook a student can actually practise on, plus the quiz, assignment or rubric that tests the same conceptual errors the notebook demonstrates.
**Depends on**: Phase 3, Phase 4, Phase 5 (every solution notebook frozen)
**Requirements**: EXER-01, EXER-02, EXER-03, EXER-04, EXER-05, ASSESS-01, ASSESS-02, ASSESS-03, ASSESS-04
**Success Criteria** (what must be TRUE):

  1. Author runs one make target driving a unit-tested generator script that derives every exercise notebook from its tagged solution notebook (`solution`, `stub`, `hidden-test`), and the regenerated files match the committed ones byte for byte.
  2. Every solution notebook has an exercise twin with the same narrative, data and headings, in which roughly 30–40% of the learning code cells (not I/O boilerplate) have become tasks with a consistent stub.
  3. A student runs an exercise notebook top to bottom, reaches the first stub cleanly, gets a friendly checkpoint assert with an expected-output hint and at least one visible test per task, never has a solution spoiled by running all cells, can reveal solutions on demand, and finishes on reflection prompts and stretch tasks.
  4. Student takes an ungraded 5-question diagnostic after the refresher and a 5–8 question conceptual-error multiple-choice quiz per module in which each option's explanation quotes the notebook cell demonstrating the answer.
  5. Student reads assignment texts for the similarity/classification, change-detection and ecosystems modules matching the published weights (15%, 20%, 20%, 10% portability), and the capstone rubric (validation design 30%, reproducibility/provenance 15%, CRS/alignment 15%, interpretation/uncertainty 15%, representation choice 15%, licensing/ethics 10%) alongside a proposal template.

**Plans**: 6 plans

Plans:
**Wave 1**

- [x] 06-01-PLAN.md — exercise-notebook generator (tools/derive_exercise.py) with unit tests, tag vocabulary
- [x] 06-02-PLAN.md — tag learning cells + appendix content: 00_embedding_refresher, 00b_representation_inspection, 01_alphaearth_access_visualize, 02_similarity_and_classification
- [x] 06-03-PLAN.md — tag learning cells + appendix content: 03_change_detection_and_validation, 04_embedding_ecosystems, 05_capstone_artificialization
- [x] 06-04-PLAN.md — refresher diagnostic + quizzes for 00b, 01, 02
- [x] 06-05-PLAN.md — quizzes for 03, 04; assignments for 02, 03, 04; capstone rubric + proposal template

**Wave 2** *(blocked on Wave 1 completion)*

- [ ] 06-06-PLAN.md — solution-link mechanism, generate all 7 exercise notebooks, regeneration + stub-boundary tests

**Rationale for grouping assessments here:** quizzes and exercise checkpoints are the same layer — the learner's self-verification — and both are derived from a frozen solution notebook by quoting the exact cell that proves the point. Building them together keeps each module's practice-and-check bundle consistent, and it puts the quizzes on disk before Phase 8, where SCRIPT-05 requires every narration script to reference its module's exercise tasks and quiz.

### Phase 7: Slide Decks

**Goal**: Every module has a 16:9 deck built from the repository that carries the module's objectives, real notebook figures, the trap slides and the attribution — with speaker notes substantial enough to serve as the narration's first draft.
**Depends on**: Phase 5 (every solution notebook frozen and exporting figures)
**Requirements**: SLIDE-01, SLIDE-02, SLIDE-03, SLIDE-04, SLIDE-05
**Success Criteria** (what must be TRUE):

  1. Author runs one build from markdown sources in the repo and gets eight 16:9 decks as PDF/HTML — one per module including the refresher — each opening on objectives and closing on a recap that mirrors its notebook's objectives.
  2. Every figure in every deck is embedded from a solution-notebook export rather than a manual screenshot, and the concept diagrams are present: pixel/patch/location taxonomy, provider decision flowchart, analytical chain, and "1 − cosine measures representation movement".
  3. Each deck contains a WRONG-conclusion slide mirroring its notebook's trap cell, plus an attribution/license slide and a version-banner slide.
  4. Every slide carries speaker notes detailed enough that the author can read them aloud as a first narration draft.
  5. The ecosystems deck carries the provider comparison table and the foundations deck carries the "Custom Satellite Embeddings: private preview, watch this space" slide.

**Plans**: TBD
**UI hint**: yes

### Phase 8: Narration Scripts

**Goal**: The author can sit down and record — every module has a two-column AV script, segmented into lecture-sized units, timed to the syllabus, anchored to specific notebook cells and slides.
**Depends on**: Phase 6, Phase 7
**Requirements**: SCRIPT-01, SCRIPT-02, SCRIPT-03, SCRIPT-04, SCRIPT-05
**Success Criteria** (what must be TRUE):

  1. Author opens one recording-ready script per module in two-column VISUAL | AUDIO format with a duration on every row and cumulative timing marks.
  2. Each module is segmented into lectures of 2–7 minutes (codealongs up to 12), each carrying an objective line, a recap line and an end-state line, with module totals matching the syllabus and summing to 360 minutes.
  3. Every row names the notebook cell heading or slide number it covers and uses explicit cue tokens ([RUN CELL], [ZOOM], [PAUSE], [CUT]).
  4. The key teaching messages appear verbatim — unit-length so dot equals cosine; A17 is not NDVI; random splits leak spatially; Dynamic World is a model output; 1 − cosine is not a semantic transition — with pronunciation notes for provider and place names.
  5. Each script references its module's exercise tasks and quiz so video, notebook and assessment tie together.

**Plans**: TBD

## Progress

**Execution Order:**
Phases execute in numeric order: 1 → 2 → 3 → 4 → 5 → 6 → 7 → 8

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Repository and Environment Scaffold | 4/5 | In Progress|  |
| 2. Frozen Two-Region Teaching Datasets | 9/12 | In Progress|  |
| 3. Similarity Search and Classification Notebook | 4/4 | Complete   | 2026-09-03 |
| 4. Earlier Module Solution Notebooks | 7/7 | Complete   | 2026-09-04 |
| 5. Later Module Solution Notebooks | 9/9 | Complete   | 2026-09-04 |
| 6. Exercise Notebooks and Assessments | 5/6 | In Progress|  |
| 7. Slide Decks | 0/TBD | Not started | - |
| 8. Narration Scripts | 0/TBD | Not started | - |

## Coverage

All 58 v1 requirements map to exactly one phase. No orphans, no duplicates.

| Category | Count | Phase |
|----------|------:|-------|
| ENV-01..05 | 5 | Phase 1 |
| DATA-01..10 | 10 | Phase 2 |
| SIM-01..13 | 13 | Phase 3 |
| EARLY-01..05 | 5 | Phase 4 |
| LATE-01..06 | 6 | Phase 5 |
| EXER-01..05, ASSESS-01..04 | 9 | Phase 6 |
| SLIDE-01..05 | 5 | Phase 7 |
| SCRIPT-01..05 | 5 | Phase 8 |

---
*Roadmap created: 2026-09-03*

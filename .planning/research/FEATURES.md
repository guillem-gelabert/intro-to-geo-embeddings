# Feature Research

**Domain:** Developer-oriented, notebook-based Udemy course on geospatial embeddings (solution notebooks, exercise notebooks, slide decks, narration scripts, frozen teaching datasets, assessments)
**Researched:** 2026-09-03
**Confidence:** MEDIUM-HIGH overall (HIGH where the comparable's actual notebook/README was read; MEDIUM for Udemy platform rules, whose support pages are Cloudflare-gated and were reached only via search summaries and a 2023 third-party article)

How to read this file: features are grouped **by deliverable type** (A–G) because that is how requirements will be written. Within each group: table stakes, differentiators, anti-features. A dedicated section specifies the first deliverable (`02_similarity_and_classification.ipynb`). Dependencies, MVP, prioritization and the competitor matrix follow the template.

---

## Comparables Studied (what they actually contain)

| Comparable | Format | What it has | What it lacks (our opening) | Confidence |
|---|---|---|---|---|
| **ISPRS 2026 "Towards Geospatial Embeddings"** (Klemmer; MIT) | 2 Python notebooks, free Colab CPU, no EE account | 23 and 22 cells (11/10 code); single `# === Setup ===` cell with `RUNNING_IN_COLAB = "google.colab" in sys.modules` and conditional `pip install -q`; `fetch()` helper that tries `local/demo1/` first then `hf_hub_download` from a public HF dataset; frozen parquet **0.30–0.42 MB each** (`aef_crop_train.parquet` = 3,000 rows x 78 cols: `A00..A63`, Sentinel-2 `B2..B8A`, `crop_label`, `lat`, `lon`, `crop_name`); "✏️ EDIT ME" knob (`HOLDOUT = ["Neotropic"]`); "**Takeaway:**" cells after each experiment; Sentinel-2 raw-band baseline with the *same* linear probe; normalized confusion matrix; geographic transfer to an unseen region B with per-class breakdown and a **map of where errors occur**; optional illustrative GEE cell kept as markdown; Wrap-up bullets; `scripts/` (organizers-only data prep, needs GEE), `tests/`, `local/` staging; README lists every data source with license | Within-region split is a plain random `train_test_split` (no spatial-block CV); parquet files carry only `pandas` metadata (no provenance/license in-file); HF dataset repo has **no README card**; demo-only (no exercise variant, no blanks, no checkpoints/asserts); no provenance dict; 229 MB EuroSAT `.npz` makes demo 2 slow | HIGH (notebooks downloaded and parsed) |
| **Spatial Thoughts, Satellite Embedding Deep Dive** (Gandhi; CC BY 4.0 content, MIT code) | Earth Engine **JavaScript** Code Editor scripts + full video + slides | 4 sections: Visualizing Embeddings (pseudo-RGB, k-means 3/5/10), Crop Type Mapping (unsupervised, validated against USDA CDL and county acreage statistics), Mapping Mangroves (supervised KNN from hand-drawn samples; qualitative comparison to Global Mangrove Watch), Object Detection with Similarity Search (brick kilns: dot product to reference samples, threshold 0.90–0.97, `reduceToVectors`, `connectedPixelCount` area filter; supplementary section adds **negative examples**). Every section ships a *complete* script plus an *Exercise* script whose tasks are code comments ("Delete the geometry / Draw a geometry for your region of interest / Try visualizing the embeddings with different bands (A01, A02, A03...) / Try changing the number of clusters"). Citation format and license stated | JavaScript, not Python; needs EE account; no formal train/test split, no confusion matrix, no spatial validation, no quizzes | MEDIUM (page fetched; one summarizer claim about dimensionality was inconsistent with the dataset and is not used here) |
| **Google Satellite Embedding community tutorials 01–05** | Earth Engine JavaScript | 01: "individual bands have no independent meaning", unit-length vectors, spatial-temporal context, pseudo-RGB, k-means sampling. 02: `wekaCascadeKMeans` 4–5 clusters on 1,000 stratified samples, clusters labelled via county crop statistics, validated against CDL. 03: ~10 hand-labelled points per class, `smileKNN` "for low-shot classification", **no train/test split, no metrics**, qualitative check vs Global Mangrove Watch, caveat "may not scale to larger regions". 04: RF (50 trees, REGRESSION) on GEDI biomass; RMSE/R² reported **on training data only**. 05: 3 reference points, `sampleRegions`, dot product = cosine on unit vectors, *mean* similarity over references, `threshold = 0.90`, heatmap, vectorize, validate by zooming in; caveat to verify the object exists in the chosen year | No held-out evaluation anywhere; no Python; no raw-band baseline; no exercises | MEDIUM-HIGH (all five pages fetched) |
| **Clay tutorials** (Apache-2.0 code) | Jupyter Book pages; wall-to-wall is a notebook, EuroSAT classify is a Lightning CLI script | Wall-to-wall: 13 sections, STAC (Element84) Sentinel-2 L2A, Portugal fire AOI, 256x256 chips, pinned `clay-v1.5.ckpt` from HF, 1-component PCA separating pre-fire / cloud / post-fire, SVM with hand-picked `fit=[0,1,3,4,7,8,9]`, `test=[2,5,6,10,11]`, "Matched 4 out of 5 correctly"; GPU if available; Binder button | No exercises; toy evaluation; GPU-oriented; EuroSAT example is not a notebook | MEDIUM |
| **fast.ai fastbook** | 20 chapter notebooks + `clean/` mirror | Colab link per chapter; `#hide` setup cells; `clean/` notebooks contain only headings and code (prose stripped) for active recall; every chapter ends with `## Questionnaire` and `### Further Research` | GPU course; prose not redistributable | HIGH (repo and `clean/01_intro.ipynb` inspected) |
| **Hugging Face LLM course** | Web chapters + `huggingface/notebooks` | Per-section banner "run the code in either Google Colab or Amazon SageMaker Studio Lab"; "Ask a question" banner to forum; chapter sized to ~6–8 h/week; end-of-chapter multiple-choice quiz (login required) | Not geospatial | MEDIUM |
| **Kaggle Learn (`learntools`)** | Paired tutorial + exercise notebooks generated from one `raw/` source | Exercise pattern: setup cell `from learntools.core import binder; binder.bind(globals()); from learntools.machine_learning.ex2 import *`; blanks are `____`; every step ends with `step_1.check()`; `#step_1.hint()` / `#step_1.solution()` shipped **commented** (`#_COMMENT_IF(PROD)_`) "so they need to put in a small amount of effort to peek, and won't accidentally get spoiled if they run all cells"; `#%%RM_IF(PROD)%%` cells hold `step_1.assert_check_failed()` / `assert_check_passed()` to test the checker against wrong and right answers; `NotAttempted` raised if starter code unchanged; "Think About Your Data" reflection cells; `#$HIDE_OUTPUT$`, `#$EXERCISE_URL(N)$`, `KEEP_GOING`, `YOURTURN` macros | Requires their checker package and platform | HIGH (raw `ex2.ipynb` and `MACROS.txt` read) |
| **nbgrader** | Source → release generation | `### BEGIN SOLUTION` / `### END SOLUTION` replaced by `# YOUR CODE HERE\nraise NotImplementedError()`; `### BEGIN HIDDEN TESTS` / `### END HIDDEN TESTS`; autograded test cells are `assert`s with points; docs warn to leave at least one visible test; read-only locked cells; `nbgrader generate_assignment` writes `release/` from `source/` | Heavy for a Udemy course (no submission server) | HIGH (docs fetched) |
| **Carpentries geospatial-python** | Lesson episodes | "Questions" and "Objectives" boxes at top; "Challenge" blocks with collapsible "Show me the solution"; "Callout" boxes; "Key Points" at end | Not embedding-specific | HIGH |
| **Project Pythia notebook template** | Cookbook standard | Title; `## Overview` with numbered topics mapping to `##` sections; `## Prerequisites` table (Concepts / Importance / Notes) plus "Time to learn"; `## Imports` up-front; body; `## Summary`; `### What's next?`; `## Resources and references`; "Kernel > Restart Kernel and Run All Cells... to confirm that your notebook will cleanly run from start to finish"; "try to avoid using code comments as narrative" | Not exercise-oriented | HIGH |
| **Udemy platform rules** | Marketplace | Minimum 30 min video, 5 lectures, 720p/1080p, audio on both channels; lectures recommended **2–6 min** (exceptions include codealongs), intro lecture 2–4 min; curriculum items: video lecture, quiz (MCQ), coding exercise (browser runner, Python among languages), practice test (certification-style), assignment (text/video instructions + downloadable resources, instructor feedback); downloadable resources per lecture; 30-day refund; recurring complaints in reviews: outdated content, poor audio | Coding exercises are a language runner, not notebooks (environment/library support unverified) | MEDIUM / LOW for coding-exercise details |

---

## Feature Landscape

### A. Solution notebooks

#### Table Stakes (Users Expect These)

| Feature | Why Expected | Complexity | Notes / Depends on |
|---|---|---|---|
| Runs top-to-bottom on **free Colab CPU and locally**, no Earth Engine account, no token | ISPRS proves it is possible and states it in the README's first paragraph; a paid course that fails on auth is refund bait (Udemy 30-day refund) | MEDIUM | Depends on frozen datasets (E) and pinned env (G). Path A (live EE) is an *appendix*, never the default execution path |
| "Open in Colab" badge + local instructions in the notebook header | ISPRS, fastbook, HF course all do it; Udemy cannot host notebooks, so the repo link is the delivery mechanism | LOW | Badge URL pattern `https://colab.research.google.com/github/<org>/<repo>/blob/main/notebooks/<nb>.ipynb` |
| Single `Setup` cell: Colab detection, conditional pinned `pip install -q`, all imports, `RANDOM_STATE`, version constants | ISPRS pattern (`RUNNING_IN_COLAB`); Pythia "Imports up-front" | LOW | Version constants (`DATASET_VERSION`, `DATA_RELEASE`) feed the provenance dict |
| Local-first `fetch()` data helper with remote fallback | ISPRS: local path → `hf_hub_download`; lets the author test offline and students run online | LOW | Depends on E hosting decision |
| Pythia-style header: title, 1-paragraph overview, **numbered learning objectives**, prerequisites table, time to complete, runtime callout | Pythia template, Carpentries "Questions/Objectives" | LOW | Objectives are reused verbatim in slides and script |
| Narrative in markdown, not in code comments; `##` sections mirroring objectives | Pythia ("avoid using code comments as narrative"); ISPRS reads as prose between short code cells | LOW | Section headings become the script's row anchors |
| Short code cells (< ~40 lines), 20–45 cells total | ISPRS 22–23 cells; Google tutorials one idea per block | LOW | Long cells kill screencast pacing (egghead "20-second paragraphs") |
| Every figure titled and labelled; confusion matrix rendered (`ConfusionMatrixDisplay`), not printed | ISPRS normalized CM; report requires CM and per-class metrics | LOW | |
| **"Takeaway"** cell after each experiment and a **Wrap-up** cell with 3–5 bullets | ISPRS does both; Carpentries "Key Points"; Pythia "Summary" | LOW | Wrap-up bullets = quiz stems |
| **Baseline comparison** with identical downstream model (Sentinel-2 raw bands vs embeddings) | ISPRS does this with the same linear probe; PROJECT.md requires it | LOW | Requires S2 bands in the frozen parquet (E) |
| Conceptual traps as **explicit cells** ("WRONG conclusion" cell, random-split trap) | PROJECT.md constraint; no comparable does it (ISPRS comes closest with its transfer sweep) | LOW | Cell text is reused verbatim in slides, script and quiz |
| Provenance dictionary cell written to JSON next to outputs | Report's model card requirement; AEF license *requires* the attribution sentence | LOW | Schema fixed before datasets are built (E) |
| `Restart Kernel & Run All` passes; outputs committed cleared or deterministic | Pythia checklist; needed for nbmake CI (G) | LOW | |
| Resources & references cell with URLs, dataset versions and license/attribution | Pythia, ISPRS README | LOW | |

#### Differentiators (Competitive Advantage)

| Feature | Value Proposition | Complexity | Notes / Depends on |
|---|---|---|---|
| **Random split vs 10 km spatial-block CV vs leave-region-out, same model, one bar chart** | No comparable does it: Google 03/04 have *no* held-out split, Spatial Thoughts validates qualitatively, ISPRS uses random `train_test_split` within region then a separate transfer region. This is the course's core value | MEDIUM | `GroupKFold(n_splits, shuffle=True, random_state)` verified in current scikit-learn; blocks from EPSG:2056 coordinates; needs second region in dataset (E) |
| **Map of errors** (where misclassification happens) next to the scalar metrics | ISPRS does it for transfer; report demands "a map of errors rather than only one scalar score" | LOW | Frozen data carries lon/lat |
| **Query-design ladder** for search-by-example: single pixel → polygon-mean prototype → positive-minus-negative prototype, each scored with precision@k against labels | Google 05 averages 3 points and thresholds at 0.90; Spatial Thoughts adds negatives only in a supplement; neither *measures* retrieval quality | MEDIUM | Needs labelled points to compute precision@k (E) |
| **Ranking + precision@k instead of a magic threshold** (with a histogram showing why 0.90 is arbitrary) | Both Google and Spatial Thoughts hard-code 0.90–0.97 thresholds and say "experiment" | LOW | |
| **Unit-norm assertion cell** proving dot product = cosine on this data (`np.allclose(norms, 1, atol=1e-3)`) | Turns the key teaching message into executable evidence; also catches int8-not-dequantized data bugs | LOW | Depends on dequantized float32 in E |
| **Few-shot curve**: accuracy vs training samples per class (5/10/25/100) under spatial CV | Google 03 asserts "10 samples should be enough" without evidence; we test the claim | MEDIUM | |
| **"✏️ EDIT ME" knobs** (query id, k, block size, holdout region) in dedicated cells | ISPRS `HOLDOUT`; Spatial Thoughts "change bands / clusters" exercises; invites experimentation without breaking the flow | LOW | Knobs become exercise tasks in B |
| **Reusable helper cell** (`cosine_similarity_map`, `make_blocks`, `spatial_cv_report`) that later notebooks import or copy | PROJECT.md: module 3 code is reused by 03/05; ISPRS keeps a `tutorial/` lib with `tests/` | MEDIUM | Consider `course_utils.py` alongside notebooks, unit-tested |
| Path A appendix: illustrative EE code to regenerate the table, guarded (`if RUN_LIVE:`) or kept as markdown | ISPRS "Optional — reproduce the AlphaEarth data yourself" cell; teaches provenance without breaking offline runs | LOW | |
| **Reference-environment banner** ("Course reference environment: 2026-08 release; provider APIs may change; every cloud notebook has an offline fallback") | Report's maintenance policy; Udemy's most common complaint is outdated content | LOW | |

#### Anti-Features (Commonly Requested, Often Problematic)

| Feature | Why Requested | Why Problematic | Alternative |
|---|---|---|---|
| Live Earth Engine / geemap interactive map as the *default* path | Looks impressive; Google and Spatial Thoughts do it | Requires GCP project + eligibility; interactive widgets do not render on GitHub/nbviewer or in recorded video review; breaks on quota | Static matplotlib/geopandas plots by default; geemap only in `01_alphaearth_access_visualize` Path A with Path B fallback |
| Earth Engine JavaScript snippets "for completeness" | All Google/Spatial Thoughts material is JS | Second language; PROJECT.md excludes it | Python only; link to Google's JS tutorials in Resources |
| Big notebooks that do everything (60+ cells) | "One notebook per module" sounds tidy | Unrecordable pacing; Colab session timeouts; hard to derive exercises | Cap at ~45 cells; split into parts with clear `##` sections |
| UMAP / FAISS / vector DB demos | Trendy | Extra heavy dependencies; PROJECT.md excludes vector-DB engineering | `sklearn.neighbors` / NumPy einsum; optional `faiss-cpu` mention only |
| Physical interpretation of embedding axes ("A17 is vegetation") | Students ask what bands mean | Google: "individual bands have no independent meaning"; report's core message | PCA/pseudo-RGB "structure, not meaning" cell + quiz item |
| Training a model live (Clay encoder, torch) in the flagship notebook | "Show where embeddings come from" | GPU dependence, minutes of runtime, dependency conflicts (report isolates Clay env) | Defer to `04_embedding_ecosystems` optional section |
| Hidden setup cells (`#hide`) | fastbook style | Obscures what the student must reproduce locally | Visible, short setup cell |

### B. Exercise notebooks (derived from each solution notebook)

#### Table Stakes

| Feature | Why Expected | Complexity | Notes / Depends on |
|---|---|---|---|
| **Derived 1:1 from the solution notebook**, same narrative, same data, same headings | Kaggle pairs tutorial and exercise per lesson; nbgrader generates `release/` from `source/` | LOW–MEDIUM | Hard dependency on the finished solution notebook (PROJECT.md build order) |
| Blanks with a **consistent stub**: `____` inline (Kaggle) or `# YOUR CODE HERE` + `raise NotImplementedError()` (nbgrader default) | Both conventions are widely recognized by Python learners | LOW | Pick one; recommend nbgrader stub for multi-line cells, `____` for single-expression fills |
| **Checkpoint cells** with friendly asserts right after each task (`assert np.allclose(np.linalg.norm(q), 1.0), "Renormalise the prototype"`) | Kaggle `step_1.check()`; nbgrader autograded asserts; students need to know they are on track before the next step | LOW | At least one visible test per task (nbgrader guidance) |
| **Expected-output hints** ("You should see about 0.85–0.92") | Kaggle and Carpentries show expected output; prevents silent wrong answers | LOW | |
| **Hidden solutions** accessible on demand: collapsible `<details><summary>Solution</summary>` in markdown or link to the solution notebook | Carpentries "Show me the solution"; Kaggle ships `.solution()` commented so "Run all" does not spoil | LOW | `<details>` renders in JupyterLab and Colab; verify in nbviewer |
| Setup and data-loading cells **kept intact** (read-only in spirit) | nbgrader locks them; students should struggle with the concept, not with I/O | LOW | |
| Exercise tasks target the *learning* code (cosine function, prototype, block ids, `cross_validate` call), not boilerplate | Kaggle: focus "only on the new concept they've learned, not on solving Python problems"; intermediate steps as comments | LOW | 30–40% of code cells become tasks |
| Runs to the first `NotImplementedError` cleanly; **everything before it executes** | Otherwise students cannot tell environment failures from their own | LOW | nbmake with `allow_errors` or solution-filled variant in CI (G) |

#### Differentiators

| Feature | Value Proposition | Complexity | Notes / Depends on |
|---|---|---|---|
| **Single-source generation**: cell tags (`solution`, `stub:...`, `hidden-test`) on the solution notebook + a small `nbformat` script produce the exercise notebook | Kaggle `raw/` → `rendered/` and nbgrader `source/` → `release/` avoid divergence; keeps exercises in sync when the solution changes | MEDIUM | Script lives in `tools/`; unit-tested; run in CI |
| **Checker self-tests**: hidden cells that assert the checkpoint fails on a wrong answer and passes on the right one | Kaggle `#%%RM_IF(PROD)%% ... assert_check_failed()` pattern; catches useless asserts | LOW | Removed by the generator |
| **Reflection prompts** ("Think about your data": Why did block CV drop 12 points? Which class collapsed?) with model answers hidden | Kaggle "Think About Your Data"; the report's quizzes test conceptual errors | LOW | Feeds quizzes (F) |
| **Stretch tasks** at the end (change block size; use `StratifiedGroupKFold`; add negatives) | Spatial Thoughts exercise scripts and ISPRS knobs; fastbook "Further Research" | LOW | |
| **Graded lab variant** with a short rubric cell (what to submit: figure + 3 sentences) | Maps to Udemy Assignment items and the report's assessment weights | LOW | Depends on F |

#### Anti-Features

| Feature | Why Requested | Why Problematic | Alternative |
|---|---|---|---|
| Full nbgrader/JupyterHub autograding | Real autograding is attractive | Needs a server; Udemy students are anonymous; maintenance burden | Self-check asserts + hidden solutions + Udemy assignments |
| Udemy built-in coding exercises for notebook content | Udemy recommends coding exercises per section | Browser runner is not Jupyter; geospatial libraries unverified; duplicates the notebook | At most 1–2 pure-NumPy exercises (cosine similarity, renormalise prototype) if the runner supports numpy; validate before committing |
| Removing *all* narrative from the exercise ("clean" notebook) | fastbook `clean/` | Students lose the why; fine for recall practice, poor for first exposure | Offer `clean/` only as optional extra later |
| Exercises that require drawing polygons in a live map | Spatial Thoughts style | Needs EE; not reproducible; unassessable | Provide candidate polygons in the frozen dataset; task = choose/aggregate |

### C. Slide decks (per module)

#### Table Stakes

| Feature | Why Expected | Complexity | Notes / Depends on |
|---|---|---|---|
| 16:9, 1080p-legible; one idea per slide; large code fonts (80–120 char column) | Udemy 720p/1080p; egghead font/column guidance | LOW | |
| Module objectives slide (same numbered objectives as the notebook) and recap slide | Udemy lecture structure (objective → content → summary) | LOW | Depends on A header |
| Concept diagrams: pixel/patch/location taxonomy, provider decision flowchart, "1 − cosine measures representation movement" | Report's mermaid diagrams; Stewart et al. taxonomy | MEDIUM | Reusable across modules |
| **Figures exported from the solution notebook** (same confusion matrix, same bar chart) | Keeps slides and code consistent; avoids stale screenshots (Udemy complaint) | LOW | Depends on A producing `figures/*.png` |
| Attribution and license slide ("The AlphaEarth Foundations Satellite Embedding dataset is produced by Google and Google DeepMind", CC BY 4.0) | AEF license requires it; Spatial Thoughts shows citation block | LOW | |
| Version banner (dataset versions, env release date) | Report's maintenance policy | LOW | |

#### Differentiators

| Feature | Value Proposition | Complexity | Notes |
|---|---|---|---|
| **"WRONG conclusion" slides** mirroring the notebook trap cells, followed by the correct framing | Reinforces the course's methodological spine | LOW | Text identical to notebook cells and quiz stems |
| Markdown-sourced deck (Marp/Quarto/reveal) generated with the notebook figures | Diffable, regenerable when data or versions change | MEDIUM | Tool choice belongs to STACK.md |
| Speaker notes = first draft of narration | Halves the scripting effort; egghead/Udemy both recommend scripting | LOW | Feeds D |
| Comparison slides (AlphaEarth vs TESSERA vs Clay vs LGND vs OlmoEarth table from the report) | Provider-portability is a stated course promise | LOW | |

#### Anti-Features

| Feature | Why Requested | Why Problematic | Alternative |
|---|---|---|---|
| Transformer/MAE architecture deep dives | "Where do embeddings come from" | Out of scope per PROJECT.md; eats minutes | One "black box with inputs/outputs" slide + reading list |
| Screenshots of Earth Engine Code Editor | Familiar to GEE users | JS; goes stale | Python/geemap screenshot only in Module 2 Path A |
| Dense text slides read aloud | Easy to write | Udemy: "too much screencast or talking head can become tedious"; egghead: show, then explain | Diagram + one sentence; narration carries detail |

### D. Narration scripts (recording-ready)

#### Table Stakes

| Feature | Why Expected | Complexity | Notes / Depends on |
|---|---|---|---|
| **Two-column AV format**: VISUAL (which notebook cell / slide, what to highlight, cursor/zoom) | AUDIO (narration verbatim), with a duration per row | Standard AV script (StudioBinder, Boords, Celtx); rows of ~20 s match egghead's "20-second paragraphs" | LOW | Depends on final notebook cell order and slide numbers (A, C) |
| Lecture segmentation to Udemy's **2–6 min** guideline (codealongs may run longer, target ≤ 10–12 min) with an objective line and a recap line per lecture | Udemy quality standards; writerontheside 2023: objective → concept → summary | LOW | Module 3 (65 min) ≈ 8–10 lectures |
| Cell anchors: every row names the notebook cell id/heading being executed so recording follows the solution notebook exactly | egghead "your words should reflect what's happening on the screen" | LOW | |
| **Timing marks** (cumulative mm:ss) and explicit pause/cut cues (`[PAUSE 2s]`, `[CUT]`, `[RUN CELL]`, `[ZOOM 150%]`) | AV script convention; egghead "record in tiny takes" | LOW | |
| Key teaching messages **verbatim** (unit-length → dot = cosine; A17 is not NDVI; random split leaks; DW is a model output; 1 − cosine ≠ semantic transition) | PROJECT.md "messages the materials must carry" | LOW | Same sentences in slides and quiz explanations |
| Show-then-explain ordering; no reading code aloud; plain instructions ("run the cell", "note the drop from 0.97 to 0.82") | egghead style guide | LOW | |
| Pronunciation/notation notes (AlphaEarth, TESSERA, GeoTessera, EPSG:2056, precision@k) | Reduces retakes | LOW | |

#### Differentiators

| Feature | Value Proposition | Complexity | Notes |
|---|---|---|---|
| "End-state" line per lecture (what must be on screen at the last frame) | Makes editing and re-recording deterministic | LOW | |
| Muted-playback check column (does the visual alone convey the point?) | egghead recommends watching muted playback | LOW | |
| Callbacks to the exercise ("in the exercise you will replace this line") and to the quiz | Ties deliverables together; drives completion | LOW | Depends on B and F |
| Script-derived lecture titles and Udemy lecture descriptions | Saves publishing time (author's manual step) | LOW | |

#### Anti-Features

| Feature | Why Requested | Why Problematic | Alternative |
|---|---|---|---|
| Fully improvised recording from an outline | egghead allows bullet outlines | Udemy courses are long; fillers and drift accumulate; consistency of key messages suffers | Verbatim script for concept lines, bullet outline allowed for typing segments |
| Scripting before the notebook and slides are frozen | Parallel work | Any cell reorder invalidates anchors and timings | PROJECT.md order: notebook → exercise → slides → script |
| Long single-take lectures (15–20 min) | Fewer files | Udemy 2–6 min guidance; harder to update stale parts | Split at `##` section boundaries |

### E. Frozen teaching datasets

#### Table Stakes

| Feature | Why Expected | Complexity | Notes / Depends on |
|---|---|---|---|
| **Small**: a few thousand rows per table; ≤ ~1 MB per parquet (ISPRS: 3,000 x 78 cols = 0.42 MB); whole course bundle well under 100 MB | ISPRS demo 1 loads in seconds; its 229 MB EuroSAT `.npz` is the slow outlier | LOW | |
| **Parquet/GeoParquet** with `geo` metadata (`version`, `primary_column`, `columns.{encoding, geometry_types, crs}`) or explicit `lon`/`lat` + projected `x`/`y` columns | GeoParquet 1.1 is the interoperable standard; ISPRS uses plain parquet with `lat`/`lon` | LOW | GeoPandas writes it directly |
| Columns: `A00..A63` **float32, dequantized, unit-norm**; `lon`, `lat`; `year`; `label`; `label_source`; `region` (A/B); plus Sentinel-2 bands `B2..B12` for the baseline | Mirrors ISPRS schema; AEF GCS README: dequantize `((v/127.5)**2)*sign(v)` then vectors are unit length | MEDIUM | Assertion cell in A depends on this |
| **Dataset card / README** (HF template sections: Description, License, Sources, Uses, Structure, Creation, Bias/Limitations, Citation) | Datasheets for Datasets; HF card template; ISPRS *lacks* one (gap) | LOW | |
| Per-source **license and attribution**: AEF CC BY 4.0 + exact attribution sentence; Dynamic World CC BY 4.0; Copernicus HRL terms verified before bundling; Sentinel-2 Copernicus terms | AEF README makes the sentence mandatory; PROJECT.md constraint | LOW | Legal check on Copernicus is a task, not a feature |
| **Provenance JSON** shipped with the data: `embedding_product`, `dataset_version` (`GOOGLE_SATELLITE_EMBEDDING_V1_ANNUAL`), `year`, `extraction_date`, `ee_asset_or_gcs_path`, `sampling_method`, `crs`, `label_source`, `validation_source`, `license`, `created_by`, `sha256` | Report's provenance dict; version drift (AEF 1.1 regenerated 2017) | LOW | Same schema the notebooks write |
| **Reproducible prep scripts** committed (`scripts/`), clearly "author-only, needs Earth Engine", with run order | ISPRS `scripts/README.md` pattern; makes the frozen data auditable | MEDIUM | Author must authenticate EE (PROJECT.md finding) |
| Pinned release (git tag / HF revision) and checksums | Course must survive silent data changes | LOW | |
| Public, **no-login hosting** (GitHub release assets or public HF dataset repo) with local-first fetch | ISPRS: HF dataset, "no login, no Earth Engine" | LOW | |

#### Differentiators

| Feature | Value Proposition | Complexity | Notes |
|---|---|---|---|
| **Two geographically distinct regions** in one schema (train region A, transfer region B) | Enables leave-region-out in Module 3 without extra downloads; ISPRS does this (Saskatchewan/Manitoba) | MEDIUM | Region choice per PROJECT.md (Bern/Swiss Plateau + distinct region) |
| **Two label sources side by side** (`label_dw`, `label_copernicus`) with a `label_source` column | Makes "Dynamic World is not independent ground truth" demonstrable, not just stated | MEDIUM | Copernicus terms check first |
| **Two years** (2020, 2024) for the same points | Module 4 change lab reuses the same table | LOW–MEDIUM | |
| **Candidate query polygons** as a small GeoJSON (solar farm, quarry, new development) | Search-by-example without a live map | LOW | |
| Dataset **unit tests** in CI (norms ≈ 1, no NaN, column set, class counts, CRS present) | Catches prep regressions; ISPRS has `tests/` for code but not data | LOW | |
| Dense **grid tables** for map rendering (ISPRS `aef_crop_grid.parquet`, 0.3 MB) | Lets students draw a classified map offline | LOW | |

#### Anti-Features

| Feature | Why Requested | Why Problematic | Alternative |
|---|---|---|---|
| Bundling raw AEF COG tiles or Sentinel-2 scenes | "Real data" | Hundreds of MB; slow Colab; redistribution and provider-pays egress issues | Sampled tables + one tiny clipped GeoTIFF (< 5 MB) for the raster lesson |
| Redistributing Copernicus Global Embeddings or TESSERA tiles without checking terms | Convenience for Module 5 | Licensing unverified per report | Fetch live in Module 5 with a tiny cached fallback only after terms are confirmed |
| Shipping raw int8 values | Smaller files | Students average int8 and break unit-norm; report warns explicitly | Ship float32 dequantized; document the formula |
| Global random samples | "More general" | Kills the running story and spatial-CV lesson | Two compact regions tied to the artificialization narrative |

### F. Assessments (quizzes, labs, capstone)

#### Table Stakes

| Feature | Why Expected | Complexity | Notes / Depends on |
|---|---|---|---|
| Udemy **MCQ quiz per module** (5–8 questions) written as conceptual-error questions with per-option explanations | Report's quiz examples; HF end-of-chapter quizzes; Udemy quiz item | LOW | Stems come from Wrap-up/Takeaway cells and WRONG-conclusion cells (A) |
| Ungraded 5-question diagnostic for the optional refresher | Report syllabus | LOW | |
| **Graded labs as Udemy Assignments** (instructions + downloadable exercise notebook + what to submit) for Modules 3, 4, 5 | Udemy Assignment supports resources and instructor feedback; report weights 15/20/20/10% | LOW | Depends on B |
| **Capstone rubric** published up front (30% validation design, 15% reproducibility/provenance, 15% CRS/alignment, 15% interpretation/uncertainty, 15% representation choice, 10% licensing/ethics) | Report's capstone criteria | LOW | |
| Self-check asserts inside exercise notebooks | Immediate formative feedback (Kaggle/nbgrader) | LOW | B |

#### Differentiators

| Feature | Value Proposition | Complexity | Notes |
|---|---|---|---|
| Quiz explanations that quote the notebook cell where the answer was demonstrated | Closes the loop between video, notebook and quiz | LOW | |
| "Spot the leakage" question type (given a split description, is it valid?) | Directly tests the course's highest-weighted skill | LOW | |
| Capstone proposal template notebook with provenance dict and rubric checklist pre-filled | Lowers barrier; enforces methodology | LOW–MEDIUM | |

#### Anti-Features

| Feature | Why Requested | Why Problematic | Alternative |
|---|---|---|---|
| Udemy Practice Tests | Available item type | Certification-exam format; irrelevant here | Quizzes + assignments |
| Terminology-recall quizzes | Easy to write | Report explicitly rejects; low signal | Conceptual-error questions |
| Autograded capstone | Scales | Not possible on Udemy; methodology needs judgment | Rubric + optional peer/community review |

### G. Repository, environment and delivery (cross-cutting)

| Feature | Category | Why | Complexity | Notes |
|---|---|---|---|---|
| Public repo with README listing notebooks, Colab badges, data sources and licenses | Table stakes | ISPRS README is the model; Udemy resources link here | LOW | |
| Reproducible env: `pyproject.toml` + `uv.lock`, Python 3.12, pinned versions; optional isolated Clay env | Table stakes | PROJECT.md constraint; GeoTessera needs 3.12+ | MEDIUM | STACK.md decides details |
| **CI executes every solution notebook** (`pytest --nbmake`) against frozen data on a CPU runner | Differentiator | Guarantees "it runs" before each recording and after each library bump; no comparable does this visibly | MEDIUM | Depends on E hosting and A cleanliness |
| Exercise generator + checker self-tests run in CI | Differentiator | Keeps exercises in sync (Kaggle/nbgrader pattern) | MEDIUM | B |
| Per-lecture downloadable zip (notebook pair + data pointer + slides PDF) | Table stakes | Udemy resources per lecture; Spatial Thoughts ships a zip | LOW | Generated by a script from the repo tag |
| `jupytext` pairing (`ipynb,py:percent`) for reviewable diffs | Nice-to-have | Easier review of notebook changes | LOW | Optional |

---

## The First Deliverable: `02_similarity_and_classification.ipynb` — what "excellent" means

Synthesised from what the comparables do well (ISPRS structure and baseline, Google 05 prototype averaging, Spatial Thoughts negatives) and what all of them omit (spatial CV, measured retrieval quality, provenance).

### Required cell blueprint (~40 cells, ≤ 3 min runtime on Colab CPU)

| # | Section | Cells | Must contain | Evidence |
|---|---|---|---|---|
| 0 | Header | 2 md | Title; Colab badge; overview; **objectives** (1. cosine search-by-example, 2. prototype queries, 3. 2–4 class classifier, 4. random vs spatial-block vs leave-region-out, 5. raw-band baseline); prerequisites table; "runs on free Colab CPU, no Earth Engine account"; reference-environment banner | Pythia, ISPRS, PROJECT.md |
| 1 | Setup | 1 code | `RUNNING_IN_COLAB`, pinned `pip install -q`, imports, `RANDOM_STATE=42`, `DATASET_VERSION`, `DATA_RELEASE`, `fetch()` local-first | ISPRS setup cell |
| 2 | Data | 2 md + 3 code | Load `aef_points_<regionA>.parquet`, `aef_points_<regionB>.parquet`; print schema; scatter of points coloured by label; class counts; **assert** 64 `A` columns and `np.allclose(norms, 1, atol=1e-3)` with a Takeaway: "this is why dot product = cosine here" | AEF GCS README; report |
| 3 | Similarity 1 | 2 md + 3 code | `cosine_similarity_map` via `einsum`; single-pixel query → top-k table + map; histogram of similarities; **WRONG conclusion cell**: "similarity > 0.90 means same land cover" → discussion | Google 05 threshold; report |
| 4 | Similarity 2 | 2 md + 3 code | Polygon-mean prototype (renormalised) → top-k; precision@k vs labels; ✏️ EDIT ME: `QUERY_ID`, `K`; Takeaway on query stability | Report §cosine; Google 05 mean of references |
| 5 | Similarity 3 (optional) | 1 md + 2 code | Positive-minus-negative prototype; precision@k comparison table for the three query designs | Spatial Thoughts negatives supplement |
| 6 | Classification | 2 md + 4 code | 2–4 classes; `Pipeline(StandardScaler, LogisticRegression)` and `RandomForestClassifier(class_weight="balanced")`; **random split** accuracy + `ConfusionMatrixDisplay` (the trap number, labelled as such) | ISPRS crop_probe; report |
| 7 | Spatial CV | 2 md + 4 code | Reproject to EPSG:2056; `make_blocks(10_000 m)` → `groups`; `GroupKFold(n_splits=5, shuffle=True, random_state=RANDOM_STATE)`; `cross_validate` with `balanced_accuracy`, `f1_macro`; leave-region-out on region B; **one bar chart**: random vs block vs region; per-class precision/recall; **map of errors** | sklearn docs (verified); ISPRS transfer map; report |
| 8 | Baseline | 1 md + 2 code | Same pipeline and same CV on `B2..B12`; comparison table; Takeaway: "embeddings vs raw bands under honest validation" | ISPRS S2 baseline |
| 9 | Few-shot (optional) | 1 md + 2 code | Accuracy vs samples/class curve under block CV; tests Google's "10 samples" claim | Google 03 |
| 10 | Provenance | 1 md + 1 code | `provenance` dict (product, `dataset_version`, year, CRS, label source, validation source, license, attribution sentence, `created_by`) written to `outputs/provenance.json` | Report; AEF license |
| 11 | Wrap-up | 3 md | Takeaways (5 bullets); What's next (Module 4 uses these helpers); Resources with URLs and licenses; Path A appendix (illustrative EE sampling code, not executed) | ISPRS wrap-up + optional GEE cell |

### Quality gates for this notebook

- `Restart & Run All` passes locally (uv env) and in Colab CPU; nbmake in CI.
- Every claim in a Takeaway cell is visible in the cell output above it.
- Stub-able cells for the exercise are identified by tag before the exercise is generated (targets: `cosine_similarity_map`, prototype renormalisation, `make_blocks`, the `cross_validate` call, the baseline column selection).
- Figures saved to `figures/02_*.png` for the slide deck.
- No cell depends on network beyond `fetch()`.

---

## Feature Dependencies

```
[G: pinned env + repo + hosting]
    └──requires──> nothing (foundation)

[E: frozen dataset schema + provenance JSON schema]
    └──requires──> [G hosting decision]
    └──requires──> [author EE authentication] (Path A prep scripts only)

[A: solution notebook 02]
    └──requires──> [E: region A + region B tables with A00..A63 float32, S2 bands, labels]
    └──requires──> [G: env]
    └──produces──> figures/02_*.png, course_utils helpers, provenance.json

[A: solution notebooks 00, 01, 03, 04, 05]
    └──reuse──> [A02 helpers: cosine_similarity_map, make_blocks, spatial_cv_report]

[B: exercise notebook 02]
    └──requires──> [A02 frozen (cell tags placed)]
    └──requires──> [tools/make_exercise.py]

[C: slides 02]
    └──requires──> [A02 figures + objectives + trap-cell text]

[D: script 02]
    └──requires──> [C02 slide numbers] and [A02 final cell order]
    └──references──> [B02 tasks] and [F quiz]

[F: quiz 02]
    └──requires──> [A02 Takeaway/WRONG-conclusion cells]
[F: assignment 02]
    └──requires──> [B02]

[G: CI nbmake] ──enhances──> [A, B]  (guarantees "it runs")
[E: dataset unit tests] ──enhances──> [A02 assertion cell]

[Live geemap default path] ──conflicts──> [offline guarantee / nbmake CI]
[Large raster bundles] ──conflicts──> [Colab CPU runtime, redistribution terms]
```

### Dependency Notes

- **B requires A frozen:** exercise generation is mechanical only if the solution's cell order and tags are final; regenerating after solution edits is cheap with a generator, expensive by hand.
- **D requires C and A:** timing marks and cell anchors break on any reorder; scripts are the last artifact per module (matches PROJECT.md order).
- **A02 requires E with two regions and S2 bands:** the two headline features (leave-region-out, baseline) are impossible without them; schema must be decided before extraction because the author has to authenticate Earth Engine once for prep.
- **F requires A's trap cells:** the report's quiz style ("what can you conclude from A17 rising?") only works if the notebook demonstrated the trap.
- **CI enhances everything:** ISPRS ships `tests/` for code; adding notebook execution catches the failure class students actually hit (library drift).

---

## MVP Definition

### Launch With (v1)

- [ ] `02_similarity_and_classification.ipynb` solution notebook meeting the blueprint above — core value of the course
- [ ] Frozen dataset v1: region A + region B point tables (float32 `A00..A63`, `B2..B12`, labels with `label_source`, lon/lat, year), provenance JSON, dataset card, prep scripts, checksums, public no-login hosting — nothing runs without it
- [ ] Pinned `uv` environment (Python 3.12) and Colab setup cell verified on a fresh Colab CPU runtime — the "it runs" promise
- [ ] Repo README with Colab badges, data sources and licenses (ISPRS pattern) — delivery mechanism for Udemy
- [ ] Exercise notebook 02 with stubs, checkpoints, expected outputs, hidden solutions — Udemy hands-on expectation
- [ ] Slides 02 with notebook-exported figures, objectives, WRONG-conclusion slides, attribution slide
- [ ] Script 02 in two-column AV format with timing marks and cell anchors, segmented into 2–7 min lectures
- [ ] Quiz 02 (6–8 conceptual questions with explanations) and Assignment 02 text with rubric
- [ ] Remaining modules follow the same pipeline (00, 01 → 03, 04, 05), each solution-first

### Add After Validation (v1.x)

- [ ] CI notebook execution (`pytest --nbmake`) and dataset unit tests — trigger: first library-drift failure or before recording
- [ ] Single-source exercise generator with checker self-tests — trigger: second module's exercise (manual derivation twice is the signal)
- [ ] Few-shot curve and positive-minus-negative prototype sections — trigger: Module 3 runtime under 2 min with headroom
- [ ] Dense grid table for offline classified-map rendering — trigger: student feedback asking "show me the map"
- [ ] Per-lecture downloadable zips generated from a tag — trigger: Udemy upload

### Future Consideration (v2+)

- [ ] `clean/`-style prose-stripped notebooks for recall practice — after core content stabilises
- [ ] Udemy coding exercises for pure-NumPy steps — only after verifying the runner supports numpy
- [ ] Interactive geemap Path A recordings as bonus lectures — after EE eligibility/quota is confirmed for the author
- [ ] Community/peer review flow for capstones — needs audience size

---

## Feature Prioritization Matrix

| Feature | User Value | Implementation Cost | Priority |
|---|---|---|---|
| Offline-guaranteed solution notebook 02 (Colab CPU, no EE) | HIGH | MEDIUM | P1 |
| Random vs spatial-block vs leave-region-out comparison chart | HIGH | MEDIUM | P1 |
| Frozen two-region dataset with S2 bands + provenance + card | HIGH | MEDIUM | P1 |
| Unit-norm assertion + WRONG-conclusion cells | HIGH | LOW | P1 |
| Sentinel-2 raw-band baseline, same pipeline | HIGH | LOW | P1 |
| Prototype query ladder with precision@k | HIGH | LOW | P1 |
| Exercise notebook with stubs, checkpoints, hidden solutions | HIGH | LOW | P1 |
| Slides with notebook-exported figures | MEDIUM | LOW | P1 |
| Two-column AV script with timing marks | MEDIUM | LOW | P1 |
| Conceptual MCQ quizzes + assignment rubric | MEDIUM | LOW | P1 |
| Pinned uv env + Colab setup cell | HIGH | LOW | P1 |
| Map of errors | MEDIUM | LOW | P1 |
| CI notebook execution (nbmake) | HIGH (author) | MEDIUM | P2 |
| Exercise generator + checker self-tests | MEDIUM | MEDIUM | P2 |
| Few-shot curve | MEDIUM | LOW | P2 |
| Two label sources side by side | MEDIUM | MEDIUM | P2 |
| Dense grid table for offline maps | MEDIUM | LOW | P2 |
| Reusable `course_utils.py` with tests | MEDIUM | MEDIUM | P2 |
| `clean/` recall notebooks | LOW | LOW | P3 |
| Udemy coding exercises (NumPy only) | LOW | LOW–UNKNOWN | P3 |
| geemap interactive Path A recordings | LOW | HIGH (credentials) | P3 |

**Priority key:** P1 must have for launch; P2 should have; P3 nice to have.

---

## Competitor Feature Analysis

| Feature | ISPRS 2026 tutorial | Google tutorials (JS) | Spatial Thoughts workshop (JS) | Clay wall-to-wall | Our approach |
|---|---|---|---|---|---|
| Runs without EE account | Yes (HF frozen parquet, Colab CPU) | No | No | Yes (STAC + GPU preferred) | Yes; Path B default, Path A appendix |
| Language | Python | JavaScript | JavaScript | Python | Python only |
| Similarity query | Single query patch, cosine map (demo 2) | Mean of 3 reference points, dot product, threshold 0.90 | Reference samples, threshold 0.90–0.97, negatives in supplement | n/a | Ladder: pixel → polygon mean → pos−neg; ranked; precision@k; histogram vs threshold |
| Classifier evaluation | Random stratified split + separate transfer region; normalized CM; error map | None (03), training-data R² (04) | Acreage vs statistics; qualitative | 5 hand-picked test chips | Random split (shown as trap) vs 10 km GroupKFold vs leave-region-out; CM; per-class P/R; error map |
| Raw-band baseline | Yes, same probe | No | No | No | Yes, same pipeline and CV |
| Exercises | None (demo, one EDIT ME knob) | None | Comment-driven exercise scripts | None | Derived exercise notebooks: stubs, checkpoints, expected output, hidden solutions, stretch tasks |
| Assessments | None | None | None | None | Conceptual MCQ per module, assignments with rubric, capstone rubric |
| Data provenance | README source list; parquet with pandas metadata only; no dataset card | EE catalog | EE assets | HF checkpoint pinned | Dataset card + provenance JSON + in-notebook provenance dict + checksums + prep scripts |
| Slides / video | Lecture PDF | None | Full video + slides | None | Per-module deck with notebook figures; scripted 2–7 min lectures |
| Version policy | Implicit | Live service | Live service | Pinned ckpt | Reference-environment banner, pinned versions, CI execution |

---

## Sources

Confidence levels: HIGH = primary artifact read (notebook JSON, README, official docs); MEDIUM = official page fetched via summarizer or multiple agreeing secondary sources; LOW = single secondary source or unverified.

- ISPRS 2026 tutorial repo, README, `scripts/README.md`, both notebooks parsed cell-by-cell, HF dataset file listing and `aef_crop_train.parquet` schema — https://github.com/konstantinklemmer/isprs26-embeddings-tutorial , https://huggingface.co/datasets/kklmmr/isprs26-earth-embeddings — HIGH
- Spatial Thoughts, Satellite Embedding Deep Dive — https://courses.spatialthoughts.com/gee-satellite-embedding.html — MEDIUM; Python Foundation course (exercise/zip conventions) — https://courses.spatialthoughts.com/python-foundation.html — MEDIUM
- Google Earth Engine community tutorials 01–05 — https://developers.google.com/earth-engine/tutorials/community/satellite-embedding-01-introduction (…-02-unsupervised-classification, -03-supervised-classification, -04-regression, -05-similarity-search) — MEDIUM-HIGH
- AlphaEarth on GCS README (license, attribution sentence, dequantization, unit norm, manifest, provider-pays) — https://developers.google.com/earth-engine/guides/aef_on_gcs_readme — HIGH
- Clay docs TOC and tutorials — https://clay-foundation.github.io/model/tutorials/wall-to-wall.html , https://clay-foundation.github.io/model/finetune/classify.html — MEDIUM
- fastbook repo, `clean/01_intro.ipynb`, chapter Questionnaire/Further Research headings — https://github.com/fastai/fastbook — HIGH
- Hugging Face LLM course chapter structure and quiz — https://huggingface.co/learn/llm-course/chapter1/1 , …/chapter1/11 — MEDIUM
- Kaggle `learntools` README, `notebooks/README.md`, `MACROS.txt`, `notebooks/machine_learning/raw/ex2.ipynb`, `learntools/core/problem.py` — https://github.com/Kaggle/learntools — HIGH
- nbgrader: creating assignments and config defaults (`# YOUR CODE HERE\nraise NotImplementedError()`) — https://nbgrader.readthedocs.io/en/stable/user_guide/creating_and_grading_assignments.html , https://nbgrader.readthedocs.io/en/stable/configuration/config_options.html — HIGH
- Carpentries Incubator geospatial-python episode structure — https://carpentries-incubator.github.io/geospatial-python/05-access-data.html — HIGH
- Project Pythia notebook template — https://github.com/ProjectPythia/cookbook-template/blob/main/notebooks/notebook-template.ipynb — HIGH
- scikit-learn `GroupKFold(n_splits, shuffle, random_state)`, `StratifiedGroupKFold` — Context7 `/websites/scikit-learn_stable` — HIGH
- GeoParquet 1.1 metadata — https://geoparquet.org/releases/v1.1.0/ — HIGH
- Hugging Face dataset card template — https://github.com/huggingface/huggingface_hub/blob/main/src/huggingface_hub/templates/datasetcard_template.md — HIGH; Datasheets for Datasets — https://arxiv.org/abs/1803.09010 — HIGH
- egghead instructor guidance — https://dev.to/egghead/recording-a-great-coding-screencast-g35 , https://howtoegghead.com/instructor/style-guide/talking-about-code/ — MEDIUM
- Two-column AV script format — https://www.studiobinder.com/templates/av-scripts/two-column-script-template/ , https://boords.com/video-script-template , https://blog.celtx.com/essential-av-script-template-for-better-video-scripts/ — MEDIUM
- Udemy quality/lecture-length/curriculum-item rules (support pages Cloudflare-gated; via search summaries of https://support.udemy.com/hc/en-us/articles/229604988-Udemy-course-quality-checklist , https://support.udemy.com/hc/en-us/articles/229232767-Video-Standards , https://support.udemy.com/hc/en-us/articles/229606188-Understanding-Curriculum-Items-for-Your-Course , https://teach.udemy.com/wp-content/uploads/2016/01/Quality-Standards.pdf , and https://www.writerontheside.com/how-to-think-about-udemy-lecture-strategy-length/ (2023)) — MEDIUM; Udemy coding-exercise environment details — LOW, validate before relying on them
- nbmake (`pytest --nbmake`), jupytext pairing — local Context7 dumps — MEDIUM
- Course design report `docs/research/course-design-research-2026-08.md` and `.planning/PROJECT.md` — project-internal, authoritative for scope

---
*Feature research for: notebook-based Udemy course on geospatial embeddings*
*Researched: 2026-09-03*

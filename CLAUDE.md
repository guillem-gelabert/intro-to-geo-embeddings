<!-- GSD:project-start source:PROJECT.md -->
## Project

**Introduction to Geospatial Embeddings**

A roughly six-hour, developer-oriented Udemy course that teaches how to use geospatial embeddings (AlphaEarth / Google Satellite Embedding as the backbone, with TESSERA, Clay, LGND, OlmoEarth, Copernicus and SatCLIP for portability) as practical data products: visualize, search, classify, detect change, and validate rigorously with spatial cross-validation. It is not a course on training Earth-observation foundation models.

The deliverables are course materials: solution notebooks, exercise notebooks derived from them, slide decks, and narration scripts for each module, plus small frozen teaching datasets so every notebook runs without cloud credentials.

**Core Value:** A student can take a precomputed geospatial embedding field, run similarity search and a lightweight classifier on it, and evaluate the result with a spatially honest validation — and that entire workflow runs from a notebook without needing an Earth Engine account.

### Constraints

- **Tech stack**: Python 3.12 via uv; JupyterLab/Colab; numpy, pandas, scikit-learn, matplotlib, geopandas, shapely, pyproj, rasterio, xarray, pyarrow, duckdb, fsspec, s3fs, pystac-client, stackstac, earthengine-api, geemap; `geotessera` for TESSERA; `requests`/`httpx` for LGND; torch/lightning/torchgeo optional and isolated — the report's recommended stack, Colab-first with a reproducible local env, not Docker-first
- **Data**: Frozen teaching datasets must be small (a few thousand rows), carry source provenance and license, and be redistributable (AlphaEarth CC BY 4.0 with Google/DeepMind attribution; Clay corpus CC BY 4.0; check Copernicus terms before bundling) — a paid course must survive auth failures, quota changes and disappearing API versions
- **Credentials**: Earth Engine access is the author's to arrange (GCP project, current eligibility/quota); LGND requires a token (trial tier exists) — notebooks must never hard-depend on either
- **Pedagogy**: Every notebook includes the conceptual traps as explicit cells (the "WRONG conclusion" cell, random vs spatial split comparison) — the report's quizzes test conceptual errors, not terminology
- **Runtime**: Core path ~5 h 35 min; total 360 min with the optional refresher — Udemy positioning
- **Versioning**: Pin dataset versions (AlphaEarth `DATASET_VERSION`, GeoTessera version) and library versions; repository banner "Course reference environment: 2026-08 release" — the field moves fast enough that unpinned material rots
- **Ethics**: Concrete, not generic — where evaluated, what counts as error, who bears false-positive cost, sensitivity of inferred information vs underlying imagery
<!-- GSD:project-end -->

<!-- GSD:stack-start source:research/STACK.md -->
## Technology Stack

## TL;DR — the decisions
| Question | Decision | Confidence |
|---|---|---|
| Python version | **3.12** (uv-managed, `.python-version` = `3.12`, `requires-python = ">=3.12,<3.14"`). 3.13 is the tested secondary. 3.14 works empirically but is undeclared upstream — do not ship it as the reference. | HIGH |
| Environment manager | **uv 0.12.9** — `uv.lock` is the single source of truth; `uv export` produces the Colab `requirements` file. No conda, no Docker-first. | HIGH |
| Phase 1 notebook stack | numpy 2.5 · pandas 3.0 · pyarrow 25 · geopandas 1.1.4 (shapely 2.1, pyproj 3.7) · scikit-learn 1.9 · matplotlib 3.11 (+ folium/mapclassify for `.explore()`). Nothing cloud-related. | HIGH |
| AlphaEarth access | Path A = `earthengine-api` 1.7 + `geemap` 0.38 (`ee.Initialize(project=...)`). Path A′ (no EE account) = `rasterio` 1.5 anonymous reads of the GCS COGs (`GS_NO_SIGN_REQUEST=YES`). Path B = frozen GeoParquet. | HIGH |
| TESSERA | `geotessera` 0.10.1, pinned `GeoTessera(dataset_version="v1.1", dataset_variant="cambridge")`. | HIGH |
| Clay corpus | `duckdb` 1.5 (spatial + httpfs) reading LGND GeoParquet over plain **HTTPS** (`https://data.source.coop/...`), not S3. | HIGH (verified live) |
| LGND API | `requests` 2.34 against the OpenAPI reference. No SDK. | HIGH |
| Spatial CV | `sklearn.model_selection.GroupKFold(n_splits, shuffle=True, random_state)` (shuffle since 1.6), `StratifiedGroupKFold`, `LeaveOneGroupOut`. No third-party spatial-CV package. | HIGH |
| Exercise derivation | Custom **nbformat** script driven by cell tags (`solution`, `remove`, `keep-output`) + nbgrader-style `### BEGIN/END SOLUTION` markers inside cells. Not nbgrader, not nbdev. | HIGH |
| Headless execution / tests | `jupyter execute` (nbclient 0.11 CLI) in a `Makefile`/`justfile`; pytest only for the shared helper module. Not nbmake. | HIGH |
| Text pairing / diffs | `jupytext` 1.19 `py:percent` pairing for solution notebooks; `nbstripout` 0.9 pre-commit hook. | HIGH |
| Slides | **Quarto 1.10.18** `format: revealjs` with `{{< embed nb.ipynb#label >}}` to pull figures straight from the solution notebooks and `::: {.notes}` as the narration-script seed. Marp is the fallback. Not Slidev, not RISE. | HIGH |
| Frozen data format | **GeoParquet 1.1.0**, WKB geometry, zstd, covering bbox, embedding as 64 wide `float32` columns `A00..A63`; provenance JSON in Parquet key-value metadata + sidecar `DATA_CARD.md`. Small rasters as COG GeoTIFF. Not GeoParquet 2.0 (rc), not CSV, not pickle/npz. | HIGH |
## Python version: 3.12 vs 3.13 vs 3.14 (explicit verdict)
### Evidence
| Package (latest, date) | `requires_python` | Declares 3.12 | Declares 3.13 | Declares 3.14 | cp314 wheel |
|---|---|---|---|---|---|
| numpy 2.5.2 (2026-08-09) | >=3.12 | yes | yes | yes | yes |
| pandas 3.0.5 (2026-07-22) | >=3.11 | yes | yes | yes | yes |
| scikit-learn 1.9.0 (2026-06-02) | >=3.11 | yes | yes | yes | yes |
| scipy 1.18.1 (2026-08-21) | >=3.12 | yes | yes | yes | yes |
| matplotlib 3.11.1 (2026-07-18) | >=3.11 | yes | yes | yes | yes |
| geopandas 1.1.4 (2026-06-26) | >=3.10 | (no classifiers) | — | — | pure py |
| shapely 2.1.2 (2025-09-24) | >=3.10 | yes | yes | yes | yes |
| pyproj 3.7.2 (2025-08-14) | >=3.11 | yes | yes | **no** | **yes** (wheel exists) |
| rasterio 1.5.1 (2026-08-08) | **>=3.12** | yes | yes | yes | yes |
| rioxarray 0.23.0 (2026-07-27) | **>=3.12** | yes | yes | yes | pure py |
| xarray 2026.7.0 (2026-07-09) | >=3.11 | yes | yes | **no** | pure py |
| pyarrow 25.0.1 (2026-08-10) | >=3.10 | yes | yes | yes | yes |
| duckdb 1.5.5 (2026-07-22) | >=3.10 | yes | yes | yes | yes |
| earthengine-api 1.7.42 (2026-08-31) | >=3.10 | yes | yes | yes | pure py |
| **geemap 0.38.4** (2026-08-27) | **>=3.12** | yes | yes | **no** | pure py |
| **geotessera 0.10.1** (2026-08-27) | **>=3.12** | yes | yes | **no** | pure py |
| pystac-client 0.9.0 (2025-07-18) | >=3.10 | yes | **no** | **no** | pure py |
| odc-stac 0.5.3 (2026-07-30) | >=3.10 | yes | yes | no | pure py |
| jupyterlab 4.6.3 (2026-08-10) | >=3.10 | yes | yes | yes | pure py |
| jupytext 1.19.5 / nbformat 5.11.1 / nbstripout 0.9.1 | >=3.9/3.10 | yes | yes | yes | pure py |
| papermill 2.7.0 (2026-02-27) | >=3.10 | yes | yes | no | pure py |
| torch 2.14.0 (2026-09-02) | >=3.10 | yes | yes | yes | yes |
| torchgeo 0.10.0 (2026-08-14) | **>=3.12** | yes | yes | yes | pure py |
### Verdict
- **Reference environment: Python 3.12.** It is the *floor* imposed by numpy 2.5, rasterio 1.5, rioxarray 0.23, geemap 0.38 and geotessera 0.10 (all `>=3.12`), and it is what Colab runs today, so local and Colab behave identically.
- **3.13: supported and should be CI-tested** (`uv lock --python 3.13` + `jupyter execute` of all notebooks) because Colab is about to move there. Every package declares 3.13 except pystac-client (pure Python, imports fine).
- **3.14 (the author's system Python): do not use as the reference.** It works today in practice, but geemap, geotessera, xarray, papermill and pystac-client do not declare or test it; a future point release can break it without notice, and it diverges from Colab. Set `requires-python = ">=3.12,<3.14"` so uv refuses to resolve against the system interpreter by accident.
## Recommended Stack
### Core Technologies (used by Phase 1 — the similarity + classification notebook on frozen AlphaEarth samples)
| Technology | Version | Purpose | Why Recommended |
|---|---|---|---|
| Python | 3.12.x (uv-managed) | Runtime | Colab parity; floor of the geo stack (see above). |
| uv | 0.12.9 | Env + lockfile + Python manager | Single tool for interpreter, venv, lock, export; `uv.lock` makes "Course reference environment: 2026-08" reproducible; geotessera itself develops with uv. |
| numpy | 2.5.2 | Vectors, cosine via `einsum`, L2 normalization | Core; Colab ships 2.0.2 — stay on the numpy 2.x API surface (no 1.x-only calls, no 2.3+-only features). |
| pandas | 3.0.5 | Tabular embedding samples | Current; **Copy-on-Write and `str` dtype are default** — write CoW-safe code (no chained assignment, no `inplace=True`) so notebooks also run on Colab's pandas 2.2.x. |
| pyarrow | 25.0.1 | Parquet/GeoParquet I/O, schema metadata for provenance | Backing engine for geopandas parquet and pandas `str` dtype. |
| geopandas | 1.1.4 | GeoDataFrame, CRS reprojection, GeoParquet 1.1 write/read, `.explore()` | 1.1.3+ carries the pandas-3 fixes (CoW, `str` dtype in `from_wkb`). Writes GeoParquet up to schema 1.1.0. |
| shapely | 2.1.2 | Geometries (points, spatial blocks) | Dependency of geopandas; vectorized 2.x API. |
| pyproj | 3.7.2 | CRS transforms (EPSG:4326 → EPSG:2056 for Swiss blocks) | Dependency of geopandas. |
| scikit-learn | 1.9.0 | RF / logistic classifier, `NearestNeighbors`, `GroupKFold(shuffle=True)`, `StratifiedGroupKFold`, `LeaveOneGroupOut`, metrics, `PCA` | `GroupKFold` gained `shuffle`/`random_state` in 1.6; Colab's sklearn may be older — guard with a version check or avoid `shuffle=True` in the Colab path. |
| matplotlib | 3.11.1 | Static maps, confusion matrices, PCA scatter | Standard; `ConfusionMatrixDisplay` from sklearn. |
| folium + mapclassify | current (folium 0.20.0) | `GeoDataFrame.explore()` interactive maps without Earth Engine | Colab has folium preinstalled; gives students a Leaflet map on the frozen data. |
| JupyterLab | 4.6.3 | Local authoring | Colab-compatible notebook format (nbformat 4.5 with cell ids). |
### Supporting Libraries (later phases)
| Library | Version | Purpose | When to Use |
|---|---|---|---|
| earthengine-api | 1.7.42 | AlphaEarth `GOOGLE/SATELLITE_EMBEDDING/V1/ANNUAL`, `sampleRegions`, exports | Module 2 Path A, data-prep scripts. Requires `ee.Initialize(project="...")` with an EE-enabled Cloud project; preinstalled in Colab. |
| geemap | 0.38.4 | Interactive EE maps, `ee_to_df`/`ee_to_numpy`, layer inspection | Module 2 Path A. **Preinstalled in Colab** (official geemap Colab notebook). Requires Python >=3.12. |
| xee (optional) | 0.1.2 | `xr.open_dataset(ic, engine="ee")` lazy AlphaEarth cubes | Module 2 if you want xarray from EE; 0.1.0 broke the API — pin `>=0.1.2`. LOW priority. |
| rasterio | 1.5.1 | Read AlphaEarth GCS COGs, small course GeoTIFFs | Module 2 Path A′ (no EE account) and data prep: `rasterio.Env(GS_NO_SIGN_REQUEST="YES")` + `gs://alphaearth_foundations/...` **works anonymously today** (verified: 64 bands, int8, nodata −128, 8192², overviews 2/4/8/16, EPSG:327xx). |
| rioxarray + xarray | 0.23.0 / 2026.7.0 | Labelled raster cubes, `to_raster(driver="COG")` for frozen tiles, change-detection pairs | Module 4 (aligned 2020/2024 stacks), data prep. |
| gcsfs / fsspec | 2026.8.0 / 2026.7.0 | Anonymous read of `aef_index.parquet` (69.6 MB, 302,466 rows, GeoParquet 1.1 WKB w/ covering bbox) | Data prep: find the COG for an AOI/year. |
| duckdb | 1.5.5 | SQL over GeoParquet (`INSTALL spatial; LOAD spatial;` auto-decodes geometry), `httpfs` for remote parquet | Module 5 Clay corpus; also a nice Phase 1 aside ("embeddings are just a table"). |
| s3fs | 2026.7.0 | Listing Source Cooperative S3 (`anon=True`, region `us-west-2`) | Module 5 discovery only; read the parquet itself over HTTPS. |
| geotessera | 0.10.1 | TESSERA 128-D, 10 m embeddings; `fetch_embedding`, `sample_embeddings_at_points`, `GeoTesseraZarr` streaming | Module 5. Pin `dataset_version="v1.1", dataset_variant="cambridge"` (v1.0 frozen legacy; v2 beta and slow to produce). Pulls in zarr 3.3, obstore, dask, scikit-image, contextily — heavy, but resolves cleanly with the rest. |
| requests | 2.34.2 | LGND REST (`Authorization: Bearer $LGND_TOKEN`) | Module 5. Preinstalled everywhere; don't add httpx just for one lesson. |
| pystac-client + odc-stac | 0.9.0 / 0.5.3 | Search + load Sentinel-2 L2A from Earth Search (no credentials) for the raw-pixel baseline and Clay input | Data prep for the S2 baseline; Module 5 Clay demo. **Use odc-stac, not stackstac** (see What NOT to Use). |
| pytz | current | Needed by DuckDB's Python client to materialize `TIMESTAMP WITH TIME ZONE` columns under pandas 3 (pandas 3 dropped the pytz dependency) | Module 5 Clay corpus — verified failure without it. |
| faiss-cpu (optional) | 1.15.0 | ANN demo at scale | Only if you show >1M-vector search; `sklearn.neighbors` suffices for teaching. |
| huggingface_hub (optional) | 1.29.0 | Host/download frozen course data as an HF dataset (ISPRS-2026 pattern) | If GitHub LFS is undesirable; also fetches Clay/SatCLIP weights. |
### Optional, isolated "model" environment (Module 5 Clay encoder demo only)
| Library | Version | Notes |
|---|---|---|
| torch | 2.14.0 | CPU wheel is enough for a 1-chip demo; Colab has CUDA torch 2.11. |
| claymodel | git `Clay-foundation/model` (pyproject 1.5.0; last tag v1.0.1 2025-07; last commit 2026-03) | `requires-python >=3.11`; deps `torch>=2.4, torchvision, einops~=0.7, lightning, timm, vit-pytorch, wandb`. Weights: `https://huggingface.co/made-with-clay/Clay/resolve/main/v1.5/clay-v1.5.ckpt`. Output `[1, 1024]`. |
| stackstac (only here) | 0.5.1 | Clay's own tutorials use it; it pins `pandas<3` — another reason this env is separate. |
| torchgeo / lightning | 0.10.0 / 2.6.5 | Only if you extend to the EuroSAT frozen-encoder example. |
### Development Tools
| Tool | Version | Purpose | Notes |
|---|---|---|---|
| jupytext | 1.19.5 | Pair `notebooks/solutions/*.ipynb` ↔ `py:percent` for reviewable diffs; percent cells carry tags as `# %% tags=["solution"]` | `jupytext.toml`: `formats = "ipynb,py:percent"`, `cell_metadata_filter = "tags,-all"`. Do **not** use it to derive exercises — it round-trips, it doesn't strip. |
| nbformat | 5.11.1 | The exercise-derivation script (`tools/derive_exercise.py`) | Read → transform cells by tag/marker → `nbformat.validate` → write. |
| nbclient | 0.11.0 | `jupyter execute --timeout=600 notebooks/solutions/02_*.ipynb` for headless runs; `NotebookClient` for Python-level tests | Run every solution notebook in CI; run exercise notebooks with `--allow-errors` and assert only the expected `NotImplementedError` cells fail. |
| nbstripout | 0.9.1 | pre-commit hook; strip outputs (keep cells tagged `keep_output`) | Keeps git diffs sane; executed copies are built artifacts. |
| pre-commit | 4.6.2 | Hooks: nbstripout, jupytext `--sync`, ruff | |
| pytest | 9.1.1 | Unit tests for `course/` helper module (cosine, blocks, dequantization) | Not for notebooks — use `jupyter execute`. |
| Quarto | 1.10.18 (`brew install --cask quarto`) | Slides (`format: revealjs`), embeds notebook outputs, speaker notes | See Slides section. |
| decktape (npx) | current | `npx decktape reveal slides/02.html slides/02.pdf` for a downloadable PDF | Quarto's own PDF path for reveal is browser "print view" (E key); decktape automates it. |
## Installation
### Reference project (author's machine)
# 1. Interpreter + project
# 2. Phase 1 (frozen-data notebook) — strictly needed
# 3. Later phases — cloud / providers
# 4. Authoring & QA tooling (not shipped to students)
# 5. Lock and sync
# 6. Run JupyterLab inside the env (or register a kernel for the global JupyterLab)
# — or —
# 7. Colab requirements (students): runtime deps only, no hashes, no project
### Optional Clay model environment (separate project, `envs/clay/`)
### Colab bootstrap cell (top of every notebook)
# %% tags=["setup"]
## Access patterns verified on 2026-09-03
### AlphaEarth via GCS without an Earth Engine account (Path A′)
- Bucket `gs://alphaearth_foundations/satellite_embedding/v1/annual/{year}/{utm_zone}/*.tiff`, years **2017–2025**, "As of July 2026, this bucket is set up as **'provider pays'**" — i.e. **not requester-pays**; anonymous reads work. If Google flips it to requester-pays, set `GS_USER_PROJECT=<billing-project>` (GDAL ≥3.4) plus credentials.
- Verified: `rasterio.Env(GS_NO_SIGN_REQUEST="YES")` + `rasterio.open("gs://...")` → 64 bands `int8`, nodata −128, 8192×8192, overviews [2,4,8,16], CRS EPSG:327xx (UTM). Plain `https://storage.googleapis.com/alphaearth_foundations/...` also works via `/vsicurl/` (slower).
- Index: `aef_index.parquet` (GeoParquet 1.1.0, WKB, covering bbox; columns `fid, crs, path, year, utm_zone, utm_*, wgs84_*, geom, geom_bbox`) — filter by `wgs84_*` bounds and `year` to find the tile, read a window, then **dequantize**: `((v / 127.5) ** 2) * np.sign(v)`; mask −128 first. Never average raw int8 across pixels.
- Earth Engine catalog still lists availability `2017-01-01 – 2025-01-01` (through 2024) and image property `DATASET_VERSION` (1.1 as of 2025-11-17) — record it in provenance. Use 2023–2024 for EE exercises.
- License CC BY 4.0; attribution string: "The AlphaEarth Foundations Satellite Embedding dataset is produced by Google and Google DeepMind."
### LGND open Clay corpus (Module 5)
- `s3://us-west-2.opendata.source.coop/clay/lgnd-clay-v1-5-sentinel-2-l2a/{scene|aggregated}/...`, hive-partitioned GeoParquet 1.1 (zstd), schema `chips_id, cell_id, rasters_id, stac_item_id, collection, datetime, embedding list<float32>[1024], bbox struct, geometry (EPSG:4326)`; 2,560 m MajorTOM cells; CC BY 4.0. The Source Cooperative page lists June 2024 and June 2025 time steps (the design report says monthly 2017–2026 — **verify coverage at build time**).
- Verified with DuckDB 1.5.5: `INSTALL httpfs; LOAD httpfs; INSTALL spatial; LOAD spatial;` then `read_parquet('https://data.source.coop/clay/lgnd-clay-v1-5-sentinel-2-l2a/aggregated/geohash_l2=u0/year=2025/month=06/*.parquet')` → 80,379 rows in ~2 s, geometry auto-decoded to `GEOMETRY('EPSG:4326')`, `ST_Intersects(geometry, ST_Point(7.4474, 46.9480))` finds Bern. **Use HTTPS in notebooks.** If you must use `s3://`, the dotted bucket name breaks TLS with virtual-hosted URLs — create the secret with `URL_STYLE 'path'`. `pytz` must be installed to `.df()` the tz-aware `datetime` column under pandas 3.
- Bern's partition is `geohash_l2=u0`.
### TESSERA via geotessera (Module 5)
- `pip install geotessera` (Python ≥3.12). `GeoTessera(dataset_version="v1.1", dataset_variant="cambridge")`; `gt.sample_embeddings_at_points([(lon, lat), ...], year=2024)` → `(n, 128)`; `gt.fetch_embedding(lon, lat, year)` → `(H, W, 128), crs, transform`; `GeoTesseraZarr` for streaming. Served from Source Cooperative over public HTTPS; no auth.
- Software is MIT (geotessera and tessera repos). **The embedding-data license is not stated in the docs or README** — confirm before bundling TESSERA samples in the frozen datasets (gap).
## Notebook authoring pipeline (solution → exercise → executed artifacts)
| Cell tag | In solution | In derived exercise |
|---|---|---|
| `solution` | full code | body replaced by a `# TODO:` stub + `raise NotImplementedError("...")`; if the cell contains `### BEGIN SOLUTION` / `### END SOLUTION` markers, only the marked span is replaced (nbgrader convention, no nbgrader dependency) |
| `remove` | present (author notes, answer discussion) | deleted |
| `checkpoint` | assertion cell (`assert abs(sim.max()-1) < 1e-6`) | kept verbatim — students self-check |
| `wrong-conclusion` | the deliberate trap cell (e.g. `# artificialized = change_score > 0.25`) | kept — pedagogy requires it |
| `keep_output` | output preserved by nbstripout | same |
## Slides and narration
- `{{< embed ../notebooks/solutions/02_similarity_and_classification.ipynb#fig-cosine-map >}}` pulls the actual figure from the solution notebook (label cells with `#| label: fig-cosine-map`); `echo=true` shows the code too. Figures never drift from the notebooks.
- `::: {.notes} ... :::` speaker notes → the **narration script draft**; `quarto render --to revealjs` then `show-notes: separate-page` for a notes PDF, or keep the script in `scripts/NN_module.md` and paste into notes.
- `embed-resources: true` → single self-contained HTML per deck for recording; PDF via print view (E key) or `npx decktape reveal deck.html deck.pdf`. Same `.qmd` renders to `pptx` if Udemy download decks are wanted.
- Python execution inside `.qmd` uses the project's Jupyter kernel (`uv run quarto render`).
## Frozen course dataset format
- **Container:** GeoParquet **1.1.0**, `geometry_encoding="WKB"`, `compression="zstd"`, `write_covering_bbox=True` (verified round-trip with geopandas 1.1.4 and native read in DuckDB spatial). Not 2.0.0-rc.1 (2026-07-19, native Parquet `GEOMETRY` types — geopandas cannot write it yet; reader support uneven).
- **Layout per study area / year:** one file `data/{area}/{area}_aef_{year}_v1.1.parquet`, a few thousand rows: `sample_id, lon, lat (EPSG:4326), geometry (point), year, utm_zone, block_10km (precomputed spatial-block id in EPSG:2056/UTM), label, label_source, A00..A63 (float32, dequantized, unit-norm), S2_B02..S2_B12 (float32 reflectance baseline)`. Wide `A00..A63` columns mirror the EE band names and make `df[cols].to_numpy()` trivial; teach the `list<float32>` alternative when reading the Clay corpus.
- **Provenance:** JSON in Parquet key-value metadata (`b"course_provenance"`) *and* human-readable `data/{area}/DATA_CARD.md` (`embedding_product, dataset_version (EE DATASET_VERSION or GCS path), year, source_license, attribution, crs, sampling_method, label_source, validation_source, created_by, created_at, course_release`). Write with `pyarrow.parquet.write_table(table.replace_schema_metadata({**table.schema.metadata, b"course_provenance": json.dumps(prov).encode()}))` after `gdf.to_parquet` or via `geopandas.io.arrow._geopandas_to_arrow`; simplest: write with geopandas, re-open with pyarrow, add metadata, rewrite.
- **Rasters (change lab):** tiny COG GeoTIFF pairs (2020/2024, ≤ 512² px, float32 dequantized or int8 with the formula in tags), written with `rioxarray ... .rio.to_raster(path, driver="COG", compress="ZSTD")`; TIFF tags carry the same provenance keys.
- **Distribution:** in-repo if < ~50 MB total; otherwise a public Hugging Face dataset repo fetched with `huggingface_hub.snapshot_download` (the ISPRS-2026 tutorial pattern). Never depend on a live bucket for Path B.
## Alternatives Considered
| Recommended | Alternative | When to Use Alternative |
|---|---|---|
| uv | conda/mamba (geemap docs' suggestion) | Only if you must use `localtileserver`/GDAL-heavy extras on Windows; not needed here — every dependency has manylinux/macOS wheels. |
| Python 3.12 | 3.13 | Once Colab completes the 3.13 upgrade and geemap/geotessera CI runs on it; the lockfile should already resolve on 3.13. |
| `jupyter execute` (nbclient) | papermill | When notebooks need parameters (multi-area capstone runs). |
| Custom nbformat derivation | nbgrader | If the course ever moves to an institutional JupyterHub with autograding. |
| Quarto revealjs | Marp | Zero-execution decks, or if Quarto's binary install is unacceptable. |
| odc-stac | stackstac | Only inside the isolated Clay env, for parity with Clay's tutorials. |
| GeoParquet 1.1 | GeoParquet 2.0 | After geopandas/pyarrow/duckdb all write native `GEOMETRY` (track geopandas 1.2 changelog). |
| Wide `A00..A63` columns | single `list<float32>` column | For 1024-D Clay/TESSERA-scale vectors where 1024 columns is unwieldy. |
| requests | httpx | If you need async or HTTP/2 for LGND; not for a teaching lesson. |
| `sklearn.neighbors` | faiss-cpu | Only for an ANN scaling demo. |
## What NOT to Use
| Avoid | Why | Use Instead |
|---|---|---|
| Python 3.14 as the reference env | Undeclared by geemap, geotessera, xarray, papermill, pystac-client; diverges from Colab (3.12 → 3.13). Works today by luck of pure-Python packaging. | Python 3.12 pinned by uv; test 3.13. |
| stackstac 0.5.1 in the main env | Pins `pandas<3` (conflicts with pandas 3.0.5), no release since 2024-08. | odc-stac 0.5.3. |
| nbgrader as a dependency | Heavy (SQLAlchemy/alembic/notebook<8), classroom-grading model, JupyterLab<5 pin. | Tag-driven nbformat script; borrow only the `### BEGIN/END SOLUTION` marker idea. |
| nbmake | Last release 2024-12; unverified with pytest 9. | `jupyter execute` from nbclient 0.11. |
| Jupyter RISE / jupyterlab-rise | Unmaintained (0.43.1, 2024-12); ties slides to a running kernel. | Quarto revealjs. |
| Slidev | Node/Vue toolchain for a Python repo. | Quarto (or Marp). |
| `pip install -r requirements-colab.txt` on Colab | Forces numpy 2.5 over Colab's 2.0.2 pin; breaks TensorFlow and restarts the runtime. | Install-only-missing bootstrap cell. |
| `train_test_split` as the only validation | The course's central trap (spatial leakage). | `GroupKFold`/`StratifiedGroupKFold` on 10 km blocks; `LeaveOneGroupOut` on regions. |
| Averaging raw int8 AlphaEarth values | Quantization is non-linear (`(v/127.5)^2 · sign`); means of int8 are not means of vectors. | Dequantize → average → renormalize. |
| An LGND "SDK" dependency | None exists first-party; would rot. | `requests` against the OpenAPI reference. |
| CSV / pickle / `.npz` for frozen data | No geometry, no CRS, no schema, no provenance; pickle is version-fragile. | GeoParquet 1.1 with provenance metadata; COG for rasters. |
| GeoParquet 2.0.0-rc.1 | RC; geopandas 1.1.4 can only write ≤1.1.0. | GeoParquet 1.1.0. |
| Chained assignment / `inplace=True` / `object`-dtype string assumptions | Silently different between pandas 2.2 (Colab) and 3.0 (local). | `.loc` assignment, functional style, explicit `astype`. |
| Docker-first | Adds friction for a Colab-first audience. | uv lockfile (+ optional Dockerfile later as a secondary artifact). |
## Stack Patterns by Variant
- Notebooks load `data/*.parquet` (Path B) first; Module 2 shows the EE code as Path A with `try: ee.Initialize(project=PROJECT) except Exception: use_frozen = True`.
- Module 2 also demonstrates Path A′: anonymous `rasterio` window read of one GCS COG for the Bern tile + dequantization — proves "no account needed" for AlphaEarth itself.
- `requires-python = ">=3.12,<3.14"` + `.python-version` make uv download/use 3.12 automatically; never `python3 -m venv`.
- `uv lock --python 3.13 && uv sync && make execute-all`; no code changes expected (all core packages declare 3.13).
- Run it in `envs/clay/` (separate uv project) or on Colab GPU; the main env never imports torch.
- Host on Hugging Face Datasets; `huggingface_hub.snapshot_download(repo_id, repo_type="dataset", local_dir="data")` in the setup cell.
## Version Compatibility
| Package A | Compatible With | Notes |
|---|---|---|
| pandas 3.0.5 | geopandas ≥1.1.3 | 1.1.3 (2026-03-10) added CoW and `str`-dtype fixes; 1.1.4 in lock. |
| pandas 3.0.5 | duckdb 1.5.5 `.df()` with tz-aware timestamps | Requires `pytz` installed (pandas 3 no longer depends on it). Verified failure/fix. |
| pandas 3.0.5 | stackstac 0.5.1 | **Incompatible** (`pandas<3` pin). |
| numpy 2.5.2 (local) vs 2.0.2 (Colab) | course code | Stay within numpy 2.0 API; avoid features added after 2.0. |
| scikit-learn 1.9 `GroupKFold(shuffle=True)` | sklearn ≥1.6 | Colab's sklearn version unpublished — check `sklearn.__version__` or omit `shuffle` on Colab. |
| geemap 0.38.4 | earthengine-api ≥1.6.12, Python ≥3.12 | Colab satisfies both. |
| geotessera 0.10.1 | Python ≥3.12, zarr ≥3.3, pyarrow ≥17, scikit-learn ≥1.7.1 | Resolves cleanly alongside everything else on 3.12/3.13. |
| geopandas 1.1.4 `to_parquet` | GeoParquet ≤1.1.0 | `schema_version` accepts `'0.1.0','0.4.0','1.0.0','1.1.0'`; pass `"1.1.0"` explicitly. |
| duckdb 1.5.5 spatial | GeoParquet 1.x read/write | Geometry auto-decoded when `spatial` is loaded; native since DuckDB 1.1. |
| rasterio 1.5.1 | GDAL ≥3.4 options `GS_NO_SIGN_REQUEST`, `GS_USER_PROJECT` | Bundled GDAL in wheels is recent. |
| claymodel (git) | Python ≥3.11, torch ≥2.4, einops ~0.7 | Keep in separate env; uses stackstac in tutorials. |
| Colab 26.07 | Python 3.12.13, numpy 2.0.2, torch 2.11 | 3.13 upgrade announced 2026-08-18 (open). |
## Phase mapping (what Phase 1 strictly needs vs later)
| Phase / module | Strictly needs | Optional |
|---|---|---|
| **Phase 1 — `02_similarity_and_classification.ipynb` on frozen AlphaEarth samples** | numpy, pandas, pyarrow, geopandas (+shapely, pyproj), scikit-learn, matplotlib, folium+mapclassify; the frozen GeoParquet for 2 study areas with `A00..A63`, S2 baseline bands, labels, `block_10km`; `tools/derive_exercise.py`; `jupyter execute` in Makefile; `uv.lock` | duckdb ("embeddings are a table" aside) |
| **Phase 1 data prep (author-side script)** | rasterio + gcsfs (anonymous AlphaEarth COG windows + `aef_index.parquet`), pyarrow (provenance metadata); labels + S2 bands via **either** earthengine-api (once the author has a project) **or** pystac-client + odc-stac (Earth Search S2 L2A) and an open label raster read with rasterio | earthengine-api if credentials exist |
| Modules 0–1 (refresher, foundations) | Phase 1 core only | huggingface_hub for a SatCLIP sample |
| Module 2 (access & visualize) | earthengine-api, geemap (Path A), rasterio/rioxarray (Path A′), frozen tile COGs (Path B) | xee |
| Module 4 (change & validation) | rioxarray/xarray aligned 2020/2024 pairs, sklearn `precision_recall_curve`, `StratifiedGroupKFold` | — |
| Module 5 (ecosystems) | geotessera (pinned v1.1/cambridge), duckdb+httpfs+spatial+pytz (Clay corpus over HTTPS), requests (LGND) | separate Clay/torch env; s3fs for listing |
| Module 6–7 (provenance, capstone) | pyarrow metadata writer, DATA_CARD template | — |
| Slides / scripts (all modules) | Quarto 1.10.18, decktape | Marp |
## Sources
- PyPI JSON API (`https://pypi.org/pypi/<pkg>/json`), queried 2026-09-03 — versions, release dates, `requires_python`, classifiers, wheel tags for all packages above. **HIGH**
- Local verification: `uv lock`/`uv pip install --only-binary :all:`/import + functional smoke on CPython 3.12.13 and 3.14.7 (uv 0.12.9, macOS arm64). **HIGH**
- Live access tests: `rasterio` on `gs://alphaearth_foundations/...` with `GS_NO_SIGN_REQUEST=YES` and via HTTPS; `gcsfs` read of `aef_index.parquet`; DuckDB 1.5.5 `read_parquet` over `https://data.source.coop/clay/...` and `s3://` path-style. **HIGH**
- https://developers.google.com/earth-engine/guides/aef_on_gcs_readme — bucket path, 2017–2025, int8 dequantization, "provider pays" (July 2026), index files, CC BY 4.0 attribution. **HIGH**
- https://developers.google.com/earth-engine/datasets/catalog/GOOGLE_SATELLITE_EMBEDDING_V1_ANNUAL — availability 2017-01-01–2025-01-01, `DATASET_VERSION` 1.1, license text. **HIGH**
- https://developers.google.com/earth-engine/guides/auth — `ee.Initialize(project=...)` required; Colab auth mode. **HIGH**
- https://research.google.com/colaboratory/runtime-version-faq.html — runtime 26.07: Python 3.12.13, numpy 2.0.2, PyTorch 2.11. **HIGH**
- https://github.com/googlecolab/colabtools/issues/6081 (2026-08-18, open) — "Upgrade to Python 3.13 … very soon"; #5483 (3.12 upgrade, 2025); #4870 (pandas 2.2.2, 2024-09 — last pandas announcement found). **HIGH / MEDIUM for pandas**
- https://github.com/gee-community/geemap (README, `docs/installation.md`, `docs/notebooks/00_geemap_colab.ipynb`) — "pre-installed in Google Colab", `uv pip install geemap`, conda example with Python 3.13. **HIGH**
- https://geotessera.readthedocs.io and https://github.com/ucam-eo/geotessera README — Python ≥3.12, v1.0/v1.1/v2 versions and variants, API, Source Cooperative hosting; GitHub license API = MIT (software). Data license not stated. **HIGH / gap**
- https://source.coop/clay/lgnd-clay-v1-5-sentinel-2-l2a and AWS Open Data registry YAML — schema, partitioning, GeoParquet 1.1, CC BY 4.0, June 2024 / June 2025. **HIGH (page), MEDIUM (temporal coverage vs design report)**
- https://github.com/opengeospatial/geoparquet/releases — 1.1.0 (2024-06), 2.0.0-rc.1 (2026-07-19, native Parquet GEOMETRY/GEOGRAPHY). **HIGH**
- Context7 `/geopandas/geopandas` + https://geopandas.org/.../GeoDataFrame.to_parquet.html — `schema_version`, `geometry_encoding`, `write_covering_bbox`; CHANGELOG 1.1.3 pandas-3 fixes. **HIGH**
- https://pandas.pydata.org/docs/whatsnew/v3.0.0.html — CoW default, `str` dtype, pytz dropped, Python ≥3.11. **HIGH**
- https://scikit-learn.org/stable/modules/generated/sklearn.model_selection.GroupKFold.html — `shuffle`/`random_state` added in 1.6. **HIGH**
- https://gdal.org/en/stable/user/virtual_file_systems.html — `GS_NO_SIGN_REQUEST`, `GS_USER_PROJECT`, `AWS_NO_SIGN_REQUEST`, `AWS_REQUEST_PAYER`. **HIGH**
- https://duckdb.org/docs/current/core_extensions/spatial/overview.html + community docs (Overture, CNG) — `INSTALL spatial; LOAD spatial;`, native GeoParquet read/write since 1.1. **MEDIUM (docs) + HIGH (verified read)**
- Context7 `/mwouts/jupytext` — percent format tags, `jupytext.toml` pairing and metadata filters. **HIGH**
- https://nbclient.readthedocs.io/en/latest/client.html — `NotebookClient`, `jupyter execute` flags. **HIGH**
- https://docs.astral.sh/uv/ (jupyter integration, python-versions, sync/export) + `uv export --help` locally — `uv run --with jupyter jupyter lab`, kernel install, `uv python pin`, `--no-hashes --no-dev --no-emit-project`. **HIGH**
- Context7 `/websites/quarto` + https://quarto.org/docs/presentations/revealjs/presenting.html + https://quarto.org/docs/authoring/notebook-embed.html — revealjs, `::: {.notes}`, `embed-resources`, print-to-PDF, `{{< embed nb.ipynb#label echo=true >}}`. Homebrew cask quarto 1.10.18. **HIGH**
- https://github.com/marp-team/marp-cli README — `--pdf`, `--pptx`, `--notes`; npm 4.5.0. Slidev npm 52.19.1. **HIGH**
- https://clay-foundation.github.io/model/getting-started/quickstart.html + repo `pyproject.toml`/`environment.yml` — install from git, `requires-python >=3.11`, torch ≥2.4, v1.5 checkpoint URL. **HIGH**
- https://github.com/konstantinklemmer/isprs26-embeddings-tutorial — `requirements.txt` pattern (minimal runtime deps, data via `huggingface_hub`, prep-only deps commented out). **HIGH**
- GitHub commit/release APIs — stackstac last commit 2024-08-10; nbmake 2025-03; jupyterlab-rise release 2024-12; nbgrader deps `jupyterlab<5,>=4.2`. **HIGH**
<!-- GSD:stack-end -->

<!-- GSD:conventions-start source:CONVENTIONS.md -->
## Conventions

Conventions not yet established. Will populate as patterns emerge during development.
<!-- GSD:conventions-end -->

<!-- GSD:architecture-start source:ARCHITECTURE.md -->
## Architecture

Architecture not yet mapped. Follow existing patterns found in the codebase.
<!-- GSD:architecture-end -->

<!-- GSD:skills-start source:skills/ -->
## Project Skills

No project skills found. Add skills to any of: `.claude/skills/`, `.agents/skills/`, `.cursor/skills/`, `.github/skills/`, or `.codex/skills/` with a `SKILL.md` index file.
<!-- GSD:skills-end -->

<!-- GSD:workflow-start source:GSD defaults -->
## GSD Workflow Enforcement

Before using Edit, Write, or other file-changing tools, start work through a GSD command so planning artifacts and execution context stay in sync.

Use these entry points:
- `/gsd-quick` for small fixes, doc updates, and ad-hoc tasks
- `/gsd-debug` for investigation and bug fixing
- `/gsd-execute-phase` for planned phase work

Do not make direct repo edits outside a GSD workflow unless the user explicitly asks to bypass it.
<!-- GSD:workflow-end -->



<!-- GSD:profile-start -->
## Developer Profile

> Profile not yet configured. Run `/gsd-profile-user` to generate your developer profile.
> This section is managed by `generate-claude-profile` -- do not edit manually.
<!-- GSD:profile-end -->

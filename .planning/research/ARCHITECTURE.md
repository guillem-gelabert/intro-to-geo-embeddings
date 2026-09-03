# Architecture Research

**Domain:** Notebook-based developer course on geospatial embeddings (solution + exercise notebooks, frozen GeoParquet datasets, shared helper package, slides, narration scripts, headless tests)
**Researched:** 2026-09-03
**Confidence:** HIGH for data access and pipeline mechanics (verified live from this machine today); HIGH for notebook tooling (Context7 + PyPI); MEDIUM for repository conventions (modelled on the ISPRS 2026 tutorial repo and general practice); MEDIUM for the Earth Engine eligibility reading.

> Consistency note: this document aligns with the sibling research files written in parallel — `STACK.md` (package `course/`, `jupyter execute` for headless runs, tag-driven `nbformat` exercise derivation, Quarto slides, GeoParquet 1.1 with `course_provenance` metadata) and `FEATURES.md` (`tools/make_exercise.py`, hidden `<details>` solutions, checkpoints). Where this file adds something new it is marked **NEW**.

---

## The one finding that reshapes the plan (**NEW**, HIGH)

**The frozen-dataset pipeline does not need Earth Engine at all.** Every input for Module 3 is publicly readable without any account, and I verified each one end-to-end from this machine on 2026-09-03:

| Input | Public source | Verified today |
|---|---|---|
| AlphaEarth 64-D embeddings (2017–2025) | `https://storage.googleapis.com/alphaearth_foundations/satellite_embedding/v1/annual/{year}/{zone}/{tile}.tiff` (Google, "provider pays" since July 2026) **and** the Source Cooperative mirror `https://data.source.coop/tge-labs/aef/v1/annual/{year}/{zone}/{tile}.tiff` | Anonymous `rasterio` `/vsicurl/` reads from both hosts return **byte-identical** int8 vectors at Bern; dequantized norm 0.9963 |
| Tile lookup | `aef_index.parquet` (77.8 MB GeoParquet) on either host | DuckDB `httpfs`+`spatial`, `ST_Contains(geom, ST_Point(lon, lat))`, 10–19 s remote query; Bern (7.4474, 46.9480) → zone `32N`, EPSG:32632, tiles `x98mprxqet6sgqecq…` (2018), `x2x0ui46492ik7uhz…` (2021), `xlhcaokskggk40mla…` (2024), each `-0000008192-0000000000.tiff`, 3.68 GB |
| Exploratory land-cover labels (global) | ESA WorldCover 2021 v200, `https://esa-worldcover.s3.eu-central-1.amazonaws.com/v200/2021/map/ESA_WorldCover_10m_2021_v200_N45E006_Map.tif` (CC BY 4.0, 3°×3° COG tiles) | Point sample: Bern old town → class 50 (built-up), Bremgartenwald → class 10 (tree cover) |
| Independent artificial-surface reference (Europe) | EEA ArcGIS ImageServer `GioLandPublic/HRL_ImperviousnessDensity_2018` (10 m, 0–100 %), also `HRL_ImperviousnessChange_15_18`, `HRL_BuiltUp_2018` | `identify` (Bern → 100 %, forest → 0 %) **and** `exportImage` (GeoTIFF clip, `imageSR=32632`, 10 m) work anonymously |
| Sentinel-2 L2A bands for the raw-pixel baseline | Earth Search STAC `https://earth-search.aws.element84.com/v1`, collection `sentinel-2-l2a`, per-band COGs on `sentinel-cogs.s3.us-west-2.amazonaws.com` | Search over Bern, summer 2021, cloud < 10 % → item `S2B_32TLT_20210812_0_L2A`, assets carry `raster:bands` `scale=0.0001, offset=0`, `s2:processing_baseline=03.01`, `earthsearch:boa_offset_applied=false`, `scl` asset present |
| TESSERA embeddings (Module 5) | GeoTessera 0.10.1 → Source Cooperative, anonymous | Documented; no credentials |

Three independent products agree at the same coordinates (embedding cosine: city–city 0.85, forest–forest 0.89, city–forest 0.20; IMD 100 %/0 %; WorldCover built-up/tree cover), which also proves that point sampling on Google's unusual **bottom-up** COGs is geographically correct when done the way described in Pattern 1.

**What still needs an account** (all optional, all pluggable as label/source adapters):
- Earth Engine: live Path A in Module 2, **Dynamic World** labels (EE-only as far as I could confirm), and `S2_SR_HARMONIZED` composites. Google's noncommercial page states "Earth Engine will remain free of charge to users offering Earth Engine training … You may charge for your training services, but you cannot charge for use of Earth Engine" — a Cloud project plus the registration questionnaire is required, with monthly EECU quotas since April 2026 (MEDIUM: wording applies, eligibility is Google's decision).
- Copernicus CLMS: the **2021** imperviousness products (Density 2021 10 m, Change 2018–2021 20 m, Built-Up Change 2018–2021) require a free EU Login (CLMS download API / WEkEO). The publicly queryable EEA servers only expose 2018-generation products at 10 m and a harmonised 2006–2024 series at **100 m** (`land.discomap…/Imperviousness/HarmonisedImperviousnessLayer2021v2026`, MapServer, no pixel identify).
- LGND: token (trial tier).

---

## Standard Architecture

### System Overview

```
┌──────────────────────────────── SOURCES ────────────────────────────────────┐
│  No account (guaranteed)                      Account (optional plug-ins)    │
│  ┌──────────────┐ ┌──────────────┐ ┌────────┐ ┌───────────┐ ┌────────────┐   │
│  │ AEF COGs     │ │ ESA WorldCov.│ │ EEA    │ │ Earth     │ │ CLMS 2021  │   │
│  │ GCS/source.  │ │ 2021 S3      │ │ IMD    │ │ Engine    │ │ (EU Login) │   │
│  │ coop + index │ │              │ │ 2018   │ │ (AEF, DW, │ │ LGND token │   │
│  └──────┬───────┘ └──────┬───────┘ └───┬────┘ │  S2)      │ └─────┬──────┘   │
│  ┌──────┴───────┐ ┌──────┴───────┐     │      └─────┬─────┘       │          │
│  │ Earth Search │ │ GeoTessera   │     │            │             │          │
│  │ S2 L2A STAC  │ │ (S3 anon)    │     │            │             │          │
│  └──────┬───────┘ └──────┬───────┘     │            │             │          │
├─────────┴────────────────┴─────────────┴────────────┴─────────────┴──────────┤
│                     course/live/*  (source adapters → canonical schema)      │
│   aef_cog.py · s2_stac.py · labels.py · ee_adapter.py · tessera.py · lgnd.py │
├──────────────────────────────┬───────────────────────────────────────────────┤
│  pipeline/  (author-only)    │  notebooks/solutions/*.ipynb (Path A cells    │
│  sample_design → extract →   │  call course.live under a LIVE flag;          │
│  attach labels/S2 → write    │  Path B calls course.data.load — same schema) │
│        │                     │        │                    │                 │
│        ▼                     │        ▼                    ▼                 │
│  data/{area}/*.parquet       │  tools/make_exercise.py    notebooks/figures/ │
│  data/{area}/clips/*.tif ────┼──►     │                    │                 │
│  DATA_CARD.md, manifest.json │        ▼                    ▼                 │
│                              │  notebooks/exercises/      slides/*.qmd       │
│                              │  (generated, CI-checked)   narration/*.md     │
├──────────────────────────────┴───────────────────────────────────────────────┤
│  course/  (imported by every notebook, pipeline and test)                    │
│  schema · data · embeddings · spatial · evaluation · change · provenance ·   │
│  plotting                                                                    │
├──────────────────────────────────────────────────────────────────────────────┤
│  tests/ + CI: pytest (course, tools, data integrity) · jupyter execute       │
│  solutions in Path B · regenerate exercises and diff · manifest checksums    │
└──────────────────────────────────────────────────────────────────────────────┘
```

### Component Responsibilities

| Component | Responsibility | Typical Implementation |
|-----------|----------------|------------------------|
| `course/` (importable package) | Everything a notebook imports: canonical schema + validation, data loader with download fallback, embedding math (dequantize, renormalise, cosine map, prototypes), spatial blocks / leave-region-out groups, evaluation helpers, change helpers, provenance dict, plotting. Zero cloud calls at import time. | Flat package at repo root, `[tool.uv] package = true`, `uv_build` backend; pure numpy/pandas/geopandas/sklearn/matplotlib deps in `[project.dependencies]` |
| `course/live/` (source adapters) | Turn any external source into the canonical GeoDataFrame schema. Every adapter is optional-import (`try: import ee except ImportError`) and raises a clear `LiveSourceUnavailable` so notebooks can fall back. Shared by Path A cells **and** the pipeline. | `aef_cog.py` (index lookup, north-up read, point sampling, dequantize), `s2_stac.py` (pystac-client + rasterio/odc-stac point sampling with SCL mask and scale/offset), `labels.py` (WorldCover COG sample; EEA ImageServer `exportImage`), `ee_adapter.py` (`init_ee(project)`, `sampleRegions` at 10 m), `tessera.py`, `lgnd.py` |
| `pipeline/` (author-only) | Deterministic build of the frozen datasets: sampling design per AOI, extraction per year, label/S2 attachment, GeoParquet + COG clip writing, manifest with checksums, DATA_CARD rendering. Idempotent; caches raw windows under `data/raw/` (git-ignored). | `python -m pipeline.build --area bern --years 2018 2021 2024`; config in `pipeline/areas.yaml`; heavy deps in `[dependency-groups] pipeline` |
| `data/` | The product students actually depend on: small GeoParquet tables (≈ 0.3–1 MB each), tiny north-up COG clips for visualisation, `DATA_CARD.md`, `manifest.json` (sha256, row counts, builder git SHA, source versions). Raw/cache dirs git-ignored. | Committed to git (each file ≪ 50 MB) **and** mirrored as a tagged GitHub Release / HF dataset for Colab download |
| `notebooks/solutions/` | Single source of truth per module. Hand-edited. Executed with outputs committed. Carry the cell tags that drive exercise derivation. Path A cells guarded by a `LIVE` flag; Path B default. | `.ipynb` + jupytext `py:percent` pair for diffs (`cell_metadata_filter = "tags,-all"`) |
| `notebooks/exercises/` | Generated artefacts, never hand-edited. CI regenerates and fails on drift. | `tools/make_exercise.py` (nbformat) |
| `tools/` | Notebook build tooling: exercise generator, notebook lint (every live cell guarded, provenance cell present, no author paths), figure export for slides, release-zip builder. | Small Python scripts, unit-tested in `tests/` |
| `slides/`, `narration/`, `assessment/` | Quarto revealjs decks embedding figures produced by the solution notebooks; recording scripts with cell anchors; quizzes + capstone rubric. | Quarto 1.10 (`{{< embed >}}`), Markdown |
| `tests/` + CI | Unit tests for `course/` and `tools/`; data-integrity tests (checksums, unit norms, label coverage, CRS, provenance key present); headless execution of every solution notebook in Path B; exercise regeneration diff. | `pytest`; `jupyter execute` (nbclient 0.11) with `skip-execution` / `raises-exception` tags honoured |
| `envs/clay/` | Isolated uv project for the optional Clay encoder demo (torch, stackstac `pandas<3`). Never imported by the main package. | Separate `pyproject.toml` |

---

## Recommended Project Structure

```
intro-to-geo-embeddings/
├── README.md                      # banner: "Course reference environment: 2026-08 release …"
├── LICENSE-CODE  (MIT)            # code; course text/slides licence decided separately
├── pyproject.toml                 # [project] name="geo-embeddings-course"; requires-python ">=3.12,<3.14";
│                                  # package `course`; [dependency-groups] dev, pipeline, ee, ecosystems
├── uv.lock
├── jupytext.toml                  # formats = "ipynb,py:percent"; cell_metadata_filter = "tags,-all"
├── .pre-commit-config.yaml        # nbstripout (exercises only), jupytext --sync, ruff
├── Makefile                       # env · data · notebooks · exercises · figures · slides · test · release
├── .github/workflows/ci.yml       # uv sync --group dev; pytest; make exercises && git diff --exit-code
├── .gitignore                     # data/raw/ data/cache/ .venv/ **/.ipynb_checkpoints notebooks/**/*.nbconvert.ipynb
│
├── course/                        # THE importable helper package (import course)
│   ├── __init__.py                # __version__ = "2026.08"; COURSE_RELEASE tag used for data URLs
│   ├── config.py                  # study areas (AOI bounds, EPSG:2056 / EPSG:32632), years, tile ids, data URLs, sha256s
│   ├── schema.py                  # A_COLS = [f"A{i:02d}" ...]; S2_COLS; REQUIRED; validate(gdf); to_matrix(gdf)
│   ├── data.py                    # load("bern", 2021) -> GeoDataFrame: data/ first, else download pinned release + checksum
│   ├── embeddings.py              # dequantize(), renormalize(), cosine_similarity_map(), prototype(), knn_search()
│   ├── spatial.py                 # spatial_block_groups(gdf, block_m, crs), leave_region_out_groups(), to_projected()
│   ├── evaluation.py              # compare_splits(random vs block vs region), report(), confusion_df(), error_map()
│   ├── change.py                  # embedding_change_score(), calibrate_threshold(), transition_matrix()
│   ├── provenance.py              # Provenance dataclass, ATTRIBUTIONS, attach_to_parquet(), from_parquet()
│   ├── plotting.py                # pseudo_rgb(clip, axes=("A01","A16","A09")), plot_points(), plot_blocks()
│   └── live/                      # source adapters -> canonical schema; optional imports; used by Path A AND pipeline
│       ├── __init__.py            # class LiveSourceUnavailable(RuntimeError)
│       ├── aef_cog.py             # find_tile(lon, lat, year) via aef_index.parquet; open_north_up(url); sample_points(); read_window()
│       ├── s2_stac.py             # search_scenes(aoi, year, months, cloud_lt); sample_bands(points, items, scl_mask=True)
│       ├── labels.py              # worldcover_at(points, year=2021); eea_imd_2018_clip(aoi) via exportImage
│       ├── ee_adapter.py          # init_ee(project); sample_alphaearth_ee(points, year); dynamic_world_labels(points, year)
│       ├── tessera.py             # sample_tessera(points, year, version="v1.1") -> 128-D in the same schema (cols T000..T127)
│       └── lgnd.py                # thin requests wrapper; reads LGND_TOKEN; never imported by default path
│
├── pipeline/                      # author-only frozen-dataset build (NOT imported by notebooks)
│   ├── README.md                  # run order, expected runtime, which steps need which (optional) credentials
│   ├── areas.yaml                 # bern / change_area / transfer: AOI polygon, projected CRS, n_samples, strata, seed
│   ├── sample_design.py           # stratified-by-WorldCover, min-spacing points inside AOI; stable sample_id
│   ├── extract_aef.py             # per (area, year): read AOI window once (cached), sample points, dequantize+renormalize
│   ├── attach_labels.py           # WorldCover 2021, IMD 2018 (public); DW / CLMS 2021 if credentials present (nullable cols)
│   ├── attach_s2.py               # Earth Search scenes -> per-point SCL-masked median of B02,B03,B04,B08,B11,B12
│   ├── write.py                   # GeoParquet 1.1 (WKB, zstd, covering bbox) + course_provenance metadata; COG clips; manifest
│   └── build.py                   # python -m pipeline.build --area bern --years 2018 2021 2024 [--live-ee]
│
├── data/
│   ├── DATA_CARD.md               # per-source licence + attribution text, sampling design, versions, how to rebuild
│   ├── manifest.json              # {file: {sha256, rows, built_at, builder_git_sha, sources: {...}}}
│   ├── bern/
│   │   ├── bern_aef_2018_v1.1.parquet     # ~3,000 rows, wide A00..A63 float32 + labels + S2 bands
│   │   ├── bern_aef_2021_v1.1.parquet
│   │   ├── bern_aef_2024_v1.1.parquet
│   │   ├── bern_aoi.geojson
│   │   └── clips/                          # tiny north-up rasters for Module 2 / Module 4 maps
│   │       ├── bern_aef_2024_clip_int8.tif # e.g. 600x600 px, int8 + dequant formula in TIFF tags
│   │       ├── bern_imd_2018_clip.tif
│   │       └── bern_worldcover_2021_clip.tif
│   ├── change_area/ …                      # same layout (added in the Module 4 phase)
│   ├── transfer/ …                         # same layout, same label sources (needed by Module 3 leave-region-out)
│   ├── raw/                                # git-ignored: cached AOI windows, downloaded scenes, index parquet
│   └── cache/                              # git-ignored
│
├── notebooks/
│   ├── solutions/                 # single source of truth; hand-edited; tagged; outputs committed
│   │   ├── 00_embedding_refresher.ipynb   (+ .py jupytext pair)
│   │   ├── 01_alphaearth_access_visualize.ipynb
│   │   ├── 02_similarity_and_classification.ipynb      # FIRST DELIVERABLE
│   │   ├── 03_change_detection_and_validation.ipynb
│   │   ├── 04_embedding_ecosystems.ipynb
│   │   └── 05_capstone_artificialization.ipynb
│   ├── exercises/                 # GENERATED by tools/make_exercise.py — do not edit; CI verifies
│   └── figures/                   # PNG/SVG exported by solution notebooks; embedded by slides
│
├── tools/
│   ├── make_exercise.py           # nbformat, tag-driven (see Pattern 3)
│   ├── check_notebooks.py         # lint: LIVE guard on every course.live call, provenance cell, no /Users/ paths, cell cap
│   ├── export_figures.py          # runs solutions, harvests tagged figure cells to notebooks/figures/
│   └── make_release_zip.py        # per-lecture zip: notebook pair + data pointer + slides PDF
│
├── slides/                        # Quarto revealjs, one .qmd per module; {{< embed ../notebooks/solutions/02_… #fig-cm >}}
├── narration/                     # 02_similarity_and_classification.md … recording-ready, cell anchors
├── assessment/                    # quizzes/*.md, capstone_rubric.md, provenance_checklist.md
├── tests/
│   ├── test_embeddings.py         # dequantize round-trip, unit norm, cosine == dot on unit vectors
│   ├── test_spatial.py            # block ids stable, no group leakage across folds
│   ├── test_schema_data.py        # every parquet: schema, CRS, checksums vs manifest, norms≈1, label coverage, provenance key
│   ├── test_make_exercise.py      # stubs applied, hidden solutions wrapped, no solution text leaks, runs to first NotImplementedError
│   └── test_notebooks.py          # wrapper: jupyter execute each solution notebook (Path B), timeout, kernel = project env
├── envs/clay/                     # separate uv project for the optional Clay encoder demo
└── docs/research/                 # existing design report
```

### Structure Rationale

- **`course/` flat at repo root, not `src/`:** notebooks do `import course` after `%pip install -e .` locally or `%pip install "geo-embeddings-course @ git+…@v2026.08"` in Colab; a src-layout adds nothing here and complicates `sys.path` fallbacks. The name is generic but unambiguous inside this repo; it is what the author and `STACK.md` already use.
- **`course/live/` inside the package, `pipeline/` outside:** the COG/STAC/label readers are needed both by Module 2's "Path A′ — read the public COG yourself" cells and by the dataset build, so they belong in the importable package. Orchestration (sampling design, caching, writing, manifest) is author-only and must never be imported by a student notebook.
- **`notebooks/solutions` vs `notebooks/exercises`:** one hand-edited source, one generated target. This is the nbgrader `source/→release/` and Kaggle `raw/→rendered/` pattern without their infrastructure.
- **`data/` committed + released:** the tables are tiny (ISPRS's comparable `aef_crop_train.parquet` with 3,000 rows × 78 cols is 0.42 MB). Committing them makes `git clone && uv sync && jupyter lab` sufficient; the tagged release URL exists for Colab and for people who download a lecture zip.
- **`envs/clay/` separate:** `stackstac` pins `pandas<3`, torch is heavy; keeping it out protects the main lock file.

---

## Architectural Patterns

### Pattern 1: Read AlphaEarth from the public COGs without Earth Engine (**NEW**, HIGH — verified)

**What:** Locate the tile with the GeoParquet index, open the COG anonymously, wrap it in a `WarpedVRT` to get a north-up view, read the AOI window once, dequantize, renormalise. Point sampling can also go straight through `ds.sample()` on the raw dataset (verified equal to the VRT result).
**When to use:** The pipeline (always), Module 2 Path A′ (teaching "embeddings are just a raster you can read"), any later regeneration.
**Trade-offs:** First open of a 3.68 GB, 64-band COG over `/vsicurl/` costs 20–55 s of header/IFD reads; after that a 305×245 px × 64-band window read took 0.1 s. Cache windows under `data/raw/`. `gs://` with `GS_NO_SIGN_REQUEST=YES` (verified in `STACK.md`) is faster than HTTPS `/vsicurl/`; HTTPS needs no GDAL configuration, which is friendlier in a notebook.

```python
import duckdb, numpy as np, rasterio
from rasterio.vrt import WarpedVRT
from rasterio.windows import from_bounds

IDX = "https://data.source.coop/tge-labs/aef/v1/annual/aef_index.parquet"   # or the gs:// twin
GCS = "https://storage.googleapis.com/alphaearth_foundations/satellite_embedding/v1/annual"

def find_tile(lon, lat, year):
    con = duckdb.connect(); con.execute("INSTALL httpfs; LOAD httpfs; INSTALL spatial; LOAD spatial;")
    year_, zone, crs, path = con.execute(f"""
        SELECT year, utm_zone, crs, path FROM read_parquet('{IDX}')
        WHERE year = {year} AND ST_Contains(geom, ST_Point({lon}, {lat}))""").fetchone()
    return zone, crs, f"{GCS}/{year}/{zone}/{path.rsplit('/', 1)[-1]}"

def dequantize(raw):                      # Google's mapping, then renormalise (norm comes out ≈0.996 otherwise)
    v = np.where(raw == -128, np.nan, raw).astype(np.float32)
    d = (v / 127.5) ** 2 * np.sign(v)
    return d / (np.linalg.norm(d, axis=0, keepdims=True) + 1e-9)

zone, crs, url = find_tile(7.4474, 46.9480, 2024)
with rasterio.open(f"/vsicurl/{url}") as ds, WarpedVRT(ds, crs=ds.crs) as vrt:   # vrt.transform.e == -10 (north-up)
    win = from_bounds(*aoi_bounds_in(crs), vrt.transform).round_offsets().round_lengths()
    emb = dequantize(vrt.read(window=win))      # (64, h, w) float32, unit vectors
    win_transform = vrt.window_transform(win)
```

Two facts the code above encodes, both verified today and **absent from the sibling PITFALLS.md**:
1. The raw COG transform has `e = +10` (bottom-up). `rasterio.windows.from_bounds(..., ds.transform)` raises `WindowError: Bounds and transform are inconsistent` on the raw dataset; `WarpedVRT(ds, crs=ds.crs)` flips it to north-up with no reprojection. Source Cooperative also ships a `.vrt` per tile (a `VRTWarpedDataset` with the corrected GeoTransform), readable via `/vsis3/us-west-2.opendata.source.coop/...` with `AWS_NO_SIGN_REQUEST=YES`.
2. Windows must be snapped with `.round_offsets().round_lengths()`; with fractional offsets the VRT resamples on a shifted grid and the values no longer equal `ds.sample()` at the same coordinates.

### Pattern 2: Canonical schema as the contract between sources and notebooks (HIGH)

**What:** Every adapter (`course.live.*`) and the frozen loader return a `GeoDataFrame` that passes `course.schema.validate()`. Downstream cells only ever see this shape; nothing after the "source" cell knows which path produced the data.
**When to use:** Always — it is what makes "same downstream code on either path" true rather than aspirational, and what makes Module 5's provider swap a one-line change.
**Trade-offs:** Embedding dimensionality differs across providers (AEF 64, TESSERA 128, Clay 1024). Keep wide `A00..A63` for AEF (mirrors EE band names, `df[A_COLS].to_numpy()` is trivial) and let `schema.embedding_cols(gdf)` discover the provider's columns by prefix; the Clay corpus's `list<float32>` column is explicitly taught as the alternative.

```python
# course/schema.py
A_COLS  = [f"A{i:02d}" for i in range(64)]
S2_COLS = ["S2_B02", "S2_B03", "S2_B04", "S2_B08", "S2_B11", "S2_B12"]
REQUIRED = ["sample_id", "lon", "lat", "year", "label", "label_source"]

def validate(gdf, embedding_prefix="A"):
    missing = [c for c in REQUIRED if c not in gdf]
    assert not missing, f"missing columns: {missing}"
    assert gdf.crs is not None and gdf.crs.to_epsg() == 4326, "points must be EPSG:4326; reproject inside the notebook"
    cols = embedding_cols(gdf, embedding_prefix)
    norms = np.linalg.norm(gdf[cols].to_numpy(np.float32), axis=1)
    assert np.allclose(norms, 1.0, atol=1e-3), "embeddings must be unit length (dequantized + renormalised)"
    return gdf
```

Frozen table schema (per `data/{area}/{area}_aef_{year}_v1.1.parquet`, aligned with `STACK.md`):
`sample_id` (stable across years), `area`, `region_id` (for leave-region-out), `lon`, `lat`, `geometry` (Point, EPSG:4326), `year`, `utm_zone`, `aef_tile`, `aef_source` (`gcs`/`source.coop`/`ee`), `A00..A63` float32, `S2_B02..S2_B12` float32 reflectance + `s2_n_scenes`, `label` (2–4 course classes, e.g. `built`/`vegetation`/`crop`/`water`), `label_source`, reference columns `worldcover_2021` (uint8 code), `imd_2018` (0–100), optional nullable `dw_label_{year}` and `imd_2021`/`imd_change_2018_2021` if the author obtains them, and `block_10km` as a *reference* answer (the notebook computes its own and asserts equality in a checkpoint).

### Pattern 3: Two-path cell layout inside one notebook (HIGH)

**What:** One `parameters`-tagged configuration cell, one "source" cell that tries Path A and falls back to Path B, one `validate()` call, then path-agnostic code. Path A is an appendix-grade capability, Path B is the default that CI executes.
**When to use:** Every notebook that touches an external source (Modules 2, 3, 4, 5, capstone). Module 2 gets three tiers — A (Earth Engine + geemap), A′ (public COG via Pattern 1), B (frozen clip) — because its subject *is* access.
**Trade-offs:** Slight ceremony at the top of each notebook; in exchange the notebook is testable without secrets and survives auth/quota failures during recording.

```python
# %% tags=["parameters"]
import os
LIVE       = os.environ.get("COURSE_LIVE", "0") == "1"     # papermill/CI can inject; students flip to True
EE_PROJECT = os.environ.get("EE_PROJECT")                   # only used when LIVE
AREA, YEAR = "bern", 2021

# %% tags=["source"]
from course import data, schema
from course.live import LiveSourceUnavailable
if LIVE:
    try:
        from course.live.ee_adapter import init_ee, sample_alphaearth_ee
        init_ee(EE_PROJECT)
        gdf, SOURCE = sample_alphaearth_ee(data.sample_points(AREA), year=YEAR), "earth-engine"
    except (ImportError, LiveSourceUnavailable, Exception) as e:   # ee.EEException is not importable without ee
        print(f"Live path unavailable ({type(e).__name__}: {e}). Falling back to frozen data.")
        LIVE = False
if not LIVE:
    gdf, SOURCE = data.load(AREA, YEAR), "frozen"
gdf = schema.validate(gdf)
provenance = gdf.attrs["course_provenance"] | {"source_path": SOURCE}
X, y = schema.to_matrix(gdf), gdf["label"].to_numpy()
# ---- everything below is identical on both paths ----
```

Headless runs: `jupyter execute notebooks/solutions/02_*.ipynb` with `COURSE_LIVE` unset executes Path B; a credentialed author run uses `COURSE_LIVE=1 EE_PROJECT=… jupyter execute …` (or papermill injecting `LIVE=True`). Cells that must not run headlessly (geemap widgets, LGND without token) carry the `skip-execution` tag; the deliberate "WRONG conclusion" cell, if it executes to an error, carries `raises-exception`. Both tags are honoured by nbclient.

### Pattern 4: Tag-driven exercise derivation from the solution notebook (HIGH)

**What:** The solution notebook is the only hand-edited file. `tools/make_exercise.py` walks it with `nbformat` and rewrites cells according to tags; the result is written to `notebooks/exercises/` and never edited. Sync is enforced by regenerating in CI and failing on `git diff`.
**When to use:** Every module, once its solution notebook is frozen (cell order final, tags placed).
**Trade-offs:** Requires discipline placing tags; in exchange, a solution fix propagates to the exercise by running `make exercises`. nbgrader would do this too but drags in a gradebook database, `notebook<8` and a formgrader UI a Udemy course never uses; jupytext cannot remove or rewrite cells (`active-ipynb/active-py` selects by *runtime*, not by audience).

Tag vocabulary (superset of `STACK.md`'s, adds the two hidden/checkpoint tags `FEATURES.md` asks for):

| Tag | Effect in the exercise notebook |
|---|---|
| `solution` | Code replaced by `# TODO: …\nraise NotImplementedError("…")`; if the cell contains `### BEGIN SOLUTION` / `### END SOLUTION` only that span is replaced (nbgrader's convention, no nbgrader dependency) |
| `hidden-solution` | Code cell converted to a Markdown cell: `<details><summary>Show solution</summary>` + fenced code; renders collapsed in JupyterLab and Colab |
| `checkpoint` | Kept verbatim (assert cells that give students feedback); outputs cleared |
| `remove` | Dropped (teaching notes, author asides) |
| `exercise-only` | Kept only in the exercise (task wording, hints); hidden in the executed solution by tagging with `remove`-in-solution semantics handled by the lint, or simply kept in both as a "Task" box |
| `keep-output` | Output retained (expected figure/table so students know what "right" looks like) |
| `parameters`, `source`, `skip-execution`, `raises-exception` | Pass through unchanged (execution semantics, not audience) |

```python
# tools/make_exercise.py (core)
import re, nbformat
STUB = "# TODO: implement this step\nraise NotImplementedError('replace this stub')"
SPAN = re.compile(r"### BEGIN SOLUTION.*?### END SOLUTION\n?", re.S)

def derive(nb):
    out = []
    for c in nb.cells:
        tags = set(c.metadata.get("tags", []))
        if "remove" in tags:
            continue
        if "solution" in tags and c.cell_type == "code":
            c.source = SPAN.sub(STUB + "\n", c.source) if SPAN.search(c.source) else STUB
        elif "hidden-solution" in tags and c.cell_type == "code":
            c = nbformat.v4.new_markdown_cell(
                f"<details><summary>Show solution</summary>\n\n```python\n{c.source}\n```\n</details>")
        if c.cell_type == "code" and "keep-output" not in tags:
            c.outputs, c.execution_count = [], None
        out.append(c)
    nb.cells = out
    return nb
```

Unit tests for the tool assert: every `solution` cell is stubbed, no solution text survives outside `<details>`, the exercise executes cleanly up to the first `NotImplementedError` (so students can tell environment failures from their own).

### Pattern 5: Provenance travels with the data (HIGH — verified round-trip)

**What:** A `Provenance` dict is written into the Parquet key-value metadata under `course_provenance` next to the GeoParquet `geo` key, and rendered into `DATA_CARD.md`. `course.data.load()` reads it back into `gdf.attrs`, so every notebook's final provenance cell starts from the dataset's own record and adds `source_path`, model, CV design and validation source.
**When to use:** Every frozen file; every notebook output.
**Trade-offs:** geopandas 1.1.4's `to_parquet` has no custom-metadata argument, so the write is a two-step (`to_parquet`, then pyarrow `replace_schema_metadata`, rewrite). Verified today: `geo` metadata (GeoParquet 1.1.0, covering bbox) and CRS survive, `gpd.read_parquet` reads the result.

```python
import json, pyarrow.parquet as pq
gdf.to_parquet(path, schema_version="1.1.0", write_covering_bbox=True, compression="zstd")
t = pq.read_table(path)
pq.write_table(t.replace_schema_metadata({**t.schema.metadata,
    b"course_provenance": json.dumps(provenance, ensure_ascii=False).encode()}), path)
```

Attribution strings to carry: AlphaEarth — "The AlphaEarth Foundations Satellite Embedding dataset is produced by Google and Google DeepMind." (CC BY 4.0); ESA WorldCover 2021 v200 (CC BY 4.0, ESA WorldCover project / VITO et al.); Copernicus Land Monitoring Service HRL Imperviousness 2018 (EEA, free/open with attribution — exact wording to confirm on the product page in the data phase); Sentinel-2 (Copernicus Sentinel data 2021/2024, ESA terms).

---

## Data Flow

### Build flow (author, once per release)

```
areas.yaml (AOI, CRS, n, seed)
    │
    ▼
sample_design ── WorldCover 2021 COG (anon S3) ──► stratified, min-spaced points, stable sample_id, region_id
    │
    ▼
extract_aef ── aef_index.parquet ──► tile per (area, year) ──► WarpedVRT window (cached data/raw/) ──► dequantize+renormalise ──► A00..A63
    │
    ▼
attach_labels ── WorldCover code ──► course label map (built/vegetation/crop/water)
              ── EEA IMD 2018 exportImage clip ──► imd_2018
              ── [optional] EE Dynamic World ──► dw_label_{year}      (nullable if no credentials)
              ── [optional] CLMS IMD 2021 / change 2018–2021 ──► imd_2021, imd_change   (nullable if no EU Login)
    │
    ▼
attach_s2 ── Earth Search STAC (year, Jun–Aug, cloud<10) ──► per-point SCL-masked median × scale/offset ──► S2_B02..S2_B12
    │
    ▼
write ── GeoParquet 1.1 + course_provenance ──► data/{area}/{area}_aef_{year}_v1.1.parquet
      ── north-up int8 COG clips ──► data/{area}/clips/*.tif
      ── manifest.json (sha256, rows, builder git sha, source versions) + DATA_CARD.md
```

Everything in the left column runs with **no credentials**. The two `[optional]` steps are the only ones that need accounts; they add nullable columns and never gate the build.

### Notebook flow (student, every run)

```
parameters cell ─► source cell ─┬─ LIVE and adapter succeeds ─► course.live.* ─┐
                                └─ else ─► course.data.load() ─────────────────┤
                                                                               ▼
                                                            schema.validate() ─► X, y, gdf, provenance
                                                                               │
              similarity ◄──── embeddings.cosine_similarity_map ◄──────────────┤
              classify   ◄──── sklearn + spatial.spatial_block_groups ◄────────┤
              change     ◄──── change.embedding_change_score ◄─── second year ─┤
                                                                               ▼
                                            figures/ (tagged) ─► slides ; provenance cell ─► JSON
```

### Derivation flow (author, per module, after the solution is frozen)

```
notebooks/solutions/NN.ipynb (tagged) ─► tools/make_exercise.py ─► notebooks/exercises/NN.ipynb
                                      ─► tools/export_figures.py ─► notebooks/figures/NN_*.png ─► slides/NN.qmd ─► narration/NN.md
CI: jupyter execute solutions (Path B) ; make exercises && git diff --exit-code ; pytest tests/
```

### Key Data Flows

1. **Frozen-first, live-optional:** the arrows never point from live to frozen at student runtime; the frozen table is a build artefact produced by the same adapters the live cells use, so Path A and Path B are two entry points into one schema, not two codebases.
2. **Stable `sample_id` across years:** the sampling design is fixed once per area; embeddings for 2018/2021/2024 are extracted at the *same* points, which is what makes the change module a join on `sample_id` and makes "does the 2021 classifier transfer to 2024?" a two-line aside.
3. **Label availability drives the anchor year (NEW):** WorldCover is 2021-only (v200); public 10 m imperviousness is 2018; AEF covers 2017–2025. Recommended frozen years per point: **2018, 2021, 2024**. Module 3 pairs 2021 embeddings with 2021 WorldCover labels (temporal alignment), Module 4 pairs 2018→2021 embeddings with IMD change 2018–2021 if the author does the one-time EU Login download, else falls back to 2018 IMD status + hand-verified change points. Live EE cells in Module 2 show 2024 for freshness, as `PROJECT.md` requires.

---

## Scaling Considerations

Users do not scale here (a static repo is downloaded by students); the dataset and the pipeline do.

| Scale | Architecture Adjustments |
|-------|--------------------------|
| Course v1: 3 areas × 3 years × ~3,000 points | Everything in git; per-file < 1 MB; single `manifest.json`; DuckDB not required by students (nice aside only) |
| Larger frozen tables (10⁴–10⁵ rows) or wall-to-wall AOI rasters | Move data out of git to the tagged Release / HF dataset only; loader keeps the local-first fallback; AOI rasters as int8 COGs with the dequant formula in tags (≤ 30 MB each) |
| More study areas / capstone student AOIs | `areas.yaml` is the only thing that grows; `pipeline.build --area` is idempotent; students run the same pipeline against their own AOI in the capstone (it needs no credentials) |
| Whole-tile analysis (8192² × 64) | Out of scope for the course; if a demo needs it, read overview level 2–4 (Google pre-computed them with the sum-and-renormalise rule) instead of the base level |

### Scaling Priorities

1. **First bottleneck: COG header opens over HTTP** (20–55 s per tile per session). Cache AOI windows to `data/raw/` in the pipeline; never open the 3.7 GB tiles from a student notebook except in the deliberate Module 2 Path A′ demo.
2. **Second bottleneck: per-point HTTP label queries.** Use `exportImage`/COG window reads once per AOI and sample locally; never loop `identify` over thousands of points.

---

## Anti-Patterns

### Anti-Pattern 1: Helper functions defined inside notebooks and copy-pasted between modules

**What people do:** `cosine_similarity_map`, block-id code and the provenance dict live in cells of notebook 02 and are pasted into 03, 04, 05.
**Why it's wrong:** They drift; a bug fix in one notebook silently leaves the others wrong; the exercise generator then stubs slightly different functions per module.
**Do this instead:** Put them in `course/` with unit tests; notebooks *show* the two or three functions that are the lesson (the notebook may re-implement `cosine_similarity_map` pedagogically and then assert it matches `course.embeddings.cosine_similarity_map`).

### Anti-Pattern 2: Hand-editing exercise notebooks

**What people do:** Copy the solution, delete code by hand, save under `exercises/`.
**Why it's wrong:** The second time the solution changes, the exercise is stale; `FEATURES.md` and `PITFALLS.md` both flag exercise drift.
**Do this instead:** Tags + `tools/make_exercise.py`; exercises are build artefacts checked by CI.

### Anti-Pattern 3: Making Earth Engine the default execution path

**What people do:** Cell 1 is `ee.Authenticate(); ee.Initialize(project=...)` and everything depends on it.
**Why it's wrong:** The author has no credentials today; students may not qualify; quotas changed in April 2026; geemap widgets do not render in CI or on GitHub. A paid course that fails on auth is refund bait.
**Do this instead:** Pattern 3. Path B default; Path A guarded; Module 2 also teaches Path A′ (public COG), which is both credential-free and truer to the "embeddings as data" message.

### Anti-Pattern 4: Treating Google's COGs as ordinary north-up rasters (**NEW**)

**What people do:** `from_bounds(..., ds.transform)`, `rioxarray.open_rasterio(...).rio.clip_box(...)`, `gdaladdo -r average` on the int8 values, or `np.flipud` guesses.
**Why it's wrong:** The transform is bottom-up (`e = +10`); `from_bounds` raises, other tools silently produce mirrored or shifted windows; averaging raw int8 violates the documented aggregation rule (dequantize → sum → renormalise).
**Do this instead:** `WarpedVRT(ds, crs=ds.crs)` (or the mirror's `.vrt`), snapped windows, dequantize before any arithmetic, use Google's pre-built overviews if you need coarser levels.

### Anti-Pattern 5: Frozen data without machine-readable provenance

**What people do:** `df.to_parquet("bern.parquet")` and a README sentence.
**Why it's wrong:** ISPRS's otherwise excellent dataset carries only `pandas` metadata and no HF README; the course's own Module 6 teaches the opposite.
**Do this instead:** Pattern 5 — `course_provenance` in the file, `DATA_CARD.md` beside it, `manifest.json` checksums, and the loader surfaces provenance into `gdf.attrs`.

### Anti-Pattern 6: Precomputing the lesson away

**What people do:** Ship `block_10km` and `fold` columns and have students call `cross_validate(groups=df.fold)`.
**Why it's wrong:** Building spatial blocks correctly (projected CRS, block size vs autocorrelation range) *is* the lesson; `PITFALLS.md` Pitfall 3.
**Do this instead:** Ship `block_10km` only as a reference answer; the notebook computes blocks in EPSG:2056/UTM and a `checkpoint` cell asserts equality.

---

## No-Earth-Engine Build Strategy (concrete fallback plan, **NEW**)

| Situation | What the architecture does |
|---|---|
| Today: no EE credentials, no gcloud | `pipeline.build` runs fully on public sources (Pattern 1 + WorldCover + EEA IMD 2018 + Earth Search). Module 3 is buildable **now**. |
| Author registers a Cloud project for noncommercial EE ("offering Earth Engine training" clause) before recording Module 2 | `course.live.ee_adapter` is written against the documented API (`ee.Initialize(project=…)`, `image.sampleRegions(collection, properties, scale=10)`), tagged "untested until credentials", and exercised by `COURSE_LIVE=1` runs. `pipeline.build --live-ee` then adds `dw_label_{year}` columns and re-writes the same files (schema unchanged, manifest bumped). |
| EE registration fails or is delayed | Module 2's live tier becomes Path A′ (public COG via rasterio/DuckDB, already verified); the geemap cells stay as `skip-execution` demonstrations recorded later or replaced by static maps. Nothing else in the course changes. |
| Copernicus 2021 products wanted for Module 4 | One-time free EU Login → CLMS API/WEkEO download of IMD 2021 + Change 2018–2021 for the change AOI → `attach_labels` fills `imd_2021`, `imd_change_2018_2021`. Without it: IMD 2018 status + Change 2015–2018 (public) plus a small set of author-verified change/no-change points from imagery (the report's "manual interpretation" tier). |
| Dynamic World unavailable (no EE) | `label` comes from WorldCover 2021 (global, CC BY 4.0, 10 m). Dynamic World remains an optional nullable column and a slide ("model output, not ground truth"). |

---

## Build Order and Dependencies (honours "Module 3 solution notebook first")

### What must exist before `02_similarity_and_classification.ipynb` runs end-to-end

1. **Environment:** `pyproject.toml` (`requires-python ">=3.12,<3.14"`, `course` package, core deps: numpy, pandas, pyarrow, geopandas, shapely, pyproj, scikit-learn, matplotlib; `[dependency-groups] dev` with jupyterlab, ipykernel, jupytext, nbformat, nbclient, pytest, ruff; `pipeline` with rasterio, duckdb, pystac-client, odc-stac, requests), `uv.lock`, `Makefile`.
2. **`course/` minimum:** `schema`, `data` (local-first loader), `embeddings` (dequantize, renormalise, cosine map, prototype), `spatial` (block groups, leave-region-out), `evaluation` (random vs block vs region comparison, confusion matrix, error map), `provenance`, `plotting` basics; unit tests green.
3. **`course/live/aef_cog.py`, `labels.py`, `s2_stac.py`** — needed by the pipeline (not by the notebook's default path).
4. **Frozen data:** `data/bern/bern_aef_2021_v1.1.parquet` and `data/transfer/transfer_aef_2021_v1.1.parquet` (leave-region-out needs a second region) with labels and S2 bands; `DATA_CARD.md`; `manifest.json`; data-integrity tests green.
5. **Headless run:** `jupyter execute notebooks/solutions/02_*.ipynb` passes in Path B on the project kernel.

Not needed before Module 3: Earth Engine credentials, exercises, slides, narration, other notebooks, COG clips, TESSERA/Clay/LGND adapters.

### Suggested phase sequence

| Phase | Deliverable | Depends on | Notes |
|---|---|---|---|
| 1 | Repo scaffold: pyproject/uv, `course/` skeleton + tests, Makefile, CI, README banner, `.gitignore` | — | Half a day; establishes the schema contract everything else targets |
| 2 | Frozen-data pipeline v1 for **Bern + transfer region**, years 2018/2021/2024, public sources only | 1 | Pattern 1 + labels + S2; `DATA_CARD.md`, manifest; integrity tests. Choose the transfer region inside HRL coverage (Europe) so IMD 2018 exists for both |
| 3 | **`02_similarity_and_classification.ipynb` solution** (first deliverable) | 1, 2 | Path B default; Path A cells written but untested; tags placed as you go; figures tagged |
| 4 | Backtrack: `00_embedding_refresher`, `01_alphaearth_access_visualize` (needs `clips/` — a small pipeline extension), Module 1 inspection notebook | 3 | Module 2 tiers A/A′/B; register EE noncommercial project in parallel if desired |
| 5 | Forward: `03_change_detection_and_validation` (adds change AOI + IMD change labels, EU Login decision), `04_embedding_ecosystems` (TESSERA/Clay frozen samples at the same `sample_id`s, LGND behind token), `05_capstone` (runs `pipeline.build` on a student AOI), Module 6 checklist | 3, 4 | Same schema contract makes Module 5 mostly adapter work |
| 6 | Per module: `tools/make_exercise.py` (first at Module 3) → exercise → figures → Quarto slides → narration → quiz | each solution frozen | Generator built once, applied per module; CI drift check from the first exercise onward |
| 7 | Release: tag `v2026.08`, GitHub Release data mirror, per-lecture zips, `COURSE_RELEASE` pinned in `course/__init__.py` and Colab bootstrap cells | all | |

**Ordering rationale:** the schema contract (Phase 1) must precede the data (Phase 2), which must precede the notebook (Phase 3) — but the *design* of all three is driven backwards from the Module 3 blueprint, so write the notebook outline first, then the schema, then the pipeline. Modules 0–2 come after Module 3 because they reuse its helpers and its frozen table; Modules 4–7 come after because they extend the same table with more years and label columns rather than introducing new structures.

**Research flags for the roadmap:** Phase 2 needs a short decision on the transfer and change AOIs (bounds, HRL coverage, WorldCover class balance) and on whether to create the EU Login; Phase 4 needs the EE registration outcome; Phase 5 needs a check of TESSERA v1.1 coverage over Bern and the Clay corpus's actual monthly coverage (`STACK.md` flags a discrepancy with the design report). Phases 1, 3, 6 are standard patterns.

---

## Integration Points

### External Services

| Service | Integration Pattern | Notes |
|---------|---------------------|-------|
| AlphaEarth COGs (GCS / Source Cooperative) | `rasterio` `/vsicurl/https://…` or `gs://` + `GS_NO_SIGN_REQUEST=YES`; index via DuckDB `httpfs`+`spatial` | Bottom-up transform (Pattern 1); nodata −128; 3.68 GB per tile — window reads only; provider pays, no credentials; mirror "not officially supported by Google" — prefer the GCS URL in shipped code, keep the mirror as fallback constant |
| ESA WorldCover 2021 v200 | `rasterio` `/vsicurl/` on `https://esa-worldcover.s3.eu-central-1.amazonaws.com/v200/2021/map/…_{lat}{lon}_Map.tif` (3°×3° tiles, EPSG:4326) | 106 MB per tile; point sampling and small windows fine; CC BY 4.0 |
| EEA ImageServer (IMD 2018, Change 15–18, BuiltUp 2018) | `…/ImageServer/exportImage?bbox=&bboxSR=4326&imageSR=32632&size=&format=tiff&f=image` → GeoTIFF in memory; `identify` for spot checks | Only 2018-generation at 10 m publicly; 2021 needs EU Login; ArcGIS `size` limits (~4,000 px) → tile large AOIs |
| Earth Search STAC (Sentinel-2 L2A) | `pystac-client` search → per-band COG hrefs → `rasterio`/`odc-stac`; apply `raster:bands` scale/offset per asset; mask with `SCL`; median over Jun–Aug | Baseline ≥ 04.00 scenes need the −0.1 offset unless `earthsearch:boa_offset_applied`; keep the scene-id list in provenance |
| Earth Engine | `course.live.ee_adapter`: `ee.Initialize(project=…)`, `ImageCollection("GOOGLE/SATELLITE_EMBEDDING/V1/ANNUAL").filterDate().filterBounds().mosaic().sampleRegions(collection, properties, scale=10)` → `geemap.ee_to_gdf` | Optional; noncommercial registration + quota; EE catalog shows through 2024 |
| GeoTessera | `GeoTessera(dataset_version="v1.1", …).sample_embeddings_at_points(points, year)` → 128-D → schema with `T000..T127` | Anonymous; pin version; "never mix versions" |
| LGND REST | `requests` with `LGND_TOKEN`; `skip-execution` unless token present | Trial tier; no SDK |
| Data hosting | Git (tables) + tagged GitHub Release / HF dataset (Colab download via `course.data`) | Loader verifies sha256 from `manifest.json` |

### Internal Boundaries

| Boundary | Communication | Notes |
|----------|---------------|-------|
| `course.live.*` ↔ `course.schema` | Every adapter returns a GeoDataFrame that passes `validate()` | The contract that makes two paths one codebase |
| `pipeline/` → `course.live.*` | Direct import; pipeline never contains reader logic of its own | Keeps Module 2 Path A′ and the build on the same code |
| `pipeline/` → `data/` | Files + `manifest.json`; never imported | Students only ever see `data/` |
| notebooks → `course/` | `import course`; notebooks may re-implement 2–3 teaching functions and assert equality | Prevents helper drift |
| `notebooks/solutions` → `notebooks/exercises` | `tools/make_exercise.py`; one direction only | CI diff |
| `notebooks/solutions` → `slides/` | Tagged figure cells → `notebooks/figures/` → Quarto `{{< embed >}}` | No screenshots |
| main env ↔ `envs/clay/` | None (separate lock, separate kernel) | `stackstac`/torch isolation |

---

## Sources

**Verified live from this machine, 2026-09-03 (HIGH):**
- Google, *AlphaEarth Foundations GCS data* (README, last updated 2026-07-07): bucket layout, "provider pays", int8 dequantization, −128 nodata, unit normalisation, overview rule, `manifest.txt`, `aef_index.parquet/.gpkg/.csv`, index columns, licence/attribution — https://developers.google.com/earth-engine/guides/aef_on_gcs_readme
- Source Cooperative mirror README + `.vrt` companions (`VRTWarpedDataset`, north-up) — https://source.coop/tge-labs/aef/README.md ; index at https://data.source.coop/tge-labs/aef/v1/annual/aef_index.parquet
- Anonymous reads of the Bern 2024 tile from `https://storage.googleapis.com/alphaearth_foundations/satellite_embedding/v1/annual/2024/32N/xlhcaokskggk40mla-0000008192-0000000000.tiff` and the mirror; `WarpedVRT` behaviour; `from_bounds` failure on the raw transform; dequantized norm 0.9963; cosine sanity values
- EEA ArcGIS: `https://image.discomap.eea.europa.eu/arcgis/rest/services/GioLandPublic` (IMD 2018 `identify` + `exportImage`), `https://land.discomap.eea.europa.eu/arcgis/rest/services/Imperviousness` (harmonised 100 m series to 2024)
- ESA WorldCover 2021 v200 S3 listing and point samples — https://esa-worldcover.s3.eu-central-1.amazonaws.com/ ; https://github.com/ESA-WorldCover/esa-worldcover-datasets
- Earth Search STAC search over Bern — https://earth-search.aws.element84.com/v1
- GeoParquet 1.1.0 + custom metadata round-trip with geopandas 1.1.4 / pyarrow 25.0.1
- PyPI versions: geopandas 1.1.4, pyarrow 25.0.1, duckdb 1.5.5, rasterio 1.5.1, rioxarray 0.23.0, geemap 0.38.4, earthengine-api 1.7.42, scikit-learn 1.9.0, pystac-client 0.9.0, odc-stac 0.5.3, stackstac 0.5.1, geotessera 0.10.1, nbclient 0.11.0, jupytext 1.19.5, nbformat/nbstripout 0.9.1, papermill 2.7.0, nbgrader 0.9.5, nbmake 1.5.5

**Documentation (HIGH):**
- Context7 `/mwouts/jupytext` — `formats = "ipynb,py:percent"`, `cell_metadata_filter`, percent-cell tag syntax, `--sync`, pre-commit hook, `active-ipynb`/`active-py`
- Context7 `/jupyter/nbgrader` — `ClearSolutions` preprocessor usable standalone, `### BEGIN/END SOLUTION`, `code_stub`, hidden tests
- Context7 `/treebeardtech/nbmake` and nbclient behaviour — `skip-execution`, `raises-exception` tags, `--nbmake-timeout`, `--nbmake-kernel`
- Context7 `/astral-sh/uv` — `[dependency-groups]`, `[tool.uv] default-groups`, `uv run --with jupyter jupyter lab`, `uv_build`
- GeoTessera quick start — https://geotessera.readthedocs.io/en/latest/quickstart.html
- Google community tutorial 03 (`sampleRegions({collection, properties, scale: 10})`) — https://developers.google.com/earth-engine/tutorials/community/satellite-embedding-03-supervised-classification
- ISPRS 2026 tutorial repo layout (`notebooks/ slides/ scripts/ tutorial/ tests/ local/`, HF dataset `kklmmr/isprs26-earth-embeddings`, parquet 0.3–0.4 MB per table) — https://github.com/konstantinklemmer/isprs26-embeddings-tutorial
- Colab default runtime Python 3.12 since 2025-08-27 — https://developers.google.com/colab/release-notes

**Policy / product pages (MEDIUM — wording verified, applicability is the provider's call):**
- Earth Engine noncommercial eligibility incl. training clause — https://earthengine.google.com/noncommercial/ ; Cloud-project requirement and April 2026 quota tiers — https://developers.google.com/earth-engine/guides/noncommercial_tiers
- Copernicus HRL Imperviousness 2021 products and CLMS API (EU Login) — https://land.copernicus.eu/en/products/high-resolution-layer-imperviousness ; https://eea.github.io/clms-api-docs/authentication.html
- Sentinel-2 processing-baseline offset — https://github.com/Element84/earth-search ; https://github.com/stactools-packages/sentinel2/issues/44
- A. Zuspan, *Efficiently exporting AlphaEarth embeddings from GEE* (quantize/dequantize round-trip is lossless) — https://www.aazuspan.dev/blog/efficiently-exporting-alphaearth-embeddings-from-gee/

---
*Architecture research for: notebook-based geospatial-embeddings course repository*
*Researched: 2026-09-03*

# Introduction to Geospatial Embeddings

A roughly six-hour, developer-oriented Udemy course that teaches how to use geospatial embeddings — AlphaEarth (Google Satellite Embedding) as the backbone — as practical data products: visualize, search, classify, detect change, and validate rigorously with spatial cross-validation.

Course reference environment: 2026-08 release. Provider APIs may change. Every cloud notebook has a local/offline fallback.

## Local setup

Run these commands from the repository root, in order.

```bash
# 1. Pin the interpreter (uv downloads/manages Python 3.12 automatically)
uv python pin 3.12

# 2. Install the project plus the authoring/dev tooling group
uv sync --group dev

# 3. Register the Jupyter kernel against this repo's own .venv
uv run ipython kernel install --user --env VIRTUAL_ENV "$(pwd)/.venv" --name=geo-embeddings-course
# Equivalent shorthand once the Makefile lands (a later plan in this phase): make kernel

# 4. Run the test suite
make test

# 5. Headlessly execute every solution notebook
make execute-notebooks
```

`make execute-notebooks` headlessly executes every solution notebook under `notebooks/solutions/`: `00_embedding_refresher.ipynb`, `00b_representation_inspection.ipynb`, `01_alphaearth_access_visualize.ipynb`, `02_similarity_and_classification.ipynb`, `03_change_detection_and_validation.ipynb`, `04_embedding_ecosystems.ipynb`, and `05_capstone_artificialization.ipynb`.

## Notebooks

| Notebook | Colab | Description |
|----------|-------|--------------|
| [`00_embedding_refresher.ipynb`](notebooks/solutions/00_embedding_refresher.ipynb) | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/guillem-gelabert/intro-to-geo-embeddings/blob/main/notebooks/solutions/00_embedding_refresher.ipynb) | Optional 25-minute refresher: NumPy vectors, cosine similarity, PCA, a tiny classifier, and CRS reprojection -- all on toy data, no network needed. |
| [`00b_representation_inspection.ipynb`](notebooks/solutions/00b_representation_inspection.ipynb) | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/guillem-gelabert/intro-to-geo-embeddings/blob/main/notebooks/solutions/00b_representation_inspection.ipynb) | Compares an AlphaEarth pixel vector, a real Clay patch embedding, and (optionally, with torch) a SatCLIP location embedding for the same area. |
| [`01_alphaearth_access_visualize.ipynb`](notebooks/solutions/01_alphaearth_access_visualize.ipynb) | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/guillem-gelabert/intro-to-geo-embeddings/blob/main/notebooks/solutions/01_alphaearth_access_visualize.ipynb) | Accesses and visualizes AlphaEarth via live Earth Engine (Path A, optional, not executed in CI) or a bundled clipped raster (Path B, no credentials). |
| [`02_similarity_and_classification.ipynb`](notebooks/solutions/02_similarity_and_classification.ipynb) | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/guillem-gelabert/intro-to-geo-embeddings/blob/main/notebooks/solutions/02_similarity_and_classification.ipynb) | Similarity search and prototype queries over frozen AlphaEarth embeddings, a land-cover classifier, and the honest spatial-CV vs. random-split comparison (with a raw-Sentinel-2 baseline) -- no Earth Engine account needed. |
| [`03_change_detection_and_validation.ipynb`](notebooks/solutions/03_change_detection_and_validation.ipynb) | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/guillem-gelabert/intro-to-geo-embeddings/blob/main/notebooks/solutions/03_change_detection_and_validation.ipynb) | Detects artificialization change between paired 2020/2024 AlphaEarth tiles, calibrates a threshold against a labelled proxy (the true Copernicus HRL Imperviousness product needs an EU Login the author has not obtained), and repeats the spatial-vs-random validation trap on the change task. |
| [`04_embedding_ecosystems.ipynb`](notebooks/solutions/04_embedding_ecosystems.ipynb) | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/guillem-gelabert/intro-to-geo-embeddings/blob/main/notebooks/solutions/04_embedding_ecosystems.ipynb) | Runs the same `course.embeddings` pipeline against TESSERA (via `geotessera`, falling back to a bundled fixture since `geotessera` is not installed in this course's core env) and the LGND Clay v1.5 corpus (via DuckDB over public GeoParquet) to show provider portability. |
| [`05_capstone_artificialization.ipynb`](notebooks/solutions/05_capstone_artificialization.ipynb) | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/guillem-gelabert/intro-to-geo-embeddings/blob/main/notebooks/solutions/05_capstone_artificialization.ipynb) | Capstone: end-to-end artificialization detection and validation over a new study area, combining similarity search, classification, change detection, and spatial cross-validation from Modules 2-4 into one graded workflow. |

Each future phase appends its own row here as its solution notebook ships. This table does not populate automatically. The Colab badges above link to a `main` branch that has not yet been pushed to a public remote -- the badge URL format is correct, but the Colab path itself has not been run and verified. **No notebook in this repository has been executed on Colab; all execution evidence below is from local, headless `jupyter execute` runs only** (see STATE.md for the open Colab timing checkpoint).

### Known gaps

- **TESSERA fixture is synthetic-illustrative, not real vectors.** `geotessera` is not installed in this course's core environment (it lives in the optional `providers` extra), so `04_embedding_ecosystems.ipynb` falls back to a bundled, illustrative fixture rather than a live `geotessera` sample. Treat any TESSERA numbers in that notebook's output as shape/format demonstrations, not real embeddings.
- **LGND API base URL is a placeholder.** `04_embedding_ecosystems.ipynb` references `https://api.lgnd.ai/v1/search` pending confirmation against the live OpenAPI reference; verify the endpoint before depending on it outside this course.
- **The change lab calibrates against a labelled proxy, not the true Copernicus product.** `03_change_detection_and_validation.ipynb` needs the Copernicus HRL Imperviousness Change 2018-2021 product for a ground-truth calibration, but that requires a free EU Login the author has not created for this course; the notebook calibrates its threshold against a labelled proxy instead and documents the substitution inline.

## Data sources and licenses

**AlphaEarth (Google Satellite Embedding).** License: CC BY 4.0. Attribution: "The AlphaEarth Foundations Satellite Embedding dataset is produced by Google and Google DeepMind."

**LGND Clay v1.5 Sentinel-2 L2A.** License: CC BY 4.0. Attribution: "LGND Clay v1.5 Sentinel-2 L2A embeddings, Source Cooperative, CC BY 4.0."

Additional per-source license entries (TESSERA, Copernicus, and others) land alongside their datasets starting in later phases. See `data/DATA_CARD.md` for the full, per-artifact license and attribution table.

## Templates

- [`templates/MODEL_DATA_CARD_TEMPLATE.md`](templates/MODEL_DATA_CARD_TEMPLATE.md) -- blank data-card template for documenting a new embedding product's provenance, license, and known limitations.
- [`templates/PROVENANCE_CHECKLIST.md`](templates/PROVENANCE_CHECKLIST.md) -- checklist for verifying a dataset's source, license, and attribution before bundling it into the course.
- [`templates/model_card_worked_example_module3.md`](templates/model_card_worked_example_module3.md) -- a filled-out example of the data-card template, using Module 3's change-detection dataset.

## Extras

The core install (`uv sync`) stays light and Colab-installable in under two minutes because the packages below are excluded by default. `rasterio` and `xarray` ship in the core install itself, per REQUIREMENTS.md's ENV-01 pinned core stack — they are not part of either extra below.

- **`ee`** — `earthengine-api` and `geemap`, for the Earth Engine access path (Path A: `ee.Initialize(project=...)`, interactive maps, band inspection).
- **`providers`** — `duckdb`, `fsspec`, `gcsfs`, `geotessera`, `odc-stac`, `pystac-client`, `pytz`, `requests`, `rioxarray`, `s3fs`, for the no-EE-account paths (Path A′/B) and the author's data-build pipeline.

Install an extra with uv:

```bash
uv sync --extra ee
uv sync --extra providers
```

Or, for a non-uv install:

```bash
pip install "geo-embeddings-course[ee]"
pip install "geo-embeddings-course[providers]"
```

## requirements-colab.txt

`requirements-colab.txt` is a generated, pinned reference artifact, produced by a Makefile target, kept for provenance and for non-uv installs. Notebook Setup cells never `pip install` from it directly — doing so would drag Colab's numpy off its TensorFlow-compatible pin. Setup cells install only the specific packages a notebook needs that Colab does not already ship.

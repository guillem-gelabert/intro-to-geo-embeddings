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

`make execute-notebooks` currently no-ops safely and prints a message that no solution notebooks were found — Phase 3 has not shipped one yet.

## Notebooks

| Notebook | Colab | Description |
|----------|-------|--------------|
| _(none yet)_ | | |

<!--
Colab badge URL template (used once notebooks exist):
https://colab.research.google.com/github/ORG/REPO/blob/main/notebooks/solutions/NAME.ipynb
-->

Each future phase appends its own row here as its solution notebook ships. This table does not populate automatically.

## Data sources and licenses

**AlphaEarth (Google Satellite Embedding).** License: CC BY 4.0. Attribution: "The AlphaEarth Foundations Satellite Embedding dataset is produced by Google and Google DeepMind."

Additional per-source license entries (TESSERA, Clay, LGND, Copernicus, and others) land alongside their datasets starting in Phase 2.

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

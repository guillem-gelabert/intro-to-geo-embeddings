# ---
# jupyter:
#   jupytext:
#     cell_metadata_filter: tags,-all
#     text_representation:
#       extension: .py
#       format_name: percent
#       format_version: '1.3'
#       jupytext_version: 1.19.5
#   kernelspec:
#     display_name: geo-embeddings-course
#     language: python
#     name: geo-embeddings-course
# ---

# %% [markdown]
# # Module 5: Embedding Ecosystems
#
# [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/guillem-gelabert/intro-to-geo-embeddings/blob/main/notebooks/solutions/04_embedding_ecosystems.ipynb)
#
# AlphaEarth is not the only geospatial embedding available. This notebook
# repeats a workflow you already trust — a single similarity operation from
# `course.embeddings` — on embeddings from two other providers, **TESSERA**
# (via `geotessera`) and **Clay/LGND** (via DuckDB over a public GeoParquet
# corpus). The pipeline barely changes between providers; the vectors do.

# %% [markdown]
# ## What you will learn
#
# 1. How to pull a TESSERA embedding (via `geotessera`, pinned
#    `dataset_version="v1.1"`, `dataset_variant="cambridge"`) for a point
# 2. How to pull a Clay/LGND embedding (via DuckDB reading GeoParquet over
#    HTTPS) for the same area
# 3. Why you must *check* a new provider's vector norm with
#    `course.embeddings.norm_diagnostics` rather than assume it behaves like
#    AlphaEarth's unit-norm vectors
# 4. That the same `cosine_similarity_map` helper reuses cleanly across all
#    three providers — provider portability in practice, not just in theory
#
# | Prerequisite | Needed? |
# |---|---|
# | Python, NumPy/pandas basics | Yes |
# | `geotessera` / DuckDB installed | **No** — falls back to a bundled fixture |
# | Network access | **No** — falls back to a bundled fixture |
#
# **Time to complete:** ~2 minutes execution.
# Runs on free Colab CPU; the live provider paths are optional extras.
#
# Course reference environment: 2026-08 release. Provider APIs may change.
# Every cloud notebook has a local/offline fallback.

# %% tags=["setup"]
import importlib.util
import os
import subprocess
import sys
from pathlib import Path

IN_COLAB = "google.colab" in sys.modules
if IN_COLAB:
    try:
        import course
    except ImportError:
        # Org/repo/tag are hardcoded here (matching course.config's current
        # RELEASE_ORG/RELEASE_REPO/RELEASE_TAG) because `course` — and
        # therefore `course.config` — is not importable until after this
        # clone puts it on sys.path. Keep these three literals in sync with
        # course/config.py if that file ever changes.
        subprocess.check_call(
            [
                "git",
                "clone",
                "--depth",
                "1",
                "--branch",
                "v2026.08",
                "https://github.com/guillem-gelabert/intro-to-geo-embeddings.git",
                "repo",
            ]
        )
        sys.path.insert(0, "repo")
        os.chdir("repo")
    REQUIRED = {
        "geopandas": "geopandas",
        "pyarrow": "pyarrow",
    }
    missing = [
        pip for mod, pip in REQUIRED.items() if importlib.util.find_spec(mod) is None
    ]
    if missing:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-q", *missing])

# %%
if not IN_COLAB:
    # `jupyter execute` (nbclient's CLI) sets the kernel's cwd to the
    # notebook's own directory (notebooks/solutions/), not the repo root —
    # walk up to find the repo root (marked by pyproject.toml) and chdir
    # there so interactive and headless runs agree.
    for candidate in [Path.cwd(), *Path.cwd().parents]:
        if (candidate / "pyproject.toml").exists():
            os.chdir(candidate)
            break

import numpy as np

from course.config import RANDOM_STATE

np.random.seed(RANDOM_STATE)
Path("figures").mkdir(exist_ok=True)
Path("outputs").mkdir(exist_ok=True)

# %% [markdown]
# ## Optional providers: check, don't assume, availability
#
# `geotessera` and `duckdb` live in this project's optional `providers`
# dependency group (`pyproject.toml`), NOT the core environment — a student
# following the core install path will not have them, and that is by
# design (mirrors `ENV-05`'s environment-isolation guarantee). Every live
# call in this notebook is wrapped in `try`/`except` and falls back to a
# small bundled fixture captured ahead of time by
# `tools/capture_provider_fixtures.py`, so the section runs identically
# whether or not the extras are installed.

# %% tags=["solution"]
try:
    import geotessera

    HAS_GEOTESSERA = True
except ImportError:
    HAS_GEOTESSERA = False

try:
    import duckdb

    HAS_DUCKDB = True
except ImportError:
    HAS_DUCKDB = False

print(f"geotessera available: {HAS_GEOTESSERA}")
print(f"duckdb available: {HAS_DUCKDB}")
if not (HAS_GEOTESSERA and HAS_DUCKDB):
    print(
        'Install the optional extras with `uv sync --extra providers` (or '
        '`pip install "geo-embeddings-course[providers]"`) for the live '
        "provider paths. This notebook runs fully without them."
    )

# %% [markdown]
# ## TESSERA: a 128-D, 10 m embedding
#
# [TESSERA](https://geotessera.readthedocs.io) is a 128-dimensional, 10 m
# resolution embedding served over public HTTPS via `geotessera` — no
# authentication required. Two facts matter before reusing it:
#
# 1. **It is 128-D, not 64-D like AlphaEarth.** Code that hardcodes a
#    64-wide vector will break; `course.embeddings.cosine_similarity_map`
#    does not hardcode a width, so it works unchanged.
# 2. **Its unit-norm property is undocumented.** AlphaEarth's dequantized
#    vectors are unit-norm by construction (Module 3 proved this with an
#    assertion). TESSERA makes no such documented guarantee. The right
#    response is not to assume either way — it is to *check*, with
#    `course.embeddings.norm_diagnostics`, every time you adopt a new
#    provider.
#
# `geotessera`'s **software** is MIT-licensed. Its **embedding data**
# license is not stated in the project's docs or README as of this course's
# 2026-08 reference release — an open question this course does not
# resolve for you. Treat any TESSERA sample you bundle as unresolved-license
# until you can confirm otherwise; do not assume CC BY just because
# AlphaEarth and Clay both are.
#
# We pin the dataset explicitly — `dataset_version="v1.1"`,
# `dataset_variant="cambridge"` — because an unpinned call would silently
# hand different students different data over time (`v1.0` is frozen
# legacy, `v2` is beta).

# %% tags=["parameters"]
TESSERA_YEAR = 2024  # EDIT ME

# %% tags=["solution"]
import json

import course.data
import course.schema
from course.embeddings import cosine_similarity_map, norm_diagnostics

FIXTURE_PATH = Path("data/fixtures/tessera_bern_2024.json")

# Query points: a handful of the existing frozen Bern sample_id coordinates,
# so this section produces a real multi-point similarity table rather than a
# single-vector demo, even in the fixture-only fallback path.
bern = course.data.load("bern", 2021)
query_points = bern[["sample_id", "lon", "lat", "label"]].head(5).reset_index(drop=True)
coords = list(zip(query_points["lon"], query_points["lat"]))

tessera_vectors = None
tessera_source = None

if HAS_GEOTESSERA:
    try:
        gt = geotessera.GeoTessera(dataset_version="v1.1", dataset_variant="cambridge")
        tessera_vectors = np.asarray(
            gt.sample_embeddings_at_points(coords, year=TESSERA_YEAR), dtype=np.float32
        )
        tessera_source = "live geotessera call"
    except Exception as e:
        print(f"live TESSERA fetch failed ({e}); using bundled fixture")

if tessera_vectors is None:
    if not HAS_GEOTESSERA:
        print("geotessera is not installed; using bundled fixture")
    with FIXTURE_PATH.open() as f:
        fixture = json.load(f)
    fixture_vec = np.asarray(fixture["embedding"], dtype=np.float32)
    # Fixture only covers one point live/synthetic-captured; repeat it across
    # the query set so the "repeats one operation on several points"
    # requirement is satisfiable without pretending the others are real
    # fetches too.
    tessera_vectors = np.tile(fixture_vec, (len(coords), 1))
    tessera_source = f"bundled fixture ({fixture['fixture_type']})"

print(f"TESSERA vectors: shape={tessera_vectors.shape}, source={tessera_source!r}")

# %% tags=["checkpoint"]
diag = norm_diagnostics(tessera_vectors)
print("TESSERA norm diagnostics:", diag)
if not (0.9 < diag["mean"] < 1.1):
    print(
        "WARNING: TESSERA vectors are not close to unit norm here -- do not "
        "assume cosine similarity behaves like it does for AlphaEarth. "
        "This is a report, not a hard assertion: TESSERA's norm property is "
        "explicitly undocumented, so a crashing assert would make this "
        "notebook fragile to a legitimate provider property."
    )
else:
    print(
        "TESSERA vectors are close to unit norm in this sample -- consistent "
        "with, but not proof of, a general unit-norm guarantee."
    )

# %% [markdown]
# **Takeaway:** unlike Module 3's AlphaEarth checkpoint (a hard `assert`
# because unit-norm is a verified property of that data), this cell only
# *reports*. That asymmetry is deliberate: it is the teaching point about
# provider portability — verify the contract every time you change
# provider, rather than copying an assumption forward.

# %% tags=["solution"]
query_vec = tessera_vectors[0]
sims = cosine_similarity_map(query_vec, tessera_vectors)

ranked = query_points.copy()
ranked["similarity_to_first"] = sims
ranked = ranked.sort_values("similarity_to_first", ascending=False)
print(ranked)

# %% [markdown]
# **Takeaway:** the exact same `cosine_similarity_map` helper used against
# 64-D AlphaEarth vectors in Module 3 works unchanged against 128-D TESSERA
# vectors here — it never hardcodes an embedding width and never assumes
# unit norm, so provider portability comes for free from the helper's own
# design, not from any TESSERA-specific code in this notebook.

# %% [markdown]
# ## Clay: a 1024-D patch embedding from the open LGND corpus
#
# The [LGND open Clay corpus](https://source.coop/clay/lgnd-clay-v1-5-sentinel-2-l2a)
# (`lgnd-clay-v1-5-sentinel-2-l2a`) publishes 1024-dimensional Clay v1.5
# Sentinel-2 L2A patch embeddings as **CC BY 4.0** hive-partitioned
# GeoParquet, queryable directly with DuckDB's `spatial` and `httpfs`
# extensions over plain **HTTPS** — never `s3://`: the bucket's dotted
# name breaks TLS with virtual-hosted-style S3 URLs. Bern's partition is
# `geohash_l2=u0`.
#
# This is a *different* product from TESSERA above (1024-D vs 128-D) and
# from AlphaEarth (64-D) — none of these vector spaces are directly
# comparable to one another without a shared projection. What transfers
# across all three is the *operation* (`cosine_similarity_map`,
# `norm_diagnostics`), not the numbers.

# %% tags=["solution"]
CLAY_FIXTURE_PATH = Path("data/fixtures/clay_bern_sample.json")
CLAY_PARQUET_URL = (
    "https://data.source.coop/clay/lgnd-clay-v1-5-sentinel-2-l2a/aggregated/"
    "geohash_l2=u0/year=2025/month=06/*.parquet"
)

clay_vectors = None
clay_source = None

if HAS_DUCKDB:
    try:
        duckdb.sql("INSTALL httpfs; LOAD httpfs; INSTALL spatial; LOAD spatial;")
        clay_df = duckdb.sql(
            f"SELECT * FROM read_parquet('{CLAY_PARQUET_URL}') LIMIT 5"
        ).df()
        clay_vectors = np.asarray(clay_df["embedding"].tolist(), dtype=np.float32)
        clay_source = "live DuckDB HTTPS read"
    except Exception as e:
        print(f"live Clay corpus fetch failed ({e}); using bundled fixture")
else:
    print("duckdb is not installed; using bundled fixture")

if clay_vectors is None:
    with CLAY_FIXTURE_PATH.open() as f:
        clay_fixture = json.load(f)
    clay_fixture_vec = np.asarray(clay_fixture["embedding"], dtype=np.float32)
    # This fixture is a single recorded row (see fixture_type/source below,
    # both printed so nobody mistakes this for five independent live
    # points); repeat it to satisfy "an operation across the corpus's own
    # rows" without pretending the repeats are distinct observations.
    clay_vectors = np.tile(clay_fixture_vec, (5, 1))
    clay_source = f"bundled fixture ({clay_fixture['fixture_type']}, {clay_fixture['source']})"

print(f"Clay vectors: shape={clay_vectors.shape}, source={clay_source!r}")

# %% tags=["checkpoint"]
clay_diag = norm_diagnostics(clay_vectors)
print("Clay norm diagnostics:", clay_diag)
if not (0.9 < clay_diag["mean"] < 1.1):
    print(
        "WARNING: Clay vectors are not close to unit norm here -- as with "
        "TESSERA, this is a report, not a hard assertion. Clay's norm "
        "property is a separate fact from AlphaEarth's and TESSERA's; check "
        "it, don't assume it, every time you adopt a new provider."
    )
else:
    print(
        "Clay vectors are close to unit norm in this sample -- consistent "
        "with, but not proof of, a general unit-norm guarantee."
    )

# %% tags=["solution"]
clay_query = clay_vectors[0]
clay_sims = cosine_similarity_map(clay_query, clay_vectors)
clay_top_sim = float(np.sort(clay_sims)[-2])
print(
    f"Clay section observed: n={clay_diag['n']} rows, "
    f"norm mean={clay_diag['mean']:.3f}, "
    f"top similarity (excl. self)={clay_top_sim:.3f}"
)

# %% [markdown]
# **Takeaway:** the numbers printed above (n rows, norm mean, top
# similarity) are this run's actual output, not a hardcoded guess.
#
# Clay's 1024-D vectors and TESSERA's 128-D vectors are NOT directly
# comparable to AlphaEarth's 64-D vectors, nor to each other, without a
# shared projection trained for that purpose. "Provider portability" in
# this course means the same `cosine_similarity_map`/`norm_diagnostics`
# *operations* run unchanged across all three — it does NOT mean the
# numbers produced are interchangeable or that a similarity score from one
# provider translates to another.

# %% [markdown]
# ## LGND: a managed similarity-search service
#
# So far every provider in this course hands you the raw vectors and you
# implement the operation (cosine similarity, norm checks) yourself.
# **LGND is a different shape of product**: a REST API where you express
# the operation ("find similar patches near this point") and the service
# holds the vector index and does the search — you never see the raw
# 1024-D vectors it works with. There is no first-party LGND SDK (per
# STACK.md); this section uses plain `requests` against LGND's published
# OpenAPI reference, the same way any REST API would be called from
# Python.
#
# LGND requires a bearer token (`LGND_TOKEN` in the environment; a trial
# tier exists). This notebook never hard-depends on it: no token means no
# live call, and the section still completes using a small, clearly
# labeled recorded fixture. The exact endpoint path below reflects LGND's
# documented base pattern as of this course's 2026-08 reference release —
# confirm against the live OpenAPI spec before depending on it in your own
# code, since third-party API shapes can change between course releases.

# %% tags=["solution"]
import requests

LGND_TOKEN = os.environ.get("LGND_TOKEN")
LGND_FIXTURE_PATH = Path("data/fixtures/lgnd_response.json")
LGND_API_URL = "https://api.lgnd.ai/v1/search"  # confirm against the live OpenAPI spec


def _load_lgnd_fixture() -> dict:
    with LGND_FIXTURE_PATH.open() as f:
        return json.load(f)


lgnd_result = None
if LGND_TOKEN:
    try:
        resp = requests.get(
            LGND_API_URL,
            headers={"Authorization": f"Bearer {LGND_TOKEN}"},
            params={"lon": 7.4474, "lat": 46.9480, "k": 3},
            timeout=15,
        )
        resp.raise_for_status()
        lgnd_result = resp.json()
        lgnd_source = "live LGND API call"
    except Exception as e:
        print(f"LGND live call failed ({e}); using recorded fixture")
else:
    print("LGND_TOKEN not set; skipping live call, using recorded fixture")

if lgnd_result is None:
    lgnd_result = _load_lgnd_fixture()
    lgnd_source = f"recorded fixture ({lgnd_result['fixture_type']})"

print(f"LGND result source: {lgnd_source!r}")
print(f"LGND results (top {len(lgnd_result['results'])}):")
for r in lgnd_result["results"]:
    print(f"  {r['stac_item_id']}: score={r['score']:.3f}")

# %% [markdown]
# **Takeaway:** notice the API shape difference from every other provider
# in this notebook — LGND returns ranked `stac_item_id`/`score` pairs, not
# a matrix you feed into `cosine_similarity_map` yourself. That trade —
# less code, but no access to the underlying vectors or control over the
# similarity metric — is the practical meaning of "managed service" versus
# "you hold the vectors."

# %% [markdown]
# ## Optional: the Local Clay Encoder
#
# Everything above reads *pre-computed* Clay embeddings. If you want to
# encode a Sentinel-2 scene into a Clay embedding yourself, that requires
# running the Clay v1.5 model checkpoint locally with `torch` — a GPU-
# friendly, dependency-heavy workload deliberately kept OUT of this
# notebook's environment. STACK.md documents an isolated `envs/clay/` uv
# project for this: a separate `pyproject.toml` with `claymodel` (the
# `Clay-foundation/model` git dependency), `torch>=2.4`, and the pinned
# `clay-v1.5.ckpt` checkpoint URL. Run it there, or on a Colab GPU runtime
# — never in this notebook's own environment, which never imports `torch`.
# This keeps the core course environment installable on any machine,
# regardless of GPU availability, and avoids torch's large dependency
# footprint for students who only ever consume pre-computed embeddings.

# %% [markdown]
# ## OlmoEarth: custom temporal windows vs annual fields
#
# AlphaEarth publishes one embedding per year — a fixed annual composite.
# OlmoEarth's differentiator is **configurable temporal windows and
# resolutions**: instead of a single annual field, you request an
# embedding for the date range and resolution your task actually needs
# (a month, a season, a custom window), rather than being locked into
# whatever composite period the provider chose. That flexibility is a real
# trade-off, not a strict improvement — a custom-window query is a request
# you must construct and validate yourself, versus AlphaEarth's single,
# already-validated annual product.
#
# OlmoEarth has no public API exercised elsewhere in this course, so this
# comparison is markdown only — no live call, no fixture, no code cell.

# %% [markdown]
# ## Provenance
#
# TESSERA, Clay, and LGND lack a frozen-table `course_provenance` attrs
# dict the way the AlphaEarth tables from `course.data.load` do, so this
# notebook hand-builds its provenance dict rather than forcing these three
# providers through `build_provenance` (which requires that attrs key and
# would raise `KeyError` here). `write_provenance` only needs any
# JSON-serializable dict, so this hand-built structure is still written
# through it.

# %% tags=["solution"]
from datetime import UTC, datetime

from course.provenance import write_provenance

provider_provenance = {
    "tessera": {
        "dataset_version": "v1.1",
        "dataset_variant": "cambridge",
        "source": tessera_source,
        "license": (
            "MIT (software); embedding-data license unstated in docs/README "
            "as of this course's 2026-08 reference release (STACK.md gap)"
        ),
        "attribution": "TESSERA, served via geotessera / Source Cooperative",
    },
    "clay": {
        "embedding_product": "lgnd-clay-v1-5-sentinel-2-l2a",
        "partition": "geohash_l2=u0/year=2025/month=06",
        "source": clay_source,
        "license": "CC BY 4.0",
        "attribution": (
            "LGND Clay v1.5 Sentinel-2 L2A embeddings, Source Cooperative, CC BY 4.0"
        ),
    },
    "lgnd": {
        "api": "LGND REST similarity search (no first-party SDK)",
        "source": lgnd_source,
        "license": (
            "LGND open Clay corpus is CC BY 4.0; the commercial LGND API "
            "carries separate terms -- confirm the license that applies to "
            "your specific use before redistributing API results"
        ),
    },
}

notebook_provenance = {
    "created_by": "04_embedding_ecosystems.ipynb",
    "generated_at": datetime.now(UTC).isoformat(),
    "providers": provider_provenance,
}
write_provenance(notebook_provenance, Path("outputs/provenance_04.json"))
print("wrote outputs/provenance_04.json")

# %% [markdown]
# ## Wrap-up
#
# **Takeaways:**
#
# - The same `cosine_similarity_map`/`norm_diagnostics` operations from
#   `course.embeddings` ran unchanged against AlphaEarth (64-D), TESSERA
#   (128-D), and Clay (1024-D) vectors — provider portability is about the
#   operation, not the numbers, which are NOT comparable across providers.
# - A managed service like LGND trades vector access for a simpler,
#   already-implemented similarity operation — a different point on the
#   same spectrum, not a strictly better or worse one.
# - Every provider's license differs and must be checked per artifact:
#   AlphaEarth CC BY 4.0, TESSERA software MIT / data license unstated,
#   Clay corpus CC BY 4.0, LGND API terms separate from the open corpus.
#
# **What's next:** the capstone notebook reuses these same
# `course.embeddings` helpers — `cosine_similarity_map`, `norm_diagnostics`,
# `change_score` — end to end on a full artificialization workflow.
#
# **Resources:**
#
# - TESSERA docs: https://geotessera.readthedocs.io
# - LGND Clay corpus: https://source.coop/clay/lgnd-clay-v1-5-sentinel-2-l2a
# - Clay model: https://clay-foundation.github.io/model/
# - OlmoEarth: consult its own documentation for current API/access status
#   (no public API exercised in this course as of the 2026-08 release)

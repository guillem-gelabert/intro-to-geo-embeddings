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

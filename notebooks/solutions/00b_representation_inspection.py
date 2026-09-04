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
# # Module 1: Representations — Pixel, Patch and Location Embeddings
#
# [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/guillem-gelabert/intro-to-geo-embeddings/blob/main/notebooks/solutions/00b_representation_inspection.ipynb)
#
# This notebook inspects the same real-world location through three
# different embedding "shapes" before the course goes deeper into any one
# of them. AlphaEarth, Clay and SatCLIP are not competing brands of the
# same thing — they describe different spatial units and different
# temporal support, and mixing them up is the single easiest way to draw
# the wrong conclusion from an embedding.

# %% [markdown]
# ## What you will learn
#
# 1. Load an AlphaEarth 64-D pixel embedding for one point
# 2. Load a Clay 1024-D patch embedding for a nearby location
# 3. Compare shape, spatial unit, temporal support and metadata side by side
# 4. (Optional) Load a SatCLIP location embedding, if torch is installed
#
# | Prerequisite | Needed? |
# |---|---|
# | Python, NumPy/pandas basics | Yes |
# | Earth Engine account | **No** |
# | torch | **No** (optional, only for the SatCLIP section) |
#
# **Time to complete:** ~10 minutes.
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
    # notebook's own directory (notebooks/solutions/), not the repo root,
    # so a bare `Path("data")` would resolve to the wrong place there even
    # though it resolves correctly when this notebook is opened
    # interactively from the repo root. Walk up to find the repo root
    # (marked by pyproject.toml) and chdir there so both cases agree.
    for candidate in [Path.cwd(), *Path.cwd().parents]:
        if (candidate / "pyproject.toml").exists():
            os.chdir(candidate)
            break

import json

import numpy as np
import pandas as pd

from course.data import load
from course.schema import A_COLS

# %% [markdown]
# ## The AlphaEarth pixel vector
#
# AlphaEarth (Google Satellite Embedding) produces one 64-D vector per
# 10 m pixel, per calendar year. It is a **pixel** embedding: the smallest
# spatial unit in this notebook, and the only one with a fixed annual
# cadence.

# %%
bern = load("bern", 2024)
row = bern.iloc[0]
ae_vector = row[A_COLS].to_numpy(dtype="float32")
ae_norm = float(np.linalg.norm(ae_vector))

print("AlphaEarth pixel vector shape:", ae_vector.shape)
print("AlphaEarth pixel vector L2 norm:", round(ae_norm, 4))
print("Spatial unit: one 10m pixel")
print("Temporal support: one calendar-year composite (2024)")

# %% [markdown]
# **Takeaway:** the AlphaEarth vector is a single point in a 64-D space
# with no independently interpretable axis — see
# `01_alphaearth_access_visualize.ipynb` for what that means visually.

# %% [markdown]
# ## The Clay patch embedding
#
# Clay (via the LGND corpus) produces one 1024-D vector per Sentinel-2
# L2A scene, per MajorTOM patch. It is a **patch** embedding: a much
# larger footprint than an AlphaEarth pixel, and tied to a single
# observation rather than a yearly composite.

# %%
clay = pd.read_parquet("data/clay_sample_fixture.parquet")
clay_row = clay.iloc[0]
clay_vector = np.array(clay_row["embedding"], dtype="float32")
clay_norm = float(np.linalg.norm(clay_vector))

print("Clay patch embedding shape:", clay_vector.shape)
print("Clay patch embedding L2 norm:", round(clay_norm, 4))
print("Spatial unit: one Sentinel-2 patch (MajorTOM cell, 2,560 m)")
print("Temporal support: one Sentinel-2 L2A scene at", clay_row["datetime"])

with open("data/clay_sample_fixture.provenance.json") as f:
    clay_provenance = json.load(f)
print("Clay fixture provenance:", json.dumps(clay_provenance, indent=2))

# %% [markdown]
# **Takeaway:** a Clay patch embedding covers a much larger area and a
# single scene, not a yearly composite — "the same location" means
# something different for a pixel vector than for a patch embedding.

# %% [markdown]
# ## Side-by-side comparison
#
# Shape and spatial unit are the first two things to check before
# combining or comparing embeddings from different providers.

# %%
comparison = pd.DataFrame(
    {
        "dims": [ae_vector.shape[0], clay_vector.shape[0]],
        "spatial_unit": [
            "one 10m pixel",
            "one Sentinel-2 patch (MajorTOM cell, 2,560 m)",
        ],
        "temporal_support": [
            "one calendar-year composite (2024)",
            f"one Sentinel-2 L2A scene ({clay_row['datetime']})",
        ],
        "source": ["AlphaEarth (Google Satellite Embedding)", "Clay v1.5 (LGND corpus)"],
    },
    index=["AlphaEarth pixel", "Clay patch"],
)
print(comparison)

# %% [markdown]
# **Takeaway:** shape and spatial unit are the first two things to check
# before combining or comparing embeddings from different providers —
# Module 5 revisits this with TESSERA and OlmoEarth.


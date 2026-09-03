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
# # Module 3: Similarity Search and Classification
#
# [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/guillem-gelabert/intro-to-geo-embeddings/blob/main/notebooks/solutions/02_similarity_and_classification.ipynb)
#
# This notebook is the flagship exercise of the course: it takes a
# precomputed AlphaEarth (Google Satellite Embedding) field for two
# geographically distinct regions and shows what you can actually do with
# embeddings before ever touching a training loop — search by example,
# build prototype queries, and (in the second half of this notebook,
# authored separately) classify land cover and validate the result
# honestly.

# %% [markdown]
# ## What you will learn
#
# 1. Cosine similarity search-by-example over a 64-dimensional embedding
# 2. Prototype queries built from a polygon mean and from positive-minus-negative centroids
# 3. A 2-4 class land-cover classifier
# 4. Why random splits, spatial-block splits and leave-region-out splits give different, honest answers
# 5. How the embedding classifier compares to a raw-Sentinel-2-band baseline
#
# | Prerequisite | Needed? |
# |---|---|
# | Python, NumPy/pandas basics | Yes |
# | Earth Engine account | **No** |
# | GIS background | **No** |
#
# **Time to complete:** ~3 minutes execution.
# Runs on free Colab CPU, no Earth Engine account.
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
        import course  # noqa: F401
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
    REQUIRED = {"geopandas": "geopandas", "pyarrow": "pyarrow", "mapclassify": "mapclassify"}
    missing = [pip for mod, pip in REQUIRED.items() if importlib.util.find_spec(mod) is None]
    if missing:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-q", *missing])
else:
    # `jupyter execute` (nbclient's CLI) sets the kernel's cwd to the
    # notebook's own directory (notebooks/solutions/), not the repo root,
    # so a bare `Path("data")`/`Path("figures")` would resolve to the wrong
    # place there even though it resolves correctly when this notebook is
    # opened interactively from the repo root. Walk up to find the repo
    # root (marked by pyproject.toml) and chdir there so both cases agree.
    for candidate in [Path.cwd(), *Path.cwd().parents]:
        if (candidate / "pyproject.toml").exists():
            os.chdir(candidate)
            break

import numpy as np

from course.config import RANDOM_STATE, COURSE_RELEASE

np.random.seed(RANDOM_STATE)
Path("figures").mkdir(exist_ok=True)
Path("outputs").mkdir(exist_ok=True)

# %% [markdown]
# ## Data
#
# Two regions ground this whole notebook: **Bern** (Swiss Plateau) and
# **Seville** (Andalusia) — chosen to be geographically and climatically
# distinct. Everything computed on Bern alone looks great; whether it
# generalizes to Seville is a question this notebook keeps coming back to,
# and it is the whole point of the leave-region-out split later in the
# module.

# %% tags=["solution"]
import course.data
import course.schema
from course.config import AREAS
from course.embeddings import cosine_similarity_map

bern = course.data.load("bern", 2021)
seville = course.data.load("seville", 2021)

# %%
import pandas as pd

for name, gdf in [("bern", bern), ("seville", seville)]:
    n_embedding_cols = len(course.schema.embedding_cols(gdf))
    print(f"{name}: {gdf.shape[0]} rows, {len(gdf.columns)} columns, "
          f"{n_embedding_cols} embedding columns")
    print(sorted(gdf.columns.tolist()))

class_counts = pd.DataFrame(
    {"bern": bern["label"].value_counts(), "seville": seville["label"].value_counts()}
)
print(class_counts)

# %%
import matplotlib.pyplot as plt

fig, axes = plt.subplots(1, 2, figsize=(12, 5), sharey=True)
for ax, name, gdf in zip(axes, ["bern", "seville"], [bern, seville]):
    for label, group in gdf.groupby("label"):
        ax.scatter(group["lon"], group["lat"], s=6, label=label)
    ax.set_title(name)
    ax.set_xlabel("lon")
axes[0].set_ylabel("lat")
axes[0].legend(loc="upper right", fontsize="small", markerscale=2)
fig.tight_layout()
fig.savefig("figures/02_points_map.png")
plt.show()

# %% tags=["checkpoint"]
course.schema.validate_frozen(bern)
course.schema.validate_frozen(seville)
print("Both regions confirmed: 64 embedding dimensions, unit norm.")

# %% [markdown]
# **Takeaway:** dot product equals cosine similarity here because every
# embedding row is exactly unit-norm — the assertion above just proved it
# for both regions. That is a property of *this* data, not something the
# similarity helper assumes (it always divides by the real norms, so it
# stays correct for embeddings that are not unit-norm too).

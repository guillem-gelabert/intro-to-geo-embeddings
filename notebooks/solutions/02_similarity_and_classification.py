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

# %% [markdown]
# ## Similarity 1: Search by example
#
# Pick a single point ("the query") and rank every other point in the same
# region by cosine similarity to it. This is the simplest possible use of
# an embedding: no training, no labels required at query time — just "find
# me more of this."

# %% tags=["parameters"]
QUERY_REGION = "bern"  # EDIT ME
QUERY_ID = 150  # EDIT ME -- a "built" point in bern
K = 10  # EDIT ME

# %%
gdf = bern if QUERY_REGION == "bern" else seville
assert QUERY_ID in gdf.index, (
    f"QUERY_ID={QUERY_ID!r} is out of range for region {QUERY_REGION!r} "
    f"(valid range: 0..{gdf.index.max()})"
)
matrix = course.schema.to_matrix(gdf)
query_vec = matrix[QUERY_ID]
sims = cosine_similarity_map(query_vec, matrix)

order = np.argsort(-sims)
order = order[order != QUERY_ID][:K]
ranked = pd.DataFrame(
    {
        "rank": np.arange(1, K + 1),
        "sample_id": gdf.iloc[order]["sample_id"].to_numpy(),
        "label": gdf.iloc[order]["label"].to_numpy(),
        "similarity": sims[order],
    }
)
print(f"query: sample_id={gdf.loc[QUERY_ID, 'sample_id']}, label={gdf.loc[QUERY_ID, 'label']!r}")
print(ranked)

# %%
fig, ax = plt.subplots(figsize=(6, 6))
ax.scatter(gdf["lon"], gdf["lat"], s=6, c="lightgray", label="all points")
top_k_rows = gdf.iloc[order]
ax.scatter(top_k_rows["lon"], top_k_rows["lat"], s=30, c="tab:orange", label=f"top-{K} matches")
ax.scatter(
    gdf.loc[QUERY_ID, "lon"], gdf.loc[QUERY_ID, "lat"],
    s=200, marker="*", c="tab:red", edgecolors="black", label="query",
)
ax.set_title(f"{QUERY_REGION}: top-{K} matches for query {QUERY_ID}")
ax.legend(loc="upper right", fontsize="small")
fig.tight_layout()
fig.savefig("figures/02_topk_matches_map.png")
plt.show()

# %%
fig, ax = plt.subplots(figsize=(6, 4))
ax.hist(sims, bins=50)
ax.axvline(0.90, color="red", linestyle="--", label="similarity = 0.90")
ax.set_xlabel("cosine similarity to query")
ax.set_ylabel("count")
ax.set_title(f"{QUERY_REGION}: similarity of every point to the query")
ax.legend()
fig.tight_layout()
fig.savefig("figures/02_similarity_histogram.png")
plt.show()

# %% tags=["wrong-conclusion"]
# WRONG CONCLUSION: "similarity > 0.90 means same land cover"
same_class_rate = (gdf.loc[sims > 0.90, "label"] == gdf.loc[QUERY_ID, "label"]).mean()
print(
    f"WRONG: {same_class_rate:.0%} of points with similarity > 0.90 share the "
    f"query's label ({gdf.loc[QUERY_ID, 'label']!r}), so a similarity above 0.90 "
    "must mean 'same land cover'."
)

# %% [markdown]
# ### Why this is wrong
#
# The 0.90 cutoff is arbitrary — nothing about the embedding's geometry
# singles out 0.90 as a meaningful boundary. Pick 0.85 or 0.95 instead and
# the apparent "agreement rate" above changes with it, even though nothing
# about the underlying data changed. A fixed threshold answers "how many
# points cross an arbitrary line," not "how good is this query." Ranking,
# plus **precision@k** (introduced next), is the honest alternative: it
# asks how good the top-K matches are, which is exactly the question a
# search-by-example workflow actually needs answered.

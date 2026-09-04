# ---
# jupyter:
#   jupytext:
#     cell_metadata_filter: tags,-all
#     formats: ipynb,py:percent
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
# # Module 1: Embedding Refresher
#
# [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/guillem-gelabert/intro-to-geo-embeddings/blob/main/notebooks/solutions/00_embedding_refresher.ipynb)
#
# This notebook is optional background for students without a linear-algebra
# or GIS background. It builds, on tiny synthetic data, every vocabulary
# word the rest of the course assumes: vectors, normalization, cosine
# similarity, PCA, a train/test split, and a CRS reprojection — none of it
# tied to any real dataset, provider, or network call.

# %% [markdown]
# ## What you will learn
#
# 1. NumPy vectors and L2 normalization
# 2. Cosine similarity
# 3. PCA on a toy embedding matrix
# 4. A tiny classifier with a train/test split
# 5. CRS reprojection
#
# | Prerequisite | Needed? |
# |---|---|
# | Python basics | Yes |
# | Linear algebra | **No** |
# | GIS background | **No** |
#
# **Time to complete:** ~25 minutes.
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
    # This notebook only uses core-install packages (numpy, scikit-learn,
    # matplotlib, geopandas) -- no extra pip installs needed.
    REQUIRED = {"geopandas": "geopandas"}
    missing = [
        pip for mod, pip in REQUIRED.items() if importlib.util.find_spec(mod) is None
    ]
    if missing:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-q", *missing])

# %%
if not IN_COLAB:
    # `jupyter execute` (nbclient's CLI) sets the kernel's cwd to the
    # notebook's own directory (notebooks/solutions/), not the repo root,
    # so a bare `Path("figures")` would resolve to the wrong place there
    # even though it resolves correctly when this notebook is opened
    # interactively from the repo root. Walk up to find the repo root
    # (marked by pyproject.toml) and chdir there so both cases agree.
    for candidate in [Path.cwd(), *Path.cwd().parents]:
        if (candidate / "pyproject.toml").exists():
            os.chdir(candidate)
            break

import numpy as np

from course.config import RANDOM_STATE

np.random.seed(RANDOM_STATE)
Path("figures").mkdir(exist_ok=True)

# %% [markdown]
# ## Vectors and L2 normalization
#
# A geospatial embedding is just a vector — a fixed-length list of numbers
# describing a location. Two synthetic "location clusters" below stand in
# for that idea: six 8-dimensional vectors, three drawn tightly around one
# center and three around another.

# %%
rng = np.random.default_rng(RANDOM_STATE)
cluster_a_center = rng.normal(loc=0.0, scale=1.0, size=8)
cluster_b_center = cluster_a_center + 4.0

toy_matrix = np.vstack(
    [
        rng.normal(loc=cluster_a_center, scale=0.3, size=(3, 8)),
        rng.normal(loc=cluster_b_center, scale=0.3, size=(3, 8)),
    ]
)
cluster_labels = np.array(["A", "A", "A", "B", "B", "B"])

raw_norms = np.linalg.norm(toy_matrix, axis=1)
print("raw (non-unit) norms:", np.round(raw_norms, 3))

# %% tags=["task"]
# TODO: Vectors and L2 normalization
raise NotImplementedError("Implement this cell — see the module's solution notebook if you get stuck.")


# %% [markdown]
# <details>
# <summary>Show solution</summary>
#
# See <code>notebooks/solutions/00_embedding_refresher.ipynb</code> — the same section, just above this point in the notebook.
# </details>

# %% [markdown]
# **Takeaway:** unit-length vectors turn the dot product into cosine
# similarity — the same fact `02_similarity_and_classification.ipynb`
# relies on for real AlphaEarth data.

# %% [markdown]
# ## Cosine similarity
#
# With every row unit-norm, the full pairwise dot-product matrix below IS
# the pairwise cosine similarity matrix — no extra division needed.

# %% tags=["checkpoint"]
similarity_matrix = normalized @ normalized.T
assert abs(similarity_matrix.max() - 1.0) < 1e-6

import matplotlib.pyplot as plt

fig, ax = plt.subplots(figsize=(5, 4))
im = ax.imshow(similarity_matrix, vmin=-1, vmax=1, cmap="viridis")
ax.set_xticks(range(6))
ax.set_yticks(range(6))
ax.set_xticklabels(cluster_labels)
ax.set_yticklabels(cluster_labels)
ax.set_title("Pairwise cosine similarity (toy vectors)")
fig.colorbar(im, ax=ax, label="cosine similarity")
fig.tight_layout()
fig.savefig("figures/00_cosine_similarity_matrix.png")
plt.show()

# %% [markdown]
# **Takeaway:** vectors within the same synthetic cluster score high cosine
# similarity; vectors across clusters score low — this is the same signal
# `cosine_similarity_map` computes at scale.

# %% [markdown]
# ## PCA on a toy embedding matrix
#
# Real embeddings have far more dimensions than can be plotted directly.
# PCA finds the 2 directions of greatest variance in the toy matrix so it
# can be visualized on a page, at the cost of discarding everything else.

# %% tags=["task"]
# TODO: PCA on a toy embedding matrix
raise NotImplementedError("Implement this cell — see the module's solution notebook if you get stuck.")


# %% [markdown]
# <details>
# <summary>Show solution</summary>
#
# See <code>notebooks/solutions/00_embedding_refresher.ipynb</code> — the same section, just above this point in the notebook.
# </details>

# %%
fig, ax = plt.subplots(figsize=(5, 4))
for label in ["A", "B"]:
    mask = cluster_labels == label
    ax.scatter(components[mask, 0], components[mask, 1], s=80, label=f"cluster {label}")
ax.set_xlabel("PC1")
ax.set_ylabel("PC2")
ax.set_title("PCA of the toy embedding matrix")
ax.legend()
fig.tight_layout()
fig.savefig("figures/00_pca_scatter.png")
plt.show()

# %% [markdown]
# **Takeaway:** the first two components separate the two synthetic
# clusters in this toy sample — they do not correspond to a named physical
# variable.

# %% [markdown]
# ## A tiny classifier
#
# With unit-normalized vectors and known cluster labels in hand, the next
# natural question is whether a simple linear model can recover the
# clusters from the vectors alone.

# %% tags=["task"]
# TODO: A tiny classifier
raise NotImplementedError("Implement this cell — see the module's solution notebook if you get stuck.")


# %% [markdown]
# <details>
# <summary>Show solution</summary>
#
# See <code>notebooks/solutions/00_embedding_refresher.ipynb</code> — the same section, just above this point in the notebook.
# </details>

# %% [markdown]
# **Takeaway:** a linear classifier separates the two synthetic clusters
# using only the unit-normalized vectors.

# %% [markdown]
# ## A CRS reprojection reminder
#
# Coordinates in EPSG:4326 (longitude/latitude, degrees) are not metres —
# every later notebook reprojects to a projected CRS before measuring
# distances. Three tiny points near Bern, reused from the same study area
# `02_similarity_and_classification.ipynb` uses, make this concrete.

# %% tags=["task"]
# TODO: A CRS reprojection reminder
raise NotImplementedError("Implement this cell — see the module's solution notebook if you get stuck.")


# %% [markdown]
# <details>
# <summary>Show solution</summary>
#
# See <code>notebooks/solutions/00_embedding_refresher.ipynb</code> — the same section, just above this point in the notebook.
# </details>

# %% [markdown]
# **Takeaway:** every later notebook reprojects to a projected CRS
# (EPSG:2056 for the Bern region) before measuring distances in metres —
# EPSG:4326 degrees are not metres.

# %% [markdown]
# ## Wrap-up
#
# **Takeaways:**
#
# - L2-normalizing vectors makes the dot product equal to cosine
#   similarity.
# - Cosine similarity separates the toy clusters cleanly; the same idea
#   scales to real 64-D AlphaEarth embeddings.
# - PCA compresses a high-dimensional embedding to 2 axes for plotting,
#   at the cost of everything those 2 axes do not capture.
# - A simple linear classifier can already recover known clusters from
#   unit-normalized vectors and a train/test split.
# - EPSG:4326 degrees must be reprojected to a projected CRS (e.g.
#   EPSG:2056) before any metre-based distance calculation.
#
# **What's next:** `00b_representation_inspection.ipynb` and
# `01_alphaearth_access_visualize.ipynb` build directly on these ideas
# using real AlphaEarth data.
#
# **Resources:**
#
# - scikit-learn PCA: https://scikit-learn.org/stable/modules/generated/sklearn.decomposition.PCA.html
# - scikit-learn LogisticRegression: https://scikit-learn.org/stable/modules/generated/sklearn.linear_model.LogisticRegression.html
# - pyproj/geopandas CRS docs: https://geopandas.org/en/stable/docs/user_guide/projections.html

# %% [markdown]
# ## Reflection
#
# - Why does L2-normalizing a vector turn the dot product into cosine similarity? What would change if the vectors were not normalized first?
# - The PCA scatter separates cluster A from cluster B on the toy matrix. Does that mean PC1 and PC2 correspond to a named, physical variable? Why or why not?
# - The classifier reaches high accuracy on 6 tiny synthetic points. What about this toy setup makes that result unsurprising, and why wouldn't the same accuracy number be trustworthy on real AlphaEarth data?

# %% [markdown]
# ## Stretch tasks
#
# - Change `cluster_b_center`'s offset from the origin (currently +4.0) to a smaller value and re-run the cosine similarity matrix — at what offset do the two clusters stop being cleanly separable?
# - Add a third synthetic cluster and re-fit the PCA and the classifier. Does a linear classifier still separate all three classes cleanly?
# - Reproject the three toy points to a different projected CRS (e.g. EPSG:32632, UTM zone 32N) instead of EPSG:2056 and compare the resulting coordinates — why do they differ?

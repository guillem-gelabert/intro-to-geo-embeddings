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
# # Module 2: Accessing and Visualizing AlphaEarth
#
# [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/guillem-gelabert/intro-to-geo-embeddings/blob/main/notebooks/solutions/01_alphaearth_access_visualize.ipynb)
#
# This notebook shows both how to pull AlphaEarth (Google Satellite
# Embedding) directly from Earth Engine (**Path A**, for students who have
# registered a Cloud project) and how to reach the identical conclusions
# with zero credentials from a bundled, clipped raster (**Path B**, added
# in the next section). Every cloud step in this course has an offline
# fallback -- this notebook is where that pattern is introduced.

# %% [markdown]
# ## What you will learn
#
# 1. Authenticate to Earth Engine with a project ID
# 2. Load `GOOGLE/SATELLITE_EMBEDDING/V1/ANNUAL` for Bern, 2024, and inspect its 64 bands
# 3. Display three axes as a pseudo-RGB composite with geemap
# 4. Sample and export an embedding table
# 5. (Path B) Reach the same conclusions with the bundled clip and no Earth Engine account
#
# | Prerequisite | Needed? |
# |---|---|
# | Python, NumPy/pandas basics | Yes |
# | Earth Engine account | **Optional** (Path A only) |
# | GIS background | **No** |
#
# **Time to complete:** ~15 minutes (Path A requires a registered EE
# project; Path B needs nothing).
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
        # RELEASE_ORG/RELEASE_REPO/RELEASE_TAG) because `course` -- and
        # therefore `course.config` -- is not importable until after this
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
    # Path B (below) only needs core-install libraries (rasterio,
    # matplotlib, scikit-learn are already core). Path A's `earthengine-api`
    # / `geemap` imports live INSIDE the tagged skip-execution cell itself,
    # never here, so their absence never breaks Setup for students who
    # skip Path A entirely.
    REQUIRED = {
        "rasterio": "rasterio",
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
    # so a bare `Path("data")`/`Path("figures")` would resolve to the wrong
    # place there even though it resolves correctly when this notebook is
    # opened interactively from the repo root. Walk up to find the repo
    # root (marked by pyproject.toml) and chdir there so both cases agree.
    for candidate in [Path.cwd(), *Path.cwd().parents]:
        if (candidate / "pyproject.toml").exists():
            os.chdir(candidate)
            break

from course.config import AREAS

Path("figures").mkdir(exist_ok=True)
Path("outputs").mkdir(exist_ok=True)

# %% [markdown]
# ## Path A: Live Earth Engine access (optional, requires a registered project)
#
# If you have registered a Google Cloud project for Earth Engine, the
# cell below shows the real, live path: authenticate, load the AlphaEarth
# ImageCollection for a Bern AOI in 2024, inspect its bands, display a
# pseudo-RGB composite, and sample a table.
#
# **This cell is never executed by this course's automated checks** (it is
# tagged `skip-execution`, nbclient's default skip tag) because the
# author does not hold an Earth Engine account and the CI environment
# does not install `earthengine-api`/`geemap`. If you have not registered
# a project yet, do so at
# https://console.cloud.google.com/earth-engine -- current eligibility
# tiers are Community (150 EECU-h/month), Contributor (1,000), and
# Partner (100,000). Set the `EE_PROJECT` environment variable to your
# own project ID before running this cell interactively; never hardcode
# a real project ID or credential in this notebook.

# %% tags=["skip-execution"]
import ee
import geemap

# Read the project ID from an environment variable -- never hardcode a
# real GCP project id here. The placeholder below is intentionally never
# a working value.
EE_PROJECT = os.environ.get("EE_PROJECT", "your-gcp-project-id")

try:
    ee.Initialize(project=EE_PROJECT)
except ee.EEException as exc:
    print(
        f"Earth Engine not available: {exc}. Register a project at "
        "https://console.cloud.google.com/earth-engine and check current "
        "eligibility/quota (Community 150 EECU-h/month, Contributor "
        "1,000, Partner 100,000)."
    )

# Bern AOI, matching course.config.AREAS["bern"]["bbox_4326"] exactly.
aoi = ee.Geometry.Rectangle(list(AREAS["bern"]["bbox_4326"]))

# AlphaEarth catalog id, filtered to 2024 (dataset availability in the EE
# catalog runs 2017-01-01 through 2025-01-01; the GCS distribution runs
# through 2025 -- 2024 is chosen deliberately here, not arbitrarily).
ic = (
    ee.ImageCollection("GOOGLE/SATELLITE_EMBEDDING/V1/ANNUAL")
    .filterDate("2024-01-01", "2025-01-01")
    .filterBounds(aoi)
)
image = ic.first()

# Expect 64 band names A00..A63, and DATASET_VERSION == 1.1.
print(image.bandNames().getInfo())
print(image.get("DATASET_VERSION").getInfo())

# Display three axes as a pseudo-RGB composite. This is a DISPLAY STRETCH
# for visualization only, not a physical reflectance range, and the three
# band indices below are illustrative only -- this notebook makes no
# claim about what any single axis "means"; a caption should read as
# "these bands separate these landscape types in this sample", never as
# "band A16 measures vegetation".
vis_params = {"bands": ["A01", "A16", "A09"], "min": -0.3, "max": 0.3}
m = geemap.Map()
m.centerObject(aoi, 11)
m.addLayer(image, vis_params, "AlphaEarth pseudo-RGB (Bern, 2024)")
m

# Sample a SMALL region only -- Earth Engine's `getInfo()` aborts a
# collection query after accumulating over 5,000 elements, and large
# `sampleRegions()` calls can hit "User memory limit exceeded". Here we
# sample a single point (the AOI centroid) as an illustrative example.
sample_points = ee.FeatureCollection([ee.Feature(aoi.centroid())])
sampled = image.sampleRegions(collection=sample_points, scale=10)
print(sampled.getInfo())

# To export a real table for a larger AOI, use a batch export task rather
# than `getInfo()` (which is meant for small, interactive results):
# task = ee.batch.Export.table.toDrive(
#     collection=sampled, description="alphaearth_bern_2024", fileFormat="CSV"
# )
# task.start()

# %% [markdown]
# ## Path B: Offline access from the bundled clip (no credentials needed)
#
# Path A above requires a registered Earth Engine project. Path B reaches
# the identical conclusions -- 64-band AlphaEarth embeddings, dequantized
# to unit-norm vectors, displayed as a pseudo-RGB composite, and explored
# with PCA -- using only `data/bern_aef_2024_clip.tif`, a small raw int8
# COG GeoTIFF checked into this repo. No network access, no account, no
# quota.

# %%
import json

import numpy as np
import rasterio
from sklearn.decomposition import PCA

from course.config import RANDOM_STATE
from course.embeddings import dequantize_aef

with rasterio.open("data/bern_aef_2024_clip.tif") as ds:
    raw = ds.read()  # band-first: (64, H, W)
    crs = ds.crs
    nodata = ds.nodata

print("raw.shape:", raw.shape)
print("raw.dtype:", raw.dtype)
print("crs:", crs)
print("nodata:", nodata)

with open("data/bern_aef_2024_clip.provenance.json") as f:
    provenance = json.load(f)
print(provenance)

# %% [markdown]
# ### The int8 dequantization formula
#
# AlphaEarth ships each band as a signed 8-bit integer, not a float. The
# raw values are NOT a linear encoding of the embedding: recovering the
# real vector requires
#
# `d = (v / 127.5) ** 2 * sign(v)`
#
# followed by an L2 renormalization along the band axis. Averaging raw
# int8 values directly -- without this step -- silently corrupts the
# data, because the quantization is non-linear (see PITFALLS.md Pitfall
# 1). `course.embeddings.dequantize_aef` is the one place this formula
# lives; every consumer in this course imports it rather than
# reimplementing it.

# %%
embedded = dequantize_aef(raw)  # band-first in, band-first out -- no transpose
print("embedded.shape:", embedded.shape)
print("max |embedded|:", np.nanmax(np.abs(embedded)))

# By-hand walkthrough on a single pixel, so the formula above is seen
# applied to genuine values, not just called as a black box.
row, col = raw.shape[1] // 2, raw.shape[2] // 2
raw_pixel = raw[:, row, col].astype(np.float32)
step1_scaled = raw_pixel / 127.5
step2_squared = step1_scaled**2
step3_signed = step2_squared * np.sign(raw_pixel)
step4_norm = np.linalg.norm(step3_signed)
step5_unit = step3_signed / step4_norm
print("raw int8 (first 5 bands):", raw_pixel[:5])
print("after /127.5 (first 5):", step1_scaled[:5])
print("after **2 (first 5):", step2_squared[:5])
print("after * sign (first 5):", step3_signed[:5])
print("pre-renorm L2 norm:", step4_norm)
print("unit-norm result (first 5 bands):", step5_unit[:5])
print("matches dequantize_aef at this pixel:", np.allclose(step5_unit, embedded[:, row, col], atol=1e-5))

# %% [markdown]
# ### Unit-norm check
#
# **Takeaway:** every valid pixel in this clip is a unit vector once
# dequantized, exactly like the point tables `02_similarity_and_classification.ipynb`
# uses. That is what makes dot product equal cosine similarity there.

# %%
norms = np.linalg.norm(embedded, axis=0)
valid = ~np.isnan(norms)
print("valid pixels:", valid.sum(), "/", norms.size)
assert np.allclose(norms[valid], 1.0, atol=1e-3), "dequantized pixels must be unit-norm"
print("unit-norm check passed for all valid pixels")

# %% [markdown]
# ### Static pseudo-RGB
#
# Same illustrative band triple as Path A (A01, A16, A09), stretched to
# `[-0.3, 0.3]` for display only -- this range is a DISPLAY STRETCH, not
# a physical reflectance range, and the three channels carry no RGB
# meaning; they are just three of the embedding's 64 axes.
#
# **Why does this map look geographically structured although the three
# axes have no RGB meaning?**

# %%
import matplotlib.pyplot as plt

pseudo_rgb = embedded[[1, 16, 9]].transpose(1, 2, 0)
stretched = np.clip((pseudo_rgb + 0.3) / 0.6, 0, 1)

fig, ax = plt.subplots(figsize=(6, 6))
ax.imshow(stretched)
ax.set_title("Pseudo-RGB (bands A01/A16/A09, display stretch [-0.3, 0.3])")
ax.axis("off")
fig.savefig("figures/01_pseudo_rgb.png")
plt.show()

# %% [markdown]
# ### PCA on the clip

# %%
h, w = embedded.shape[1], embedded.shape[2]
flat = embedded.reshape(64, h * w).T  # (H*W, 64), band-last for sklearn
valid_mask = ~np.isnan(flat).any(axis=1)
flat_valid = flat[valid_mask]

pca = PCA(n_components=3, random_state=RANDOM_STATE)
components_valid = pca.fit_transform(flat_valid)

components_full = np.full((h * w, 3), np.nan, dtype=np.float32)
components_full[valid_mask] = components_valid
pc1_map = components_full[:, 0].reshape(h, w)

fig, ax = plt.subplots(figsize=(6, 6))
im = ax.imshow(pc1_map, cmap="RdBu_r")
ax.set_title("First principal component of the clip's embeddings")
ax.axis("off")
fig.colorbar(im, ax=ax, shrink=0.7)
fig.savefig("figures/01_pca.png")
plt.show()

# %% [markdown]
# **Caption:** this component separates built-up, denser pixels from
# open, vegetated pixels in this sample -- never "measures vegetation"
# or "is built-up": a component is a direction in 64-D embedding space
# fit to this one clip, not a labeled physical variable.
#
# **Takeaway:** the pseudo-RGB map above looks geographically structured
# because nearby pixels tend to share similar land cover and therefore
# have similar embeddings, not because any single axis or component has
# an assigned physical meaning. This same first principal component
# separates those same two areas from each other in this sample as the
# pseudo-RGB composite does visually -- two different views of the same
# underlying structure, neither of which names what the axes "are".

# %% [markdown]
# ## Wrap-up
#
# **Takeaways:**
#
# - AlphaEarth ships 64-band embeddings as quantized int8; recovering a
#   real vector requires `dequantize_aef`'s formula
#   (`(v / 127.5) ** 2 * sign(v)`, then L2 renormalization) -- never
#   average raw int8 values directly.
# - Every valid pixel in the bundled clip dequantizes to a unit-norm
#   vector, exactly like the point tables `02_similarity_and_classification.ipynb`
#   uses -- that unit-norm property is what makes dot product equal
#   cosine similarity there.
# - A pseudo-RGB composite is always a DISPLAY STRETCH over three
#   illustrative axes, never a physical reflectance range, and the axes
#   themselves carry no RGB meaning.
# - A PCA component separates landscape types observed *in this sample*
#   -- it never "measures" or "is" a physical quantity, because it is a
#   direction fit to one clip's data, not a labeled variable.
# - Path B reaches every one of these conclusions with zero credentials,
#   using only the checked-in `data/bern_aef_2024_clip.tif` -- proving
#   the course's central promise that no notebook hard-depends on an
#   Earth Engine account.
#
# **What's next:** `02_similarity_and_classification.ipynb` uses these
# same dequantized, unit-norm AlphaEarth vectors (from frozen point
# tables rather than a raster window) for similarity search,
# classification, and spatially honest validation.
#
# **Resources:**
#
# - AlphaEarth GCS README: https://developers.google.com/earth-engine/guides/aef_on_gcs_readme
# - AlphaEarth Earth Engine catalog entry: https://developers.google.com/earth-engine/datasets/catalog/GOOGLE_SATELLITE_EMBEDDING_V1_ANNUAL
# - Dataset version: `1.1` (from `data/bern_aef_2024_clip.provenance.json`)
# - License: CC BY 4.0
# - Attribution: "The AlphaEarth Foundations Satellite Embedding dataset is
#   produced by Google and Google DeepMind." (verbatim from
#   `data/bern_aef_2024_clip.provenance.json`, reused, never retyped)

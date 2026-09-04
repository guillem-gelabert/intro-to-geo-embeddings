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

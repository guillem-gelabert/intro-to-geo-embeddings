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
# # Module 4: Change Detection and Validation
#
# [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/guillem-gelabert/intro-to-geo-embeddings/blob/main/notebooks/solutions/03_change_detection_and_validation.ipynb)
#
# This notebook takes the same AlphaEarth embeddings you already used for
# search and classification and asks a harder question: did the land at a
# point actually change between two years? A single cosine-based "change
# score" is easy to compute and easy to misread -- this notebook builds it,
# shows exactly how it misleads you, and then calibrates a threshold
# honestly against an independent reference instead of eyeballing one.

# %% [markdown]
# ## What you will learn
#
# 1. A cosine-based change score between two years of the same point's embedding
# 2. Why a fixed change-score threshold is not itself a semantic-change decision
# 3. Calibrating a threshold against an independent reference with `precision_recall_curve`
# 4. Per-year classifiers and a land-cover transition matrix (second half of this notebook, authored in a later plan)
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
        "mapclassify": "mapclassify",
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

import numpy as np

from course.config import RANDOM_STATE

np.random.seed(RANDOM_STATE)
Path("figures").mkdir(exist_ok=True)
Path("outputs").mkdir(exist_ok=True)

# %% [markdown]
# ## Data: 2018 vs 2021, row-aligned by `sample_id`
#
# This module compares **2018 against 2021** rather than 2020 against
# 2024: Copernicus imperviousness has a series break between its 2015 and
# 2018 products, and the corresponding change product covers 2018-2021.
# The frozen tables carry 2018, 2021 and 2024 for the same `sample_id`s
# across both study areas, so a 2018/2021 pair joins directly without any
# extra sampling.

# %% tags=["solution"]
import course.data
import course.schema
from course.config import AREAS

years = (2018, 2021)
loaded = {}
for area in ("bern", "seville"):
    for year in years:
        loaded[(area, year)] = course.data.load(area, year)

# %% tags=["checkpoint"]
aligned = {}
for area in ("bern", "seville"):
    gdf_early = loaded[(area, years[0])].set_index("sample_id")
    gdf_late = loaded[(area, years[1])].set_index("sample_id")
    shared_ids = gdf_early.index.intersection(gdf_late.index)
    assert len(shared_ids) == len(gdf_early) == len(gdf_late), (
        f"{area}: expected an exact sample_id match between {years[0]} and "
        f"{years[1]} (frozen tables share sample_id across years per "
        f"data/DATA_CARD.md), got {len(shared_ids)} shared out of "
        f"{len(gdf_early)}/{len(gdf_late)} rows -- a partial join here would "
        "silently compare unrelated points."
    )
    aligned[area] = {
        years[0]: gdf_early.loc[shared_ids].reset_index(),
        years[1]: gdf_late.loc[shared_ids].reset_index(),
    }
    print(f"{area}: {len(shared_ids)} row-aligned points ({years[0]} vs {years[1]})")

# %%
import pandas as pd

summary = pd.DataFrame(
    {
        area: {
            f"{year} rows": len(loaded[(area, year)]) for year in years
        }
        for area in ("bern", "seville")
    }
).T
print(summary)

# %% [markdown]
# **Takeaway:** the same `sample_id` names the same real-world point across
# 2018 and 2021 -- that stability is what makes a paired change score
# meaningful. Without it, subtracting one year's embedding from another
# would be comparing unrelated pixels, and the resulting "change score"
# would be noise dressed up as a measurement.


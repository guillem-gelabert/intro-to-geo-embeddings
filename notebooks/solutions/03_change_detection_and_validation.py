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

# %% [markdown]
# ## Change score: `1 - cosine_similarity` per point
#
# `course.embeddings.change_score` takes two row-aligned `(n, 64)` matrices
# and returns one `(n,)` array: how far each point's embedding moved
# between the two years, as a single number. It reports representation
# movement only -- it does not know, and does not claim to know, *why* a
# point moved.

# %% tags=["solution"]
from course.embeddings import change_score

frames = []
for area in ("bern", "seville"):
    gdf_early = aligned[area][years[0]]
    gdf_late = aligned[area][years[1]]
    matrix_early = course.schema.to_matrix(gdf_early)
    matrix_late = course.schema.to_matrix(gdf_late)
    scores = change_score(matrix_early, matrix_late)
    frames.append(
        pd.DataFrame(
            {
                "sample_id": gdf_late["sample_id"],
                "region": area,
                "lon": gdf_late["lon"],
                "lat": gdf_late["lat"],
                "change_score": scores,
                "imd_2018": gdf_late["imd_2018"],
                "label": gdf_late["label"],
            }
        )
    )
change_df = pd.concat(frames, ignore_index=True)
print(change_df.groupby("region")["change_score"].describe())

# %%
import matplotlib.pyplot as plt

fig, axes = plt.subplots(1, 2, figsize=(12, 4), sharey=True)
for ax, area in zip(axes, ("bern", "seville")):
    ax.hist(change_df.loc[change_df["region"] == area, "change_score"], bins=50)
    ax.set_title(area)
    ax.set_xlabel("change score (1 - cosine similarity)")
axes[0].set_ylabel("count")
fig.tight_layout()
fig.savefig("figures/03_change_score_hist.png")
plt.show()

# %%
fig, axes = plt.subplots(1, 2, figsize=(12, 5))
for ax, area in zip(axes, ("bern", "seville")):
    sub = change_df.loc[change_df["region"] == area]
    sc = ax.scatter(sub["lon"], sub["lat"], c=sub["change_score"], s=8, cmap="viridis")
    ax.set_title(area)
    ax.set_xlabel("lon")
fig.colorbar(sc, ax=axes, label="change score", shrink=0.8)
axes[0].set_ylabel("lat")
fig.savefig("figures/03_change_score_map.png")
plt.show()

# %% [markdown]
# ## The WRONG conclusion
#
# It is tempting to pick a threshold by eye and call every point above it
# "artificialized." The cell below does exactly that -- and it is wrong.

# %% tags=["wrong-conclusion"]
# WRONG CONCLUSION: "change_score > 0.25 means the point was artificialized"
artificialized = change_df["change_score"] > 0.25
print(
    "WRONG: "
    + ", ".join(
        f"{area}={int((artificialized & (change_df['region'] == area)).sum())} of "
        f"{int((change_df['region'] == area).sum())} points flagged"
        for area in ("bern", "seville")
    )
)

# %% [markdown]
# ### Why this is wrong
#
# `1 - cosine_similarity` collapses the full 64-dimensional embedding into
# one number, and 0.25 was picked by eye with no reference data behind it.
# Google's own analysis of change scores derived this way found "widespread
# speckling, scattered false positives" -- harvest cycles, a drought year,
# early snow cover, or a swath-boundary artifact in the underlying imagery
# can all move a point's embedding by as much as genuine land-cover change
# does. A large change score means the *representation* moved; it does not
# by itself mean the *land cover* changed, let alone that it became
# "artificialized" specifically. Treating an unvalidated cutoff as a
# semantic-change decision is Pitfall 5 of this course, and it is the
# reason the rest of this section calibrates a threshold against a
# reference instead of asserting one.

# %% [markdown]
# ## Calibrating a threshold against a proxy independent reference
#
# The true Copernicus HRL Imperviousness Change 2018-2021 product would be
# the right reference here -- but it requires a free EU Login the author
# has not created for this course (see `02-RESEARCH.md`, "Is the free EU
# Login genuinely needed?"). Rather than skip validation, or worse, quietly
# reuse `label` as if it were an independent change product, this notebook
# builds an explicitly labeled **proxy** from two columns already in the
# frozen tables:
#
# - `known_change`: `imd_2018 < 20` (measurably non-impervious in 2018)
#   **and** `label == "built"` (labeled built by the 2021-sourced
#   WorldCover pass).
# - `known_unchanged`: either stayed built (`imd_2018 >= 70` and
#   `label == "built"`), or stayed clearly non-built
#   (`imd_2018 < 20` and `label != "built"`).
#
# This proxy is weaker than a real two-epoch change product for a specific
# reason: `label` is a **single 2021 snapshot**, not a genuine 2018-vs-2021
# label pair, so "known_change" here really means "was clearly non-built in
# 2018 and is built in the one epoch we have a label for" -- consistent
# with a 2018-2021 transition to built, but not directly observed as one.
# A student with an EU Login should replace this proxy with the true HRL
# change product and re-run this calibration; what follows is the honest,
# currently-available substitute, not a claim of equivalence.

# %% tags=["solution"]
known_change = (change_df["imd_2018"] < 20) & (change_df["label"] == "built")
known_unchanged = ((change_df["imd_2018"] >= 70) & (change_df["label"] == "built")) | (
    (change_df["imd_2018"] < 20) & (change_df["label"] != "built")
)
controls = change_df.loc[known_change | known_unchanged].copy()
controls["y_true"] = known_change.loc[controls.index].astype(int)
print(
    f"controls: {len(controls)}/{len(change_df)} rows kept "
    f"({int(known_change.sum())} known_change, {int(known_unchanged.sum())} known_unchanged)"
)

# %%
from sklearn.metrics import f1_score, precision_score, recall_score
from sklearn.metrics import precision_recall_curve

precision_curve, recall_curve, thresholds = precision_recall_curve(
    controls["y_true"], controls["change_score"]
)
f1_curve = np.where(
    (precision_curve[:-1] + recall_curve[:-1]) > 0,
    2 * precision_curve[:-1] * recall_curve[:-1]
    / (precision_curve[:-1] + recall_curve[:-1] + 1e-9),
    0.0,
)
best_idx = int(np.argmax(f1_curve))
best_threshold = float(thresholds[best_idx])
print(f"calibrated threshold (max F1 on controls): {best_threshold:.3f}")

calibrated_pred = (controls["change_score"] > best_threshold).astype(int)
precision = precision_score(controls["y_true"], calibrated_pred)
recall = recall_score(controls["y_true"], calibrated_pred)
f1 = f1_score(controls["y_true"], calibrated_pred)
print(f"overall: precision={precision:.3f}, recall={recall:.3f}, f1={f1:.3f}")

for group_name, mask in [
    ("known_change controls", controls["y_true"] == 1),
    ("known_unchanged controls", controls["y_true"] == 0),
]:
    group = controls.loc[mask]
    group_pred = (group["change_score"] > best_threshold).astype(int)
    flagged_rate = group_pred.mean()
    print(f"{group_name}: {len(group)} points, flagged rate={flagged_rate:.2f}")

# %%
calibrated_flagged = int(
    (change_df["change_score"] > best_threshold).sum()
)
wrong_flagged = int(artificialized.sum())
print(
    f"WRONG threshold (0.25, unvalidated): {wrong_flagged} points flagged\n"
    f"calibrated threshold ({best_threshold:.3f}, validated on proxy controls): "
    f"{calibrated_flagged} points flagged"
)

# %% [markdown]
# **Takeaway:** the calibrated threshold above is not just "a different
# number" than 0.25 -- it comes with a precision, a recall, and an F1 score
# measured against a labeled reference, so you know how much to trust a
# flag it produces. The 0.25 threshold from the WRONG-conclusion cell came
# with none of that. The proxy reference used here is honestly weaker than
# the true HRL 2018-2021 change product would be (it leans on a single
# 2021 label snapshot, not a genuine two-epoch label), and this notebook
# says so explicitly rather than presenting it as equivalent -- a student
# with an EU Login should swap in the real change product and recalibrate.
#
# **What's next:** the second half of this notebook (a later plan) adds
# per-year classifiers and a land-cover transition matrix on top of this
# same change-score foundation.

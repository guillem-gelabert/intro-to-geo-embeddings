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
# # Module 6: Capstone — Artificialization Pipeline Template
#
# [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/guillem-gelabert/intro-to-geo-embeddings/blob/main/notebooks/solutions/05_capstone_artificialization.ipynb)
#
# This notebook is a **template**, not a finished analysis. It assembles an
# end-to-end AOI-to-provenance pipeline entirely from `course` helpers you
# already used in Modules 3-5 — `course.data.load`, `course.schema.to_matrix`,
# `course.embeddings.change_score`, `course.validation.make_blocks` /
# `spatial_cv_report` — on the existing Bern/Seville frozen data as the
# worked example. Every cell marked `# EDIT ME` is a substitution point: swap
# in your own AOI, labels, and classes and the rest of the pipeline runs
# unchanged.

# %% [markdown]
# ## What you will learn
#
# 1. How to assemble a full AOI-to-provenance pipeline from reusable course
#    helpers, without reimplementing any of them
# 2. The capstone rubric you are graded against, and what satisfies each row
# 3. Why the rubric weights validation design above every other criterion
#
# | Prerequisite | Needed? |
# |---|---|
# | Module 3 (similarity + classification) | Yes |
# | Module 4 (change + validation) | Yes |
# | Module 5 (ecosystems: TESSERA/Clay/LGND) | Recommended |
# | Earth Engine account | **No** |
#
# **Time to complete:** ~2 minutes execution.
# Runs on free Colab CPU, no Earth Engine account.
#
# Course reference environment: 2026-08 release. Provider APIs may change.
# Every cloud notebook has a local/offline fallback.

# %% [markdown]
# ## Capstone rubric
#
# Your own capstone submission (a new AOI, your own labels, your own
# question) is graded against these six weighted criteria. Validation
# design is worth more than any other single row — a convincing classifier
# with a dishonest validation still fails this rubric.
#
# | Criterion | Weight | What satisfies this row |
# |---|---|---|
# | Validation design | 30% | Spatial-block CV **and** leave-region-out (or leave-one-AOI-out), not a random split; both reported, not either/or |
# | Reproducibility and provenance | 15% | `course.provenance.build_provenance`/`write_provenance` output committed alongside the notebook; pinned dataset versions |
# | CRS and alignment correctness | 15% | Reprojection to a projected CRS before any metre-based operation (`make_blocks`, buffers); no geographic-CRS distances |
# | Interpretation and uncertainty | 15% | Reported metrics carry the CV fold spread (mean ± std), not a single point estimate; claims are scoped to what was measured |
# | Representation choice | 15% | The embedding product used is stated explicitly, with a one-sentence trade-off against at least one alternative |
# | Licensing and ethics | 10% | Attribution and license of every input recorded; who bears the cost of a false positive is named |

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
# ## AOI
#
# **This is the cell a student replaces for their own capstone.** The AOI
# knob below picks which of the course's two frozen regions this worked
# example runs on; a real capstone submission would point `course.data.load`
# at a newly-prepared region instead (same loader, same schema, same
# validation calls) — nothing downstream needs to change.

# %% tags=["parameters"]
AOI = "bern"  # EDIT ME -- try "seville", or point course.data.load at your own AOI

# %% tags=["solution"]
import course.data
import course.schema
from course.config import ANCHOR_YEARS, AREAS

HELD_OUT_REGION = "seville" if AOI == "bern" else "bern"
assert AOI in AREAS, f"AOI={AOI!r} not in course.config.AREAS: {sorted(AREAS)}"

years = {year: course.data.load(AOI, year) for year in ANCHOR_YEARS}
held_out = course.data.load(HELD_OUT_REGION, ANCHOR_YEARS[-1])

for year, gdf in years.items():
    course.schema.validate_frozen(gdf)
course.schema.validate_frozen(held_out)
print(
    f"AOI={AOI!r}: loaded {sorted(years)} ({len(years[ANCHOR_YEARS[0]])} rows each); "
    f"held-out region {HELD_OUT_REGION!r}: {len(held_out)} rows"
)

# %% [markdown]
# ## Features
#
# **Representation choice** (rubric row, stated explicitly): this capstone
# uses AlphaEarth directly, at its native 64 dimensions. A stronger
# submission might compare against TESSERA or Clay per Module 5, trading
# off AlphaEarth's global 10 m/annual coverage against TESSERA's finer
# spatial resolution or Clay's Sentinel-2-derived embedding and different
# license terms.
#
# The feature matrix stacks the most recent anchor year's embedding (the
# "current state" signal) with `change_score` computed between the two
# earlier anchor years (a "recent trend" signal) — the **baseline-aware**
# configuration PITFALLS.md's Pitfall 5 recommends: base-year embedding
# stacked with the delta feature, never the delta alone. A delta-only
# feature cannot distinguish "moved a lot from a stable state" from "moved
# a lot and is still moving," which is exactly the ambiguity a raw
# `1 - cosine` threshold falls into.

# %% tags=["solution"]
from course.embeddings import change_score

X_base = course.schema.to_matrix(years[ANCHOR_YEARS[-1]])
X_trend = change_score(
    course.schema.to_matrix(years[ANCHOR_YEARS[0]]),
    course.schema.to_matrix(years[ANCHOR_YEARS[1]]),
).reshape(-1, 1)
X_aoi = np.hstack([X_base, X_trend])
print(
    f"feature matrix: {X_aoi.shape} "
    f"({X_base.shape[1]} embedding dims from {ANCHOR_YEARS[-1]} + 1 change-score dim "
    f"from {ANCHOR_YEARS[0]}->{ANCHOR_YEARS[1]})"
)

# %% [markdown]
# ## Predictions
#
# **Representation/target choice** (stated explicitly, as the rubric
# requires): this worked example classifies the same four adequately-
# represented classes Module 3 used — **built, crop, vegetation, water**
# (`bare` dropped as a sparse residual category, per Module 3) — rather than
# collapsing to a binary artificialized/not-artificialized target. A
# capstone submission is free to pick either target; whichever is chosen,
# state it here and justify it, exactly as this cell does.

# %% tags=["solution"]
CLASSES = ["built", "crop", "vegetation", "water"]

label_aoi = years[ANCHOR_YEARS[-1]]["label"].to_numpy()
class_mask = np.isin(label_aoi, CLASSES)
X_aoi_clf = X_aoi[class_mask]
y_aoi_clf = label_aoi[class_mask]
print(f"{AOI}: {len(y_aoi_clf)}/{len(label_aoi)} rows kept after dropping 'bare'")

# %%
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

model = Pipeline(
    [
        ("scaler", StandardScaler()),
        ("clf", LogisticRegression(random_state=RANDOM_STATE, max_iter=1000)),
    ]
)
model.fit(X_aoi_clf, y_aoi_clf)
print(f"fitted logreg on {AOI}: train accuracy={model.score(X_aoi_clf, y_aoi_clf):.3f}")

# %% [markdown]
# ## Validation: spatial-block CV and leave-region-out
#
# **Validation design is the single largest rubric weight (30%)** — larger
# than every other criterion combined would need to be small for that not
# to matter. Both validations below reuse the *exact same*
# `course.validation.spatial_cv_report` call shape Module 3 used, changing
# only `groups` and `cv` — never a hand-rolled CV loop.

# %% tags=["solution"]
from sklearn.model_selection import GroupKFold, LeaveOneGroupOut

from course.config import BLOCK_SIZE_M
from course.validation import make_blocks, spatial_cv_report

years_gdf = years[ANCHOR_YEARS[-1]].loc[class_mask].reset_index(drop=True)
epsg = AREAS[AOI]["epsg"]
gdf_projected = years_gdf.to_crs(epsg)
groups_block = make_blocks(gdf_projected, block_size_m=BLOCK_SIZE_M)
n_blocks = len(np.unique(groups_block))
assert n_blocks >= 5, (
    f"only {n_blocks} spatial blocks at block_size_m={BLOCK_SIZE_M} -- need at "
    "least 5 for GroupKFold(n_splits=5)"
)

block_report = spatial_cv_report(
    model,
    X_aoi_clf,
    y_aoi_clf,
    groups=groups_block,
    cv=GroupKFold(n_splits=5, shuffle=True, random_state=RANDOM_STATE),
)
print(
    f"SPATIAL-BLOCK CV ({AOI}, {n_blocks} blocks): balanced_accuracy="
    f"{block_report['mean_balanced_accuracy']:.3f} ± "
    f"{block_report['std_balanced_accuracy']:.3f}"
)

# %% tags=["solution"]
held_out_label = held_out["label"].to_numpy()
held_out_class_mask = np.isin(held_out_label, CLASSES)
held_out_clf = held_out.loc[held_out_class_mask].reset_index(drop=True)
X_held_out_clf = course.schema.to_matrix(held_out_clf)
# The held-out region only carries the single most-recent anchor year loaded
# above, so its feature matrix is embedding-only; pad a zero change-score
# column to match X_aoi_clf's width -- an explicit, visible substitution
# because the trend feature is undefined without a second timestamp for
# this region, not a silent shape mismatch.
X_held_out_clf = np.hstack(
    [X_held_out_clf, np.zeros((len(X_held_out_clf), 1), dtype=np.float32)]
)

X_region = np.vstack([X_aoi_clf, X_held_out_clf])
y_region = np.concatenate([y_aoi_clf, held_out_label[held_out_class_mask]])
region_groups = np.concatenate(
    [np.full(len(y_aoi_clf), AOI), np.full(len(X_held_out_clf), HELD_OUT_REGION)]
)

lro_report = spatial_cv_report(
    model, X_region, y_region, groups=region_groups, cv=LeaveOneGroupOut()
)
print(
    f"LEAVE-REGION-OUT (train {AOI}, predict {HELD_OUT_REGION}): balanced_accuracy="
    f"{lro_report['mean_balanced_accuracy']:.3f} ± "
    f"{lro_report['std_balanced_accuracy']:.3f}"
)

# %% [markdown]
# **Takeaway:** on this course's measured data (Module 3), leave-region-out
# costs roughly 17-19 balanced-accuracy points relative to in-region
# spatial-block CV, while spatial-block CV costs almost nothing relative to
# a random split. The gap printed above should show the same pattern: the
# honest cross-region number, not the in-region one, is where this
# pipeline's real generalization test lives. A capstone submission that
# reports only a random split, or only one of these two validations, does
# not satisfy the validation-design rubric row — **both are required.**

# %%
import pandas as pd

comparison = pd.DataFrame(
    {
        "scenario": ["spatial-block CV (in-region)", "leave-region-out"],
        "mean_balanced_accuracy": [
            block_report["mean_balanced_accuracy"],
            lro_report["mean_balanced_accuracy"],
        ],
        "std_balanced_accuracy": [
            block_report["std_balanced_accuracy"],
            lro_report["std_balanced_accuracy"],
        ],
    }
)
print(comparison)

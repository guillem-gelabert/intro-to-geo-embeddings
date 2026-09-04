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

# %%
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

# %% tags=["task"]
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

# %% tags=["task"]
CLASSES = ["built", "crop", "vegetation", "water"]

label_aoi = years[ANCHOR_YEARS[-1]]["label"].to_numpy()
class_mask = np.isin(label_aoi, CLASSES)
X_aoi_clf = X_aoi[class_mask]
y_aoi_clf = label_aoi[class_mask]
print(f"{AOI}: {len(y_aoi_clf)}/{len(label_aoi)} rows kept after dropping 'bare'")

# %% tags=["task"]
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

# %% tags=["task"]
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

# %% tags=["task"]
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

# %% [markdown]
# ## Map: predictions over the AOI
#
# A prediction map on its own invites a reader to treat it as settled fact.
# **This map is deliberately paired with the uncertainty section right
# below it, not left as a standalone figure** -- per this notebook's own
# rubric row on interpretation/uncertainty, and because the leave-region-out
# result above just showed this exact model loses a large share of its
# accuracy outside its training region. A ranked, human-verified candidate
# layer is the honest framing; an unqualified "artificialized/not" map is
# not.

# %% tags=["task"]
import matplotlib.pyplot as plt

pred_aoi = model.predict(X_aoi_clf)
map_gdf = years_gdf.assign(pred=pred_aoi)

fig, ax = plt.subplots(figsize=(6, 6))
for cls, group in map_gdf.groupby("pred"):
    ax.scatter(group["lon"], group["lat"], s=8, label=cls, alpha=0.7)
ax.set_title(f"{AOI}: predicted class per point (in-region fit)")
ax.set_xlabel("lon")
ax.set_ylabel("lat")
ax.legend(loc="upper right", fontsize="small")
fig.tight_layout()
fig.savefig("figures/05_prediction_map.png")
plt.show()

# %% [markdown]
# ## Uncertainty: model-level and validation-level
#
# These are two genuinely different kinds of uncertainty, and conflating
# them is exactly the overconfidence trap this section exists to avoid:
#
# - **Model uncertainty** -- how close a single prediction was to a
#   different class, for THIS fitted model on THIS data. Computed below as
#   the margin between the top two predicted-class probabilities: a small
#   margin means the model itself is unsure, even before asking whether the
#   model generalizes at all.
# - **Validation uncertainty** -- how much the reported accuracy itself
#   would swing under a different sample of the same evaluation, i.e. the
#   fold-to-fold spread (`std_balanced_accuracy`) already computed by
#   `spatial_cv_report` above. A model can show a confident (small) margin
#   on every point and still have a large validation std -- these are not
#   the same signal, and reporting only one is a form of the confident-
#   map-hiding-real-uncertainty problem this phase's threat model calls
#   out (T-05-14).
#
# A single accuracy number, with neither of these alongside it, is an
# overconfident presentation of a change/classification map.

# %% tags=["task"]
proba = model.predict_proba(X_aoi_clf)
sorted_proba = np.sort(proba, axis=1)
margin = sorted_proba[:, -1] - sorted_proba[:, -2]

fig, ax = plt.subplots(figsize=(6, 4))
ax.hist(margin, bins=30, color="tab:blue", alpha=0.8)
ax.set_title(f"{AOI}: model-level uncertainty (top-1 minus top-2 probability margin)")
ax.set_xlabel("margin (0 = maximally uncertain, 1 = maximally confident)")
ax.set_ylabel("count")
fig.tight_layout()
fig.savefig("figures/05_uncertainty_margin_hist.png")
plt.show()

print(
    f"MODEL-LEVEL uncertainty ({AOI}): mean margin={margin.mean():.3f}, "
    f"{(margin < 0.2).sum()}/{len(margin)} points with margin < 0.2 (low confidence)"
)
print(
    f"VALIDATION-LEVEL uncertainty: spatial-block CV std_balanced_accuracy="
    f"{block_report['std_balanced_accuracy']:.3f}; leave-region-out "
    f"std_balanced_accuracy={lro_report['std_balanced_accuracy']:.3f} "
    "(fold-to-fold spread, not a per-point number)"
)

# %% [markdown]
# **Takeaway:** the map above should be read as a ranked candidate layer a
# human verifies -- ordered by the margin computed here, low-margin points
# reviewed first -- never as a finished classification. Both uncertainty
# numbers printed above matter: a tight model-level margin does not rescue
# a wide validation-level spread, and vice versa.

# %% [markdown]
# ## Provenance
#
# Every number and figure above traces back to a specific dataset version,
# CRS, label source and license -- recorded once per table when it was
# loaded (`course.data.load`) and summarized here with `build_provenance`
# / `write_provenance` (`course/provenance.py`), never hand-typed. This
# notebook's own output is held to the same `templates/PROVENANCE_CHECKLIST.md`
# standard demonstrated throughout the course, rather than only described.

# %%
import json

from course.provenance import build_provenance, write_provenance

provenance = build_provenance(
    {f"{AOI}_{year}": gdf for year, gdf in years.items()},
    created_by="05_capstone_artificialization.ipynb",
)
write_provenance(provenance, Path("outputs/provenance_05.json"))
print(json.dumps(provenance, indent=2))

# %% [markdown]
# ## Rubric self-check
#
# The Header's rubric table, revisited here with THIS run's own evidence
# named for each row -- the worked example a capstone submission's own
# self-check should imitate:
#
# | Criterion | Weight | This notebook's evidence |
# |---|---|---|
# | Validation design | 30% | The spatial-block CV cell and the leave-region-out cell above, both required and both reported side by side in the `comparison` table -- not either/or |
# | Reproducibility and provenance | 15% | The Provenance cell's `outputs/provenance_05.json`, built entirely from `course.data.load`'s carried metadata, never hand-typed |
# | CRS and alignment correctness | 15% | The `gdf_projected = years_gdf.to_crs(epsg)` reprojection cell before `make_blocks`, guarded by `make_blocks`' own distance-sanity assertion |
# | Interpretation and uncertainty | 15% | The model-level margin histogram and the validation-level `std_balanced_accuracy` cells above, kept explicitly distinct |
# | Representation choice | 15% | The Features section's explicit AlphaEarth-at-64-D choice, stated with its trade-off against TESSERA/Clay |
# | Licensing and ethics | 10% | The Wrap-up's verbatim attribution/license strings below, plus the false-positive-cost statement: a false "artificialized" flag on someone's land can trigger real regulatory or compliance consequences, so a low-confidence flag (per the margin histogram above) must never be presented as certain. Inferred labels like "artificialized" can also be more sensitive than the underlying imagery itself -- they imply a judgment about the land's status that the raw pixels alone do not. |

# %% [markdown]
# ## Wrap-up
#
# **Takeaways:**
#
# - This capstone template assembles an AOI-to-provenance pipeline
#   entirely from `course` helpers reused, unmodified, from Modules 3-5.
# - Validation design carries the largest rubric weight for a reason: the
#   leave-region-out gap measured earlier is the single largest source of
#   overconfidence this pipeline could produce if only in-region numbers
#   were reported.
# - A prediction map is only honest alongside both a model-level and a
#   validation-level uncertainty measure -- neither substitutes for the
#   other.
# - The provenance file and the rubric self-check above are not optional
#   extras; they are graded rubric rows, produced automatically from
#   metadata already carried by `course.data.load`.
#
# **What's next:** the blank templates in `templates/PROVENANCE_CHECKLIST.md`
# and `templates/MODEL_DATA_CARD_TEMPLATE.md` are what you fill in for your
# own capstone AOI -- this notebook is the worked example of applying them
# to a finished run, not a substitute for filling them in yourself.
#
# **Resources (verbatim attribution/license strings for every source used
# in this notebook):**
#
# - AlphaEarth / Satellite Embedding -- CC BY 4.0 -- "The AlphaEarth
#   Foundations Satellite Embedding dataset is produced by Google and
#   Google DeepMind."
# - ESA WorldCover 2021 v200 (label source) -- CC BY 4.0 -- "© ESA
#   WorldCover project 2021 / Contains modified Copernicus Sentinel data
#   (2021) processed by ESA WorldCover consortium (citation: Zanaga et al.
#   2022, https://doi.org/10.5281/zenodo.7254221)"

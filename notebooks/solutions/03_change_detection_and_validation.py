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

# %%
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

# %% tags=["task"]
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

# %%
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

# %% tags=["task"]
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
# **What's next:** the rest of this notebook adds per-year classifiers and
# a land-cover transition matrix on top of this same change-score
# foundation, then validates both approaches with spatially- and
# temporally-grouped cross-validation.

# %% [markdown]
# ## Per-year classifiers and a class-transition matrix
#
# The change score above answers "how far did the embedding move," but it
# cannot answer "moved *from what* to *what*." A transition matrix can: fit
# one classifier per year on that year's own embeddings, predict every
# point's class in each year, and cross-tabulate the two predictions.
#
# **Important caveat, stated before the code below runs it:** `label` does
# not itself vary by year -- WorldCover 2021 is the only labeled epoch in
# this dataset. So "per-year classifier" here does NOT mean "trained
# against a year-specific ground truth." It means: train the identical
# model architecture separately on each year's own embedding distribution
# (still supervised by the same 2021 `label` column, pooled across both
# regions), then predict from each year's embeddings. The interesting
# signal is where `clf_2018`'s prediction and `clf_2021`'s prediction
# *disagree* for the same point -- something a single continuous change
# score cannot show, because it never assigns a class at all.

# %% tags=["task"]
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

CLASSES = ["built", "crop", "vegetation", "water"]

pooled = {}
for year in years:
    frames_year = []
    for area in ("bern", "seville"):
        gdf_year = aligned[area][year]
        frames_year.append(gdf_year.loc[gdf_year["label"].isin(CLASSES)])
    pooled[year] = pd.concat(frames_year, ignore_index=True)
    print(f"{year}: {len(pooled[year])} pooled rows after dropping 'bare'")

classifiers = {}
predictions = {}
for year in years:
    X_year = course.schema.to_matrix(pooled[year])
    y_year = pooled[year]["label"].to_numpy()
    clf = Pipeline(
        [
            ("scaler", StandardScaler()),
            ("clf", LogisticRegression(random_state=RANDOM_STATE, max_iter=1000)),
        ]
    )
    clf.fit(X_year, y_year)
    classifiers[year] = clf
    predictions[year] = clf.predict(X_year)
    print(f"{year}: classifier fit on {len(y_year)} pooled points")

# %% [markdown]
# The two pooled tables are already row-aligned by `sample_id` within each
# area (the `aligned` dict built earlier), and `pooled[2018]`/`pooled[2021]`
# were built with the identical per-area concatenation order and the
# identical `bare`-dropping filter, so `predictions[2018][i]` and
# `predictions[2021][i]` refer to the same real-world point.

# %% tags=["task"]
from sklearn.metrics import ConfusionMatrixDisplay, confusion_matrix

pred_2018 = predictions[years[0]]
pred_2021 = predictions[years[1]]

transition = confusion_matrix(pred_2018, pred_2021, labels=CLASSES)
fig, ax = plt.subplots(figsize=(6, 6))
ConfusionMatrixDisplay(transition, display_labels=CLASSES).plot(ax=ax, colorbar=False)
ax.set_xlabel("predicted 2021 class")
ax.set_ylabel("predicted 2018 class")
ax.set_title("Class-transition matrix (predicted, not true, classes)")
fig.tight_layout()
fig.savefig("figures/03_transition_matrix.png")
plt.show()

# %% [markdown]
# **Why the axis labels say "predicted," never "true":** every cell in
# this matrix comes from two classifier predictions, not from any
# 2018-vs-2021 ground-truth transition label (none exists in this
# dataset). Reading it as observed truth would silently overstate how much
# is actually validated here.

# %% tags=["task"]
artificialized_mask = (pred_2018 == "vegetation") & (pred_2021 == "built")
crop_to_built_mask = (pred_2018 == "crop") & (pred_2021 == "built")
print(
    f"vegetation -> built: {int(artificialized_mask.sum())} points\n"
    f"crop -> built: {int(crop_to_built_mask.sum())} points"
)
if crop_to_built_mask.sum() > artificialized_mask.sum() * 0.2:
    artificialized_mask = artificialized_mask | crop_to_built_mask
    print("crop -> built is non-trivial relative to vegetation -> built; folded in.")

# %% [markdown]
# ## Comparing the transition-matrix mask against the continuous change score
#
# `pooled[years[1]]` drops the `bare` class that `change_df` still carries,
# so the two tables cannot be compared by row position -- join on
# `sample_id` (unique per point within a region, matched together with
# `region` since both regions reuse the same `sample_id` numbering).

# %%
mask_lookup = pd.DataFrame(
    {
        "sample_id": pooled[years[1]]["sample_id"],
        "region": pooled[years[1]]["region"],
        "artificialized_mask": artificialized_mask,
    }
)
joined = change_df.merge(mask_lookup, on=["sample_id", "region"], how="inner")
assert len(joined) == len(mask_lookup), (
    f"expected every classifier-pooled point ({len(mask_lookup)}) to also "
    f"appear in change_df, got {len(joined)} matched rows -- a join key "
    "mismatch would silently drop points from this comparison"
)

joined["cosine_wrong"] = joined["change_score"] > 0.25
joined["cosine_calibrated"] = joined["change_score"] > best_threshold

comparison_rows = []
for name, col in [
    ("WRONG threshold (0.25)", "cosine_wrong"),
    ("calibrated threshold", "cosine_calibrated"),
]:
    mask_col = joined["artificialized_mask"]
    cosine_col = joined[col]
    both = int((mask_col & cosine_col).sum())
    mask_only = int((mask_col & ~cosine_col).sum())
    cosine_only = int((~mask_col & cosine_col).sum())
    comparison_rows.append(
        {
            "cosine flag": name,
            "transition-mask only": mask_only,
            "cosine only": cosine_only,
            "both": both,
        }
    )
disagreement_table = pd.DataFrame(comparison_rows)
print(disagreement_table)

# %% [markdown]
# **Takeaway:** the transition-matrix mask and the continuous change score
# answer different questions -- cosine measures how far the embedding
# vector moved, the transition matrix asks what class it moved *between*.
# They only partly agree, and that disagreement is itself the teaching
# point (Pitfall 5): a point can move a lot in embedding space without
# crossing the vegetation-to-built class boundary (phenology, a dry year),
# and a point can cross that boundary with a modest cosine movement if the
# two classes' embedding centroids are already close. Neither number alone
# tells the whole story; that is exactly why this notebook builds both.

# %% [markdown]
# ## Validating the artificialization mask: spatially- and temporally-grouped CV
#
# `artificialized_mask` above is itself the output of a classifier
# (well, two). Before trusting it, this notebook validates it the same
# honest way Module 3 validated the land-cover classifier -- with grouped
# CV, never a random split.
#
# **A second trap lurks here that Module 3 did not have: temporal
# leakage.** The pooled 2018+2021 table contains the SAME real-world
# locations twice (once per year). A random split -- or even a spatial
# split that ignores year -- can put a point's 2018 row in the training
# fold and its 2021 row in the test fold. The model would then partly
# "recognise the site" (soil colour, terrain, whatever is stable across
# both years) rather than learn a signal that transfers to genuinely new
# locations or new years. This is the temporal analogue of Module 3's
# spatial-block lesson: group by the thing that must NOT leak across the
# split, spatial blocks there, year here.

# %% tags=["task"]
from sklearn.model_selection import GroupKFold, LeaveOneGroupOut

from course.config import BLOCK_SIZE_M
from course.validation import make_blocks, spatial_cv_report

pooled_all = pd.concat([pooled[years[0]], pooled[years[1]]], ignore_index=True)
mask_all = np.concatenate([artificialized_mask, artificialized_mask])
year_array = np.concatenate(
    [
        np.full(len(pooled[years[0]]), years[0]),
        np.full(len(pooled[years[1]]), years[1]),
    ]
)
X_pooled_all = course.schema.to_matrix(pooled_all)

pooled_2056 = pooled_all.to_crs("EPSG:2056")
spatial_blocks = make_blocks(pooled_2056, block_size_m=BLOCK_SIZE_M)
n_blocks = len(np.unique(spatial_blocks))
print(f"pooled table: {n_blocks} spatial blocks at {BLOCK_SIZE_M} m")

artif_model = Pipeline(
    [
        ("scaler", StandardScaler()),
        ("clf", LogisticRegression(random_state=RANDOM_STATE, max_iter=1000)),
    ]
)

spatial_report = spatial_cv_report(
    artif_model,
    X_pooled_all,
    mask_all,
    groups=spatial_blocks,
    cv=GroupKFold(n_splits=5, shuffle=True, random_state=RANDOM_STATE),
)
print(
    f"SPATIAL-BLOCK CV: balanced_accuracy="
    f"{spatial_report['mean_balanced_accuracy']:.3f} ± "
    f"{spatial_report['std_balanced_accuracy']:.3f}"
)

# %% tags=["task"]
temporal_report = spatial_cv_report(
    artif_model,
    X_pooled_all,
    mask_all,
    groups=year_array,
    cv=LeaveOneGroupOut(),
)
print(
    f"LEAVE-ONE-YEAR-OUT CV: balanced_accuracy="
    f"{temporal_report['mean_balanced_accuracy']:.3f} ± "
    f"{temporal_report['std_balanced_accuracy']:.3f}"
)

# %%
cv_comparison = pd.DataFrame(
    {
        "scenario": ["spatial-block CV", "leave-one-year-out"],
        "mean_balanced_accuracy": [
            spatial_report["mean_balanced_accuracy"],
            temporal_report["mean_balanced_accuracy"],
        ],
        "std_balanced_accuracy": [
            spatial_report["std_balanced_accuracy"],
            temporal_report["std_balanced_accuracy"],
        ],
    }
)
print(cv_comparison)

fig, ax = plt.subplots(figsize=(6, 4))
ax.bar(
    cv_comparison["scenario"],
    cv_comparison["mean_balanced_accuracy"],
    yerr=cv_comparison["std_balanced_accuracy"],
    color=["tab:blue", "tab:orange"],
)
ax.set_ylabel("balanced accuracy")
ax.set_ylim(0, 1)
ax.set_title("Artificialization-mask CV: space-grouped vs year-grouped")
fig.tight_layout()
fig.savefig("figures/03_spatiotemporal_cv_comparison.png")
plt.show()

# %% [markdown]
# **Takeaway:** the numbers printed above are the honest, measured
# comparison -- not an assumed direction. If leave-one-year-out scores
# lower than spatial-block CV, that supports the hypothesis this section
# opened with: year-specific artifacts (Sentinel swath differences,
# atmospheric conditions, a different phenological state) make the model
# partly overfit to a year's own signature rather than learn a
# transferable artificialization signal, and spatial-block CV alone would
# have hidden that gap because it never separates by year. If the two
# scores land close together instead, that is reported just as plainly:
# it would mean this mask generalizes across years about as well as it
# generalizes across space, on this sample. Either way, grouping by the
# dimension that must not leak -- space for the spatial split, year for
# this one -- is what makes the number trustworthy in the first place.

# %% [markdown]
# ## Provenance

# %%
import json

from course.provenance import build_provenance, write_provenance

provenance_loaded = {
    "bern_2018": loaded[("bern", 2018)],
    "bern_2021": loaded[("bern", 2021)],
    "seville_2018": loaded[("seville", 2018)],
    "seville_2021": loaded[("seville", 2021)],
}
provenance = build_provenance(
    provenance_loaded,
    created_by="03_change_detection_and_validation.ipynb",
)
write_provenance(provenance, Path("outputs/provenance_03.json"))
print(json.dumps(provenance, indent=2))

# %% [markdown]
# ## Wrap-up
#
# **Takeaways:**
#
# - A cosine-based change score reports how far a point's embedding moved
#   between two years -- a real, cheap signal, but not by itself a
#   semantic change decision. Calibrating a threshold against an
#   independent proxy reference (`precision_recall_curve`) turns it into
#   one with a known precision/recall/F1, unlike an eyeballed cutoff.
# - A class-transition matrix built from two per-year classifiers answers
#   a different, more direct question: what class did a point move *from*
#   and *to*? The two approaches agree only partly -- that disagreement,
#   not either number alone, is the honest picture of what changed.
# - Both the calibrated change-score threshold and this transition-matrix
#   artificialization mask stay honest about a real limitation: the true
#   Copernicus HRL Imperviousness change product (2018-2021) requires a
#   free EU Login the author has not created for this course, so this
#   notebook validates against the best available proxy and says so,
#   rather than presenting the proxy as equivalent to a real change
#   product.
# - Validating the artificialization mask required grouping by TWO
#   different things that must not leak across a CV split: space (the
#   Module 3 lesson, reused here via `make_blocks`/`GroupKFold`) and year
#   (this module's new lesson, via `LeaveOneGroupOut` grouped on the year
#   label) -- `label_source` (`esa_worldcover_2021`) and
#   `validation_source` (`eea_hrl_imperviousness_2018`) also stay two
#   architecturally distinct strings throughout, never conflated
#   (Pitfall 6).
#
# **What's next:** Module 5 reuses these SAME `course.embeddings.change_score`
# and `course.validation.spatial_cv_report` helpers across TESSERA, Clay
# and LGND embeddings, so the change-detection and validation logic built
# here stays identical across providers.
#
# **Resources:**
#
# - AlphaEarth GCS README: https://developers.google.com/earth-engine/guides/aef_on_gcs_readme
# - Copernicus HRL Imperviousness: https://land.copernicus.eu/en/products/high-resolution-layer-imperviousness
# - Course reference environment: `course.config.COURSE_RELEASE` = `"2026.08"`
# - License and attribution (verbatim from `data/DATA_CARD.md`, reused here,
#   never retyped):
#   - AlphaEarth / Satellite Embedding -- CC BY 4.0 -- "The AlphaEarth
#     Foundations Satellite Embedding dataset is produced by Google and
#     Google DeepMind."
#   - ESA WorldCover 2021 v200 -- CC BY 4.0 -- "© ESA WorldCover project
#     2021 / Contains modified Copernicus Sentinel data (2021) processed
#     by ESA WorldCover consortium (citation: Zanaga et al. 2022,
#     https://doi.org/10.5281/zenodo.7254221)"
#   - Copernicus HRL Imperviousness Density 2018 -- Free/open, commercial
#     use allowed -- "Generated using European Union's Copernicus Land
#     Monitoring Service information"
# - **Limitation repeated once more for anyone skimming only this
#   section:** the true HRL Imperviousness Change 2018-2021 product needs
#   a free EU Login the author has not created for this course; both
#   correction paths above (calibrated threshold, transition-matrix mask)
#   validate against the best currently-available proxy, not that product.

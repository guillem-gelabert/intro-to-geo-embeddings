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

# %% [markdown]
# ## Similarity 2: Prototype queries
#
# A single pixel is noisy — one point can sit right on a boundary, under a
# cloud-shadow artifact, or just be an unlucky sample. A **prototype**
# query averages several points that are known examples of what you are
# looking for, which trades away single-pixel precision for stability.
#
# The raw mean of several unit-norm embedding vectors is **not itself
# unit-norm** — averaging shrinks the vector toward the origin whenever the
# inputs disagree even slightly in direction. Renormalizing (dividing by
# the mean's own norm) is required, not optional, to get back a valid
# query vector that `cosine_similarity_map` can compare on equal footing
# with everything else in this notebook.


# %%
def precision_at_k(
    sims: np.ndarray,
    labels: np.ndarray,
    target_label: str,
    k: int,
    exclude_idx: int | None = None,
) -> float:
    """Fraction of the top-k ranked (by `sims`) points whose label matches
    `target_label`. `exclude_idx` drops a self-match (e.g. the query point
    itself) from the ranking before taking the top-k."""
    order = np.argsort(-sims)
    if exclude_idx is not None:
        order = order[order != exclude_idx]
    top_k = order[:k]
    return float((labels[top_k] == target_label).mean())


target_label = gdf.loc[QUERY_ID, "label"]
precision_single = precision_at_k(sims, gdf["label"].to_numpy(), target_label, K, exclude_idx=QUERY_ID)
print(f"single-pixel precision@{K} vs label {target_label!r}: {precision_single:.2f}")

# %% tags=["parameters"]
POLYGON_ID = "bern-quarry-01"  # EDIT ME

# %%
import geopandas as gpd

polygons = gpd.read_file("data/query_polygons.geojson")
selected = polygons.loc[polygons["id"] == POLYGON_ID]
if selected.empty:
    raise KeyError(
        f"POLYGON_ID={POLYGON_ID!r} not found in data/query_polygons.geojson; "
        f"valid ids: {sorted(polygons['id'])}"
    )
polygon_region = selected.iloc[0]["region"]
assert polygon_region == QUERY_REGION, (
    f"POLYGON_ID={POLYGON_ID!r} is in region {polygon_region!r}, but "
    f"QUERY_REGION={QUERY_REGION!r}; pick a polygon in the same region for "
    "this comparison to be meaningful"
)

epsg = AREAS[polygon_region]["epsg"]
polygon_proj = selected.to_crs(epsg).geometry.iloc[0]
points_proj = gdf.to_crs(epsg)
buffered = polygon_proj.buffer(300)
within_mask = points_proj.geometry.within(buffered).to_numpy()
contributing = gdf.loc[within_mask]

if len(contributing) < 3:
    print(f"WARNING: only {len(contributing)} points within 300m of {POLYGON_ID}; "
          "falling back to the 5 nearest points to its centroid")
    dists = points_proj.geometry.distance(polygon_proj.centroid)
    contributing = gdf.loc[dists.nsmallest(5).index]
print(f"{len(contributing)} points contribute to the {POLYGON_ID} polygon-mean prototype")

# %%
positive_centroid_raw = course.schema.to_matrix(contributing).mean(axis=0)
positive_centroid = positive_centroid_raw / np.linalg.norm(positive_centroid_raw)

sims_polygon = cosine_similarity_map(positive_centroid, matrix)
precision_polygon = precision_at_k(sims_polygon, gdf["label"].to_numpy(), target_label, K)
print(f"polygon-mean prototype precision@{K} vs label {target_label!r}: {precision_polygon:.2f}")

# %% [markdown]
# ## Similarity 3: Positive-minus-negative prototype (optional)
#
# A positive prototype alone can still drift toward whatever is common
# everywhere (shared soil signal, shared illumination). Subtracting a
# **negative** centroid — the mean of points known to be a *different*
# class — sharpens the query toward what is distinctive about the positive
# examples, not just present in them.

# %%
rng = np.random.default_rng(RANDOM_STATE)
other_labels = [label for label in gdf["label"].unique() if label != target_label]
negative_label = other_labels[0]
negative_pool = gdf.index[gdf["label"] == negative_label].to_numpy()
n_negative = min(len(contributing), len(negative_pool))
negative_idx = rng.choice(negative_pool, size=n_negative, replace=False)

negative_centroid_raw = course.schema.to_matrix(gdf.loc[negative_idx]).mean(axis=0)
pos_minus_neg_raw = positive_centroid - negative_centroid_raw
pos_minus_neg = pos_minus_neg_raw / np.linalg.norm(pos_minus_neg_raw)

sims_pos_neg = cosine_similarity_map(pos_minus_neg, matrix)
precision_pos_neg = precision_at_k(sims_pos_neg, gdf["label"].to_numpy(), target_label, K)
print(
    f"positive-minus-negative (vs {negative_label!r}) prototype precision@{K} "
    f"vs label {target_label!r}: {precision_pos_neg:.2f}"
)

# %%
comparison = pd.DataFrame(
    {
        "query_design": ["single-pixel", "polygon-mean", "positive-minus-negative"],
        f"precision@{K}": [precision_single, precision_polygon, precision_pos_neg],
    }
)
print(comparison)

fig, ax = plt.subplots(figsize=(6, 4))
ax.bar(comparison["query_design"], comparison[f"precision@{K}"], color=["tab:blue", "tab:orange", "tab:green"])
ax.set_ylabel(f"precision@{K}")
ax.set_ylim(0, 1)
ax.set_title(f"Query design comparison (target label: {target_label!r})")
fig.tight_layout()
fig.savefig("figures/02_prototype_precision_at_k.png")
plt.show()

# %% [markdown]
# **Takeaway:** prototype queries average out single-pixel noise, at the
# cost of assuming the polygon is spatially homogeneous (that everything
# inside the 300 m buffer really is an example of what you're looking
# for). When that assumption holds, prototypes tend to be at least as
# stable as the single-pixel query above; when a polygon straddles a
# boundary or mixes land-cover types, its mean is diluted and the
# single-pixel query can win instead. There is no query design that is
# unconditionally best — that is why this notebook measures rather than
# assumes.

# %% [markdown]
# ## Classification: the random-split trap
#
# Search-by-example needs no labels. A classifier does — and once labels
# are in play, *how* you split the data into train/test sets stops being a
# formality and becomes the single most consequential methodological
# choice in this notebook.
#
# **Class filtering:** both regions carry a `bare` class, but it is a
# residual, sparse category in each region's WorldCover-derived label
# balance (219 points in Bern's full candidate pool, per
# `02-RESEARCH.md`'s "Phase Requirements" table) — too thin to support a
# stable per-class precision/recall estimate under 5-fold grouped CV. This
# notebook classifies the four classes with adequate representation in
# both regions: **built, crop, vegetation, water.** `bare` is dropped, and
# that filtering is a deliberate, stated decision, not a silent one.

# %% tags=["solution"]
CLASSES = ["built", "crop", "vegetation", "water"]
bern_clf = bern.loc[bern["label"].isin(CLASSES)].reset_index(drop=True)
seville_clf = seville.loc[seville["label"].isin(CLASSES)].reset_index(drop=True)
print(f"bern: {len(bern_clf)}/{len(bern)} rows kept after dropping 'bare'")
print(f"seville: {len(seville_clf)}/{len(seville)} rows kept after dropping 'bare'")
print(bern_clf["label"].value_counts())

# %%
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    ConfusionMatrixDisplay,
    balanced_accuracy_score,
    classification_report,
)
from sklearn.model_selection import GroupKFold, LeaveOneGroupOut, train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

MODELS = {
    "logreg": Pipeline(
        [
            ("scaler", StandardScaler()),
            ("clf", LogisticRegression(random_state=RANDOM_STATE, max_iter=1000)),
        ]
    ),
    "random_forest": RandomForestClassifier(
        n_estimators=200,
        class_weight="balanced",
        random_state=RANDOM_STATE,
        n_jobs=-1,
    ),
}

X_bern = course.schema.to_matrix(bern_clf)
y_bern = bern_clf["label"].to_numpy()

# %%
X_train, X_test, y_train, y_test = train_test_split(
    X_bern, y_bern, test_size=0.3, random_state=RANDOM_STATE, stratify=y_bern
)

trap_results = {}
for name, model in MODELS.items():
    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)
    trap_results[name] = {
        "accuracy": model.score(X_test, y_test),
        "balanced_accuracy": balanced_accuracy_score(y_test, y_pred),
    }
    print(
        f"TRAP ACCURACY (random split, {name}): "
        f"accuracy={trap_results[name]['accuracy']:.3f}, "
        f"balanced_accuracy={trap_results[name]['balanced_accuracy']:.3f}"
    )

rf_pred = MODELS["random_forest"].predict(X_test)
fig, ax = plt.subplots(figsize=(6, 6))
ConfusionMatrixDisplay.from_predictions(y_test, rf_pred, ax=ax, colorbar=False)
ax.set_title("Random Forest — random split (the trap): looks great, proves little")
fig.tight_layout()
fig.savefig("figures/02_confusion_matrix_random_split.png")
plt.show()

# %% [markdown]
# ## Spatial CV: project first, then grid
#
# A random split lets adjacent points — potentially metres apart — land on
# opposite sides of train/test. AlphaEarth embeddings make this worse than
# raw pixels, not better: a full year of spatial/temporal context is baked
# into every embedding, so neighbouring points are *more* similar than raw
# spectra would be (PITFALLS.md Pitfall 2).
#
# `make_blocks` refuses a geographic CRS outright (PITFALLS.md Pitfall 3:
# "blocks computed in degrees are meaningless metre sizes"). So this
# notebook reprojects Bern to **EPSG:2056** (Swiss LV95, metre-based) as an
# explicit, visible step *before* gridding — never the other way around.

# %% tags=["solution"]
from course.config import BLOCK_SIZE_M
from course.validation import make_blocks, spatial_cv_report

bern_2056 = bern_clf.to_crs("EPSG:2056")
groups_block = make_blocks(bern_2056, block_size_m=BLOCK_SIZE_M)
n_blocks = len(np.unique(groups_block))
assert n_blocks >= 5, (
    f"only {n_blocks} spatial blocks at block_size_m={BLOCK_SIZE_M} — need at "
    "least 5 for GroupKFold(n_splits=5); the AOI may have shrunk below the "
    "DATA-08 floor"
)
print(f"bern: {n_blocks} spatial blocks at {BLOCK_SIZE_M} m")

block_results = {}
for name, model in MODELS.items():
    report = spatial_cv_report(
        model,
        X_bern,
        y_bern,
        groups=groups_block,
        cv=GroupKFold(n_splits=5, shuffle=True, random_state=RANDOM_STATE),
    )
    block_results[name] = report
    print(
        f"BLOCK CV ({name}): balanced_accuracy="
        f"{report['mean_balanced_accuracy']:.3f} ± {report['std_balanced_accuracy']:.3f} "
        f"(random-split was {trap_results[name]['balanced_accuracy']:.3f})"
    )

# %% [markdown]
# **Measured so far:** the random-split and spatial-block numbers above sit
# within a few points of each other, not tens of points apart. That gap is
# real and worth teaching, but it is not yet the dramatic effect this
# notebook is building toward — that comes next, from leave-region-out.

# %% [markdown]
# ## Leave-region-out: the dramatic, honest gap
#
# Train on Bern only, predict Seville only — a climatically and
# geographically distinct region the model never saw during training. This
# reuses the *exact same* `spatial_cv_report` call shape as the block CV
# above, changing only `groups` (now the region label) and `cv` (now
# `LeaveOneGroupOut`), which is itself the point: the helper is genuinely
# generic, not two different code paths dressed up to look similar.
#
# **Why leave-region-out is where the real gap lives, and in-region block
# CV is not:** AlphaEarth embeddings aggregate a full year of multi-modal
# satellite signal into every pixel, which plausibly makes them more
# resistant to naive *adjacent-pixel* leakage than raw single-date spectral
# bands would be — that is a within-region effect. Nothing about that
# aggregation helps a model trained only on Bern's spectral/embedding
# signature recognize Seville's, which is a genuinely different climate,
# soil, and crop-calendar signal — an extrapolation problem, not an
# interpolation one. The Sentinel-2 baseline in the next section tests this
# hypothesis directly.

# %% tags=["solution"]
combined = pd.concat([bern_clf, seville_clf], ignore_index=True)
X_all = course.schema.to_matrix(combined)
y_all = combined["label"].to_numpy()
region_groups = combined["region"].to_numpy()

lro_results = {}
for name, model in MODELS.items():
    report = spatial_cv_report(
        model, X_all, y_all, groups=region_groups, cv=LeaveOneGroupOut()
    )
    lro_results[name] = report
    print(
        f"LEAVE-REGION-OUT ({name}): balanced_accuracy="
        f"{report['mean_balanced_accuracy']:.3f} ± {report['std_balanced_accuracy']:.3f} "
        f"(random-split was {trap_results[name]['balanced_accuracy']:.3f}, "
        f"block CV was {block_results[name]['mean_balanced_accuracy']:.3f})"
    )

# %% [markdown]
# **The headline result:** the leave-region-out numbers printed above show
# a double-digit balanced-accuracy drop relative to the random-split and
# block-CV numbers from the previous section — a large, robust gap,
# consistent with a similar sample measured previously on this data
# (02-RESEARCH.md: 17-19 points for logistic regression and random forest,
# train Bern → predict Seville). In-region spatial-block CV, by contrast,
# showed only a 1-4 point gap above. **Leave-region-out is the primary
# evidence that a random split lies here** — the in-region block-vs-random
# comparison is a real, smaller, second lesson about interpolation vs.
# extrapolation, not the dramatic effect.

# %%
model_names = list(MODELS.keys())
scenarios = ["random split", "spatial-block CV", "leave-region-out"]
scores = {
    name: [
        trap_results[name]["balanced_accuracy"],
        block_results[name]["mean_balanced_accuracy"],
        lro_results[name]["mean_balanced_accuracy"],
    ]
    for name in model_names
}

fig, ax = plt.subplots(figsize=(7, 5))
bar_width = 0.35
x = np.arange(len(scenarios))
for i, name in enumerate(model_names):
    ax.bar(x + i * bar_width, scores[name], width=bar_width, label=name)
ax.set_xticks(x + bar_width / 2)
ax.set_xticklabels(scenarios)
ax.set_ylabel("balanced accuracy")
ax.set_ylim(0, 1)
ax.set_title("Leave-region-out is the dramatic gap; in-region block CV is a smaller one")
ax.legend()
fig.tight_layout()
fig.savefig("figures/02_cv_comparison_bar_chart.png")
plt.show()

# %%
rf_model = MODELS["random_forest"]
lro_cv = LeaveOneGroupOut()
# LeaveOneGroupOut yields one (train, test) split per unique group; pick the
# split whose held-out fold is Seville specifically (the headline scenario).
train_idx, test_idx = next(
    (tr, te)
    for tr, te in lro_cv.split(X_all, y_all, groups=region_groups)
    if (region_groups[te] == "seville").all()
)

rf_model.fit(X_all[train_idx], y_all[train_idx])
seville_pred = rf_model.predict(X_all[test_idx])
seville_true = y_all[test_idx]

report_df = pd.DataFrame(
    classification_report(seville_true, seville_pred, output_dict=True)
).T
print("Per-class precision/recall, leave-region-out (train Bern, predict Seville, random_forest):")
print(report_df)

# %%
seville_eval = combined.iloc[test_idx].reset_index(drop=True)
correct = seville_pred == seville_true

fig, ax = plt.subplots(figsize=(6, 6))
ax.scatter(
    seville_eval.loc[correct, "lon"], seville_eval.loc[correct, "lat"],
    s=8, c="tab:green", label="correct", alpha=0.6,
)
ax.scatter(
    seville_eval.loc[~correct, "lon"], seville_eval.loc[~correct, "lat"],
    s=8, c="tab:red", label="incorrect", alpha=0.6,
)
ax.set_title("Seville errors under leave-region-out (train Bern, random_forest)")
ax.set_xlabel("lon")
ax.set_ylabel("lat")
ax.legend(loc="upper right", fontsize="small")
fig.tight_layout()
fig.savefig("figures/02_error_map.png")
plt.show()

# %% [markdown]
# **Takeaway:** leave-region-out is where the dramatic, generalization-
# relevant gap lives for this modality — a model that looks excellent on
# Bern alone loses a large fraction of its accuracy the moment it has to
# extrapolate to a different climate and land-cover mix. In-region spatial
# blocking matters too, and is worth teaching in its own right, just far
# less dramatically here than the leave-region-out effect above.

# %% [markdown]
# ## Baseline: the identical pipeline on raw Sentinel-2 bands
#
# Everything above ran on 64-dimensional AlphaEarth embeddings. This
# section re-runs the *identical* pipeline — same classifiers, same
# `test_size`/`random_state`, same `make_blocks`/`GroupKFold` call, same
# `LeaveOneGroupOut` call — on `S2_COLS`, the frozen table's raw Sentinel-2
# reflectance bands, changing nothing except which feature matrix goes in.
# This isolates the feature representation as the only variable, testing
# the hypothesis raised above: are embeddings more leakage-resistant than
# raw single-date spectral bands, or not? The numbers below are measured,
# not assumed either way.

# %% tags=["solution"]
from course.schema import S2_COLS

# A handful of points sit at the very edge of a Sentinel-2 scene and come
# back NaN in these raw bands even though their AlphaEarth embedding (a
# yearly composite) is complete -- drop them for this baseline only, and
# say so, rather than let NaN silently propagate into StandardScaler/
# LogisticRegression (which would otherwise produce a nonsense NaN score).
bern_clf_s2 = bern_clf.dropna(subset=S2_COLS).reset_index(drop=True)
combined_s2 = combined.dropna(subset=S2_COLS).reset_index(drop=True)
print(
    f"S2 baseline: dropped {len(bern_clf) - len(bern_clf_s2)} Bern row(s) and "
    f"{len(combined) - len(combined_s2)} combined row(s) with NaN Sentinel-2 bands"
)

X_bern_s2 = bern_clf_s2[S2_COLS].to_numpy(np.float32)
y_bern_s2 = bern_clf_s2["label"].to_numpy()
groups_block_s2 = make_blocks(bern_clf_s2.to_crs("EPSG:2056"), block_size_m=BLOCK_SIZE_M)

X_all_s2 = combined_s2[S2_COLS].to_numpy(np.float32)
y_all_s2 = combined_s2["label"].to_numpy()
region_groups_s2 = combined_s2["region"].to_numpy()

# %%
s2_models = {
    "logreg": Pipeline(
        [
            ("scaler", StandardScaler()),
            ("clf", LogisticRegression(random_state=RANDOM_STATE, max_iter=1000)),
        ]
    ),
    "random_forest": RandomForestClassifier(
        n_estimators=200,
        class_weight="balanced",
        random_state=RANDOM_STATE,
        n_jobs=-1,
    ),
}

s2_trap, s2_block, s2_lro = {}, {}, {}
for name, model in s2_models.items():
    Xtr, Xte, ytr, yte = train_test_split(
        X_bern_s2, y_bern_s2, test_size=0.3, random_state=RANDOM_STATE, stratify=y_bern_s2
    )
    model.fit(Xtr, ytr)
    s2_trap[name] = balanced_accuracy_score(yte, model.predict(Xte))

    s2_block[name] = spatial_cv_report(
        model, X_bern_s2, y_bern_s2, groups=groups_block_s2,
        cv=GroupKFold(n_splits=5, shuffle=True, random_state=RANDOM_STATE),
    )["mean_balanced_accuracy"]

    s2_lro[name] = spatial_cv_report(
        model, X_all_s2, y_all_s2, groups=region_groups_s2, cv=LeaveOneGroupOut()
    )["mean_balanced_accuracy"]

    print(
        f"S2 baseline ({name}): random_split={s2_trap[name]:.3f}, "
        f"block_cv={s2_block[name]:.3f}, leave_region_out={s2_lro[name]:.3f}"
    )

# %%
baseline_table = pd.DataFrame(
    {
        "AlphaEarth embeddings": [
            trap_results["random_forest"]["balanced_accuracy"],
            block_results["random_forest"]["mean_balanced_accuracy"],
            lro_results["random_forest"]["mean_balanced_accuracy"],
        ],
        "Sentinel-2 raw bands": [
            s2_trap["random_forest"],
            s2_block["random_forest"],
            s2_lro["random_forest"],
        ],
    },
    index=["random split", "spatial-block CV", "leave-region-out"],
)
print("Comparison (random_forest, balanced accuracy):")
print(baseline_table)

embedding_block_gap = (
    trap_results["random_forest"]["balanced_accuracy"]
    - block_results["random_forest"]["mean_balanced_accuracy"]
)
s2_block_gap = s2_trap["random_forest"] - s2_block["random_forest"]
print(
    f"in-region block-CV gap: embeddings={embedding_block_gap:.3f}, "
    f"Sentinel-2={s2_block_gap:.3f}"
)

# %% [markdown]
# **Takeaway:** the table above reports what this run actually measured,
# not an assumed direction. If the Sentinel-2 in-region block-CV gap comes
# out larger than the embeddings' gap, that supports the hypothesis raised
# earlier — AlphaEarth embeddings, which already aggregate a full year of
# multi-modal spatial/temporal context per pixel, are more resistant to
# naive adjacent-pixel leakage than raw single-date reflectance values,
# which is itself a genuinely interesting, teachable result. If it does
# not come out that way on this sample, that is reported just as plainly:
# the honest number is the lesson, not a story picked in advance. Either
# way, the leave-region-out gap — for both feature representations —
# remains the larger, more consequential effect in this notebook.

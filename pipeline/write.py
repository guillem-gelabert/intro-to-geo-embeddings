"""Assemble the final per-(area, year) frozen table from the three
extraction modules, write it as GeoParquet 1.1.0 (WKB, zstd, covering
bbox) with embedded `course_provenance` metadata, and build the
sha256/row-count manifest that verifies every written table's integrity
(02-09-PLAN.md Task 1; DATA-01/DATA-05).

`assemble_table` joins the fixed sample-point set
(`pipeline.sample_design.generate_sample_points`) against the three
per-year extraction outputs (`pipeline.extract_aef.extract_area_year`,
`pipeline.attach_labels.attach_labels`, `pipeline.attach_s2.attach_s2`) on
`sample_id` -- every input is expected to cover the IDENTICAL fixed point
set, so a row count that diverges after any join step raises `ValueError`
rather than silently producing a shorter table (T-02-18 adjacent: a
structurally wrong table is caught at build time, not discovered later by
a student).

`write_table` follows the verbatim provenance round-trip pattern from
02-RESEARCH.md "Extraction Mechanics" step 7 / ARCHITECTURE.md Pattern 5:
`gdf.to_parquet(...)` first, then a `pyarrow.parquet` re-open +
`replace_schema_metadata` + rewrite to inject `course_provenance`.

`write_manifest` computes every `sha256` directly from the written file's
own bytes -- never hand-entered or carried over from a prior run
(T-02-18 mitigation).
"""

from __future__ import annotations

import hashlib
import json
import subprocess
from datetime import UTC, datetime
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
import pyarrow.parquet as pq

from course.schema import A_COLS, FROZEN_REQUIRED

# Columns pulled from attach_labels' output BEYOND what `sample_points`
# already carries. attach_labels returns `points.copy()` with these four
# columns appended (region/lon/lat/x/y/block_id/worldcover_class/geometry
# are already present on `sample_points` itself) -- re-merging the whole
# frame would collide on every one of those pre-existing columns.
# `validation_source` is deliberately excluded here: it is a per-area
# constant (never per-row varying), recorded once in the table's
# `course_provenance` metadata by `pipeline.build` instead of being
# repeated identically on every row.
_LABEL_COLS = ["sample_id", "label", "label_source", "imd_2018"]

# Informative extras beyond `course.schema.FROZEN_REQUIRED`
# (02-09-PLAN.md Task 1 behavior spec).
_EXTRA_COLS = ["worldcover_class", "imd_2018", "s2_n_scenes"]


def _assert_row_count(merged: pd.DataFrame, expected: int, step: str) -> None:
    if len(merged) != expected:
        raise ValueError(
            f"assemble_table: row count changed after joining {step} "
            f"({len(merged)} != {expected}) -- inputs must cover the "
            f"identical sample_id set produced by generate_sample_points"
        )


def assemble_table(
    sample_points: gpd.GeoDataFrame,
    aef_df: pd.DataFrame,
    labels_gdf: gpd.GeoDataFrame,
    s2_df: pd.DataFrame,
    year: int,
) -> gpd.GeoDataFrame:
    """Join the fixed sample points, AlphaEarth embeddings, labels, and
    Sentinel-2 bands into one frozen-table row set, on `sample_id`.

    Returns a GeoDataFrame (`crs="EPSG:4326"`) with columns matching
    `course.schema.FROZEN_REQUIRED` plus `A00..A63`
    (`course.schema.A_COLS`) plus `worldcover_class`/`imd_2018`/
    `s2_n_scenes` as informative extras, in a stable column order.
    """
    n = len(sample_points)

    merged = sample_points.merge(aef_df, on="sample_id", how="inner")
    _assert_row_count(merged, n, "aef_df")

    merged = merged.merge(labels_gdf[_LABEL_COLS], on="sample_id", how="inner")
    _assert_row_count(merged, n, "labels_gdf")

    s2_value_cols = [c for c in s2_df.columns if c != "sample_id"]
    merged = merged.merge(
        s2_df[["sample_id", *s2_value_cols]], on="sample_id", how="inner"
    )
    _assert_row_count(merged, n, "s2_df")

    merged["year"] = year

    geometry = merged["geometry"]
    column_order = [*FROZEN_REQUIRED, *A_COLS, *_EXTRA_COLS]
    attrs = pd.DataFrame(merged)[column_order].copy()

    result = gpd.GeoDataFrame(
        attrs, geometry=geometry, crs=sample_points.crs
    ).reset_index(drop=True)
    _assert_embeddings_present(result)
    return result


# Tolerance, not zero: an isolated nodata pixel inside an otherwise-covered AOI
# is plausible. A systematic miss is not, and that is what this catches.
MAX_NAN_EMBEDDING_FRACTION = 0.02


def _assert_embeddings_present(table: gpd.GeoDataFrame) -> None:
    """Refuse to build a table whose embeddings are substantially NaN.

    The first Seville build wrote 448 of 2050 rows (21.9%) with every
    embedding NaN, in all three years, because the AOI crossed an AlphaEarth
    tile boundary and the points past that edge read as -128 nodata. Nothing
    in the pipeline objected; the defect only surfaced when a classifier
    refused the data much later. An AOI that misses its tile is a
    configuration error, so fail here rather than write a table that looks
    valid and is not.
    """
    values = table[list(A_COLS)].to_numpy(dtype="float32")
    nan_rows = np.isnan(values).any(axis=1)
    fraction = float(nan_rows.mean())
    if fraction > MAX_NAN_EMBEDDING_FRACTION:
        lons = table.loc[nan_rows, "lon"]
        raise ValueError(
            f"{nan_rows.sum()} of {len(table)} rows ({fraction:.1%}) have NaN "
            f"embeddings, above the {MAX_NAN_EMBEDDING_FRACTION:.0%} tolerance. "
            f"Affected longitudes span {lons.min():.4f}..{lons.max():.4f}. "
            "This usually means the AOI extends past the edge of the single "
            "AlphaEarth tile being read -- check the bbox in course.config.AREAS "
            "against the tile bounds in aef_index.parquet."
        )


def write_table(gdf: gpd.GeoDataFrame, path: Path, provenance: dict) -> None:
    """Write `gdf` as GeoParquet 1.1.0 (WKB, zstd, covering bbox) and embed
    `provenance` as JSON under the `course_provenance` Parquet key-value
    metadata key.

    Verbatim two-step pattern (geopandas 1.1.4's `to_parquet` has no
    custom-metadata argument): write first via `gdf.to_parquet(...)`, then
    re-open with `pyarrow.parquet`, inject `course_provenance` into the
    existing schema metadata (preserving the `geo` key GeoParquet already
    wrote), and rewrite.
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    gdf.to_parquet(
        path, schema_version="1.1.0", write_covering_bbox=True, compression="zstd"
    )

    table = pq.read_table(path)
    existing_metadata = table.schema.metadata or {}
    pq.write_table(
        table.replace_schema_metadata(
            {**existing_metadata, b"course_provenance": json.dumps(provenance).encode()}
        ),
        path,
    )


def _git_sha() -> str:
    """Best-effort `git rev-parse HEAD`; `"unknown"` if git is unavailable
    or this is not a git checkout (never raises)."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return "unknown"


def write_manifest(entries: list[dict], out_path: Path) -> None:
    """Write `out_path` (JSON): `{filename: {sha256, rows, built_at,
    builder_git_sha}}`, one entry per already-written parquet file.

    Each `entry` must carry at least `path` (a `Path` to an
    already-written file). `sha256` is always computed directly from
    `path.read_bytes()` -- never hand-entered or copied from a prior run
    (T-02-18 mitigation).
    """
    git_sha = _git_sha()
    built_at = datetime.now(UTC).isoformat()

    manifest: dict = {}
    for entry in entries:
        path = Path(entry["path"])
        sha256 = hashlib.sha256(path.read_bytes()).hexdigest()
        rows = pq.read_table(path).num_rows
        manifest[path.name] = {
            "sha256": sha256,
            "rows": rows,
            "built_at": built_at,
            "builder_git_sha": git_sha,
        }

    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(manifest, indent=2))

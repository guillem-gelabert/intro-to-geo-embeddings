"""CLI orchestrator: build the frozen per-(area, year) GeoParquet tables
from the three extraction modules, then the top-level `manifest.json` and
`DATA_CARD.md` covering every table written so far (02-09-PLAN.md Task 3;
DATA-01/02/05/06/07/09).

    python -m pipeline.build --area bern --years 2018 2021 2024

Orchestration per area: `generate_sample_points` once, `attach_labels`
once (label/validation are year-independent), then per requested year --
AlphaEarth extraction, `attach_s2`, `assemble_table`, a per-table
`course_provenance` dict, `write_table`.

Idempotency: the AlphaEarth window read is the slow step (190-342s per
02-RESEARCH.md for a full-AOI read) -- `_extract_aef_cached` caches the
raw window (and the tile lookup that finds it) under
`{out_dir}/raw/{area}/{year}/` so a re-invocation (e.g. retrying after a
transient failure on a later year) never re-fetches an already-cached
(area, year) window. This deliberately duplicates
`pipeline.extract_aef.extract_area_year`'s own find_tile/read_window/
dequantize_aef/sample_points_from_window sequence with a cache check
inserted between the network read and the dequantization step --
`pipeline/extract_aef.py` itself is intentionally left unmodified (it is
not in this plan's `files_modified`, and Plan 02-07's own call-count
tests must keep passing unchanged against it).

`manifest.json` and `DATA_CARD.md` are rebuilt from a full re-scan of
`{out_dir}` on every invocation (not just the current run's area) --
they are top-level artifacts covering all regions/years already written
to disk, matching ARCHITECTURE.md's structure tree.
"""

from __future__ import annotations

import argparse
import json
import os
from datetime import UTC, datetime
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
import pyarrow.parquet as pq
from affine import Affine
from rasterio.crs import CRS

from course.config import ANCHOR_YEARS, AREAS, COURSE_RELEASE, DATA_DIR

# Defensive GDAL retry/timeout tuning for the large (hundreds-of-MB) AEF
# window reads: a live full-AOI regeneration run measured this session hit
# a transient `RasterioIOError` ("Read failed") after several minutes on
# GDAL's default (unset) retry policy against
# storage.googleapis.com -- setting GDAL_HTTP_MAX_RETRY/RETRY_DELAY/TIMEOUT
# resolved it on the very next attempt (same URL, same window). A real
# build touches 6 area-years, each a multi-hundred-second remote read
# (02-RESEARCH.md: 311-342s measured); without this, one transient network
# hiccup on any of the six aborts the whole invocation. `setdefault` so an
# operator's own environment always wins.
os.environ.setdefault("GDAL_HTTP_MAX_RETRY", "5")
os.environ.setdefault("GDAL_HTTP_RETRY_DELAY", "2")
os.environ.setdefault("GDAL_HTTP_TIMEOUT", "180")
from course.embeddings import dequantize_aef
from course.live.aef_cog import find_tile, read_window, sample_points_from_window
from course.live.labels import EEA_IMD_BASE, WORLDCOVER_BASE, worldcover_tile_name
from course.schema import A_COLS
from pipeline.attach_labels import attach_labels
from pipeline.attach_s2 import attach_s2
from pipeline.data_card import (
    ALPHAEARTH_ATTRIBUTION,
    ALPHAEARTH_LICENSE,
    HRL_ATTRIBUTION,
    HRL_LICENSE,
    SENTINEL2_ATTRIBUTION_TEMPLATE,
    SENTINEL2_LICENSE,
    WORLDCOVER_ATTRIBUTION,
    WORLDCOVER_LICENSE,
    render_data_card,
)
from pipeline.sample_design import generate_sample_points
from pipeline.write import assemble_table, write_manifest, write_table

# AEF GCS COGs carry no DATASET_VERSION TIFF tag (02-RESEARCH.md Pitfall 6 /
# T-02-20) -- this is hand-recorded from the EE catalog page value known at
# research time, not read from the source itself.
AEF_DATASET_VERSION = "1.1"


def _window_cache_path(out_dir: Path, area: str, year: int) -> Path:
    return out_dir / "raw" / area / str(year) / "window.npz"


def _tile_cache_path(out_dir: Path, area: str, year: int) -> Path:
    return out_dir / "raw" / area / str(year) / "tile.json"


def _extract_aef_cached(
    area: str, year: int, points: gpd.GeoDataFrame, out_dir: Path
) -> tuple[pd.DataFrame, dict]:
    """AlphaEarth `A00..A63` extraction for `(area, year)`, with the raw
    AOI window (and the tile lookup that found it) cached on disk so a
    re-invocation never re-fetches an already-built (area, year).

    Returns `(df, tile)`: `df` matches
    `pipeline.extract_aef.extract_area_year`'s return contract
    (`sample_id` + `A00..A63`, `points`' original row order); `tile` is
    `{"utm_zone", "crs", "url"}` (from cache on a hit, from `find_tile` on
    a miss).
    """
    window_cache = _window_cache_path(out_dir, area, year)
    tile_cache = _tile_cache_path(out_dir, area, year)

    if (
        window_cache.exists()
        and window_cache.stat().st_size > 0
        and tile_cache.exists()
    ):
        with np.load(window_cache) as cached:
            raw = cached["raw"]
            transform = Affine(*cached["transform"].tolist())
        tile = json.loads(tile_cache.read_text())
    else:
        center_lon = float(points["lon"].iloc[0])
        center_lat = float(points["lat"].iloc[0])
        tile = find_tile(center_lon, center_lat, year)
        bbox_4326 = AREAS[area]["bbox_4326"]
        raw, transform = read_window(tile["url"], bbox_4326, dst_crs=tile["crs"])

        window_cache.parent.mkdir(parents=True, exist_ok=True)
        np.savez(window_cache, raw=raw, transform=np.asarray(transform)[:6])
        tile_cache.write_text(json.dumps(tile))

    raw_unit = dequantize_aef(raw)

    tile_crs = CRS.from_user_input(tile["crs"])
    area_crs = CRS.from_user_input(AREAS[area]["epsg"])
    has_projected_xy = "x" in points.columns and "y" in points.columns
    reuse_xy = has_projected_xy and tile_crs == area_crs

    if reuse_xy:
        points_xy = points[["x", "y"]].to_numpy(dtype=np.float64)
    else:
        reprojected = gpd.GeoSeries(
            gpd.points_from_xy(points["lon"], points["lat"]), crs="EPSG:4326"
        ).to_crs(tile_crs)
        points_xy = np.column_stack(
            [reprojected.x.to_numpy(), reprojected.y.to_numpy()]
        )

    vectors = sample_points_from_window(raw_unit, transform, points_xy)
    result = pd.DataFrame(vectors, columns=A_COLS)
    result.insert(0, "sample_id", points["sample_id"].to_numpy())
    return result, tile


def _build_provenance(
    area: str,
    year: int,
    tile: dict,
    labels_gdf: gpd.GeoDataFrame,
    s2_df: pd.DataFrame,
    n_rows: int,
) -> dict:
    """Build the per-table `course_provenance` dict (DATA-05): embedding
    product, dataset version, year, extraction date, source paths/tile
    URL/scene IDs, sampling method, CRS, label source, validation source,
    license, attribution, creator -- every value pulled from the actual
    sources used for this table, not a placeholder.
    """
    min_lon, min_lat, max_lon, max_lat = AREAS[area]["bbox_4326"]
    worldcover_tile = worldcover_tile_name(
        (min_lon + max_lon) / 2, (min_lat + max_lat) / 2
    )

    return {
        "embedding_product": "AlphaEarth Foundations Satellite Embedding v1 (annual)",
        "dataset_version": AEF_DATASET_VERSION,
        "dataset_version_note": (
            "hand-recorded; AlphaEarth GCS COGs carry no DATASET_VERSION "
            "TIFF tag (02-RESEARCH.md Pitfall 6)"
        ),
        "region": area,
        "year": year,
        "extraction_date": datetime.now(UTC).date().isoformat(),
        "n_rows": n_rows,
        "crs": "EPSG:4326",
        "sampling_method": (
            "stratified by ESA WorldCover 2021 class, capped per class, "
            "50m minimum-spacing candidate grid, seeded (pipeline/areas.yaml)"
        ),
        "source_aef_tile_url": tile["url"],
        "source_worldcover_url": (
            f"{WORLDCOVER_BASE}/ESA_WorldCover_10m_2021_v200_{worldcover_tile}_Map.tif"
        ),
        "source_hrl_imperviousness_url": f"{EEA_IMD_BASE}/exportImage",
        "source_s2_item_ids": list(s2_df.attrs.get("s2_item_ids", [])),
        "label_source": str(labels_gdf["label_source"].iloc[0]),
        "validation_source": str(labels_gdf["validation_source"].iloc[0]),
        "license_alphaearth": ALPHAEARTH_LICENSE,
        "attribution_alphaearth": ALPHAEARTH_ATTRIBUTION,
        "license_worldcover": WORLDCOVER_LICENSE,
        "attribution_worldcover": WORLDCOVER_ATTRIBUTION,
        "license_hrl_imperviousness": HRL_LICENSE,
        "attribution_hrl_imperviousness": HRL_ATTRIBUTION,
        "license_sentinel2": SENTINEL2_LICENSE,
        "attribution_sentinel2": SENTINEL2_ATTRIBUTION_TEMPLATE.format(year=year),
        "created_by": "Introduction to Geospatial Embeddings course pipeline (pipeline.build)",
        "course_release": COURSE_RELEASE,
    }


def _table_path(out_dir: Path, area: str, year: int) -> Path:
    return out_dir / area / f"{area}_aef_{year}_v1.1.parquet"


def build_area(area: str, years: list[int], out_dir: Path) -> None:
    """Build and write every requested `(area, year)` table for one region.

    `generate_sample_points` and `attach_labels` each run exactly once for
    the whole `years` list (label/validation are year-independent); the
    AlphaEarth window read is the only per-year step cached on disk (see
    `_extract_aef_cached`).
    """
    points = generate_sample_points(area)
    labels_gdf = attach_labels(area, points)

    for year in years:
        aef_df, tile = _extract_aef_cached(area, year, points, out_dir)
        s2_df = attach_s2(area, year, points)
        table = assemble_table(points, aef_df, labels_gdf, s2_df, year)

        provenance = _build_provenance(area, year, tile, labels_gdf, s2_df, len(table))
        write_table(table, _table_path(out_dir, area, year), provenance)


def _discover_all_tables(out_dir: Path) -> list[Path]:
    """Every already-written frozen table under `out_dir`, across ALL
    areas/years -- not just the current invocation's `--area`."""
    return sorted(out_dir.glob("*/*_aef_*_v1.1.parquet"))


def _read_provenance(path: Path) -> dict:
    table = pq.read_table(path)
    return json.loads(table.schema.metadata[b"course_provenance"])


def run(area: str, years: list[int], out_dir: Path) -> list[dict]:
    """Build `area`'s requested years, then rebuild the top-level
    `manifest.json`/`DATA_CARD.md` from a full re-scan of `out_dir` (every
    area/year already on disk, not just this run's) so a multi-invocation
    build (one `--area` at a time) ends with artifacts covering everything
    built so far. Returns the full list of provenance dicts used."""
    out_dir = Path(out_dir)
    build_area(area, years, out_dir)

    all_paths = _discover_all_tables(out_dir)
    provenance_records = [_read_provenance(p) for p in all_paths]

    write_manifest([{"path": p} for p in all_paths], out_dir / "manifest.json")
    (out_dir / "DATA_CARD.md").write_text(render_data_card(provenance_records))

    return provenance_records


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        prog="python -m pipeline.build",
        description=(
            "Build the frozen per-(area, year) GeoParquet teaching tables "
            "from public, no-login-required sources."
        ),
    )
    parser.add_argument(
        "--area",
        required=True,
        choices=sorted(AREAS),
        help="Study region to build (bern or seville).",
    )
    parser.add_argument(
        "--years",
        nargs="+",
        type=int,
        default=list(ANCHOR_YEARS),
        help=f"Anchor years to build (default: {list(ANCHOR_YEARS)}).",
    )
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=Path(DATA_DIR),
        help=f"Output directory (default: {DATA_DIR!r}).",
    )
    args = parser.parse_args(argv)

    run(area=args.area, years=args.years, out_dir=args.out_dir)


if __name__ == "__main__":
    main()

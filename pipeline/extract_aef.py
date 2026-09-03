"""AlphaEarth embedding extraction: one windowed read per (area, year), then
array-indexed sampling for every fixed sample point.

`extract_area_year` is the only place in this phase that turns the fixed
sample-point set (`pipeline.sample_design.generate_sample_points`) into
`A00..A63` embedding values. It calls `course.live.aef_cog.find_tile` and
`course.live.aef_cog.read_window` exactly ONCE per (area, year), then
`course.embeddings.dequantize_aef` exactly ONCE on the whole window, then
`course.live.aef_cog.sample_points_from_window` exactly ONCE with the full
point array -- never a per-point remote fetch (02-RESEARCH.md "Extraction
Mechanics" #4, PITFALLS.md Pitfall 4: scattered `.sample()` calls against a
remote COG cost 0.3-0.7 seconds PER POINT).
"""

from __future__ import annotations

import geopandas as gpd
import numpy as np
import pandas as pd
from rasterio.crs import CRS

from course.config import AREAS
from course.embeddings import dequantize_aef
from course.live.aef_cog import find_tile, read_window, sample_points_from_window
from course.schema import A_COLS


def extract_area_year(
    area: str,
    year: int,
    points: gpd.GeoDataFrame,
    bbox_4326: tuple[float, float, float, float] | None = None,
) -> pd.DataFrame:
    """Extract AlphaEarth `A00..A63` embeddings for every point in `points`.

    `points` must carry `sample_id`, `lon`, `lat` columns (EPSG:4326) and MAY
    carry `x`/`y` columns already projected into the region's UTM CRS
    (`course.config.AREAS[area]["epsg"]`), as produced by
    `pipeline.sample_design.generate_sample_points`.

    `bbox_4326` defaults to `course.config.AREAS[area]["bbox_4326"]` (the
    region's full AOI); callers may pass a smaller sub-bbox explicitly (e.g.
    a live-network test scoped to ~200m x 200m around a handful of points --
    a full-AOI window read measured 311-342s in 02-RESEARCH.md).

    Reads exactly ONE bounded window for `(area, year)` via `find_tile` +
    `read_window`, dequantizes it exactly ONCE via `dequantize_aef`, then
    indexes every point out of that single in-memory array via
    `sample_points_from_window`.

    If `points` already carries `x`/`y` columns AND those columns are
    already in the SAME CRS the AlphaEarth tile is served in (`tile["crs"]`,
    compared via `rasterio.crs.CRS` equality, not string equality), they are
    reused directly -- no second reprojection. Otherwise `lon`/`lat` are
    explicitly reprojected into the tile's CRS; a mismatched CRS is never
    silently reused.

    Returns a `pd.DataFrame` with `sample_id` and `A00..A63`
    (`course.schema.A_COLS`) columns, one row per input point, in `points`'
    original row order.
    """
    if bbox_4326 is None:
        bbox_4326 = AREAS[area]["bbox_4326"]

    center_lon = float(points["lon"].iloc[0])
    center_lat = float(points["lat"].iloc[0])
    tile = find_tile(center_lon, center_lat, year)

    raw, window_transform = read_window(tile["url"], bbox_4326, dst_crs=tile["crs"])
    raw_unit = dequantize_aef(raw)

    tile_crs = CRS.from_user_input(tile["crs"])
    has_projected_xy = "x" in points.columns and "y" in points.columns
    area_crs = CRS.from_user_input(AREAS[area]["epsg"])
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

    vectors = sample_points_from_window(raw_unit, window_transform, points_xy)

    result = pd.DataFrame(vectors, columns=A_COLS)
    result.insert(0, "sample_id", points["sample_id"].to_numpy())
    return result

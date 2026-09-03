"""AlphaEarth COG adapter: tile lookup, windowed reads, and point sampling.

This module is the only place in the project that talks to the live
AlphaEarth GCS bucket. Every extraction in this phase, and Module 2's Path A'
in a later phase, reuse it rather than re-implementing tile lookup or window
reads. See 02-RESEARCH.md "Extraction Mechanics, Verified End to End" for the
verified working code this module implements against.

Two pitfalls this module exists specifically to avoid:
- Pitfall 2 ("bottom-up COGs"): Google's AlphaEarth COGs have a positive
  transform.e (bottom-up). Reading windows from the raw dataset either
  raises or silently returns a garbage/zero-size window. `read_window`
  always wraps the dataset in a `WarpedVRT(ds, crs=ds.crs)` before windowing.
- Pitfall 4 ("scattered point sampling is catastrophically slow"): looping
  `.sample()` over a remote COG costs 0.3-0.7 seconds PER POINT. This module
  reads one bounded window per (region, year) via `read_window`, and
  `sample_points_from_window` extracts every point by indexing that
  already-fetched in-memory array — it never re-queries the remote COG.
"""

from __future__ import annotations

import numpy as np
import rasterio
from rasterio.crs import CRS
from rasterio.vrt import WarpedVRT
from rasterio.warp import transform_bounds
from rasterio.windows import from_bounds

from course.live import LiveSourceUnavailable

AEF_INDEX_URL = "https://data.source.coop/tge-labs/aef/v1/annual/aef_index.parquet"
AEF_GCS_BASE = (
    "https://storage.googleapis.com/alphaearth_foundations/satellite_embedding/v1/annual"
)


def find_tile(lon: float, lat: float, year: int) -> dict:
    """Find the AlphaEarth GCS tile covering (lon, lat) for `year`.

    Queries the public `aef_index.parquet` GeoParquet index via DuckDB's
    `httpfs`+`spatial` extensions (02-RESEARCH.md "Extraction Mechanics"
    step 1) — this never downloads a tile, only looks up which one to read.

    Returns `{"utm_zone": ..., "crs": ..., "url": ...}` where `url` is the
    full path to the tile on the AlphaEarth GCS bucket.

    Raises `LiveSourceUnavailable` if `duckdb` is not installed (it lives
    behind the `providers` optional-dependencies extra per ENV-05/T-01-10 —
    `course.live.aef_cog` itself must stay importable without it, only this
    function needs it), if the index query fails (network or DuckDB error),
    or if no tile covers this (lon, lat, year).
    """
    try:
        import duckdb
    except ImportError as exc:
        raise LiveSourceUnavailable(
            "duckdb is required for AlphaEarth tile lookup; install the "
            "'providers' extra (uv sync --extra providers)"
        ) from exc

    query = """
        SELECT utm_zone, crs, path
        FROM read_parquet(?)
        WHERE year = ?
          AND ST_Contains(geom, ST_Point(?, ?))
    """
    try:
        con = duckdb.connect()
        con.execute(
            "INSTALL httpfs; LOAD httpfs; INSTALL spatial; LOAD spatial; "
            "SET enable_progress_bar=false;"
        )
        rows = con.execute(query, [AEF_INDEX_URL, year, lon, lat]).fetchall()
    except duckdb.Error as exc:
        raise LiveSourceUnavailable(
            f"AlphaEarth tile index query failed for lon={lon}, lat={lat}, "
            f"year={year}: {exc}"
        ) from exc

    if not rows:
        raise LiveSourceUnavailable(
            f"no AlphaEarth tile found for lon={lon}, lat={lat}, year={year}"
        )

    utm_zone, crs, path = rows[0]
    filename = path.rsplit("/", 1)[-1]
    url = f"{AEF_GCS_BASE}/{year}/{utm_zone}/{filename}"
    return {"utm_zone": utm_zone, "crs": crs, "url": url}


def read_window(
    url: str,
    bbox_4326: tuple[float, float, float, float],
    dst_crs: str,
) -> tuple[np.ndarray, rasterio.Affine]:
    """Read one bounded AOI window from a remote AlphaEarth COG, north-up.

    `url` is opened via GDAL's `/vsicurl/` virtual file system (plain HTTPS,
    no credentials). `bbox_4326` is `(min_lon, min_lat, max_lon, max_lat)`.

    `dst_crs` is the CRS the caller expects this tile to be in (e.g. an
    area's registered `epsg` from `course.config.AREAS`) — it is compared
    against the opened tile's own CRS as a defensive check (ASVS V5: a tile
    in an unexpected CRS is a structurally wrong response, the same class of
    problem the threat model's T-02-03 mitigation targets). The actual
    orientation fix always reprojects into the tile's OWN native CRS via
    `WarpedVRT(ds, crs=ds.crs)`, per 02-RESEARCH.md step 2 — never into an
    arbitrary target CRS.

    Google's AlphaEarth COGs are bottom-up (positive `transform.e`).
    `rasterio.windows.from_bounds` against the raw dataset either raises or
    silently returns a garbage/zero-size window. `WarpedVRT(ds, crs=ds.crs)`
    flips the transform to north-up before any windowing happens — this
    function only ever reads from `vrt`, never from `ds` directly.

    The window offsets/lengths are rounded (`.round_offsets().round_lengths()`)
    because fractional offsets resample on a shifted grid (02-RESEARCH.md).

    Returns `(raw, window_transform)`: `raw` is `(64, H, W)` int8, nodata
    -128; `window_transform` is the rasterio `Affine` for that window, used
    by `sample_points_from_window` to map point coordinates to array
    indices.
    """
    try:
        with (
            rasterio.open(f"/vsicurl/{url}") as ds,
            WarpedVRT(ds, crs=ds.crs) as vrt,
        ):
            expected_crs = CRS.from_user_input(dst_crs)
            if vrt.crs != expected_crs:
                raise LiveSourceUnavailable(
                    f"tile at {url} is in CRS {vrt.crs}, expected {dst_crs}"
                )
            utm_bbox = transform_bounds("EPSG:4326", vrt.crs, *bbox_4326)
            win = (
                from_bounds(*utm_bbox, vrt.transform)
                .round_offsets()
                .round_lengths()
            )
            raw = vrt.read(window=win)
            window_transform = vrt.window_transform(win)
    except rasterio.errors.RasterioIOError as exc:
        raise LiveSourceUnavailable(
            f"could not read AlphaEarth tile at {url}: {exc}"
        ) from exc

    return raw, window_transform

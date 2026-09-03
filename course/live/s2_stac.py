"""Sentinel-2 L2A raw-band adapter over Earth Search STAC.

Provides `search_scenes` (STAC scene search), `select_scenes` (deterministic
duplicate-item resolution), and `sample_bands` (SCL-masked, point-sampled
reflectance with a defensive plausibility assertion).

Two empirically-discovered correctness traps this module exists to avoid
(02-RESEARCH.md "Extraction Mechanics, Verified End to End" step 6):

1. Earth Search's `sentinel-2-l2a` collection carries duplicate items for
   some archive dates (e.g. `..._0_L2A` original processing vs `..._1_L2A`
   Element84 reprocessing) — a naive search can return both for one date.
2. The collection's `raster:bands.offset` / `earthsearch:boa_offset_applied`
   metadata is contradictory: applying the documented offset produced
   implausible reflectance across three scenes of different processing
   baselines at the same ground point; not applying it produced consistent,
   plausible values. This module never subtracts the offset and instead
   asserts the computed reflectance lands in a physically plausible range,
   so the pipeline is correct regardless of which way the upstream metadata
   convention eventually settles.
"""

import calendar
from datetime import date, datetime

import numpy as np
import pandas as pd
import rasterio
import requests
from rasterio.warp import transform as warp_transform

from course.live import LiveSourceUnavailable
from course.schema import S2_COLS

STAC_SEARCH_URL = "https://earth-search.aws.element84.com/v1/search"
COLLECTION = "sentinel-2-l2a"

# Earth Search asset keys use band common names, not Sentinel-2 band codes
# (verified live against the collection this session) — map the course's
# B02.. band-code vocabulary onto them.
BAND_ASSET_KEYS = {
    "B02": "blue",
    "B03": "green",
    "B04": "red",
    "B08": "nir",
    "B11": "swir16",
    "B12": "swir22",
}

# The date Element84's reprocessing note (02-RESEARCH.md §6) associates with
# the pre-/post-baseline-04 archive split; used only to decide which
# duplicate-item convention to prefer when a date carries more than one item.
DEDUP_BASELINE_CUTOVER = date(2022, 1, 25)

# SCL class codes to mask before compositing (cloud shadow, cloud medium/high
# probability, thin cirrus) — per plan spec, keep everything else including
# 0 (no data) and 11 (snow/ice).
SCL_MASK_CLASSES = frozenset({3, 8, 9, 10})


def _item_datetime(item: dict) -> datetime:
    return datetime.fromisoformat(item["properties"]["datetime"])


def _item_cloud_cover(item: dict) -> float:
    return item["properties"]["eo:cloud_cover"]


def search_scenes(
    bbox_4326: tuple,
    year: int,
    months: tuple[int, int] = (6, 8),
    cloud_lt: float = 10.0,
) -> list[dict]:
    """POST a Sentinel-2 L2A scene search to Earth Search STAC.

    Returns the raw `features` list. Raises `LiveSourceUnavailable` if the
    request fails or returns zero features.

    Deviation from the plan's literal datetime string
    (`f"{year}-{months[0]:02d}-01/{year}-{months[1]:02d}-31"`): verified live
    against this endpoint, a date-only range is rejected with "datetime
    value is invalid, does not match RFC3339 format", and a hardcoded day
    31 is invalid for any end month with fewer than 31 days. Fixed by
    emitting full RFC3339 datetimes with `calendar.monthrange` computing the
    end month's actual last day.
    """
    start_month, end_month = months
    last_day = calendar.monthrange(year, end_month)[1]
    datetime_range = (
        f"{year}-{start_month:02d}-01T00:00:00Z/"
        f"{year}-{end_month:02d}-{last_day:02d}T23:59:59Z"
    )
    body = {
        "collections": [COLLECTION],
        "bbox": list(bbox_4326),
        "datetime": datetime_range,
        "query": {"eo:cloud_cover": {"lt": cloud_lt}},
        "limit": 20,
    }
    try:
        response = requests.post(STAC_SEARCH_URL, json=body, timeout=30)
        response.raise_for_status()
        features = response.json()["features"]
    except (requests.RequestException, KeyError, ValueError) as exc:
        raise LiveSourceUnavailable(
            f"Earth Search STAC request failed for bbox={bbox_4326} "
            f"year={year} months={months} cloud_lt={cloud_lt}: {exc}"
        ) from exc

    if not features:
        raise LiveSourceUnavailable(
            f"No Sentinel-2 L2A scenes found for bbox={bbox_4326} year={year} "
            f"months={months} cloud_lt={cloud_lt}"
        )
    return features


def select_scenes(items: list[dict]) -> list[dict]:
    """Deterministically resolve duplicate same-date archive items.

    Groups items by acquisition date. Within a date-group with more than one
    item: for dates before 2022-01-25, prefer the item whose `id` contains
    `_0_` (original processing); otherwise prefer the lowest `eo:cloud_cover`.
    Ties are broken by sorting `id` ascending. Returns one item per unique
    date, sorted by `eo:cloud_cover` ascending overall.
    """
    groups: dict[date, list[dict]] = {}
    for item in items:
        acquisition_date = _item_datetime(item).date()
        groups.setdefault(acquisition_date, []).append(item)

    selected: list[dict] = []
    for acquisition_date, group in groups.items():
        if len(group) == 1:
            selected.append(group[0])
            continue

        if acquisition_date < DEDUP_BASELINE_CUTOVER:
            zero_items = [it for it in group if "_0_" in it["id"]]
            candidates = zero_items if zero_items else group
        else:
            min_cloud = min(_item_cloud_cover(it) for it in group)
            candidates = [it for it in group if _item_cloud_cover(it) == min_cloud]

        selected.append(min(candidates, key=lambda it: it["id"]))

    selected.sort(key=_item_cloud_cover)
    return selected


def _apply_scale(dn: np.ndarray, scale: float) -> np.ndarray:
    """Scale raw digital numbers to reflectance.

    Deliberately does NOT subtract any `offset` from `raster:bands` metadata
    — see module docstring and 02-RESEARCH.md Extraction Mechanics §6: this
    collection's offset metadata is contradictory, and applying it produces
    implausible reflectance. Only `scale` (documented and verified
    consistent at 0.0001 for every checked asset) is applied.
    """
    return dn.astype(np.float32) * np.float32(scale)


def _assert_plausible_reflectance(values: np.ndarray) -> None:
    """Defensive check: fail loudly if mean reflectance falls outside a
    physically plausible surface-reflectance range, regardless of which
    offset convention upstream metadata claims to use."""
    finite = values[np.isfinite(values)]
    mean = float(np.mean(finite)) if finite.size else float("nan")
    assert -0.05 < mean < 0.6, (
        "Sentinel-2 reflectance out of plausible range — check offset "
        f"handling (mean={mean:.4f})"
    )


def _asset_href(item: dict, asset_key: str) -> str:
    try:
        return item["assets"][asset_key]["href"]
    except KeyError as exc:
        raise LiveSourceUnavailable(
            f"item {item.get('id')!r} has no asset {asset_key!r}"
        ) from exc


def _asset_scale(item: dict, asset_key: str) -> float:
    try:
        return float(item["assets"][asset_key]["raster:bands"][0]["scale"])
    except (KeyError, IndexError) as exc:
        raise LiveSourceUnavailable(
            f"item {item.get('id')!r} asset {asset_key!r} has no raster:bands scale"
        ) from exc


def _sample_at_points(href: str, points_lonlat: np.ndarray) -> np.ndarray:
    """Read one dataset's first band at each lon/lat point, reprojecting the
    points into the dataset's own CRS (as verified necessary in
    02-RESEARCH.md Extraction Mechanics §2). Returns float64 values, with the
    dataset's nodata value (if any) mapped to NaN."""
    try:
        with rasterio.open(href) as ds:
            xs, ys = warp_transform(
                "EPSG:4326",
                ds.crs,
                points_lonlat[:, 0].tolist(),
                points_lonlat[:, 1].tolist(),
            )
            values = np.array([v[0] for v in ds.sample(zip(xs, ys))], dtype=np.float64)
            if ds.nodata is not None:
                values = np.where(values == ds.nodata, np.nan, values)
    except rasterio.errors.RasterioIOError as exc:
        raise LiveSourceUnavailable(f"failed to read {href}: {exc}") from exc
    return values


def sample_bands(
    items: list[dict],
    points_lonlat: np.ndarray,
    bands: tuple[str, ...] = ("B02", "B03", "B04", "B08", "B11", "B12"),
) -> pd.DataFrame:
    """SCL-masked, point-sampled Sentinel-2 reflectance composited across
    scenes.

    For each item (scene), each requested band's COG asset is read at every
    point, scaled by `raster:bands.scale` with NO offset subtraction (see
    `_apply_scale`), and pixels whose SCL class is in `SCL_MASK_CLASSES` are
    dropped before compositing. The per-point median across contributing
    scenes is returned, one row per point, columns `S2_B02..S2_B12` (matching
    `course.schema.S2_COLS`) plus `s2_n_scenes` (nodata-aware count of scenes
    that contributed at least one unmasked band reading to that point).

    After computing the full output, asserts mean reflectance across all
    bands/points falls in a physically plausible range — see
    `_assert_plausible_reflectance` and the module docstring.
    """
    points_lonlat = np.asarray(points_lonlat, dtype=np.float64)
    n_points = points_lonlat.shape[0]

    band_readings: dict[str, list[list[float]]] = {
        b: [[] for _ in range(n_points)] for b in bands
    }
    scene_contributed = np.zeros((len(items), n_points), dtype=bool)

    for scene_idx, item in enumerate(items):
        scl_href = _asset_href(item, "scl")
        scl_values = _sample_at_points(scl_href, points_lonlat)
        valid_scl = ~np.isin(scl_values, list(SCL_MASK_CLASSES)) & np.isfinite(
            scl_values
        )

        for band in bands:
            asset_key = BAND_ASSET_KEYS[band]
            dn = _sample_at_points(_asset_href(item, asset_key), points_lonlat)
            scale = _asset_scale(item, asset_key)
            reflectance = _apply_scale(dn, scale)

            for point_idx in range(n_points):
                if valid_scl[point_idx] and np.isfinite(reflectance[point_idx]):
                    band_readings[band][point_idx].append(float(reflectance[point_idx]))
                    scene_contributed[scene_idx, point_idx] = True

    data = {}
    for band in bands:
        col = f"S2_{band}"
        data[col] = np.array(
            [np.median(values) if values else np.nan for values in band_readings[band]],
            dtype=np.float32,
        )
    data["s2_n_scenes"] = scene_contributed.sum(axis=0)

    result = pd.DataFrame(data, columns=[*[f"S2_{b}" for b in bands], "s2_n_scenes"])

    band_cols = [c for c in result.columns if c in S2_COLS]
    _assert_plausible_reflectance(result[band_cols].to_numpy(dtype=np.float64))

    return result

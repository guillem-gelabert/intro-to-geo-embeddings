"""Stratified, capped, seed-stable sample point design for the frozen datasets.

``generate_sample_points(area)`` is the single entry point: it reads one
bounded ESA WorldCover window per region (never a per-point network loop,
02-RESEARCH.md Extraction Mechanics #4), builds a regular candidate grid at
``min_spacing_m`` spacing over the in-memory class-code array, stratifies by
the course's 5-class teaching label with per-label caps (clamped to whatever
pool actually exists, per-region -- Bern's 219-candidate ``bare`` pool is the
binding example, 02-RESEARCH.md "Class pool sizes"), and assigns:

- a stable ``sample_id`` (0..N-1), assigned by sorting selected candidates on
  ``(label, row, col)`` -- not insertion/draw order -- so a re-run at the same
  seed reproduces an identical ``sample_id`` -> ``(lon, lat)`` mapping. This is
  what lets 2018/2021/2024 extraction tables join on ``sample_id`` (DATA-03).
- a ``block_id`` computed from a fixed-size grid in the region's own
  projected UTM CRS (``course.config.AREAS[area]["epsg"]``), never in
  degrees (PITFALLS.md Pitfall 3 / this phase's Pitfall 3 analogue -- block
  geometry must be computed in a projected CRS or cell sizes distort with
  latitude).

The WorldCover -> course-label mapping itself (``worldcover_class`` code ->
``label``) is deliberately NOT resolved here -- only the raw code is carried
through, so the one-per-region WorldCover fetch this module already does is
never repeated by Plan 02-07's label-attachment step.
"""

from pathlib import Path

import geopandas as gpd
import numpy as np
import yaml
from rasterio.transform import xy
from shapely.geometry import Point

from course.config import AREAS
from course.live.labels import class_to_label, worldcover_window

AREAS_YAML_PATH = Path(__file__).parent / "areas.yaml"

# WorldCover 2021 v200 native resolution. Candidate-grid spacing
# (``min_spacing_m``) is expressed in meters and converted to a pixel
# stride against this constant -- see module docstring and
# 02-RESEARCH.md Extraction Mechanics #4.
WORLDCOVER_RESOLUTION_M = 10


def _load_pipeline_areas(path: Path = AREAS_YAML_PATH) -> dict:
    """Load per-region sampling parameters from ``pipeline/areas.yaml``."""
    with open(path) as f:
        return yaml.safe_load(f)


def _candidate_grid(arr: np.ndarray, min_spacing_m: float):
    """Build a regular (row, col) candidate grid over ``arr`` at ``min_spacing_m``.

    Returns ``(rows, cols, codes)`` as flat 1-D arrays: every ``stride``-th
    pixel in each direction, where ``stride`` is ``min_spacing_m`` converted
    to whole WorldCover pixels (10 m/px).
    """
    stride = max(1, round(min_spacing_m / WORLDCOVER_RESOLUTION_M))
    row_idx = np.arange(0, arr.shape[0], stride)
    col_idx = np.arange(0, arr.shape[1], stride)
    row_grid, col_grid = np.meshgrid(row_idx, col_idx, indexing="ij")
    rows = row_grid.ravel()
    cols = col_grid.ravel()
    codes = arr[rows, cols]
    return rows, cols, codes


def _labels_for_codes(codes: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Map raw WorldCover codes to course labels via ``class_to_label``.

    Returns ``(labels, valid_mask)`` -- any code with no course-label
    mapping is marked invalid rather than raising, since a stratified
    sampler should not abort a whole region's design over one unexpected
    pixel (defensive; ``class_to_label`` covers all 11 official WorldCover
    codes, so this should not fire on real data).
    """
    labels = np.empty(codes.shape, dtype=object)
    valid = np.ones(codes.shape, dtype=bool)
    for i, code in enumerate(codes):
        try:
            labels[i] = class_to_label(int(code))
        except KeyError:
            valid[i] = False
    return labels, valid


def _stratified_indices(labels: np.ndarray, class_caps: dict, seed: int) -> np.ndarray:
    """Draw up to ``class_caps[label]`` indices per label, never unseeded.

    Labels whose candidate pool is smaller than the cap take the whole pool
    (T-02-13 mitigation: never raise or duplicate points to hit the cap).
    """
    rng = np.random.default_rng(seed)
    selected = []
    for label, cap in class_caps.items():
        pool = np.flatnonzero(labels == label)
        if pool.size == 0:
            continue
        n_take = min(cap, pool.size)
        chosen = rng.choice(pool, size=n_take, replace=False)
        selected.append(chosen)
    if not selected:
        return np.array([], dtype=int)
    return np.concatenate(selected)


def generate_sample_points(area: str) -> gpd.GeoDataFrame:
    """Draw the fixed, stratified sample point set for one region.

    Returns a GeoDataFrame (``crs="EPSG:4326"``) with columns ``sample_id``,
    ``region``, ``lon``, ``lat``, ``worldcover_class``, ``geometry`` -- the
    fixed point set every later per-year extraction step (Plan 02-07, 02-08)
    indexes into.
    """
    pipeline_areas = _load_pipeline_areas()
    if area not in pipeline_areas:
        raise KeyError(
            f"unknown area {area!r}; pipeline/areas.yaml has {sorted(pipeline_areas)}"
        )
    if area not in AREAS:
        raise KeyError(f"unknown area {area!r} in course.config.AREAS")

    params = pipeline_areas[area]
    bbox_4326 = AREAS[area]["bbox_4326"]

    arr, transform = worldcover_window(bbox_4326)

    rows, cols, codes = _candidate_grid(arr, params["min_spacing_m"])
    labels, valid = _labels_for_codes(codes)
    rows, cols, codes, labels = rows[valid], cols[valid], codes[valid], labels[valid]

    selected = _stratified_indices(labels, params["class_caps"], params["seed"])
    sel_rows, sel_cols = rows[selected], cols[selected]
    sel_codes, sel_labels = codes[selected], labels[selected]

    # Stable ordering: sort by (label, row, col) -- NOT draw order -- before
    # assigning sample_id, so an identical selection always yields identical
    # ids regardless of the order np.random.Generator.choice returned them
    # in (see module docstring).
    order = np.lexsort((sel_cols, sel_rows, sel_labels))
    sel_rows, sel_cols = sel_rows[order], sel_cols[order]
    sel_codes = sel_codes[order]

    lon, lat = xy(transform, sel_rows, sel_cols, offset="center")
    lon, lat = np.asarray(lon, dtype=np.float64), np.asarray(lat, dtype=np.float64)

    geometry = [Point(lon_i, lat_i) for lon_i, lat_i in zip(lon, lat)]
    gdf = gpd.GeoDataFrame(
        {
            "sample_id": np.arange(len(sel_rows), dtype=np.int64),
            "region": area,
            "lon": lon,
            "lat": lat,
            "worldcover_class": sel_codes.astype(np.int64),
        },
        geometry=geometry,
        crs="EPSG:4326",
    )
    return gdf

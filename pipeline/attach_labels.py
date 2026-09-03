"""Course label plus independent validation reference attachment.

`attach_labels(area, points)` turns the fixed sample-point set's already-
present `worldcover_class` column (`pipeline.sample_design.
generate_sample_points`) into the course training label (`label` /
`label_source`), and SEPARATELY attaches an INDEPENDENT validation
reference (`imd_2018` / `validation_source`) read from EEA HRL
Imperviousness Density 2018.

These two are kept architecturally distinct (02-RESEARCH.md "Extraction
Mechanics" #5; PITFALLS.md Pitfall 6, "validation_source == label_source"):
`label_source` and `validation_source` are hardcoded, never-equal string
constants -- the pipeline cannot derive one from the other. Validating one
learned product (WorldCover) against another learned product (HRL
Imperviousness) is not independent validation; the course teaches exactly
that trap, so conflating the two columns here would undermine the lesson.

`course.live.labels.imd_2018_window` is called exactly ONCE per area, then
every point is sampled by indexing that already-fetched in-memory array
(02-RESEARCH.md Pitfall 4: scattered per-point network calls against a
remote source are catastrophically slow).
"""

from __future__ import annotations

import geopandas as gpd
import numpy as np

from course.config import AREAS
from course.live.labels import class_to_label, imd_2018_window

label_source = "esa_worldcover_2021"
validation_source = "eea_hrl_imperviousness_2018"


def _sample_single_band_window(
    arr: np.ndarray, window_transform, points_xy: np.ndarray
) -> np.ndarray:
    """Array-index a single-band raster window at N `(x, y)` points.

    Mirrors `course.live.aef_cog.sample_points_from_window`'s indexing
    logic (`round(~window_transform @ (x, y))` -> `(row, col)`), adapted for
    a 2-D single-band array instead of a `(64, H, W)` stack. `points_xy` is
    `(N, 2)` in the SAME CRS as `window_transform`. Points whose rounded
    `(row, col)` fall outside `[0, H) x [0, W)` produce `NaN` instead of
    raising or wrapping around -- this function never re-queries a remote
    source, it only indexes the array already fetched by `imd_2018_window`.
    """
    points_xy = np.asarray(points_xy, dtype=np.float64)
    n_points = points_xy.shape[0]
    height, width = arr.shape

    inv_transform = ~window_transform
    cols, rows = inv_transform @ (points_xy[:, 0], points_xy[:, 1])
    rows = np.round(rows).astype(np.int64)
    cols = np.round(cols).astype(np.int64)

    in_bounds = (rows >= 0) & (rows < height) & (cols >= 0) & (cols < width)

    result = np.full(n_points, np.nan, dtype=np.float32)
    valid_idx = np.nonzero(in_bounds)[0]
    result[valid_idx] = arr[rows[valid_idx], cols[valid_idx]].astype(np.float32)
    return result


def attach_labels(area: str, points: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """Attach the course label and an independent validation reference.

    `points` must carry a `worldcover_class` column (the raw WorldCover
    code, as produced by `pipeline.sample_design.generate_sample_points`)
    and `x`/`y` columns already projected into the region's UTM CRS
    (`course.config.AREAS[area]["epsg"]`).

    Returns `points` with four columns appended, all other columns
    preserved:
    - `label`: `course.live.labels.class_to_label(worldcover_class)`, per row
    - `label_source`: constant `"esa_worldcover_2021"`
    - `imd_2018`: 0-100 imperviousness density (or `NaN` if outside the read
      window), sampled once per area from `imd_2018_window`
    - `validation_source`: constant `"eea_hrl_imperviousness_2018"`

    `label_source` and `validation_source` are always different strings --
    this pipeline architecturally cannot derive one from the other
    (T-02-14, Pitfall 6).
    """
    result = points.copy()
    result["label"] = result["worldcover_class"].apply(
        lambda code: class_to_label(int(code))
    )
    result["label_source"] = label_source

    bbox_4326 = AREAS[area]["bbox_4326"]
    epsg = AREAS[area]["epsg"]
    arr, window_transform = imd_2018_window(bbox_4326, epsg)

    points_xy = result[["x", "y"]].to_numpy(dtype=np.float64)
    result["imd_2018"] = _sample_single_band_window(arr, window_transform, points_xy)
    result["validation_source"] = validation_source

    return result

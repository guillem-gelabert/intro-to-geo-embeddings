"""Wire the fixed sample points to Sentinel-2 raw reflectance bands, per
(area, year), reusing `course.live.s2_stac` without re-implementing any STAC
search or SCL-masking logic here (single trust boundary, see 02-08-PLAN.md's
threat model).

Provenance convention: the exact Sentinel-2 scene IDs used are attached to
the returned DataFrame's `.attrs["s2_item_ids"]` (not a second return value)
-- this keeps `attach_s2`'s return type a plain `pd.DataFrame` matching the
plan's stated interface. `pipeline/write.py` (Plan 02-09) should read
`result.attrs["s2_item_ids"]` to record scene-level provenance (T-02-17).
"""

import numpy as np
import pandas as pd

from course.config import AREAS
from course.live import LiveSourceUnavailable
from course.live.s2_stac import sample_bands, search_scenes, select_scenes
from course.schema import S2_COLS


def attach_s2(area: str, year: int, points) -> pd.DataFrame:
    """Attach Sentinel-2 raw reflectance bands to a fixed sample point set.

    Calls `search_scenes` + `select_scenes` + `sample_bands` from
    `course.live.s2_stac` exactly once for the whole `points` set (never per
    point -- T-02-16, the same denial-of-service trap as the other
    extractors). Returns a DataFrame with `sample_id` plus `S2_B02..S2_B12`
    plus `s2_n_scenes`, in `points`' original row order.

    Raises `course.live.LiveSourceUnavailable` naming the area/year if no
    scenes are available after search + dedup, rather than propagating an
    empty-list error out of `sample_bands` or silently returning an all-NaN
    table. Never drops rows: every point in `points` gets exactly one output
    row, with NaN band values and `s2_n_scenes == 0` for any point outside
    the returned scenes' actual coverage (that per-point behavior lives in
    `sample_bands` itself; this function only forwards it unchanged).
    """
    if area not in AREAS:
        raise KeyError(
            f"unknown area {area!r}; course.config.AREAS has {sorted(AREAS)}"
        )

    bbox_4326 = AREAS[area]["bbox_4326"]
    items = search_scenes(bbox_4326, year)
    selected = select_scenes(items)

    if not selected:
        raise LiveSourceUnavailable(
            f"no Sentinel-2 L2A scenes available for area={area!r} year={year}"
        )

    points_lonlat = points[["lon", "lat"]].to_numpy(dtype=np.float64)
    bands = sample_bands(selected, points_lonlat)

    result = pd.DataFrame({"sample_id": np.asarray(points["sample_id"])})
    for col in [*S2_COLS, "s2_n_scenes"]:
        result[col] = bands[col].to_numpy()

    result.attrs["s2_item_ids"] = [item["id"] for item in selected]
    return result

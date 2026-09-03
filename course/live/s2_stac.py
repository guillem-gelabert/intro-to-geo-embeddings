"""Sentinel-2 L2A raw-band adapter over Earth Search STAC.

Provides `search_scenes` (STAC scene search) and `select_scenes`
(deterministic duplicate-item resolution). `sample_bands` (SCL-masked,
point-sampled reflectance with a defensive plausibility assertion) is added
in Task 2 of this plan.

Empirically-discovered correctness trap this module exists to avoid
(02-RESEARCH.md "Extraction Mechanics, Verified End to End" step 6): Earth
Search's `sentinel-2-l2a` collection carries duplicate items for some
archive dates (e.g. `..._0_L2A` original processing vs `..._1_L2A` Element84
reprocessing) — a naive search can return both for one date.
"""

import calendar
from datetime import date, datetime

import requests

from course.live import LiveSourceUnavailable

STAC_SEARCH_URL = "https://earth-search.aws.element84.com/v1/search"
COLLECTION = "sentinel-2-l2a"

# The date Element84's reprocessing note (02-RESEARCH.md §6) associates with
# the pre-/post-baseline-04 archive split; used only to decide which
# duplicate-item convention to prefer when a date carries more than one item.
DEDUP_BASELINE_CUTOVER = date(2022, 1, 25)


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

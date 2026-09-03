"""ESA WorldCover 2021 label adapter and EEA HRL Imperviousness 2018 reference reader.

This module supplies two conceptually distinct outputs that must never be
conflated (02-RESEARCH.md "Licensing and Redistribution"; PITFALLS.md
Pitfall 6, "validation_source == label_source"):

- ``worldcover_window`` / ``class_to_label`` produce the course's training
  LABEL (``label`` / ``label_source`` columns downstream). Source: ESA
  WorldCover 2021 v200, CC BY 4.0.
- ``imd_2018_window`` produces an INDEPENDENT reference value
  (``imd_2018`` / ``validation_source`` columns downstream) used only to
  teach that validating one learned product against another learned product
  is not independent validation. Source: EEA HRL Imperviousness Density
  2018 (only the 2018 generation is anonymously reachable — there is no
  public 2021 or 2018-2021-change service; see 02-RESEARCH.md "Is the free
  EU Login genuinely needed?"). It is never used to derive a label itself.

Both readers do a single bounded window read per AOI — never a per-point
network loop (02-RESEARCH.md Pitfall 4: scattered point sampling against a
remote COG costs 0.3-0.7 s/point).

## WorldCover class-code grouping rationale

WorldCover v200's 11 official raw class codes collapse into the course's 5
teaching labels (``built``, ``crop``, ``vegetation``, ``water``, ``bare``):

- ``crop`` (40 Cropland): the dominant class at both study regions.
- ``built`` (50 Built-up): the target class for change/impervious-surface
  teaching.
- ``water`` (80 Permanent water bodies): the scarcest class at both regions
  but still sampled explicitly (stratified, not proportional-random).
- ``vegetation`` (10 Tree cover, 20 Shrubland, 30 Grassland,
  90 Herbaceous wetland, 95 Mangroves): any vegetated cover other than
  cropland collapses into one class — the course does not need a
  forest-vs-shrub-vs-grass-vs-wetland distinction for its similarity/
  classification lessons.
- ``bare`` (60 Bare/sparse vegetation, 70 Snow and ice, 100 Moss and
  lichen): non-vegetated, non-built, non-water land cover. Snow/ice (70) is
  genuinely absent at both Bern and Seville but is mapped anyway so the
  dict stays total — a future region could plausibly contain it.
"""

import math

import numpy as np
import rasterio
import requests
from affine import Affine
from rasterio.io import MemoryFile
from rasterio.windows import from_bounds

from course.live import LiveSourceUnavailable

WORLDCOVER_BASE = "https://esa-worldcover.s3.eu-central-1.amazonaws.com/v200/2021/map"

EEA_IMD_BASE = (
    "https://image.discomap.eea.europa.eu/arcgis/rest/services/GioLandPublic/"
    "HRL_ImperviousnessDensity_2018/ImageServer"
)

# ESA WorldCover v200 official legend -> course's 5-class teaching scheme.
# See module docstring "WorldCover class-code grouping rationale" above.
WORLDCOVER_CLASS_TO_LABEL = {
    10: "vegetation",  # Tree cover
    20: "vegetation",  # Shrubland
    30: "vegetation",  # Grassland
    40: "crop",  # Cropland
    50: "built",  # Built-up
    60: "bare",  # Bare / sparse vegetation
    70: "bare",  # Snow and ice
    80: "water",  # Permanent water bodies
    90: "vegetation",  # Herbaceous wetland
    95: "vegetation",  # Mangroves
    100: "bare",  # Moss and lichen
}


def worldcover_tile_name(lon: float, lat: float) -> str:
    """Compute the 3x3-degree, lower-left-corner WorldCover tile name for a point.

    Confirmed this session (02-RESEARCH.md): Bern (7.4474, 46.9480) ->
    ``N45E006``; Seville (-5.9845, 37.3891) -> ``N36W006``.
    """
    lat_deg = math.floor(lat / 3) * 3
    lon_deg = math.floor(lon / 3) * 3
    ns = "N" if lat_deg >= 0 else "S"
    ew = "E" if lon_deg >= 0 else "W"
    return f"{ns}{abs(lat_deg):02d}{ew}{abs(lon_deg):03d}"


def worldcover_window(bbox_4326: tuple) -> tuple[np.ndarray, Affine]:
    """Read one bounded ESA WorldCover 2021 class-code window for an AOI.

    ``bbox_4326`` is ``(min_lon, min_lat, max_lon, max_lat)``. WorldCover
    COGs are already north-up EPSG:4326, so no reprojection/VRT is needed
    (unlike the AlphaEarth GCS COGs). Raises ``LiveSourceUnavailable`` on
    any rasterio open/read failure (e.g. a missing tile or network error).
    """
    min_lon, min_lat, max_lon, max_lat = bbox_4326
    center_lon = (min_lon + max_lon) / 2
    center_lat = (min_lat + max_lat) / 2
    tile = worldcover_tile_name(center_lon, center_lat)
    url = f"{WORLDCOVER_BASE}/ESA_WorldCover_10m_2021_v200_{tile}_Map.tif"
    try:
        with rasterio.open(f"/vsicurl/{url}") as ds:
            win = (
                from_bounds(*bbox_4326, ds.transform)
                .round_offsets()
                .round_lengths()
            )
            arr = ds.read(1, window=win)
            transform = ds.window_transform(win)
    except Exception as exc:
        raise LiveSourceUnavailable(
            f"failed to read WorldCover 2021 tile {tile!r} for bbox {bbox_4326}: {exc}"
        ) from exc
    return arr, transform


def class_to_label(code: int) -> str:
    """Map a raw WorldCover class code to the course's 5-class teaching label.

    Raises ``KeyError`` (naming the unrecognized code) for anything not in
    ``WORLDCOVER_CLASS_TO_LABEL`` — the mapping is total over the 11
    official codes, so this should only fire on genuinely corrupt/unexpected
    input.
    """
    try:
        return WORLDCOVER_CLASS_TO_LABEL[code]
    except KeyError as exc:
        raise KeyError(f"unrecognized WorldCover class code: {code}") from exc


def imd_2018_window(
    bbox_4326: tuple, dst_epsg: int, size: tuple[int, int] = (512, 512)
) -> tuple[np.ndarray, Affine]:
    """Read one bounded EEA HRL Imperviousness Density 2018 window for an AOI.

    This is an INDEPENDENT reference value, never a label (see module
    docstring). Calls the ``exportImage`` ImageServer endpoint once per AOI
    — never per-point ``identify`` (02-RESEARCH.md Pitfall 4). ``bbox_4326``
    is ``(min_lon, min_lat, max_lon, max_lat)``; the response is
    reprojected server-side into ``dst_epsg`` and requested at ``size``
    (width, height) pixels. Raises ``LiveSourceUnavailable`` if the request
    fails or the response is not a valid GeoTIFF.
    """
    min_lon, min_lat, max_lon, max_lat = bbox_4326
    params = {
        "bbox": f"{min_lon},{min_lat},{max_lon},{max_lat}",
        "bboxSR": 4326,
        "imageSR": dst_epsg,
        "size": f"{size[0]},{size[1]}",
        "format": "tiff",
        "f": "image",
    }
    try:
        response = requests.get(f"{EEA_IMD_BASE}/exportImage", params=params, timeout=60)
        response.raise_for_status()
        with MemoryFile(response.content) as memfile, memfile.open() as ds:
            arr = ds.read(1)
            transform = ds.transform
    except Exception as exc:
        raise LiveSourceUnavailable(
            f"failed to fetch HRL Imperviousness 2018 window for bbox {bbox_4326}: {exc}"
        ) from exc
    return arr, transform

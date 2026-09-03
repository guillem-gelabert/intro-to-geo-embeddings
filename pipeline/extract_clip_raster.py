"""Author-side, network-using script: clip a small AlphaEarth sub-AOI raster.

This is the ONE script in the project that produces
``data/bern_aef_2024_clip.tif`` -- a small (a few MB at most), raw int8,
64-band COG GeoTIFF for a ~1.5km sub-AOI of Bern, year 2024, checked into the
repo so ``01_alphaearth_access_visualize.ipynb``'s Path B can demonstrate the
int8 dequantization formula and unit-norm check on real raster data with no
network access or Earth Engine account. The notebook NEVER imports this
module -- it only reads the checked-in GeoTIFF this script writes.

Reuses ``course.live.aef_cog.find_tile``/``read_window`` (the only place in
the project that talks to the live AlphaEarth GCS bucket) rather than
re-implementing tile lookup or windowed reads. The written raster is raw
int8, NOT dequantized -- dequantization happens inside the notebook via
``course.embeddings.dequantize_aef``, which is the actual teaching point.

Deliberately reads a small sub-bbox, not the full region AOI in
``course.config.AREAS`` -- a full-AOI window read is documented (Phase 2
research) to cost 190-340 seconds and produce a large array; this script's
default sub-bbox is a small, hardcoded 1.5km window inside Bern.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

import rasterio

from course.config import AREAS
from course.live.aef_cog import find_tile, read_window

ATTRIBUTION = (
    "The AlphaEarth Foundations Satellite Embedding dataset is produced by "
    "Google and Google DeepMind."
)
LICENSE = "CC BY 4.0"
DATASET_VERSION = "1.1"
NODATA = -128
N_BANDS = 64


def build_clip(
    area: str = "bern",
    year: int = 2024,
    sub_bbox_4326: tuple[float, float, float, float] = (7.44, 46.94, 7.46, 46.96),
    out_path: Path = Path("data/bern_aef_2024_clip.tif"),
) -> dict:
    """Clip a small sub-AOI window from the live AlphaEarth GCS bucket.

    Writes a raw int8, 64-band COG GeoTIFF to ``out_path`` and a matching
    provenance dict (also written to
    ``data/bern_aef_2024_clip.provenance.json`` by the CLI entry point below).

    Requires network access (anonymous, no credentials) to the AlphaEarth
    GCS bucket via ``course.live.aef_cog``.
    """
    out_path = Path(out_path)
    epsg = AREAS[area]["epsg"]
    dst_crs = f"EPSG:{epsg}"

    center_lon = (sub_bbox_4326[0] + sub_bbox_4326[2]) / 2
    center_lat = (sub_bbox_4326[1] + sub_bbox_4326[3]) / 2

    tile = find_tile(center_lon, center_lat, year)
    raw, window_transform = read_window(tile["url"], sub_bbox_4326, dst_crs=dst_crs)

    _, height, width = raw.shape

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with rasterio.open(
        out_path,
        "w",
        driver="COG",
        compress="DEFLATE",
        dtype="int8",
        count=N_BANDS,
        width=width,
        height=height,
        crs=dst_crs,
        transform=window_transform,
        nodata=NODATA,
    ) as dst:
        dst.write(raw)
        dst.update_tags(
            license=LICENSE,
            attribution=ATTRIBUTION,
            dequantization_formula="((v / 127.5) ** 2) * sign(v), masking nodata=-128 first, then L2-renormalize",
            nodata_value=str(NODATA),
        )

    provenance = {
        "embedding_product": "alphaearth_satellite_embedding",
        "dataset_version": DATASET_VERSION,
        "year": year,
        "extraction_date": datetime.now(UTC).isoformat(),
        "source_path": tile["url"],
        "sampling_method": (
            "single windowed COG read via course.live.aef_cog.read_window, "
            "no point sampling, raw int8 not dequantized"
        ),
        "crs": dst_crs,
        "bbox_4326": list(sub_bbox_4326),
        "shape": [N_BANDS, height, width],
        "license": LICENSE,
        "attribution": ATTRIBUTION,
        "created_by": "pipeline/extract_clip_raster.py",
    }
    return provenance


if __name__ == "__main__":
    prov = build_clip()
    provenance_path = Path("data/bern_aef_2024_clip.provenance.json")
    provenance_path.parent.mkdir(parents=True, exist_ok=True)
    provenance_path.write_text(json.dumps(prov, indent=2) + "\n")
    print(json.dumps(prov, indent=2))

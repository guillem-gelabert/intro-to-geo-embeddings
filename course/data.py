"""Local-first, remote-fallback, checksum-verified loader for frozen
region/year teaching tables.

Every notebook (and every later test) in this course calls
``course.data.load(area, year)`` to get a region/year GeoDataFrame. The
committed copy under ``data/`` is always tried first; the network is only
touched when that file is absent, and any downloaded bytes are rejected
unless their sha256 matches the committed ``data/manifest.json`` entry.
"""

import hashlib
import json
from pathlib import Path

import geopandas as gpd
import pyarrow.parquet as pq
import requests

from course.config import RELEASE_ORG, RELEASE_REPO, RELEASE_TAG

RELEASE_BASE_TEMPLATE = "https://github.com/{org}/{repo}/releases/download/{tag}"


def _load_manifest(data_dir: Path) -> dict:
    manifest_path = data_dir / "manifest.json"
    with manifest_path.open() as f:
        return json.load(f)


def _read_course_provenance(path: Path) -> dict | None:
    """Read the course_provenance parquet key-value metadata key back out.

    geopandas' own gpd.read_parquet does not surface arbitrary custom
    metadata into .attrs automatically, so it must be read explicitly via
    pyarrow (02-RESEARCH.md, "Hosting and the Local-First Loader").
    """
    table = pq.read_table(path)
    metadata = table.schema.metadata or {}
    raw = metadata.get(b"course_provenance")
    if raw is None:
        return None
    return json.loads(raw)


def load(
    area: str,
    year: int,
    data_dir: Path = Path("data"),
    *,
    release_base: str | None = None,
) -> gpd.GeoDataFrame:
    """Load the frozen region/year table for `area`/`year`.

    Local-first: if `{data_dir}/{area}/{area}_aef_{year}_v1.1.parquet`
    exists, it is read directly and no network call is made. Otherwise the
    file is fetched from a pinned release URL, its sha256 is verified
    against `{data_dir}/manifest.json` BEFORE it is written to disk, and a
    checksum mismatch raises rather than silently accepting the bytes.

    `release_base` overrides the release base URL (used by tests to point
    at a local HTTP server); production callers should leave it unset, in
    which case it is built from `course.config`'s RELEASE_ORG/RELEASE_REPO/
    RELEASE_TAG.
    """
    data_dir = Path(data_dir)
    filename = f"{area}_aef_{year}_v1.1.parquet"
    local = data_dir / area / filename

    if local.exists():
        gdf = gpd.read_parquet(local)
        provenance = _read_course_provenance(local)
        if provenance is not None:
            gdf.attrs["course_provenance"] = provenance
        return gdf

    manifest = _load_manifest(data_dir)
    if filename not in manifest:
        raise FileNotFoundError(
            f"No local file for area={area!r} year={year!r} at {local}, and "
            f"{filename!r} is not present in {data_dir / 'manifest.json'}"
        )
    entry = manifest[filename]

    base = release_base or RELEASE_BASE_TEMPLATE.format(
        org=RELEASE_ORG, repo=RELEASE_REPO, tag=RELEASE_TAG
    )
    url = f"{base}/{filename}"
    resp = requests.get(url, timeout=60)
    resp.raise_for_status()

    actual_sha = hashlib.sha256(resp.content).hexdigest()
    expected_sha = entry["sha256"]
    assert actual_sha == expected_sha, (
        f"checksum mismatch for {filename}: expected {expected_sha}, got {actual_sha}"
    )

    local.parent.mkdir(parents=True, exist_ok=True)
    local.write_bytes(resp.content)

    gdf = gpd.read_parquet(local)
    provenance = _read_course_provenance(local)
    if provenance is not None:
        gdf.attrs["course_provenance"] = provenance
    return gdf

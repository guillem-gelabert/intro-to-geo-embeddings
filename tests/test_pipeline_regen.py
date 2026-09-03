"""pipeline.build: a non-network idempotency test for the cached AlphaEarth
window read, and the network-marked live regeneration slice that proves the
whole chain -- sampling, extraction, labels, S2, assembly, write -- produces
a structurally valid table from live sources for one (area, year)
(02-09-PLAN.md Task 3, DATA-07).
"""

import json

import geopandas as gpd
import numpy as np
import pandas as pd
import pyarrow.parquet as pq
import pytest
from affine import Affine
from shapely.geometry import Point

from course.schema import A_COLS
from pipeline import build


def _synthetic_points(n=4):
    """Points whose (x, y) land inside a small identity-ish window so
    `sample_points_from_window` returns real (non-NaN) values, without
    needing a real reprojection -- mirrors tests/test_extract_aef.py's
    pattern for `pipeline.extract_aef`."""
    rng = np.random.default_rng(3)
    lon = 7.30 + rng.uniform(0, 0.01, size=n)
    lat = 46.85 + rng.uniform(0, 0.01, size=n)
    geometry = [Point(x, y) for x, y in zip(lon, lat)]
    return gpd.GeoDataFrame(
        {
            "sample_id": np.arange(n, dtype=np.int64),
            "lon": lon,
            "lat": lat,
            # Inside the fake window's UTM32N-magnitude bounds (see
            # fake_transform below): x in [370010, 370040), y in
            # [5199960, 5199990).
            "x": 370010.0 + rng.uniform(0, 20, size=n),
            "y": 5199960.0 + rng.uniform(0, 20, size=n),
        },
        geometry=geometry,
        crs="EPSG:4326",
    )


# --- Non-network: cached AEF window read is idempotent ---------------------


def test_extract_aef_cached_does_not_refetch_on_second_call(tmp_path, monkeypatch):
    """A second call for the same (area, year) must not re-invoke
    find_tile/read_window -- the whole point of the on-disk cache
    (02-09-PLAN.md Task 3 acceptance criteria)."""
    calls = {"find_tile": 0, "read_window": 0}

    fake_tile = {
        "utm_zone": "32N",
        "crs": "EPSG:32632",
        "url": "https://fake.example/tile.tiff",
    }
    fake_raw = np.zeros((64, 4, 4), dtype=np.int8)
    # Pixel (0, 0) covers x in [370000, 370010), y in (5200000-10, 5200000].
    fake_transform = Affine(10, 0, 370000, 0, -10, 5200000)

    def fake_find_tile(lon, lat, year):
        calls["find_tile"] += 1
        return fake_tile

    def fake_read_window(url, bbox_4326, dst_crs):
        calls["read_window"] += 1
        return fake_raw, fake_transform

    monkeypatch.setattr(build, "find_tile", fake_find_tile)
    monkeypatch.setattr(build, "read_window", fake_read_window)

    points = _synthetic_points(n=3)
    out_dir = tmp_path / "data"

    result1, tile1 = build._extract_aef_cached("bern", 2021, points, out_dir)
    result2, tile2 = build._extract_aef_cached("bern", 2021, points, out_dir)

    assert calls["find_tile"] == 1
    assert calls["read_window"] == 1
    assert tile1 == tile2 == fake_tile
    pd.testing.assert_frame_equal(result1, result2)
    assert list(result1.columns) == ["sample_id", *A_COLS]

    cache_path = build._window_cache_path(out_dir, "bern", 2021)
    assert cache_path.exists() and cache_path.stat().st_size > 0


def test_extract_aef_cached_mtime_unchanged_on_second_call(tmp_path, monkeypatch):
    """Cache-file mtime doesn't change on a repeat call -- direct evidence
    the second call read from cache rather than rewriting it."""
    fake_tile = {
        "utm_zone": "32N",
        "crs": "EPSG:32632",
        "url": "https://fake.example/tile.tiff",
    }
    fake_raw = np.zeros((64, 4, 4), dtype=np.int8)
    fake_transform = Affine(10, 0, 370000, 0, -10, 5200000)

    monkeypatch.setattr(build, "find_tile", lambda lon, lat, year: fake_tile)
    monkeypatch.setattr(
        build, "read_window", lambda url, bbox_4326, dst_crs: (fake_raw, fake_transform)
    )

    points = _synthetic_points(n=3)
    out_dir = tmp_path / "data"

    build._extract_aef_cached("bern", 2021, points, out_dir)
    cache_path = build._window_cache_path(out_dir, "bern", 2021)
    mtime_after_first_call = cache_path.stat().st_mtime_ns

    build._extract_aef_cached("bern", 2021, points, out_dir)
    mtime_after_second_call = cache_path.stat().st_mtime_ns

    assert mtime_after_first_call == mtime_after_second_call


# --- Network: the live regeneration slice (DATA-07) -------------------------


@pytest.mark.network
def test_pipeline_regen_bern_2021_structural(tmp_path):
    """Run the real orchestration for ONE area/year (bern, 2021 -- the
    fastest combination) against live sources into a tmp_path out_dir.
    Asserts STRUCTURAL correctness only (schema, row-count band,
    provenance round-trip) -- not byte-identical to any committed table,
    since STAC scene selection can drift over time."""
    from course.schema import validate_frozen

    out_dir = tmp_path / "data"
    provenance_records = build.run(area="bern", years=[2021], out_dir=out_dir)

    table_path = build._table_path(out_dir, "bern", 2021)
    assert table_path.exists()

    gdf = gpd.read_parquet(table_path)
    validate_frozen(gdf)
    assert 1800 <= len(gdf) <= 2200

    pq_table = pq.read_table(table_path)
    provenance = json.loads(pq_table.schema.metadata[b"course_provenance"])
    assert provenance["region"] == "bern"
    assert provenance["year"] == 2021
    assert provenance["label_source"] != provenance["validation_source"]

    assert any(r["region"] == "bern" and r["year"] == 2021 for r in provenance_records)
    assert (out_dir / "manifest.json").exists()
    assert (out_dir / "DATA_CARD.md").exists()

    manifest = json.loads((out_dir / "manifest.json").read_text())
    assert table_path.name in manifest

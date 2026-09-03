"""Unit tests for pipeline.extract_aef -- one windowed AlphaEarth read per
(area, year), then array-indexed sampling for every point (02-07-PLAN.md
Task 1). Non-network tests monkeypatch course.live.aef_cog.find_tile/
read_window (imported into pipeline.extract_aef's own namespace) via
unittest.mock.patch, so the "exactly once, regardless of point count"
contract (02-RESEARCH.md Pitfall 4) is directly assertable via call-count.
"""

from unittest.mock import patch

import geopandas as gpd
import numpy as np
import pytest
import rasterio

from course.config import AREAS
from course.schema import A_COLS
from pipeline.extract_aef import extract_area_year

FAKE_TILE = {"utm_zone": "32N", "crs": "EPSG:32632", "url": "https://fake/tile.tiff"}


def _synthetic_points(n=5, area="bern", with_xy=True):
    """Points with lon/lat inside the region's real AOI and (if `with_xy`)
    x/y placed inside a small identity-transform pixel grid so the mocked
    window can be indexed deterministically without a real reprojection."""
    min_lon, min_lat, max_lon, max_lat = AREAS[area]["bbox_4326"]
    rng = np.random.default_rng(7)
    lon = rng.uniform(min_lon, max_lon, size=n)
    lat = rng.uniform(min_lat, max_lat, size=n)
    geometry = gpd.points_from_xy(lon, lat)

    data = {
        "sample_id": np.arange(n, dtype=np.int64),
        "lon": lon,
        "lat": lat,
    }
    if with_xy:
        data["x"] = rng.uniform(0, 4, size=n)
        data["y"] = rng.uniform(0, 4, size=n)

    return gpd.GeoDataFrame(data, geometry=geometry, crs="EPSG:4326")


def _synthetic_window(shape=(64, 5, 5), seed=1):
    rng = np.random.default_rng(seed)
    raw = rng.integers(-100, 100, size=shape, dtype=np.int8)
    return raw, rasterio.Affine.identity()


class TestExtractAreaYearReadsWindowOnce:
    """Regression test for the performance trap: read_window must be called
    exactly once per (area, year), regardless of point count."""

    def test_read_window_and_find_tile_called_exactly_once_for_five_points(self):
        points = _synthetic_points(n=5)
        raw, transform = _synthetic_window()

        with (
            patch(
                "pipeline.extract_aef.find_tile", return_value=FAKE_TILE
            ) as mock_find_tile,
            patch(
                "pipeline.extract_aef.read_window", return_value=(raw, transform)
            ) as mock_read_window,
        ):
            result = extract_area_year("bern", 2021, points)

        assert mock_find_tile.call_count == 1
        assert mock_read_window.call_count == 1
        assert result.shape == (5, 1 + len(A_COLS))

    def test_read_window_called_exactly_once_regardless_of_point_count(self):
        points = _synthetic_points(n=50)
        raw, transform = _synthetic_window()

        with (
            patch("pipeline.extract_aef.find_tile", return_value=FAKE_TILE),
            patch(
                "pipeline.extract_aef.read_window", return_value=(raw, transform)
            ) as mock_read_window,
        ):
            extract_area_year("bern", 2021, points)

        assert mock_read_window.call_count == 1


def test_returned_columns_match_schema_and_sample_id_order():
    points = _synthetic_points(n=5)
    raw, transform = _synthetic_window()

    with (
        patch("pipeline.extract_aef.find_tile", return_value=FAKE_TILE),
        patch("pipeline.extract_aef.read_window", return_value=(raw, transform)),
    ):
        result = extract_area_year("bern", 2021, points)

    assert list(result.columns) == ["sample_id"] + A_COLS
    np.testing.assert_array_equal(
        result["sample_id"].to_numpy(), points["sample_id"].to_numpy()
    )


def test_reprojects_lon_lat_when_xy_missing_never_silently_reusing_degrees():
    """When points lack x/y columns, lon/lat must be explicitly reprojected
    into the tile's CRS -- never silently reused as if they were already in
    that CRS (02-07-PLAN.md Task 1 behavior spec)."""
    points = _synthetic_points(n=3, with_xy=False)
    raw, transform = _synthetic_window(shape=(64, 200, 200))

    captured = {}

    def _fake_sample_points_from_window(raw_unit, window_transform, points_xy):
        captured["points_xy"] = points_xy
        return np.zeros((points_xy.shape[0], 64), dtype=np.float32)

    with (
        patch("pipeline.extract_aef.find_tile", return_value=FAKE_TILE),
        patch("pipeline.extract_aef.read_window", return_value=(raw, transform)),
        patch(
            "pipeline.extract_aef.sample_points_from_window",
            side_effect=_fake_sample_points_from_window,
        ),
    ):
        extract_area_year("bern", 2021, points)

    # Reprojected coordinates land in UTM32N easting/northing magnitude
    # (hundreds of thousands of meters), not degrees (single/double digits).
    assert np.all(captured["points_xy"][:, 0] > 1000)
    assert np.all(captured["points_xy"][:, 1] > 1000)


@pytest.mark.network
def test_extract_area_year_live_bern_small_sub_bbox():
    """Live integration check: a real call for ("bern", 2021) against 3-5
    real points near the Bern AOI center, scoped to a small (~200m x 200m)
    sub-bbox passed explicitly -- NOT the full AOI (02-RESEARCH.md measured
    311-342s for a full-AOI window; Plan 02-09's regen test and Plan 02-10's
    real run already exercise that path; repeating it here would add minutes
    of network time proving nothing new)."""
    lon0, lat0 = 7.4474, 46.9480
    offsets = [
        (0.0, 0.0),
        (0.0007, 0.0),
        (0.0, 0.0007),
        (-0.0007, 0.0007),
        (0.0007, -0.0007),
    ]
    lon = [lon0 + dx for dx, _dy in offsets]
    lat = [lat0 + dy for _dx, dy in offsets]
    points = gpd.GeoDataFrame(
        {
            "sample_id": np.arange(len(offsets), dtype=np.int64),
            "lon": lon,
            "lat": lat,
        },
        geometry=gpd.points_from_xy(lon, lat),
        crs="EPSG:4326",
    )
    small_bbox = (
        7.446084105175679,
        46.94709535009951,
        7.448715894824321,
        46.94890464990049,
    )

    result = extract_area_year("bern", 2021, points, bbox_4326=small_bbox)

    vectors = result[A_COLS].to_numpy(dtype=np.float32)
    norms = np.linalg.norm(vectors, axis=1)
    np.testing.assert_allclose(norms, 1.0, atol=1e-3)

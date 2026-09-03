import importlib.util

import numpy as np
import pytest
import rasterio

from course.live import LiveSourceUnavailable
from course.live.aef_cog import (
    AEF_GCS_BASE,
    find_tile,
    read_window,
    sample_points_from_window,
)

# duckdb lives behind the `providers` optional-dependencies extra
# (ENV-05/T-01-10, tests/test_core_env_isolation.py) — course.live.aef_cog
# itself stays importable without it (find_tile() imports duckdb lazily),
# and these tests skip gracefully rather than error when it isn't installed.
_HAS_DUCKDB = importlib.util.find_spec("duckdb") is not None


class _FakeConnection:
    """Stand-in for duckdb.connect() so find_tile can be unit-tested without
    hitting the real aef_index.parquet over the network."""

    def __init__(self, rows=None, raise_on_query=False):
        self._rows = rows or []
        self._raise_on_query = raise_on_query

    def execute(self, sql, params=None):
        if params is not None and self._raise_on_query:
            import duckdb

            raise duckdb.Error("simulated tile index failure")
        return self

    def fetchall(self):
        return self._rows


@pytest.mark.skipif(not _HAS_DUCKDB, reason="duckdb requires the 'providers' extra")
class TestFindTile:
    def test_raises_live_source_unavailable_when_no_tile_matches(self, monkeypatch):
        monkeypatch.setattr("duckdb.connect", lambda: _FakeConnection(rows=[]))

        with pytest.raises(LiveSourceUnavailable, match="no AlphaEarth tile"):
            find_tile(0.0, 0.0, 2021)

    def test_raises_live_source_unavailable_on_duckdb_error(self, monkeypatch):
        monkeypatch.setattr(
            "duckdb.connect", lambda: _FakeConnection(raise_on_query=True)
        )

        with pytest.raises(LiveSourceUnavailable, match="tile index query failed"):
            find_tile(0.0, 0.0, 2021)

    def test_returns_url_built_from_tile_row(self, monkeypatch):
        row = (
            "32N",
            "EPSG:32632",
            "s3://bucket/2021/32N/x2x0ui46492ik7uhz-0000008192-0000000000.tiff",
        )
        monkeypatch.setattr("duckdb.connect", lambda: _FakeConnection(rows=[row]))

        result = find_tile(7.4474, 46.9480, 2021)

        assert result == {
            "utm_zone": "32N",
            "crs": "EPSG:32632",
            "url": (
                f"{AEF_GCS_BASE}/2021/32N/x2x0ui46492ik7uhz-0000008192-0000000000.tiff"
            ),
        }


@pytest.mark.network
@pytest.mark.skipif(not _HAS_DUCKDB, reason="duckdb requires the 'providers' extra")
def test_find_tile_and_read_window_against_real_bern_tile():
    """Live integration check: find_tile against the real aef_index.parquet,
    then read_window against the real GCS tile with a small (~200m x 200m)
    sub-bbox — NOT the full AOI (02-RESEARCH.md measured 311-342s for a
    full-AOI window; plans 02-09/02-10 exercise that path, not this test)."""
    tile = find_tile(7.4474, 46.9480, 2021)

    assert "32N" in tile["url"]
    assert "2021" in tile["url"]

    small_bbox = (
        7.446084105175679,
        46.94709535009951,
        7.448715894824321,
        46.94890464990049,
    )
    raw, window_transform = read_window(tile["url"], small_bbox, dst_crs="EPSG:32632")

    assert raw.shape[0] == 64
    assert raw.dtype == np.int8
    assert window_transform is not None


class TestSamplePointsFromWindow:
    """sample_points_from_window indexes an already-dequantized (64, H, W)
    array by (row, col) derived from an inverted rasterio Affine transform —
    it never touches int8 or loops .sample() against a remote COG
    (02-RESEARCH.md Pitfall 4)."""

    def test_center_pixel_coordinate_returns_that_pixels_vector(self):
        rng = np.random.default_rng(3)
        raw = rng.normal(size=(64, 5, 5)).astype(np.float32)
        norms = np.linalg.norm(raw, axis=0, keepdims=True)
        raw_unit = (raw / norms).astype(np.float32)
        transform = rasterio.Affine.identity()
        points_xy = np.array([[2.0, 2.0]])

        result = sample_points_from_window(raw_unit, transform, points_xy)

        assert result.shape == (1, 64)
        np.testing.assert_allclose(result[0], raw_unit[:, 2, 2])

    def test_out_of_bounds_point_returns_nan_row_not_indexerror(self):
        raw_unit = np.zeros((64, 5, 5), dtype=np.float32)
        transform = rasterio.Affine.identity()
        points_xy = np.array([[10.0, 10.0]])

        result = sample_points_from_window(raw_unit, transform, points_xy)

        assert result.shape == (1, 64)
        assert np.all(np.isnan(result[0]))

    def test_three_points_map_to_three_distinct_rows_in_order(self):
        rng = np.random.default_rng(4)
        raw_unit = rng.normal(size=(64, 5, 5)).astype(np.float32)
        transform = rasterio.Affine.identity()
        # points_xy is (x, y) = (col, row)
        points_xy = np.array([[0.0, 0.0], [4.0, 4.0], [3.0, 2.0]])

        result = sample_points_from_window(raw_unit, transform, points_xy)

        assert result.shape == (3, 64)
        np.testing.assert_allclose(result[0], raw_unit[:, 0, 0])
        np.testing.assert_allclose(result[1], raw_unit[:, 4, 4])
        np.testing.assert_allclose(result[2], raw_unit[:, 2, 3])

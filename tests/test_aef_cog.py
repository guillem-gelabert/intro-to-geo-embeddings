import importlib.util

import pytest

from course.live import LiveSourceUnavailable
from course.live.aef_cog import AEF_GCS_BASE, find_tile

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
                f"{AEF_GCS_BASE}/2021/32N/"
                "x2x0ui46492ik7uhz-0000008192-0000000000.tiff"
            ),
        }

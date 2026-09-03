"""Unit tests for pipeline.attach_s2 -- wiring the fixed sample points to
Sentinel-2 raw reflectance bands via course.live.s2_stac (02-08-PLAN.md).

Non-network tests monkeypatch course.live.s2_stac's search_scenes /
select_scenes / sample_bands as imported into pipeline.attach_s2's own
namespace (matching the pattern in tests/test_sample_design.py). The single
@pytest.mark.network test performs a real, small end-to-end call and is
excluded from the default suite (pyproject.toml addopts = -m "not network").
"""

import numpy as np
import pandas as pd
import pytest

from course.schema import S2_COLS
from pipeline import attach_s2 as attach_s2_module
from pipeline.attach_s2 import attach_s2


def _points(n: int) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "sample_id": np.arange(n),
            "lon": 7.4474 + np.arange(n) * 0.001,
            "lat": 46.9480 + np.arange(n) * 0.001,
        }
    )


def _fake_bands_df(n: int, n_scenes: int = 2) -> pd.DataFrame:
    data = {col: np.full(n, 0.1, dtype=np.float32) for col in S2_COLS}
    data["s2_n_scenes"] = np.full(n, n_scenes, dtype=np.int64)
    return pd.DataFrame(data)


# --- Task 1: attach_s2 wiring and provenance -------------------------------


def test_attach_s2_calls_sample_bands_exactly_once(monkeypatch):
    calls = []

    def _fake_sample_bands(items, points_lonlat, *args, **kwargs):
        calls.append(points_lonlat.shape[0])
        return _fake_bands_df(points_lonlat.shape[0])

    monkeypatch.setattr(
        attach_s2_module, "search_scenes", lambda *a, **k: [{"id": "x"}]
    )
    monkeypatch.setattr(attach_s2_module, "select_scenes", lambda items: items)
    monkeypatch.setattr(attach_s2_module, "sample_bands", _fake_sample_bands)

    attach_s2("bern", 2021, _points(5))

    assert len(calls) == 1
    assert calls[0] == 5


def test_attach_s2_preserves_point_order(monkeypatch):
    monkeypatch.setattr(
        attach_s2_module, "search_scenes", lambda *a, **k: [{"id": "x"}]
    )
    monkeypatch.setattr(attach_s2_module, "select_scenes", lambda items: items)
    monkeypatch.setattr(
        attach_s2_module,
        "sample_bands",
        lambda items, points_lonlat, *a, **k: _fake_bands_df(points_lonlat.shape[0]),
    )

    points = _points(5)
    # Deliberately non-sequential sample_id order to catch accidental resorting.
    points["sample_id"] = [40, 10, 30, 20, 0]

    result = attach_s2("seville", 2021, points)

    assert list(result["sample_id"]) == [40, 10, 30, 20, 0]
    assert list(result.columns) == ["sample_id", *S2_COLS, "s2_n_scenes"]


@pytest.mark.network
def test_attach_s2_end_to_end_bern_2021():
    points = pd.DataFrame(
        {
            "sample_id": [0, 1, 2],
            "lon": [7.4474, 7.4480, 7.4468],
            "lat": [46.9480, 46.9475, 46.9485],
        }
    )

    result = attach_s2("bern", 2021, points)

    assert list(result["sample_id"]) == [0, 1, 2]
    assert list(result.columns) == ["sample_id", *S2_COLS, "s2_n_scenes"]
    assert len(result) == len(points)
    assert result.attrs["s2_item_ids"]

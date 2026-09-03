import pytest
import requests

from course.live import LiveSourceUnavailable
from course.live.s2_stac import STAC_SEARCH_URL, search_scenes, select_scenes


def _make_item(item_id, dt, cloud_cover):
    return {
        "id": item_id,
        "properties": {"datetime": dt, "eo:cloud_cover": cloud_cover},
    }


# --- Task 1: search_scenes / select_scenes -------------------------------


def test_select_scenes_dedups_pre2022_pair_prefers_0_item():
    items = [
        _make_item("S2B_32TLS_20210812_0_L2A", "2021-08-12T10:38:04.931000Z", 1.55),
        _make_item("S2B_32TLS_20210812_1_L2A", "2021-08-12T10:38:04.932000Z", 1.78),
    ]

    result = select_scenes(items)

    assert len(result) == 1
    assert result[0]["id"] == "S2B_32TLS_20210812_0_L2A"


def test_select_scenes_keeps_items_on_different_dates():
    items = [
        _make_item("S2B_32TLS_20210812_0_L2A", "2021-08-12T10:38:04.931000Z", 1.55),
        _make_item("S2B_32TLS_20210723_0_L2A", "2021-07-23T10:38:04.931000Z", 3.2),
    ]

    result = select_scenes(items)

    ids = {item["id"] for item in result}
    assert ids == {"S2B_32TLS_20210812_0_L2A", "S2B_32TLS_20210723_0_L2A"}


def test_select_scenes_post_cutover_prefers_lowest_cloud_cover():
    items = [
        _make_item("S2A_32TLS_20240811_0_L2A", "2024-08-11T10:38:04.931000Z", 5.0),
        _make_item("S2A_32TLS_20240811_1_L2A", "2024-08-11T10:38:05.000000Z", 1.2),
    ]

    result = select_scenes(items)

    assert len(result) == 1
    assert result[0]["id"] == "S2A_32TLS_20240811_1_L2A"


def test_select_scenes_sorted_by_cloud_cover_ascending():
    items = [
        _make_item("a", "2021-07-01T00:00:00Z", 8.0),
        _make_item("b", "2021-08-01T00:00:00Z", 2.0),
        _make_item("c", "2021-06-01T00:00:00Z", 5.0),
    ]

    result = select_scenes(items)

    assert [item["id"] for item in result] == ["b", "c", "a"]


def test_search_scenes_raises_live_source_unavailable_on_empty_result(monkeypatch):
    class _Resp:
        def raise_for_status(self):
            pass

        def json(self):
            return {"features": []}

    monkeypatch.setattr(requests, "post", lambda *a, **k: _Resp())

    with pytest.raises(LiveSourceUnavailable):
        search_scenes((7.30, 46.85, 7.60, 47.05), 2021)


def test_search_scenes_raises_live_source_unavailable_on_request_failure(monkeypatch):
    def _raise(*args, **kwargs):
        raise requests.ConnectionError("boom")

    monkeypatch.setattr(requests, "post", _raise)

    with pytest.raises(LiveSourceUnavailable):
        search_scenes((7.30, 46.85, 7.60, 47.05), 2021)


def test_search_scenes_posts_valid_rfc3339_datetime_range(monkeypatch):
    """Regression test: the plan's literal date-only format
    (`f"{year}-{months[0]:02d}-01/{year}-{months[1]:02d}-31"`) is rejected by
    the live Earth Search API ("does not match RFC3339 format") and hardcodes
    an invalid day-31 for shorter months. Assert the emitted body instead
    uses full RFC3339 datetimes with the correct end-of-month day."""
    captured = {}

    class _Resp:
        def raise_for_status(self):
            pass

        def json(self):
            return {"features": [{"id": "x"}]}

    def _post(url, json, timeout):
        captured["url"] = url
        captured["json"] = json
        return _Resp()

    monkeypatch.setattr(requests, "post", _post)

    search_scenes((7.30, 46.85, 7.60, 47.05), 2021, months=(6, 6))

    assert captured["url"] == STAC_SEARCH_URL
    assert captured["json"]["datetime"] == "2021-06-01T00:00:00Z/2021-06-30T23:59:59Z"

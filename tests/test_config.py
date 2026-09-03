from course.config import ANCHOR_YEARS, AREAS
from course.live import LiveSourceUnavailable


def test_areas_epsg_matches_settled_utm_zones():
    assert AREAS["bern"]["epsg"] == 32632
    assert AREAS["seville"]["epsg"] == 32630


def test_anchor_years_matches_settled_values():
    assert ANCHOR_YEARS == [2018, 2021, 2024]


def test_live_source_unavailable_is_runtime_error():
    assert issubclass(LiveSourceUnavailable, RuntimeError)

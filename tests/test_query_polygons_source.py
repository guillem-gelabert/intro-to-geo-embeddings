"""Non-network structural checks for `data/query_polygons.geojson`
(DATA-10, 02-10-PLAN.md Task 2).

Overpass returned HTTP 406 during 02-RESEARCH.md's research session; that
turned out to be a missing-`User-Agent` rejection, not a hard block (see
02-10-SUMMARY.md) -- every feature here was fetched live from the real
Overpass API and hand-selected, not fabricated. This file only re-verifies
the structural properties an automated test *can* judge: valid geometry
and AOI containment. Whether a polygon actually depicts a solar farm or a
quarry is a visual call left to the Task 3 human checkpoint.
"""

import json
from pathlib import Path

import pytest
from shapely.geometry import shape

from course.config import AREAS

GEOJSON_PATH = (
    Path(__file__).resolve().parent.parent / "data" / "query_polygons.geojson"
)


@pytest.fixture(scope="module")
def feature_collection():
    with open(GEOJSON_PATH) as f:
        return json.load(f)


def test_geojson_file_exists():
    assert GEOJSON_PATH.exists()


def test_is_a_feature_collection(feature_collection):
    assert feature_collection["type"] == "FeatureCollection"
    assert len(feature_collection["features"]) >= 1


def test_at_least_three_features_per_region(feature_collection):
    counts = {}
    for feature in feature_collection["features"]:
        region = feature["properties"]["region"]
        counts[region] = counts.get(region, 0) + 1
    for region in AREAS:
        assert counts.get(region, 0) >= 3, (
            f"expected at least 3 candidate query polygons for {region!r}, "
            f"found {counts.get(region, 0)}"
        )


def test_every_feature_has_required_properties(feature_collection):
    required = {"id", "region", "feature_type"}
    for feature in feature_collection["features"]:
        props = feature["properties"]
        missing = required - props.keys()
        assert not missing, f"feature {feature.get('id')} missing {missing}"
        assert props["region"] in AREAS


def test_every_feature_geometry_is_valid(feature_collection):
    for feature in feature_collection["features"]:
        geom = shape(feature["geometry"])
        assert geom.is_valid, f"invalid geometry for feature {feature.get('id')}"


def test_every_feature_falls_within_its_region_aoi(feature_collection):
    for feature in feature_collection["features"]:
        region = feature["properties"]["region"]
        min_lon, min_lat, max_lon, max_lat = AREAS[region]["bbox_4326"]
        geom = shape(feature["geometry"])
        b_min_lon, b_min_lat, b_max_lon, b_max_lat = geom.bounds
        assert b_min_lon >= min_lon, feature["properties"]["id"]
        assert b_max_lon <= max_lon, feature["properties"]["id"]
        assert b_min_lat >= min_lat, feature["properties"]["id"]
        assert b_max_lat <= max_lat, feature["properties"]["id"]

"""Unit tests for pipeline.sample_design -- stratified, capped, seed-stable
sample point design (02-06-PLAN.md). All tests run against a synthetic,
in-memory WorldCover-shaped array (rasterio.transform.from_bounds); no
network access, no dependence on pipeline.sample_design.worldcover_window
actually calling out.
"""

import numpy as np
import pytest
import yaml
from rasterio.transform import from_bounds

from course.config import AREAS, BLOCK_SIZE_M
from pipeline import sample_design
from pipeline.sample_design import AREAS_YAML_PATH, _block_id, generate_sample_points

# --- Task 1: areas.yaml ---


def test_areas_yaml_has_both_regions_with_required_keys():
    with open(AREAS_YAML_PATH) as f:
        pipeline_areas = yaml.safe_load(f)

    assert "bern" in pipeline_areas
    assert "seville" in pipeline_areas
    for region, params in pipeline_areas.items():
        assert "n_target" in params, region
        assert "class_caps" in params, region
        assert "seed" in params, region
        assert "min_spacing_m" in params, region


# --- Synthetic WorldCover array shared across tests ---


def _synthetic_worldcover_array(area: str, shape=(600, 600)):
    """Build a synthetic WorldCover-code array spanning ``area``'s real AOI.

    Background is crop (40, code appears everywhere by default) with large
    dedicated blocks of vegetation (10), built (50) and water (80) --
    each block's stride-5 candidate pool comfortably exceeds
    pipeline/areas.yaml's caps (500/500/500/400) -- plus one small bare (60)
    patch whose candidate pool is deliberately smaller than its 150 cap, to
    exercise the "clamp to available pool" path (T-02-13).
    """
    min_lon, min_lat, max_lon, max_lat = AREAS[area]["bbox_4326"]
    height, width = shape
    transform = from_bounds(min_lon, min_lat, max_lon, max_lat, width, height)

    arr = np.full(shape, 40, dtype=np.uint8)  # crop background
    arr[0:300, 0:300] = 10  # vegetation quadrant
    arr[300:600, 0:300] = 50  # built quadrant
    arr[0:300, 300:450] = 80  # water strip
    arr[300:320, 300:320] = 60  # small bare patch -- pool < cap
    return arr, transform


@pytest.fixture
def patch_worldcover_window(monkeypatch):
    """Factory fixture: monkeypatch sample_design.worldcover_window to return
    a synthetic array for the given area, with no network call."""

    def _patch(area: str, shape=(600, 600)):
        arr, transform = _synthetic_worldcover_array(area, shape)
        monkeypatch.setattr(
            sample_design, "worldcover_window", lambda bbox_4326: (arr, transform)
        )
        return arr, transform

    return _patch


def test_generate_sample_points_respects_class_caps(patch_worldcover_window):
    patch_worldcover_window("bern")
    gdf = generate_sample_points("bern")

    with open(AREAS_YAML_PATH) as f:
        caps = yaml.safe_load(f)["bern"]["class_caps"]

    # worldcover_class -> label mapping is not resolved by generate_sample_points
    # (that's Plan 02-07's job); map the raw codes back to labels here just to
    # check per-class counts against the caps.
    from course.live.labels import class_to_label

    counts = {}
    for code in gdf["worldcover_class"]:
        label = class_to_label(int(code))
        counts[label] = counts.get(label, 0) + 1

    for label, cap in caps.items():
        assert counts.get(label, 0) <= cap, f"{label} exceeded its cap of {cap}"

    # Majority classes (huge synthetic pools) should hit their cap exactly.
    assert counts["crop"] == caps["crop"]
    assert counts["vegetation"] == caps["vegetation"]
    assert counts["built"] == caps["built"]
    assert counts["water"] == caps["water"]

    # Bare's synthetic pool (20x20 = 400 px, stride 5 -> 4x4 = 16 candidates)
    # is smaller than its 150 cap -- generate_sample_points must take the
    # whole pool, never more, never raise.
    assert 0 < counts["bare"] < caps["bare"]


def test_generate_sample_points_never_exceeds_synthetic_pool(monkeypatch):
    """A tiny synthetic array where the water class's candidate pool (1
    pixel) is smaller than its cap -- generate_sample_points must return at
    most the pool size for that class, never duplicate points to reach the
    cap (T-02-13)."""
    min_lon, min_lat, max_lon, max_lat = AREAS["bern"]["bbox_4326"]
    shape = (10, 10)
    transform = from_bounds(min_lon, min_lat, max_lon, max_lat, shape[1], shape[0])
    arr = np.full(shape, 40, dtype=np.uint8)
    arr[0, 0] = 80  # exactly one water pixel

    monkeypatch.setattr(
        sample_design, "worldcover_window", lambda bbox_4326: (arr, transform)
    )
    gdf = generate_sample_points("bern")

    water_rows = gdf[gdf["worldcover_class"] == 80]
    assert len(water_rows) == 1  # only one candidate existed, cap is 400

    # No duplicate sample_ids, no duplicate (lon, lat) pairs.
    assert gdf["sample_id"].is_unique
    assert not gdf.duplicated(subset=["lon", "lat"]).any()


def test_generate_sample_points_seed_stable(patch_worldcover_window):
    """Two independent calls at the same pinned seed must produce a
    byte-identical sample_id -> (lon, lat) mapping (DATA-03 requirement --
    2018/2021/2024 tables join on sample_id)."""
    patch_worldcover_window("bern")
    gdf1 = generate_sample_points("bern")

    patch_worldcover_window("bern")
    gdf2 = generate_sample_points("bern")

    assert list(gdf1["sample_id"]) == list(gdf2["sample_id"])
    np.testing.assert_array_equal(gdf1["lon"].to_numpy(), gdf2["lon"].to_numpy())
    np.testing.assert_array_equal(gdf1["lat"].to_numpy(), gdf2["lat"].to_numpy())
    np.testing.assert_array_equal(
        gdf1["worldcover_class"].to_numpy(), gdf2["worldcover_class"].to_numpy()
    )


def test_generate_sample_points_sample_id_dense_range(patch_worldcover_window):
    patch_worldcover_window("bern")
    gdf = generate_sample_points("bern")
    assert list(gdf["sample_id"]) == list(range(len(gdf)))


def test_generate_sample_points_crs_is_4326(patch_worldcover_window):
    patch_worldcover_window("bern")
    gdf = generate_sample_points("bern")
    assert gdf.crs is not None and gdf.crs.to_epsg() == 4326


def test_generate_sample_points_unknown_area_raises():
    with pytest.raises(KeyError):
        generate_sample_points("nowhere")


# --- Task 2: _block_id (pure function, direct unit tests) ---


def test_block_id_same_within_cell_different_across_cells():
    # Two points within the same 1.5 km cell (block_size_m=1500): both in
    # cell (0, 0) since 0 <= x,y < 1500.
    x = np.array([100.0, 1400.0, 3200.0])
    y = np.array([100.0, 1100.0, 1000.0])
    ids = _block_id(x, y, block_size_m=1500)

    assert ids[0] == ids[1]  # same 1.5 km cell
    assert ids[2] != ids[0]  # one cell over on x


def test_block_id_uses_course_config_block_size_m():
    assert BLOCK_SIZE_M == 1500


# --- Task 2: x/y projection + block_id wired into generate_sample_points ---


def test_generate_sample_points_block_count_well_above_five(patch_worldcover_window):
    """Synthetic sample spans Bern's full ~23x23 km AOI -- block_id count
    must clear DATA-08's >=5-blocks-per-region floor with enormous margin,
    matching 02-RESEARCH.md's measured 150-509 groups at this AOI scale."""
    patch_worldcover_window("bern", shape=(600, 600))
    gdf = generate_sample_points("bern")

    n_blocks = gdf["block_id"].nunique()
    assert n_blocks > 5
    assert n_blocks > 50  # well into the research's measured range


def test_generate_sample_points_xy_in_utm_range_not_degrees(patch_worldcover_window):
    """x/y must be in the region's projected UTM CRS (EPSG:32632 for Bern),
    not still in EPSG:4326 degrees -- a cheap sanity check that the
    reprojection actually happened (PITFALLS.md Pitfall 3 analogue)."""
    patch_worldcover_window("bern")
    gdf = generate_sample_points("bern")

    from pyproj import Transformer

    min_lon, min_lat, max_lon, max_lat = AREAS["bern"]["bbox_4326"]
    transformer = Transformer.from_crs("EPSG:4326", "EPSG:32632", always_xy=True)
    corners_x, corners_y = zip(
        *[
            transformer.transform(lon, lat)
            for lon in (min_lon, max_lon)
            for lat in (min_lat, max_lat)
        ]
    )
    margin = 1000  # meters, generous
    x_lo, x_hi = min(corners_x) - margin, max(corners_x) + margin
    y_lo, y_hi = min(corners_y) - margin, max(corners_y) + margin

    assert (gdf["x"] >= x_lo).all() and (gdf["x"] <= x_hi).all()
    assert (gdf["y"] >= y_lo).all() and (gdf["y"] <= y_hi).all()
    # Not still in degree magnitude.
    assert (gdf["x"] > 1000).all()
    assert (gdf["y"] > 1000).all()

    # The returned GeoDataFrame's own geometry/CRS stays EPSG:4326 --
    # x/y are plain float columns, not a second geometry.
    assert gdf.crs.to_epsg() == 4326


def test_generate_sample_points_block_id_matches_direct_computation(
    patch_worldcover_window,
):
    patch_worldcover_window("bern")
    gdf = generate_sample_points("bern")

    expected = _block_id(gdf["x"].to_numpy(), gdf["y"].to_numpy(), BLOCK_SIZE_M)
    assert list(gdf["block_id"]) == list(expected)

"""Unit tests for pipeline.attach_labels -- wiring the fixed sample-point
set to its course label (ESA WorldCover 2021) and an INDEPENDENT validation
reference (EEA HRL Imperviousness 2018), never conflating the two
(02-07-PLAN.md Task 2; PITFALLS.md Pitfall 6, "validation_source ==
label_source"). class_to_label itself is already unit-tested in
tests/test_labels.py (Plan 02-03) -- these tests are about the WIRING.
"""

from unittest.mock import patch

import geopandas as gpd
import numpy as np
import rasterio

from course.config import AREAS
from course.live.labels import class_to_label
from pipeline.attach_labels import (
    _sample_single_band_window,
    attach_labels,
    label_source,
    validation_source,
)

# Covers vegetation (10, 20, 30), crop (40), built (50), bare (60), water (80).
_CODES_POOL = [10, 40, 50, 80, 60, 40, 50, 10, 30, 20]


def _synthetic_points(n=8, area="bern"):
    codes = (_CODES_POOL * ((n // len(_CODES_POOL)) + 1))[:n]
    min_lon, min_lat, max_lon, max_lat = AREAS[area]["bbox_4326"]
    rng = np.random.default_rng(11)
    lon = rng.uniform(min_lon, max_lon, size=n)
    lat = rng.uniform(min_lat, max_lat, size=n)
    x = rng.uniform(0, 9, size=n)
    y = rng.uniform(0, 9, size=n)
    geometry = gpd.points_from_xy(lon, lat)
    return gpd.GeoDataFrame(
        {
            "sample_id": np.arange(n, dtype=np.int64),
            "lon": lon,
            "lat": lat,
            "x": x,
            "y": y,
            "worldcover_class": np.array(codes, dtype=np.int64),
        },
        geometry=geometry,
        crs="EPSG:4326",
    )


def _synthetic_imd_window(shape=(10, 10), value=42):
    arr = np.full(shape, value, dtype=np.uint8)
    return arr, rasterio.Affine.identity()


class TestSampleSingleBandWindow:
    """Mirrors course.live.aef_cog's TestSamplePointsFromWindow -- indexes an
    already-fetched single-band array by (row, col) derived from an
    inverted rasterio Affine transform; never re-queries a remote source."""

    def test_center_pixel_coordinate_returns_that_pixels_value(self):
        arr = np.arange(25, dtype=np.float32).reshape(5, 5)
        transform = rasterio.Affine.identity()
        points_xy = np.array([[2.0, 2.0]])

        result = _sample_single_band_window(arr, transform, points_xy)

        assert result.shape == (1,)
        assert result[0] == arr[2, 2]

    def test_out_of_bounds_point_returns_nan_not_indexerror(self):
        arr = np.zeros((5, 5), dtype=np.float32)
        transform = rasterio.Affine.identity()
        points_xy = np.array([[10.0, 10.0]])

        result = _sample_single_band_window(arr, transform, points_xy)

        assert result.shape == (1,)
        assert np.isnan(result[0])

    def test_multiple_points_map_to_correct_values_in_order(self):
        arr = np.arange(25, dtype=np.float32).reshape(5, 5)
        transform = rasterio.Affine.identity()
        # points_xy is (x, y) = (col, row).
        points_xy = np.array([[0.0, 0.0], [4.0, 4.0], [3.0, 2.0]])

        result = _sample_single_band_window(arr, transform, points_xy)

        np.testing.assert_allclose(result, [arr[0, 0], arr[4, 4], arr[2, 3]])


class TestAttachLabelsWiring:
    def test_label_matches_class_to_label_for_every_row(self):
        points = _synthetic_points(n=8)
        arr, transform = _synthetic_imd_window()

        with patch(
            "pipeline.attach_labels.imd_2018_window", return_value=(arr, transform)
        ):
            result = attach_labels("bern", points)

        expected = [class_to_label(int(c)) for c in points["worldcover_class"]]
        assert list(result["label"]) == expected

    def test_label_source_and_validation_source_never_equal(self):
        points = _synthetic_points(n=8)
        arr, transform = _synthetic_imd_window()

        with patch(
            "pipeline.attach_labels.imd_2018_window", return_value=(arr, transform)
        ):
            result = attach_labels("bern", points)

        assert label_source != validation_source
        assert (result["label_source"] != result["validation_source"]).all()
        assert set(result["label_source"]) == {"esa_worldcover_2021"}
        assert set(result["validation_source"]) == {"eea_hrl_imperviousness_2018"}

    def test_imd_2018_window_called_exactly_once_regardless_of_point_count(self):
        for n in (3, 30):
            points = _synthetic_points(n=n)
            arr, transform = _synthetic_imd_window()

            with patch(
                "pipeline.attach_labels.imd_2018_window",
                return_value=(arr, transform),
            ) as mock_imd:
                attach_labels("bern", points)

            assert mock_imd.call_count == 1

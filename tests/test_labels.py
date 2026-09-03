from unittest.mock import MagicMock, patch

import numpy as np
import pytest
from rasterio.io import MemoryFile
from rasterio.transform import from_origin

from course.config import AREAS
from course.live import LiveSourceUnavailable
from course.live.labels import (
    WORLDCOVER_CLASS_TO_LABEL,
    class_to_label,
    imd_2018_window,
    worldcover_tile_name,
)

OFFICIAL_WORLDCOVER_CODES = {10, 20, 30, 40, 50, 60, 70, 80, 90, 95, 100}


def _synthetic_geotiff_bytes(shape=(4, 4), value=50, crs="EPSG:32632"):
    """Build a tiny in-memory single-band GeoTIFF, for mocking a network response."""
    arr = np.full(shape, value, dtype=np.uint8)
    transform = from_origin(600000, 5200000, 20, 20)
    with MemoryFile() as memfile:
        with memfile.open(
            driver="GTiff",
            height=shape[0],
            width=shape[1],
            count=1,
            dtype=arr.dtype,
            crs=crs,
            transform=transform,
        ) as ds:
            ds.write(arr, 1)
        return memfile.read()


# --- Task 1: WorldCover tile naming and class mapping (no network) ---


def test_worldcover_tile_name_bern():
    assert worldcover_tile_name(7.4474, 46.9480) == "N45E006"


def test_worldcover_tile_name_seville():
    assert worldcover_tile_name(-5.9845, 37.3891) == "N36W006"


def test_class_to_label_known_codes():
    assert class_to_label(50) == "built"
    assert class_to_label(40) == "crop"
    assert class_to_label(80) == "water"


def test_class_to_label_every_official_code_mapped():
    assert OFFICIAL_WORLDCOVER_CODES <= WORLDCOVER_CLASS_TO_LABEL.keys()


def test_class_to_label_unrecognized_code_raises_keyerror():
    with pytest.raises(KeyError, match="999"):
        class_to_label(999)


def test_worldcover_class_to_label_values_are_valid_course_labels():
    valid_labels = {"built", "crop", "vegetation", "water", "bare"}
    assert set(WORLDCOVER_CLASS_TO_LABEL.values()) <= valid_labels


def test_worldcover_window_calls_rasterio_open_once_per_aoi(monkeypatch):
    """Locks in the 'one bounded window read, never per-point' contract
    (02-RESEARCH.md Pitfall 4) for the WorldCover reader: rasterio.open must
    be called exactly once per worldcover_window() call, regardless of AOI
    size or how many sample points are later drawn from the array."""
    from course.live import labels

    call_count = {"n": 0}

    class FakeDataset:
        # A plausible north-up EPSG:4326 transform covering Bern's AOI.
        transform = from_origin(6.0, 48.0, 0.0001, 0.0001)

        def read(self, band, window=None):
            return np.full((2, 2), 40, dtype=np.uint8)

        def window_transform(self, win):
            return self.transform

        def __enter__(self):
            call_count["n"] += 1
            return self

        def __exit__(self, *exc):
            return False

    monkeypatch.setattr(labels.rasterio, "open", lambda *a, **k: FakeDataset())

    arr, _transform = labels.worldcover_window(AREAS["bern"]["bbox_4326"])

    assert call_count["n"] == 1
    assert arr.shape == (2, 2)


# --- Task 2: imd_2018_window (mocked request, no network) ---


def test_imd_2018_window_builds_correct_request_and_parses_response():
    tiff_bytes = _synthetic_geotiff_bytes(shape=(4, 4), value=50)
    mock_response = MagicMock()
    mock_response.content = tiff_bytes
    mock_response.raise_for_status = MagicMock()

    with patch(
        "course.live.labels.requests.get", return_value=mock_response
    ) as mock_get:
        arr, transform = imd_2018_window(
            AREAS["bern"]["bbox_4326"], dst_epsg=32632, size=(4, 4)
        )

    assert mock_get.call_count == 1
    _, kwargs = mock_get.call_args
    assert kwargs["params"]["bboxSR"] == 4326
    assert kwargs["params"]["imageSR"] == 32632
    assert kwargs["params"]["format"] == "tiff"
    assert kwargs["params"]["size"] == "4,4"

    assert arr.shape == (4, 4)
    assert np.all(arr == 50)
    assert transform is not None


def test_imd_2018_window_raises_live_source_unavailable_on_bad_response():
    mock_response = MagicMock()
    mock_response.content = b"not a geotiff"
    mock_response.raise_for_status = MagicMock()

    with (
        patch("course.live.labels.requests.get", return_value=mock_response),
        pytest.raises(LiveSourceUnavailable),
    ):
        imd_2018_window(AREAS["bern"]["bbox_4326"], dst_epsg=32632, size=(4, 4))


# --- Network-marked integration tests (excluded from the default fast suite) ---


@pytest.mark.network
def test_worldcover_window_live_bern():
    from course.live.labels import worldcover_window

    arr, _transform = worldcover_window(AREAS["bern"]["bbox_4326"])
    assert arr.ndim == 2
    assert arr.size > 0


@pytest.mark.network
def test_imd_2018_window_live_bern():
    bbox = AREAS["bern"]["bbox_4326"]
    size = (64, 64)
    arr, _transform = imd_2018_window(bbox, dst_epsg=32632, size=size)

    assert arr.shape == size
    in_range_or_nodata = ((arr >= 0) & (arr <= 100)) | (arr == 255)
    assert np.all(in_range_or_nodata)

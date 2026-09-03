import numpy as np
import pytest
from rasterio.transform import from_origin

from course.config import AREAS
from course.live.labels import (
    WORLDCOVER_CLASS_TO_LABEL,
    class_to_label,
    worldcover_tile_name,
)

OFFICIAL_WORLDCOVER_CODES = {10, 20, 30, 40, 50, 60, 70, 80, 90, 95, 100}


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


# --- Network-marked integration test (excluded from the default fast suite) ---


@pytest.mark.network
def test_worldcover_window_live_bern():
    from course.live.labels import worldcover_window

    arr, _transform = worldcover_window(AREAS["bern"]["bbox_4326"])
    assert arr.ndim == 2
    assert arr.size > 0

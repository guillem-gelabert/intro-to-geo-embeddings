import numpy as np
import pytest

from course.embeddings import NODATA, dequantize_aef


def test_dequantize_single_vector_unit_norm():
    rng = np.random.default_rng(0)
    raw = rng.integers(-127, 128, size=64, dtype=np.int8)

    result = dequantize_aef(raw)

    assert result.dtype == np.float32
    norm = np.linalg.norm(result)
    assert norm == pytest.approx(1.0, abs=1e-6)


def test_dequantize_window_nodata_pixel_is_nan():
    rng = np.random.default_rng(1)
    raw = rng.integers(-127, 128, size=(64, 3, 3), dtype=np.int8)
    raw[:, 1, 1] = NODATA

    result = dequantize_aef(raw)

    assert np.all(np.isnan(result[:, 1, 1]))
    finite_mask = np.ones((3, 3), dtype=bool)
    finite_mask[1, 1] = False
    for i in range(3):
        for j in range(3):
            if finite_mask[i, j]:
                assert np.all(np.isfinite(result[:, i, j]))
                assert np.linalg.norm(result[:, i, j]) == pytest.approx(1.0, abs=1e-6)


def test_dequantize_preserves_sign():
    raw = np.full(64, -50, dtype=np.int8)
    raw[0] = 50

    result = dequantize_aef(raw)

    assert result[0] > 0
    assert np.all(result[1:] < 0)


def test_dequantize_batch_no_cross_point_leakage():
    rng = np.random.default_rng(2)
    raw = rng.integers(-127, 128, size=(64, 5), dtype=np.int8)

    result = dequantize_aef(raw)

    assert result.shape == (64, 5)
    for i in range(5):
        expected = dequantize_aef(raw[:, i])
        assert np.allclose(result[:, i], expected, atol=1e-6, equal_nan=True)

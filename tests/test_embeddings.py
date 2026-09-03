import numpy as np
import pytest

from course.embeddings import NODATA, cosine_similarity_map, dequantize_aef


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


def test_dequantize_rejects_band_last_input():
    """A frozen table's A00..A63 columns come out as (n_points, 64). Passing
    that directly would normalize across points instead of bands and return
    silently wrong vectors, so it must raise instead."""
    band_last = np.zeros((5, 64), dtype=np.int8)
    with pytest.raises(ValueError, match="band axis first"):
        dequantize_aef(band_last)


def test_cosine_similarity_self_similarity_is_one():
    rng = np.random.default_rng(3)
    v = rng.normal(size=64).astype(np.float32)
    v = v / np.linalg.norm(v)
    matrix = np.tile(v, (5, 1))

    result = cosine_similarity_map(v, matrix)

    assert result[0] == pytest.approx(1.0, abs=1e-6)


def test_cosine_similarity_orthogonal_vectors_score_zero():
    a = np.zeros(64, dtype=np.float32)
    a[0] = 1.0
    b = np.zeros(64, dtype=np.float32)
    b[1] = 1.0
    matrix = b[np.newaxis, :]

    result = cosine_similarity_map(a, matrix)

    assert result[0] == pytest.approx(0.0, abs=1e-6)


def test_cosine_similarity_output_shape():
    rng = np.random.default_rng(4)
    query = rng.normal(size=64).astype(np.float32)
    matrix = rng.normal(size=(7, 64)).astype(np.float32)

    result = cosine_similarity_map(query, matrix)

    assert result.shape == (7,)
    assert result.dtype == np.float32


def test_cosine_similarity_matches_naive_loop():
    rng = np.random.default_rng(5)
    query = rng.normal(size=64).astype(np.float32) * 3.0
    matrix = (rng.normal(size=(10, 64)) * 2.0).astype(np.float32)

    result = cosine_similarity_map(query, matrix)

    naive = np.array(
        [
            row @ query / (np.linalg.norm(row) * np.linalg.norm(query))
            for row in matrix
        ]
    )
    assert np.allclose(result, naive, atol=1e-5)


def test_cosine_similarity_mismatched_dims_raises():
    query = np.zeros(64, dtype=np.float32)
    matrix = np.zeros((5, 32), dtype=np.float32)

    with pytest.raises(ValueError, match=r"\(64,\).*\(5, 32\)"):
        cosine_similarity_map(query, matrix)

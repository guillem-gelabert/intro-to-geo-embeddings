"""Tests for the checked-in Bern AlphaEarth clip raster.

Test 1/2 are non-network integrity checks against the file already checked
into the repo (``data/bern_aef_2024_clip.tif``): they must always pass, with
no internet access, so the notebook's offline Path B is provably safe.

Test 3 is network-marked (excluded from the default ``pytest`` run) and
exercises the actual regeneration path against the live AlphaEarth GCS
bucket.
"""

from pathlib import Path

import numpy as np
import pytest
import rasterio

from course.embeddings import dequantize_aef
from pipeline.extract_clip_raster import build_clip

CLIP_PATH = Path("data/bern_aef_2024_clip.tif")
MAX_BYTES = 3 * 1024 * 1024


def test_checked_in_clip_is_a_small_raw_int8_64_band_cog():
    assert CLIP_PATH.exists(), f"{CLIP_PATH} must be checked into the repo"
    assert CLIP_PATH.stat().st_size < MAX_BYTES

    with rasterio.open(CLIP_PATH) as ds:
        assert ds.count == 64
        assert ds.dtypes[0] == "int8"
        assert ds.nodata == -128


def test_checked_in_clip_dequantizes_to_unit_norm_vectors():
    with rasterio.open(CLIP_PATH) as ds:
        raw = ds.read()

    dequantized = dequantize_aef(raw)

    norms = np.linalg.norm(dequantized, axis=0)
    valid = ~np.isnan(norms)

    assert valid.any(), "expected at least some non-nodata pixels"
    finite_mask = np.isfinite(dequantized)
    # Every band at a valid pixel position must be finite.
    assert np.all(finite_mask[:, valid])
    np.testing.assert_allclose(norms[valid], 1.0, atol=1e-3)


@pytest.mark.network
def test_build_clip_regenerates_against_live_source(tmp_path):
    out_path = tmp_path / "clip.tif"

    provenance = build_clip(out_path=out_path)

    expected_keys = {
        "embedding_product",
        "dataset_version",
        "year",
        "extraction_date",
        "source_path",
        "sampling_method",
        "crs",
        "bbox_4326",
        "shape",
        "license",
        "attribution",
        "created_by",
    }
    assert expected_keys.issubset(provenance.keys())
    assert provenance["license"] == "CC BY 4.0"

    with rasterio.open(out_path) as ds:
        assert ds.count == 64
        assert ds.dtypes[0] == "int8"
        assert ds.nodata == -128

import numpy as np
import pandas as pd
import pytest

from course.schema import (
    FROZEN_REQUIRED,
    S2_COLS,
    embedding_cols,
    to_matrix,
    validate,
    validate_frozen,
)


def test_validate_happy_path(make_gdf):
    n, n_dims = 5, 64
    gdf = make_gdf(n=n, n_dims=n_dims)

    result = validate(gdf)
    assert result is gdf

    matrix = to_matrix(gdf)
    assert matrix.shape == (n, n_dims)
    assert matrix.dtype == np.float32


def test_validate_missing_required_column(make_gdf):
    gdf = make_gdf(missing_cols=["label"])
    with pytest.raises(AssertionError):
        validate(gdf)


def test_validate_wrong_crs(make_gdf):
    gdf = make_gdf(crs="EPSG:2056")
    with pytest.raises(AssertionError):
        validate(gdf)


def test_validate_non_unit_norm(make_gdf):
    gdf = make_gdf(unit_norm=False)
    with pytest.raises(AssertionError):
        validate(gdf)


def test_validate_no_embedding_columns(make_gdf):
    gdf = make_gdf()
    with pytest.raises(AssertionError):
        validate(gdf, embedding_prefix="Z")


def test_embedding_cols_matches_prefix_and_digits_only():
    df = pd.DataFrame(
        {
            "A00": [1.0],
            "A01": [2.0],
            "Abc": [3.0],
            "Alpha": [4.0],
            "B00": [5.0],
        }
    )
    cols = embedding_cols(df, prefix="A")
    assert cols == ["A00", "A01"]


def _add_frozen_columns(gdf):
    n = len(gdf)
    gdf = gdf.copy()
    gdf["region"] = "bern"
    gdf["block_id"] = np.arange(n)
    gdf["x"] = np.arange(n, dtype=np.float64)
    gdf["y"] = np.arange(n, dtype=np.float64)
    for col in S2_COLS:
        gdf[col] = 0.1
    return gdf


def test_validate_frozen_happy_path(make_gdf):
    gdf = _add_frozen_columns(make_gdf())
    result = validate_frozen(gdf)
    assert result is gdf


def test_validate_frozen_missing_block_id(make_gdf):
    gdf = _add_frozen_columns(make_gdf()).drop(columns=["block_id"])
    with pytest.raises(AssertionError, match="block_id"):
        validate_frozen(gdf)


def test_validate_frozen_missing_s2_column(make_gdf):
    gdf = _add_frozen_columns(make_gdf()).drop(columns=["S2_B11"])
    with pytest.raises(AssertionError, match="S2_B11"):
        validate_frozen(gdf)


def test_frozen_required_extends_required_without_mutating_it():
    from course.schema import REQUIRED

    assert set(REQUIRED).issubset(set(FROZEN_REQUIRED))
    for extra in ["region", "block_id", "x", "y", *S2_COLS]:
        assert extra in FROZEN_REQUIRED

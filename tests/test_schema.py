import numpy as np
import pandas as pd
import pytest

from course.schema import embedding_cols, to_matrix, validate


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

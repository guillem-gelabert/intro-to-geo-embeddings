import geopandas as gpd
import numpy as np
import pytest
from shapely.geometry import Point
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import GroupKFold, LeaveOneGroupOut

from course.schema import to_matrix
from course.validation import make_blocks, spatial_cv_report


def test_make_blocks_rejects_geographic_crs(make_gdf):
    gdf = make_gdf(n=5, crs="EPSG:4326")

    with pytest.raises(ValueError, match="(?i)projected|geographic"):
        make_blocks(gdf, block_size_m=1500)


def test_make_blocks_groups_nearby_points_and_separates_far_points():
    gdf = gpd.GeoDataFrame(
        {"id": [0, 1, 2]},
        geometry=[Point(0, 0), Point(100, 0), Point(2000, 0)],
        crs="EPSG:2056",
    )

    blocks = make_blocks(gdf, block_size_m=1500)

    assert blocks[0] == blocks[1]
    assert blocks[0] != blocks[2]


def test_make_blocks_length_and_idempotent():
    gdf = gpd.GeoDataFrame(
        {"id": range(4)},
        geometry=[Point(i * 500, 0) for i in range(4)],
        crs="EPSG:2056",
    )

    first = make_blocks(gdf, block_size_m=1500)
    second = make_blocks(gdf, block_size_m=1500)

    assert len(first) == len(gdf)
    assert np.array_equal(first, second)


def test_spatial_cv_report_with_group_kfold(make_gdf):
    gdf = make_gdf(n=40, unit_norm=True)
    X = to_matrix(gdf)
    y = gdf["label"].to_numpy()
    groups = np.array([0] * 20 + [1] * 20)

    result = spatial_cv_report(
        LogisticRegression(), X, y, groups, cv=GroupKFold(n_splits=2)
    )

    assert "test_balanced_accuracy" in result
    assert "test_f1_macro" in result
    assert result["n_groups"] == 2
    assert result["n_splits"] == 2


def test_spatial_cv_report_with_leave_one_group_out(make_gdf):
    gdf = make_gdf(n=40, unit_norm=True)
    X = to_matrix(gdf)
    y = gdf["label"].to_numpy()
    groups = np.array([0] * 20 + [1] * 20)

    result = spatial_cv_report(
        LogisticRegression(), X, y, groups, cv=LeaveOneGroupOut()
    )

    assert "test_balanced_accuracy" in result
    assert "test_f1_macro" in result
    assert result["n_groups"] == 2
    assert result["n_splits"] == 2

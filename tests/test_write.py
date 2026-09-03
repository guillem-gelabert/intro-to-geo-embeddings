"""Unit tests for pipeline.write -- table assembly, GeoParquet write with
embedded `course_provenance` metadata, and manifest generation
(02-09-PLAN.md Task 1). All non-network: synthetic 5-row inputs stand in
for generate_sample_points/extract_area_year/attach_labels/attach_s2's real
outputs, joined on the same fixed `sample_id` set.
"""

import hashlib
import json

import geopandas as gpd
import numpy as np
import pandas as pd
import pyarrow.parquet as pq
import pytest
from shapely.geometry import Point

from course.schema import A_COLS, FROZEN_REQUIRED, S2_COLS, validate_frozen
from pipeline.write import assemble_table, write_manifest, write_table


def _sample_points(n=5, area="bern"):
    rng = np.random.default_rng(0)
    lon = 7.30 + rng.uniform(0, 0.3, size=n)
    lat = 46.85 + rng.uniform(0, 0.2, size=n)
    geometry = [Point(x, y) for x, y in zip(lon, lat)]
    return gpd.GeoDataFrame(
        {
            "sample_id": np.arange(n, dtype=np.int64),
            "region": area,
            "lon": lon,
            "lat": lat,
            "x": rng.uniform(370000, 390000, size=n),
            "y": rng.uniform(5190000, 5210000, size=n),
            "block_id": [f"{i}_0" for i in range(n)],
            "worldcover_class": np.full(n, 40, dtype=np.int64),
        },
        geometry=geometry,
        crs="EPSG:4326",
    )


def _aef_df(points):
    n = len(points)
    rng = np.random.default_rng(1)
    vecs = rng.normal(size=(n, len(A_COLS))).astype(np.float32)
    vecs /= np.linalg.norm(vecs, axis=1, keepdims=True)
    df = pd.DataFrame(vecs, columns=A_COLS)
    df.insert(0, "sample_id", points["sample_id"].to_numpy())
    return df


def _labels_gdf(points):
    result = points.copy()
    result["label"] = "crop"
    result["label_source"] = "esa_worldcover_2021"
    result["imd_2018"] = 10.0
    result["validation_source"] = "eea_hrl_imperviousness_2018"
    return result


def _s2_df(points):
    n = len(points)
    data = {"sample_id": points["sample_id"].to_numpy()}
    for col in S2_COLS:
        data[col] = np.full(n, 0.1, dtype=np.float32)
    data["s2_n_scenes"] = np.full(n, 2, dtype=np.int64)
    return pd.DataFrame(data)


def test_assemble_table_matches_frozen_required():
    points = _sample_points()
    aef_df = _aef_df(points)
    labels_gdf = _labels_gdf(points)
    s2_df = _s2_df(points)

    table = assemble_table(points, aef_df, labels_gdf, s2_df, year=2021)

    assert len(table) == len(points)
    for col in FROZEN_REQUIRED:
        assert col in table.columns, f"missing FROZEN_REQUIRED column {col!r}"
    for col in A_COLS:
        assert col in table.columns
    assert (table["year"] == 2021).all()
    assert table.crs is not None and table.crs.to_epsg() == 4326
    validate_frozen(table)


def test_assemble_table_raises_on_row_count_mismatch():
    points = _sample_points(n=5)
    # aef_df is missing the row for sample_id=0 -- a real join mismatch, not
    # just a differently-ordered frame.
    aef_df = _aef_df(points)
    aef_df = aef_df[aef_df["sample_id"] != 0].reset_index(drop=True)
    labels_gdf = _labels_gdf(points)
    s2_df = _s2_df(points)

    with pytest.raises(ValueError, match="row count"):
        assemble_table(points, aef_df, labels_gdf, s2_df, year=2021)


def test_write_table_round_trips_provenance(tmp_path):
    points = _sample_points()
    aef_df = _aef_df(points)
    labels_gdf = _labels_gdf(points)
    s2_df = _s2_df(points)
    table = assemble_table(points, aef_df, labels_gdf, s2_df, year=2021)

    provenance = {
        "embedding_product": "AlphaEarth Foundations Satellite Embedding v1 (annual)",
        "region": "bern",
        "year": 2021,
        "nested": {"a": [1, 2, 3]},
    }
    path = tmp_path / "bern_aef_2021_v1.1.parquet"
    write_table(table, path, provenance)

    t = pq.read_table(path)
    assert b"course_provenance" in t.schema.metadata
    round_tripped = json.loads(t.schema.metadata[b"course_provenance"])
    assert round_tripped == provenance


def test_write_manifest_sha256_matches_independent_computation(tmp_path):
    points = _sample_points()
    aef_df = _aef_df(points)
    labels_gdf = _labels_gdf(points)
    s2_df = _s2_df(points)
    table = assemble_table(points, aef_df, labels_gdf, s2_df, year=2021)

    path = tmp_path / "bern_aef_2021_v1.1.parquet"
    write_table(table, path, {"region": "bern", "year": 2021})

    manifest_path = tmp_path / "manifest.json"
    write_manifest([{"path": path}], manifest_path)

    manifest = json.loads(manifest_path.read_text())
    expected_sha256 = hashlib.sha256(path.read_bytes()).hexdigest()
    assert manifest[path.name]["sha256"] == expected_sha256
    assert manifest[path.name]["rows"] == len(table)
    assert "built_at" in manifest[path.name]
    assert "builder_git_sha" in manifest[path.name]

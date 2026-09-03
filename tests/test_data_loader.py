import functools
import hashlib
import http.server
import json
import threading
from unittest.mock import MagicMock

import geopandas as gpd
import numpy as np
import pandas as pd
import pyarrow.parquet as pq
import pytest
from shapely.geometry import Point

import course.data as data_module


def _frozen_gdf(area="bern", year=2021, n=3):
    """Build a synthetic GeoDataFrame matching course.schema.FROZEN_REQUIRED."""
    rng = np.random.default_rng(42)
    lon = 7.4474 + rng.normal(scale=0.01, size=n)
    lat = 46.9480 + rng.normal(scale=0.01, size=n)

    embeddings = rng.normal(size=(n, 64)).astype(np.float32)
    norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
    embeddings = (embeddings / norms).astype(np.float32)

    data = {
        "sample_id": np.arange(n),
        "lon": lon,
        "lat": lat,
        "year": np.full(n, year),
        "label": ["vegetation" if i % 2 == 0 else "built" for i in range(n)],
        "label_source": ["test"] * n,
        "region": [area] * n,
        "block_id": np.arange(n),
        "x": lon,
        "y": lat,
    }
    for band in ["S2_B02", "S2_B03", "S2_B04", "S2_B08", "S2_B11", "S2_B12"]:
        data[band] = rng.uniform(0.0, 0.3, n).astype(np.float32)
    for i in range(64):
        data[f"A{i:02d}"] = embeddings[:, i]

    geometry = [Point(x, y) for x, y in zip(lon, lat)]
    return gpd.GeoDataFrame(pd.DataFrame(data), geometry=geometry, crs="EPSG:4326")


def _write_frozen_parquet(gdf, path, provenance):
    """Write gdf to path with course_provenance parquet metadata, matching the
    exact pattern Plan 02-09's writer will produce (02-RESEARCH.md
    "Provenance metadata round-trip")."""
    path.parent.mkdir(parents=True, exist_ok=True)
    gdf.to_parquet(
        path, schema_version="1.1.0", write_covering_bbox=True, compression="zstd"
    )
    table = pq.read_table(path)
    meta = dict(table.schema.metadata or {})
    meta[b"course_provenance"] = json.dumps(provenance).encode()
    pq.write_table(table.replace_schema_metadata(meta), path)


def test_local_hit_reads_directly_without_remote_fetch(tmp_path, monkeypatch):
    area, year = "bern", 2021
    gdf = _frozen_gdf(area, year)
    filename = f"{area}_aef_{year}_v1.1.parquet"
    local = tmp_path / area / filename
    provenance = {"dataset_version": "1.1", "area": area, "year": year}
    _write_frozen_parquet(gdf, local, provenance)

    mock_get = MagicMock()
    monkeypatch.setattr(data_module.requests, "get", mock_get)

    result = data_module.load(area, year, data_dir=tmp_path)

    mock_get.assert_not_called()
    assert len(result) == len(gdf)
    assert result.attrs["course_provenance"] == provenance


def test_remote_fallback_downloads_verifies_and_writes(tmp_path, monkeypatch):
    area, year = "bern", 2021
    gdf = _frozen_gdf(area, year)
    filename = f"{area}_aef_{year}_v1.1.parquet"
    provenance = {"dataset_version": "1.1", "area": area, "year": year}

    source_path = tmp_path / "_source" / filename
    _write_frozen_parquet(gdf, source_path, provenance)
    content = source_path.read_bytes()
    sha = hashlib.sha256(content).hexdigest()

    manifest = {filename: {"sha256": sha, "rows": len(gdf)}}
    (tmp_path / "manifest.json").write_text(json.dumps(manifest))

    mock_resp = MagicMock()
    mock_resp.content = content
    mock_resp.raise_for_status = MagicMock()
    mock_get = MagicMock(return_value=mock_resp)
    monkeypatch.setattr(data_module.requests, "get", mock_get)

    result = data_module.load(area, year, data_dir=tmp_path)

    mock_get.assert_called_once()
    local = tmp_path / area / filename
    assert local.exists()
    assert local.read_bytes() == content
    assert result.attrs["course_provenance"] == provenance


def test_checksum_mismatch_raises_and_leaves_no_partial_file(tmp_path, monkeypatch):
    area, year = "bern", 2021
    gdf = _frozen_gdf(area, year)
    filename = f"{area}_aef_{year}_v1.1.parquet"
    provenance = {"dataset_version": "1.1", "area": area, "year": year}

    source_path = tmp_path / "_source" / filename
    _write_frozen_parquet(gdf, source_path, provenance)
    content = source_path.read_bytes()
    actual_sha = hashlib.sha256(content).hexdigest()
    wrong_sha = "0" * 64

    manifest = {filename: {"sha256": wrong_sha, "rows": len(gdf)}}
    (tmp_path / "manifest.json").write_text(json.dumps(manifest))

    mock_resp = MagicMock()
    mock_resp.content = content
    mock_resp.raise_for_status = MagicMock()
    mock_get = MagicMock(return_value=mock_resp)
    monkeypatch.setattr(data_module.requests, "get", mock_get)

    with pytest.raises(
        AssertionError, match=f"{wrong_sha}.*{actual_sha}|{actual_sha}.*{wrong_sha}"
    ):
        data_module.load(area, year, data_dir=tmp_path)

    local = tmp_path / area / filename
    assert not local.exists()


def test_missing_manifest_entry_raises_file_not_found(tmp_path):
    area, year = "bern", 2021
    (tmp_path / "manifest.json").write_text(json.dumps({}))

    with pytest.raises(FileNotFoundError, match=f"{area}.*{year}|{year}.*{area}"):
        data_module.load(area, year, data_dir=tmp_path)


@pytest.mark.network
def test_remote_fallback_real_http_server(tmp_path):
    """Exercise the exact remote-fetch-and-verify code path end to end via a
    real local HTTP server, independent of whether a public GitHub Release
    exists yet (it does not, until Plan 02-11)."""
    area, year = "bern", 2021
    gdf = _frozen_gdf(area, year)
    filename = f"{area}_aef_{year}_v1.1.parquet"
    provenance = {"dataset_version": "1.1", "area": area, "year": year}

    serve_dir = tmp_path / "serve"
    serve_dir.mkdir()
    source_path = serve_dir / filename
    _write_frozen_parquet(gdf, source_path, provenance)
    content = source_path.read_bytes()
    sha = hashlib.sha256(content).hexdigest()

    data_dir = tmp_path / "data"
    data_dir.mkdir()
    manifest = {filename: {"sha256": sha, "rows": len(gdf)}}
    (data_dir / "manifest.json").write_text(json.dumps(manifest))

    handler = functools.partial(
        http.server.SimpleHTTPRequestHandler, directory=str(serve_dir)
    )
    httpd = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
    port = httpd.server_address[1]
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    try:
        release_base = f"http://127.0.0.1:{port}"
        result = data_module.load(
            area, year, data_dir=data_dir, release_base=release_base
        )
    finally:
        httpd.shutdown()
        thread.join(timeout=5)

    local = data_dir / area / filename
    assert local.exists()
    assert hashlib.sha256(local.read_bytes()).hexdigest() == sha
    assert result.attrs["course_provenance"] == provenance

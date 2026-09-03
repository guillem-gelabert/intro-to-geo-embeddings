import numpy as np

A_COLS = [f"A{i:02d}" for i in range(64)]
S2_COLS = ["S2_B02", "S2_B03", "S2_B04", "S2_B08", "S2_B11", "S2_B12"]
REQUIRED = ["sample_id", "lon", "lat", "year", "label", "label_source"]


def embedding_cols(gdf, prefix: str = "A") -> list[str]:
    return [
        c for c in gdf.columns if c.startswith(prefix) and c[len(prefix) :].isdigit()
    ]


def validate(gdf, embedding_prefix: str = "A"):
    missing = [c for c in REQUIRED if c not in gdf]
    assert not missing, f"missing columns: {missing}"
    assert gdf.crs is not None and gdf.crs.to_epsg() == 4326, (
        "points must be EPSG:4326; reproject inside the notebook"
    )
    cols = embedding_cols(gdf, embedding_prefix)
    assert cols, f"no embedding columns found with prefix {embedding_prefix!r}"
    norms = np.linalg.norm(gdf[cols].to_numpy(np.float32), axis=1)
    assert np.allclose(norms, 1.0, atol=1e-3), "embeddings must be unit length"
    return gdf


def to_matrix(gdf, embedding_prefix: str = "A") -> np.ndarray:
    return gdf[embedding_cols(gdf, embedding_prefix)].to_numpy(np.float32)

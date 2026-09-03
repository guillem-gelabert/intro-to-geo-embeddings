import geopandas as gpd
import nbformat
import numpy as np
import pytest
from shapely.geometry import Point


@pytest.fixture
def make_gdf():
    """Factory fixture: build a synthetic GeoDataFrame matching course.schema's contract.

    make_gdf(n=5, n_dims=64, crs="EPSG:4326", unit_norm=True, missing_cols=None)
    """

    def _make_gdf(n=5, n_dims=64, crs="EPSG:4326", unit_norm=True, missing_cols=None):
        rng = np.random.default_rng(42)
        lon = 7.4474 + rng.normal(scale=0.01, size=n)
        lat = 46.9480 + rng.normal(scale=0.01, size=n)

        embed_cols = [f"A{i:02d}" for i in range(n_dims)]
        embeddings = rng.normal(size=(n, n_dims)).astype(np.float32)
        if unit_norm:
            norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
            embeddings = (embeddings / norms).astype(np.float32)

        data = {
            "sample_id": np.arange(n),
            "lon": lon,
            "lat": lat,
            "year": np.full(n, 2021),
            "label": ["vegetation" if i % 2 == 0 else "built" for i in range(n)],
            "label_source": ["test"] * n,
        }
        for i, col in enumerate(embed_cols):
            data[col] = embeddings[:, i]

        geometry = [Point(x, y) for x, y in zip(lon, lat)]
        gdf = gpd.GeoDataFrame(data, geometry=geometry, crs=crs)

        if missing_cols:
            gdf = gdf.drop(columns=list(missing_cols))

        return gdf

    return _make_gdf


@pytest.fixture
def write_notebook(tmp_path):
    """Factory fixture: write an nbformat v4 notebook of one code cell per source string.

    write_notebook(cell_sources, filename="nb.ipynb") -> pathlib.Path
    """

    def _write_notebook(cell_sources, filename="nb.ipynb"):
        nb = nbformat.v4.new_notebook()
        nb["cells"] = [nbformat.v4.new_code_cell(src) for src in cell_sources]
        path = tmp_path / filename
        nbformat.write(nb, path)
        return path

    return _write_notebook

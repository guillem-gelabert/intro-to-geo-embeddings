"""Author-side, network-using fetch of a tiny Clay (LGND) patch-embedding
fixture for the Bern area.

This is the ONE script in the repository that queries the live LGND Clay
corpus. `notebooks/solutions/00b_representation_inspection.ipynb` never
imports this module and never reaches the network at execution time --
it reads only the checked-in `data/clay_sample_fixture.parquet` this
script produces, per the project's offline-first convention.

Corpus root (pinned, do not swap to `clay/lgnd-embeddings`, a different,
larger monthly product): `clay/lgnd-clay-v1-5-sentinel-2-l2a`. Notebooks
and scripts read the plain HTTPS mirror
`https://data.source.coop/clay/...`, never the dotted `s3://` bucket name
(it breaks TLS with virtual-hosted URLs) (STACK.md "LGND open Clay
corpus").

Requires `duckdb` (the `providers` extra, `pyproject.toml`) -- never a
dependency of the notebook path.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

import duckdb
import pyarrow as pa
import pyarrow.parquet as pq

# Bern's partition in the LGND Clay v1.5 Sentinel-2 L2A corpus
# (STACK.md "Bern's partition is `geohash_l2=u0`"). Pinned to the single
# file the bucket listing (S3 ListObjectsV2 over the HTTPS mirror)
# returns for this partition as of the extraction date recorded below --
# not a glob, since this HTTP mirror rejects `*` in the path by default
# and the partition currently contains exactly one file.
_SOURCE_PATH = (
    "https://data.source.coop/clay/lgnd-clay-v1-5-sentinel-2-l2a/"
    "aggregated/geohash_l2=u0/year=2025/month=06/"
    "data_01c1fab1-0004-5b1c-0009-b72e01d3104e_222_0_0.parquet"
)

# Bern city center (course.config.AREAS["bern"]["bbox_4326"] interior).
_BERN_LON = 7.4474
_BERN_LAT = 46.9480

_ATTRIBUTION = "LGND Clay v1.5 Sentinel-2 L2A embeddings, Source Cooperative, CC BY 4.0"


def build_fixture(
    out_path: Path = Path("data/clay_sample_fixture.parquet"),
    n_rows: int = 5,
) -> dict:
    """Query the live LGND Clay corpus for a handful of Bern-area rows,
    write them to `out_path` as GeoParquet-adjacent Parquet with embedded
    `course_provenance` metadata, and return the same provenance dict.

    Network access required (`https://data.source.coop`, anonymous, no
    credentials). Never called by any notebook.
    """
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    con = duckdb.connect()
    con.execute("INSTALL spatial; LOAD spatial;")
    con.execute("INSTALL httpfs; LOAD httpfs;")

    query = f"""
        SELECT
            chips_id, cell_id, rasters_id, stac_item_id, collection,
            datetime, embedding, bbox, ST_AsText(geometry) AS geometry_wkt
        FROM read_parquet('{_SOURCE_PATH}')
        WHERE ST_Intersects(geometry, ST_Point({_BERN_LON}, {_BERN_LAT}))
        LIMIT {n_rows}
    """
    df = con.execute(query).df()
    con.close()

    provenance = {
        "embedding_product": "lgnd_clay_v1.5_sentinel2_l2a",
        "dataset_version": "v1.5",
        "year": 2025,
        "extraction_date": datetime.now(UTC).isoformat(),
        "source_path": _SOURCE_PATH,
        "sampling_method": (
            "ST_Intersects Bern city center "
            f"({_BERN_LON}, {_BERN_LAT}), first {n_rows} rows"
        ),
        "crs": "EPSG:4326",
        "license": "CC BY 4.0",
        "attribution": _ATTRIBUTION,
        "created_by": "pipeline/fetch_clay_fixture.py",
    }

    table = pa.Table.from_pandas(df, preserve_index=False)
    meta = dict(table.schema.metadata or {})
    meta[b"course_provenance"] = json.dumps(provenance).encode()
    table = table.replace_schema_metadata(meta)
    pq.write_table(table, out_path, compression="zstd")

    provenance_path = out_path.parent / f"{out_path.stem}.provenance.json"
    provenance_path.write_text(json.dumps(provenance, indent=2))

    return provenance


if __name__ == "__main__":
    print(json.dumps(build_fixture(), indent=2))

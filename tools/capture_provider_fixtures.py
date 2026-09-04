"""One-off, author-run script to (re)generate the two provider fixtures used
by ``notebooks/solutions/04_embedding_ecosystems.ipynb`` for its offline
fallback path: ``data/fixtures/tessera_bern_2024.json`` (TESSERA, 128-D) and
``data/fixtures/clay_bern_sample.json`` (Clay/LGND, 1024-D).

This script is NOT imported by any notebook and is not part of ``course/``.
It is only ever run by hand, by the course author, when network access and
the `providers` optional-dependency group (`geotessera`, `duckdb`) are
available, to refresh the fixtures with a real live capture.

Run with: `uv run --extra providers python tools/capture_provider_fixtures.py`

If either live fetch fails (no network, package missing, upstream schema
change), this script falls back to writing a clearly-labelled
``fixture_type: "synthetic-illustrative"`` fixture instead of crashing --
the goal is that a fixture always exists for the notebook to fall back to,
never that this script must succeed end to end.
"""

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

from course.config import AREAS

FIXTURES_DIR = Path("data/fixtures")
BERN_LON, BERN_LAT = 7.4474, 46.9480  # Bern city center, inside AREAS["bern"]


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _write_synthetic_tessera(reason: str) -> None:
    print(f"TESSERA live capture unavailable ({reason}); writing synthetic fixture.")
    rng = np.random.default_rng(42)
    v = rng.normal(size=128).astype(np.float32)
    v /= np.linalg.norm(v)
    # Scaled to a plausible-but-NOT-exactly-1.0 norm: TESSERA's unit-norm
    # property is undocumented upstream (STACK.md gap) -- fabricating a
    # suspiciously perfect 1.0 would misrepresent that uncertainty.
    v = v * 0.985
    fixture = {
        "lon": BERN_LON,
        "lat": BERN_LAT,
        "year": 2024,
        "dataset_version": "v1.1",
        "dataset_variant": "cambridge",
        "embedding": [float(x) for x in v],
        "captured_at": None,
        "fixture_type": "synthetic-illustrative",
        "note": (
            f"geotessera live capture unavailable ({reason}) when this "
            "fixture was generated. This vector is a seeded "
            "(np.random.default_rng(42)) synthetic stand-in scaled to "
            "norm ~0.985 -- deliberately NOT exactly 1.0, since TESSERA's "
            "unit-norm property is undocumented upstream (see STACK.md). "
            "Regenerate via this script once network and the `providers` "
            "extra are available, to replace this with a real live-captured "
            "sample."
        ),
    }
    FIXTURES_DIR.mkdir(parents=True, exist_ok=True)
    with (FIXTURES_DIR / "tessera_bern_2024.json").open("w") as f:
        json.dump(fixture, f, indent=2)


def capture_tessera() -> None:
    try:
        from geotessera import GeoTessera
    except ImportError as e:
        _write_synthetic_tessera(f"ImportError: {e}")
        return
    try:
        gt = GeoTessera(dataset_version="v1.1", dataset_variant="cambridge")
        arr = gt.sample_embeddings_at_points([(BERN_LON, BERN_LAT)], year=2024)
        vec = np.asarray(arr[0], dtype=np.float32)
        assert vec.shape[0] == 128
        fixture = {
            "lon": BERN_LON,
            "lat": BERN_LAT,
            "year": 2024,
            "dataset_version": "v1.1",
            "dataset_variant": "cambridge",
            "embedding": [float(x) for x in vec],
            "captured_at": _now_iso(),
            "fixture_type": "live-captured",
        }
        FIXTURES_DIR.mkdir(parents=True, exist_ok=True)
        with (FIXTURES_DIR / "tessera_bern_2024.json").open("w") as f:
            json.dump(fixture, f, indent=2)
        print("TESSERA fixture captured live.")
    except Exception as e:  # noqa: BLE001 - any live-path failure falls back
        _write_synthetic_tessera(f"{type(e).__name__}: {e}")


def _write_synthetic_clay(reason: str) -> None:
    print(f"Clay live capture unavailable ({reason}); writing synthetic fixture.")
    rng = np.random.default_rng(42)
    v = rng.normal(size=1024).astype(np.float32)
    v /= np.linalg.norm(v)
    fixture = {
        "stac_item_id": "SYNTHETIC_BERN_SAMPLE",
        "datetime": _now_iso(),
        "collection": "lgnd-clay-v1-5-sentinel-2-l2a",
        "embedding": [float(x) for x in v],
        "captured_at": None,
        "fixture_type": "synthetic-illustrative",
        "note": (
            f"DuckDB/HTTPS live capture unavailable ({reason}). This vector "
            "is a seeded (np.random.default_rng(42)) synthetic unit-norm "
            "stand-in. Regenerate via this script once network access is "
            "available, to replace this with a real live-captured sample."
        ),
    }
    FIXTURES_DIR.mkdir(parents=True, exist_ok=True)
    with (FIXTURES_DIR / "clay_bern_sample.json").open("w") as f:
        json.dump(fixture, f, indent=2)


def capture_clay() -> None:
    try:
        import duckdb
    except ImportError as e:
        _write_synthetic_clay(f"ImportError: {e}")
        return
    try:
        con = duckdb.connect()
        con.sql("INSTALL spatial; LOAD spatial; INSTALL httpfs; LOAD httpfs;")
        url = (
            "https://data.source.coop/clay/lgnd-clay-v1-5-sentinel-2-l2a/"
            "aggregated/geohash_l2=u0/year=2025/month=06/*.parquet"
        )
        row = con.sql(
            f"""
            SELECT stac_item_id, datetime, collection, embedding
            FROM read_parquet('{url}')
            WHERE ST_Intersects(
                ST_GeomFromWKB(geometry_wkt), ST_Point({BERN_LON}, {BERN_LAT})
            )
            LIMIT 1
            """
        ).fetchone()
        if row is None:
            raise RuntimeError("no row found near Bern in the Clay corpus query")
        stac_item_id, dt, collection, embedding = row
        embedding = np.asarray(embedding, dtype=np.float32)
        assert embedding.shape[0] == 1024
        fixture = {
            "stac_item_id": stac_item_id,
            "datetime": str(dt),
            "collection": collection,
            "embedding": [float(x) for x in embedding],
            "captured_at": _now_iso(),
            "fixture_type": "live-captured",
        }
        FIXTURES_DIR.mkdir(parents=True, exist_ok=True)
        with (FIXTURES_DIR / "clay_bern_sample.json").open("w") as f:
            json.dump(fixture, f, indent=2)
        print("Clay fixture captured live.")
    except Exception as e:  # noqa: BLE001 - any live-path failure falls back
        _write_synthetic_clay(f"{type(e).__name__}: {e}")


def main() -> int:
    assert "bern" in AREAS  # sanity: config import worked
    capture_tessera()
    capture_clay()
    return 0


if __name__ == "__main__":
    sys.exit(main())

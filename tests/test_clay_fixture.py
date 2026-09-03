"""Tests for the checked-in Clay/LGND fixture and its author-side
regeneration script.

Tests 1-2 read the committed `data/clay_sample_fixture.parquet` and
`data/clay_sample_fixture.provenance.json` directly with `pandas`/`json`
-- no `duckdb`, no network -- so they run in the default `uv run pytest
tests/` target, which does NOT have `duckdb` installed (it lives in the
`providers` extra). Test 3 exercises the live corpus and is excluded by
default via the `network` marker (`pyproject.toml` `addopts`).
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pytest

FIXTURE_PATH = Path("data/clay_sample_fixture.parquet")
PROVENANCE_PATH = Path("data/clay_sample_fixture.provenance.json")


def test_fixture_has_valid_embeddings():
    df = pd.read_parquet(FIXTURE_PATH)
    assert 1 <= len(df) <= 5
    assert "embedding" in df.columns
    for vec in df["embedding"]:
        assert len(vec) == 1024
        assert not any(pd.isna(v) for v in vec)


def test_fixture_provenance_matches_data_card_attribution():
    provenance = json.loads(PROVENANCE_PATH.read_text())
    assert provenance["license"] == "CC BY 4.0"
    assert (
        provenance["attribution"]
        == "LGND Clay v1.5 Sentinel-2 L2A embeddings, Source Cooperative, CC BY 4.0"
    )


@pytest.mark.network
def test_build_fixture_regenerates_from_live_corpus(tmp_path):
    from pipeline.fetch_clay_fixture import build_fixture

    out_path = tmp_path / "clay.parquet"
    provenance = build_fixture(out_path=out_path, n_rows=5)

    for key in (
        "embedding_product",
        "dataset_version",
        "license",
        "attribution",
        "source_path",
    ):
        assert key in provenance

    df = pd.read_parquet(out_path)
    assert len(df) >= 1
    assert "embedding" in df.columns

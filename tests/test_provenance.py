import json
from types import SimpleNamespace

import pytest

from course.provenance import build_provenance, write_provenance


def _prov(region, year):
    return {
        "region": region,
        "year": year,
        "embedding_product": "AlphaEarth Foundations Satellite Embedding v1 (annual)",
        "dataset_version": "1.1",
        "crs": "EPSG:4326",
        "label_source": "esa_worldcover",
        "validation_source": "hrl_imperviousness",
        "license_alphaearth": "CC BY 4.0",
        "attribution_alphaearth": (
            "The AlphaEarth Foundations Satellite Embedding dataset is "
            "produced by Google and Google DeepMind."
        ),
    }


def test_build_provenance_two_tables():
    loaded = {
        "bern_2021": SimpleNamespace(attrs={"course_provenance": _prov("bern", 2021)}),
        "seville_2021": SimpleNamespace(
            attrs={"course_provenance": _prov("seville", 2021)}
        ),
    }

    result = build_provenance(loaded, created_by="test-author")

    assert len(result["tables"]) == 2
    for entry in result["tables"]:
        assert entry["region"]
        assert entry["year"]
        assert entry["dataset_version"]
        assert entry["license"]
        assert entry["attribution"]


def test_build_provenance_missing_metadata_raises_keyerror():
    loaded = {
        "bern_2021": SimpleNamespace(attrs={"course_provenance": _prov("bern", 2021)}),
        "broken_table": SimpleNamespace(attrs={}),
    }

    with pytest.raises(KeyError, match="broken_table"):
        build_provenance(loaded, created_by="test-author")


def test_write_provenance_roundtrip_and_creates_parent(tmp_path):
    provenance = {"created_by": "x", "generated_at": "now", "tables": [{"a": 1}]}
    path = tmp_path / "outputs" / "provenance.json"

    write_provenance(provenance, path)

    assert path.exists()
    assert json.loads(path.read_text()) == provenance

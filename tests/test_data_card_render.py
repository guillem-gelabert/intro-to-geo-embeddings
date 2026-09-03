"""Unit tests for pipeline.data_card.render_data_card -- exact attribution
strings for the four bundled sources, and a guard against implying
Copernicus Global Embeddings (CDSE) is ever bundled (02-09-PLAN.md Task 2,
DATA-06). All non-network: `provenance_records` here are plain synthetic
dicts, not real pipeline.build output.
"""

from pipeline.data_card import render_data_card


def _provenance_records():
    return [
        {
            "region": "bern",
            "year": 2018,
            "n_rows": 1916,
            "crs": "EPSG:4326",
        },
        {
            "region": "bern",
            "year": 2021,
            "n_rows": 1916,
            "crs": "EPSG:4326",
        },
        {
            "region": "seville",
            "year": 2021,
            "n_rows": 1904,
            "crs": "EPSG:4326",
        },
    ]


def test_render_data_card_contains_exact_alphaearth_attribution():
    text = render_data_card(_provenance_records())
    assert (
        "The AlphaEarth Foundations Satellite Embedding dataset is produced "
        "by Google and Google DeepMind."
    ) in text


def test_render_data_card_contains_exact_sentinel2_attribution():
    text = render_data_card(_provenance_records())
    assert "Contains modified Copernicus Sentinel data" in text


def test_render_data_card_contains_exact_worldcover_attribution():
    text = render_data_card(_provenance_records())
    assert "© ESA WorldCover project 2021" in text


def test_render_data_card_never_implies_cdse_is_bundled():
    text = render_data_card(_provenance_records())
    assert "CDSE" not in text or "never bundle" in text.lower()


def test_render_data_card_is_a_non_empty_markdown_string():
    text = render_data_card(_provenance_records())
    assert isinstance(text, str)
    assert text.strip().startswith("#")
    # Sanity: per-table specifics actually got pulled in, not hardcoded.
    assert "bern" in text
    assert "seville" in text
    assert "2018" in text

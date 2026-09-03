"""Render `DATA_CARD.md` from a list of per-table `course_provenance` dicts
(02-09-PLAN.md Task 2; DATA-06).

The per-source license/attribution text below is FIXED, reproduced
VERBATIM from 02-RESEARCH.md's "Licensing and Redistribution" table and
PITFALLS.md Pitfall 13 -- do not paraphrase. A paid course's attribution
requirement is met by the exact wording, not an equivalent summary. Only
the per-region/year specifics (sampling counts, years covered, CRS) are
derived from `provenance_records`, which `pipeline.build` passes in as the
list of provenance dicts already embedded in each written table's own
`course_provenance` metadata.
"""

from __future__ import annotations

from course.config import COURSE_RELEASE

ALPHAEARTH_LICENSE = "CC BY 4.0"
ALPHAEARTH_ATTRIBUTION = (
    "The AlphaEarth Foundations Satellite Embedding dataset is produced by "
    "Google and Google DeepMind."
)

WORLDCOVER_LICENSE = "CC BY 4.0"
WORLDCOVER_ATTRIBUTION = (
    "© ESA WorldCover project 2021 / Contains modified Copernicus Sentinel "
    "data (2021) processed by ESA WorldCover consortium"
)
WORLDCOVER_CITATION = "Zanaga et al. 2022, https://doi.org/10.5281/zenodo.7254221"

HRL_LICENSE = "Free/open, commercial use allowed"
HRL_ATTRIBUTION = (
    "Generated using European Union's Copernicus Land Monitoring Service information"
)

SENTINEL2_LICENSE = "EU legal notice (Reg. 1159/2013)"
SENTINEL2_ATTRIBUTION_TEMPLATE = "Contains modified Copernicus Sentinel data {year}"


def _rows_table(provenance_records: list[dict]) -> str:
    if not provenance_records:
        return "| (none built yet) | | | |"
    ordered = sorted(
        provenance_records, key=lambda r: (r.get("region", ""), r.get("year", 0))
    )
    return "\n".join(
        f"| {r.get('region', '?')} | {r.get('year', '?')} | "
        f"{r.get('n_rows', '?')} | {r.get('crs', 'EPSG:4326')} |"
        for r in ordered
    )


def render_data_card(provenance_records: list[dict]) -> str:
    """Render the course's `DATA_CARD.md` from per-table provenance dicts.

    Each dict in `provenance_records` is one already-written table's own
    `course_provenance` metadata (see `pipeline.build`) -- this function
    only reads `region`/`year`/`n_rows`/`crs` from them; every per-source
    license/attribution string below is fixed, never derived.
    """
    regions = sorted({r["region"] for r in provenance_records})
    years = sorted({r["year"] for r in provenance_records})
    regions_text = ", ".join(regions) if regions else "none built yet"
    years_text = ", ".join(str(y) for y in years) if years else "none built yet"
    sentinel2_attribution_example = SENTINEL2_ATTRIBUTION_TEMPLATE.format(year="[Year]")

    return f"""\
# Introduction to Geospatial Embeddings -- Frozen Teaching Dataset

## Description

Frozen, small (roughly 0.5 MB per table) GeoParquet tables of AlphaEarth
Foundations Satellite Embedding vectors (`A00..A63`), an ESA
WorldCover-derived training label, an INDEPENDENT Copernicus HRL
Imperviousness reference value, and Sentinel-2 L2A raw reflectance bands
(`S2_B02..S2_B12`), sampled at a fixed set of points for region(s)
{regions_text}, across anchor year(s) {years_text}. Built once by
`pipeline.build` from public, no-login-required sources and redistributed
as part of the course under the licenses below.

## Licenses and Attribution (verbatim -- do not paraphrase)

| Source | License | Attribution |
|---|---|---|
| AlphaEarth / Satellite Embedding | {ALPHAEARTH_LICENSE} | {ALPHAEARTH_ATTRIBUTION} |
| ESA WorldCover 2021 v200 | {WORLDCOVER_LICENSE} | {WORLDCOVER_ATTRIBUTION} (citation: {WORLDCOVER_CITATION}) |
| Copernicus HRL Imperviousness Density 2018 | {HRL_LICENSE} | {HRL_ATTRIBUTION} |
| Sentinel-2 L2A (derived reflectance bands) | {SENTINEL2_LICENSE} | {sentinel2_attribution_example} (the actual year is recorded per-table in that table's own `course_provenance`) |

**Copernicus Global Embeddings (CDSE) are never bundled** in this
dataset -- CDSE's portal terms prohibit redistribution of portal
material and no code path in this pipeline reads from it. If a future
phase adds a CDSE-derived column, it must ship as a live-only, opt-in
notebook cell, never a frozen column here.

## Sampling Method

Stratified by ESA WorldCover 2021 class (`built`, `crop`, `vegetation`,
`water`, `bare`), capped per class (`pipeline/areas.yaml`:
crop/vegetation/built capped at 500, water at 400, bare at 150 -- each
clamped to whatever pool actually exists per region), drawn from a
minimum-spacing (50 m) candidate grid with a seeded (`seed: 42`) random
generator so a rebuild reproduces an identical `sample_id -> (lon, lat)`
mapping. See 02-RESEARCH.md "Sampling and Block Design" for the full
row-budget and class-pool-size derivation.

`label_source` (`esa_worldcover_2021`) and `validation_source`
(`eea_hrl_imperviousness_2018`) are architecturally distinct and always
different strings -- validating one learned product (WorldCover) against
another learned product (HRL Imperviousness) is not independent
validation; this dataset keeps the two separate rather than conflating
them (PITFALLS.md Pitfall 6).

## Structure

Two regions (Bern, Seville) across three anchor years (2018, 2021,
2024): six tables, `{{region}}/{{region}}_aef_{{year}}_v1.1.parquet`.

| Region | Year | Rows | CRS |
|---|---|---|---|
{_rows_table(provenance_records)}

## Limitations

Research measured the in-region random-split-vs-spatial-block-CV gap for
AlphaEarth embeddings as WEAK (1-4 balanced-accuracy points) at this AOI
scale -- do not expect the dramatic gap often quoted for raw pixels. The
much larger, robust effect measured for this dataset is leave-region-out
transfer (21-28 balanced-accuracy points); see 02-RESEARCH.md "The
critical sanity check: does the frozen sample reproduce the
random-vs-honest-CV gap?" for the full measurement. A reader comparing
random vs. block CV on these tables alone should not be surprised by a
small in-region gap.

## Citation

If you use this dataset, cite the underlying sources above (AlphaEarth,
ESA WorldCover, Copernicus Land Monitoring Service, Sentinel-2) using
their exact attribution strings, plus:

> Introduction to Geospatial Embeddings course, frozen teaching dataset,
> course release {COURSE_RELEASE}.

## Provenance

Every table's own Parquet key-value metadata carries a
`course_provenance` JSON dict (embedding product, dataset version, year,
extraction date, source paths / tile URL / scene IDs, sampling method,
CRS, label source, validation source, license, attribution, creator) --
read it back via
`pyarrow.parquet.read_table(path).schema.metadata[b"course_provenance"]`.
`manifest.json` (sibling to this file) carries the sha256 checksum, row
count, build timestamp, and builder git SHA for every table, computed
directly from the written bytes.
"""

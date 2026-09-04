# Introduction to Geospatial Embeddings -- Frozen Teaching Dataset

## Description

Frozen, small (roughly 0.5 MB per table) GeoParquet tables of AlphaEarth
Foundations Satellite Embedding vectors (`A00..A63`), an ESA
WorldCover-derived training label, an INDEPENDENT Copernicus HRL
Imperviousness reference value, and Sentinel-2 L2A raw reflectance bands
(`S2_B02..S2_B12`), sampled at a fixed set of points for region(s)
bern, seville, across anchor year(s) 2018, 2021, 2024. Built once by
`pipeline.build` from public, no-login-required sources and redistributed
as part of the course under the licenses below.

## Licenses and Attribution (verbatim -- do not paraphrase)

| Source | License | Attribution |
|---|---|---|
| AlphaEarth / Satellite Embedding | CC BY 4.0 | The AlphaEarth Foundations Satellite Embedding dataset is produced by Google and Google DeepMind. |
| ESA WorldCover 2021 v200 | CC BY 4.0 | © ESA WorldCover project 2021 / Contains modified Copernicus Sentinel data (2021) processed by ESA WorldCover consortium (citation: Zanaga et al. 2022, https://doi.org/10.5281/zenodo.7254221) |
| Copernicus HRL Imperviousness Density 2018 | Free/open, commercial use allowed | Generated using European Union's Copernicus Land Monitoring Service information |
| Sentinel-2 L2A (derived reflectance bands) | EU legal notice (Reg. 1159/2013) | Contains modified Copernicus Sentinel data [Year] (the actual year is recorded per-table in that table's own `course_provenance`) |
| LGND Clay v1.5 Sentinel-2 L2A (fixture) | CC BY 4.0 | LGND Clay v1.5 Sentinel-2 L2A embeddings, Source Cooperative, CC BY 4.0 |

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
2024): six tables, `{region}/{region}_aef_{year}_v1.1.parquet`.

| Region | Year | Rows | CRS |
|---|---|---|---|
| bern | 2018 | 2050 | EPSG:4326 |
| bern | 2021 | 2050 | EPSG:4326 |
| bern | 2024 | 2050 | EPSG:4326 |
| seville | 2018 | 2050 | EPSG:4326 |
| seville | 2021 | 2050 | EPSG:4326 |
| seville | 2024 | 2050 | EPSG:4326 |

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
> course release 2026.08.

## Phase 4 additions

`data/clay_sample_fixture.parquet` is a 5-row fixture drawn from the LGND
Clay v1.5 Sentinel-2 L2A open corpus (`embedding` `list<float32>[1024]`),
sampled via `ST_Intersects` around Bern city center (7.4474, 46.948) from
`https://data.source.coop/clay/lgnd-clay-v1-5-sentinel-2-l2a/aggregated/geohash_l2=u0/year=2025/month=06/...parquet`.
License CC BY 4.0; attribution "LGND Clay v1.5 Sentinel-2 L2A embeddings,
Source Cooperative, CC BY 4.0" (see the table row above). It exists so
`00b_representation_inspection.ipynb` can compare a real Clay patch
embedding against an AlphaEarth pixel vector without a live network call.

`data/bern_aef_2024_clip.tif` is a small (2 MB) windowed clip of the same
AlphaEarth / Satellite Embedding product documented in the table above
(same product, license, and attribution -- CC BY 4.0, "The AlphaEarth
Foundations Satellite Embedding dataset is produced by Google and Google
DeepMind." -- this is a raster clip of that dataset, not a separate
source). It covers bbox `[7.44, 46.94, 7.46, 46.96]` (EPSG:4326) for year
2024, shape `(64, 225, 157)` in CRS EPSG:32632. Unlike the point tables
above, it ships as **raw, un-dequantized int8** deliberately, so
`01_alphaearth_access_visualize.ipynb` can teach the
`((v / 127.5) ** 2) * sign(v)` dequantization formula on real data rather
than starting from an already-processed vector.

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

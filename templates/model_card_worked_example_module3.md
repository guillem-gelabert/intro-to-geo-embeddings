# Introduction to Geospatial Embeddings -- Frozen Teaching Dataset (Module 3, `02_similarity_and_classification.ipynb`) -- Model / Data Card

This is `MODEL_DATA_CARD_TEMPLATE.md` filled out for the dataset already
shipped in `data/` and documented in `data/DATA_CARD.md`. Every value
below is copied from the existing shipped data and its `course_provenance`
metadata / `outputs/provenance.json` fields -- nothing here is invented.

## Description

Frozen, small (roughly 0.5 MB per table) GeoParquet tables of AlphaEarth
Foundations Satellite Embedding vectors (`A00..A63`), an ESA
WorldCover-derived training label, an INDEPENDENT Copernicus HRL
Imperviousness reference value, and Sentinel-2 L2A raw reflectance bands
(`S2_B02..S2_B12`), sampled at a fixed set of points for region(s) bern,
seville, across anchor year(s) 2018, 2021, 2024. Built once by
`pipeline.build` from public, no-login-required sources and redistributed
as part of the course under the licenses below. This is the dataset
consumed by `02_similarity_and_classification.ipynb`.

## Representation Choice

| Question | Answer |
|---|---|
| Representation used | AlphaEarth (Google Satellite Embedding), 64-D, `A00..A63` |
| Alternatives considered | TESSERA (128-D, 10 m, Cambridge), Clay (1024-D, LGND corpus), raw Sentinel-2 reflectance bands |
| Why this one (dimensionality, coverage, license, cost, latency) | Global annual coverage 2017-2025, CC BY 4.0 with a clear stated attribution, and both an Earth-Engine path and an anonymous-GCS path (no account required) -- lowest-friction backbone for a course that must run without cloud credentials |
| Known tradeoff accepted | The Sentinel-2 raw-reflectance columns (`S2_B02..S2_B12`) are shipped alongside the embedding as a baseline for comparison; TESSERA and Clay are demonstrated in Module 5 but not frozen into this table, partly because TESSERA's embedding-data license is unstated (see PROVENANCE_CHECKLIST.md) |

## Licenses and Attribution (verbatim -- do not paraphrase)

| Source | License | Attribution |
|---|---|---|
| AlphaEarth / Satellite Embedding | CC BY 4.0 | The AlphaEarth Foundations Satellite Embedding dataset is produced by Google and Google DeepMind. |
| ESA WorldCover 2021 v200 | CC BY 4.0 | © ESA WorldCover project 2021 / Contains modified Copernicus Sentinel data (2021) processed by ESA WorldCover consortium (citation: Zanaga et al. 2022, https://doi.org/10.5281/zenodo.7254221) |
| Copernicus HRL Imperviousness Density 2018 | Free/open, commercial use allowed | Generated using European Union's Copernicus Land Monitoring Service information |
| Sentinel-2 L2A (derived reflectance bands) | EU legal notice (Reg. 1159/2013) | Contains modified Copernicus Sentinel data [Year] (the actual year is recorded per-table in that table's own `course_provenance`) |

Copernicus Global Embeddings (CDSE) are never bundled in this dataset --
CDSE's portal terms prohibit redistribution of portal material and no
code path in this pipeline reads from it.

## Sampling Method / Model Details

Stratified by ESA WorldCover 2021 class (`built`, `crop`, `vegetation`,
`water`, `bare`), capped per class (`pipeline/areas.yaml`:
crop/vegetation/built capped at 500, water at 400, bare at 150 -- each
clamped to whatever pool actually exists per region), drawn from a
minimum-spacing (50 m) candidate grid with a seeded (`seed: 42`) random
generator so a rebuild reproduces an identical `sample_id -> (lon, lat)`
mapping.

`label_source`: `esa_worldcover_2021`
`validation_source`: `eea_hrl_imperviousness_2018`

These are architecturally distinct and always different strings --
validating one learned product (WorldCover) against another learned
product (HRL Imperviousness) is not independent validation; this dataset
keeps the two separate rather than conflating them (Pitfall 6).

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

## Provenance

- Source paths: `gs://alphaearth_foundations/satellite_embedding/v1/annual/{year}/{utm_zone}/*.tiff` (AlphaEarth, anonymous GCS reads), ESA WorldCover 2021 v200, Copernicus HRL Imperviousness Density 2018, Sentinel-2 L2A via odc-stac/Earth Search
- Dataset version: AlphaEarth `DATASET_VERSION` 1.1 (as of 2025-11-17)
- Extraction / build date: recorded per-table in that table's own `course_provenance` metadata (`pyarrow.parquet.read_table(path).schema.metadata[b"course_provenance"]`)
- CRS: EPSG:4326 (point geometry); `block_10km` spatial-block ids computed in EPSG:2056/UTM
- Checksum (sha256): recorded per table in `manifest.json` (sibling to `data/DATA_CARD.md`), computed directly from the written bytes
- Builder script: `pipeline.build`, git SHA recorded in `manifest.json`
- Created by: course author (per `course_provenance["created_by"]`, surfaced notebook-side via `course.provenance.build_provenance`)

Every table's own Parquet key-value metadata carries the full
`course_provenance` JSON dict (embedding product, dataset version, year,
extraction date, source paths / tile URL / scene IDs, sampling method,
CRS, label source, validation source, license, attribution, creator).
The notebook's `outputs/provenance.json` is generated at run time by
`course.provenance.build_provenance(loaded, created_by)`, which reads
every field directly from each loaded table's carried metadata rather
than hand-typing values -- so this card and that generated file can never
silently drift apart on a dataset-version bump.

## Ethics Statement

- Who bears the cost of a false positive from this artifact's downstream
  use? A false "artificialized" classification on a real parcel could
  mislead land-use policy decisions or property valuations if used beyond
  the teaching context; a false "not artificialized" could mask real
  land-cover change in a monitoring pipeline. Neither label_source nor
  validation_source is ground-truth field survey data -- both are
  themselves learned/derived products, which is why the two are kept
  distinct and why this card does not claim validated accuracy beyond
  the course's own measured balanced-accuracy figures.
- Is any inferred information more sensitive than the underlying imagery?
  Yes -- an "artificialization" or land-cover-change label derived from
  embeddings can reveal development activity at a specific parcel earlier
  or more precisely than a human reading the raw Sentinel-2/AlphaEarth
  imagery would, which is a consideration for any real (non-teaching)
  deployment of this workflow.

---

This is the worked example the capstone
(`05_capstone_artificialization.ipynb`) and `PROVENANCE_CHECKLIST.md`
point students toward when asked to apply the template to a previous
lab's outputs.

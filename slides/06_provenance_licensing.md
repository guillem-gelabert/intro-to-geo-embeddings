---
marp: true
theme: default
size: "16:9"
paginate: true
---

# Module 7: Provenance and Licensing

The eighth module of this course. It has no source notebook -- its
artifact is `data/DATA_CARD.md` and `templates/PROVENANCE_CHECKLIST.md`.

<!--
Speaker notes: Every other deck in this course pulls its content from a
solution notebook. This one does not, because provenance and licensing
are not a code exercise -- they are a documentation and judgment
discipline that this course teaches through the DATA_CARD.md this
project already ships plus the reusable provenance checklist template.
-->

---

## What you will learn

1. What provenance a frozen teaching dataset must carry, and where it
   physically lives (Parquet key-value metadata *and* a human-readable
   card)
2. Which licenses require which attribution string verbatim, and what
   happens when a check comes back unclear rather than clean

<!--
Speaker notes: This module is deliberately not code-first. The skill
being taught is: given an artifact (a table, a raster, a model output),
can you answer eight yes/no questions about its provenance and license
before you ship it. That skill transfers to any dataset a student builds
after this course, not just the ones bundled here.
-->

---

## Provenance fields (verbatim from DATA_CARD.md)

Every table's own Parquet key-value metadata carries a
`course_provenance` JSON dict with these fields:

- `embedding_product`
- `dataset_version` (EE `DATASET_VERSION` or GCS path)
- `year`
- `source_license`
- `attribution`
- `crs`
- `sampling_method`
- `label_source`
- `validation_source`
- `created_by`
- `created_at`
- `course_release`

`manifest.json` (sibling to `DATA_CARD.md`) additionally carries the
sha256 checksum, row count, build timestamp, and builder git SHA for
every table, computed directly from the written bytes.

<!--
Speaker notes: Read this field list back with
`pyarrow.parquet.read_table(path).schema.metadata[b"course_provenance"]`.
The point is that provenance lives in the file itself, not only in a
README a student might not open -- so the metadata survives even if the
DATA_CARD.md is lost or the file is copied elsewhere.
-->

---

## Worked example: one row of the checklist against the AlphaEarth table

Applying `templates/PROVENANCE_CHECKLIST.md` to the AlphaEarth /
Satellite Embedding source in `data/DATA_CARD.md`:

| Checklist item | Answer for this artifact |
|---|---|
| Data source documented | Yes -- `GOOGLE/SATELLITE_EMBEDDING/V1/ANNUAL`, `DATASET_VERSION` 1.1, recorded per-table |
| License identified | Yes -- CC BY 4.0 |
| Attribution copied verbatim | Yes -- "The AlphaEarth Foundations Satellite Embedding dataset is produced by Google and Google DeepMind." |
| `label_source`/`validation_source` distinct | Yes -- `esa_worldcover_2021` vs `eea_hrl_imperviousness_2018`, two independently derived products (Pitfall 6) |
| CRS recorded | Yes -- EPSG:4326 (point tables) |
| Version/checksum recorded | Yes -- `DATASET_VERSION` 1.1 plus per-table sha256 in `manifest.json` |
| Representation-choice tradeoff stated | Yes -- 64-D annual composite vs alternatives, discussed across Modules 3 and 5 |
| False-positive-cost / ethics statement present | Yes -- see the capstone rubric's ethics row for the downstream classification use |

<!--
Speaker notes: Every one of the eight checklist items must be answerable
yes/no for a specific artifact -- not "probably" or "assumed from a
similar dataset." Walk through this table live: it demonstrates a
completed card, not a template still full of placeholders.
-->

---

## Licensing caution

**CC BY 4.0 permits redistribution and adaptation but still requires the
verbatim attribution string; omitting it is a license violation even if
the data itself is unchanged.**

This module's honest, unresolved license findings:

- **TESSERA**: software (`geotessera`/`tessera`) is MIT-licensed, but the
  **embedding data itself has no stated license** in the docs or README.
  Do not invent one -- confirm with the maintainers before redistributing
  TESSERA-derived samples.
- **Copernicus Global Embeddings (CDSE)**: no stated license, and CDSE's
  portal terms prohibit redistribution of portal material -- this course
  **never bundles them**. Any future use must be a live, opt-in notebook
  cell under the student's own CDSE credentials, never a frozen artifact.
- **Clay** (code, weights, docs, released embeddings) carries **four
  different licenses across those four artifact types** -- checking "is
  Clay open" is not one question, it is four.

<!--
Speaker notes: A license check that comes back unclear is a real,
teachable outcome -- not a failure of the checklist. The TESSERA and
CDSE cases above are both worked examples of exactly that: TESSERA is an
open gap this course reports rather than resolves by assumption, and
CDSE is the worked example of a check correctly reaching a
"do not redistribute" conclusion instead of bundling data under an
assumed-permissive license.
-->

---

## Recap

- Provenance lives in two places: machine-readable Parquet metadata and a
  human-readable `DATA_CARD.md` -- both are required, neither substitutes
  for the other.
- The eight-item provenance checklist applies to one artifact at a time;
  every item must be a yes/no answer, never an assumption carried over
  from a similar dataset.
- License checks sometimes resolve cleanly (AlphaEarth, ESA WorldCover,
  Clay's open corpus) and sometimes do not (TESSERA's data license,
  CDSE) -- both outcomes are valid provided they are reported honestly.
- Attribution strings are copied verbatim, character-for-character, never
  paraphrased.

<!--
Speaker notes: This deck closes the course's data-handling thread that
opened with Module 1's frozen dataset. The skill -- run this checklist,
report what you find even when it's an open question -- is the takeaway,
more than any specific license fact bundled here.
-->

---

# Course Reference Environment

- **Course reference environment: 2026-08 release**
- AlphaEarth Foundations Satellite Embedding `DATASET_VERSION`: **1.1**
- GeoTessera: `dataset_version="v1.1", dataset_variant="cambridge"`

<!--
Speaker notes: We pin dataset and library versions because this field
moves fast enough that unpinned material rots. AlphaEarth's own
DATASET_VERSION and GeoTessera's dataset_version/variant are recorded
here so a student re-running these notebooks a year from now gets the
exact same embeddings we used to build every figure and label in this
course, not a newer revision. If a source dataset is later updated, this
course does not silently follow it.
-->

---

# Attribution and Licenses

- **AlphaEarth / Satellite Embedding** (CC BY 4.0): The AlphaEarth Foundations Satellite Embedding dataset is produced by Google and Google DeepMind.
- **ESA WorldCover 2021 v200** (CC BY 4.0): © ESA WorldCover project 2021
  / Contains modified Copernicus Sentinel data (2021) processed by ESA
  WorldCover consortium (citation: Zanaga et al. 2022,
  https://doi.org/10.5281/zenodo.7254221)
- **Copernicus HRL Imperviousness Density 2018** (Free/open, commercial
  use allowed): Generated using European Union's Copernicus Land
  Monitoring Service information
- **Sentinel-2 L2A (derived reflectance bands)** (EU legal notice, Reg.
  1159/2013): Contains modified Copernicus Sentinel data [Year] (the
  actual year is recorded per-table in that table's own
  `course_provenance`)
- **LGND Clay v1.5 Sentinel-2 L2A (fixture)** (CC BY 4.0): LGND Clay v1.5
  Sentinel-2 L2A embeddings, Source Cooperative, CC BY 4.0

<!--
Speaker notes: This is the one deck in the course where every source row
belongs, untrimmed -- the provenance/licensing module's whole subject is
these five license rows plus the two unresolved cases (TESSERA, CDSE)
discussed on the licensing-caution slide above. Every quantitative and
visual claim across every other deck in this course traces back to one
of these five licensed sources via data/DATA_CARD.md.
-->

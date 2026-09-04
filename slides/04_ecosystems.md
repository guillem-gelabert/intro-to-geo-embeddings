---
marp: true
theme: default
size: "16:9"
paginate: true
---

# Module 5: Embedding Ecosystems

AlphaEarth is not the only geospatial embedding available.

<!--
Speaker notes: This deck repeats a workflow you already trust -- a single
similarity operation from course.embeddings -- on embeddings from two other
providers, TESSERA and Clay/LGND, plus markdown-only coverage of OlmoEarth.
The pipeline barely changes between providers; the vectors do.
-->

---

## What you will learn

1. How to pull a TESSERA embedding (via `geotessera`, pinned
   `dataset_version="v1.1"`, `dataset_variant="cambridge"`) for a point
2. How to pull a Clay/LGND embedding (via DuckDB reading GeoParquet over
   HTTPS) for the same area
3. Why you must *check* a new provider's vector norm with
   `course.embeddings.norm_diagnostics` rather than assume it behaves like
   AlphaEarth's unit-norm vectors
4. That the same `cosine_similarity_map` helper reuses cleanly across all
   three providers -- provider portability in practice, not just in theory

<!--
Speaker notes: No live network access or geotessera/duckdb install is
required to follow along -- both fall back to a bundled fixture, and this
notebook has never been run on Colab as part of building this course; the
fixtures are recorded/synthetic-illustrative stand-ins, not live captures
you should treat as representative measurements.
-->

---

## Provider Comparison

| Provider | Dimensionality | Cadence | License | Access method |
|---|---|---|---|---|
| AlphaEarth (Google/DeepMind) | 64-D | Annual | CC BY 4.0 | `course.data.load` frozen GeoParquet / EE / anonymous GCS COG reads |
| TESSERA (`geotessera` v1.1, cambridge variant) | 128-D | Annual (per pinned version) | Software MIT; **embedding-data license unstated in docs/README as of 2026-08** | `geotessera` over public HTTPS, no auth |
| Clay / LGND corpus (`lgnd-clay-v1-5-sentinel-2-l2a`) | 1024-D | Monthly partitions observed (verify coverage) | CC BY 4.0 | DuckDB `spatial`+`httpfs` reading GeoParquet over HTTPS |
| LGND API (managed search) | vectors not exposed | n/a | Open corpus CC BY 4.0; **commercial API terms separate -- confirm before redistributing results** | `requests` REST call, bearer token, no SDK |
| OlmoEarth | not exercised in this course's notebooks | configurable temporal windows (not annual-only) | not exercised -- consult own docs | listed for portability awareness only, no live call |
| SatCLIP | not exercised in this course's notebooks | -- | not exercised -- consult own docs | listed for portability awareness only, no live call |

<!--
Speaker notes: Only fill in what the notebook or CLAUDE.md/STACK.md
actually states. OlmoEarth and SatCLIP rows are explicitly marked as
portability awareness only -- this course's notebooks never call either
API, so do not present invented dimensionality or license numbers for
them. TESSERA's embedding-data license gap is a real, honestly reported
open question, not an oversight.
-->

---

## WRONG conclusion

"Since AlphaEarth and Clay both produce embedding vectors, I can compare
their cosine similarities directly."

**Correct framing:** different providers' embedding spaces are not aligned
or comparable without their own calibration. A 1024-D Clay vector and a
64-D AlphaEarth vector do not share a semantic space -- they aren't even
the same width, let alone the same coordinate system. What transfers across
providers is the *operation* (`cosine_similarity_map`, `norm_diagnostics`),
never the numbers themselves.

<!--
Speaker notes: This is the module's central trap. Students who see
"cosine similarity" reused unchanged across three providers can easily
over-generalize into believing the numbers are cross-comparable. They are
not. Emphasize: same code, different vector spaces, not the same space.
-->

---

## Recap

- The same `cosine_similarity_map`/`norm_diagnostics` operations ran
  unchanged against AlphaEarth (64-D), TESSERA (128-D), and Clay (1024-D)
  vectors -- provider portability is about the operation, not the numbers.
- A managed service like LGND trades vector access for a simpler,
  already-implemented similarity operation.
- Every provider's license differs and must be checked per artifact:
  AlphaEarth CC BY 4.0, TESSERA software MIT / data license unstated, Clay
  corpus CC BY 4.0, LGND API terms separate from the open corpus.
- OlmoEarth and SatCLIP are listed here for portability awareness only --
  this course does not exercise either provider's API.

<!--
Speaker notes: Close by reminding students that "portability" in this
course specifically means the helper functions generalize, not that the
raw numbers do. That distinction is the module's whole point.
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
- **LGND Clay v1.5 Sentinel-2 L2A (fixture)** (CC BY 4.0): LGND Clay v1.5
  Sentinel-2 L2A embeddings, Source Cooperative, CC BY 4.0

<!--
Speaker notes: This module reads AlphaEarth (via course.data.load) and the
LGND Clay corpus (via DuckDB fixture/live read), so only those two rows
from the shared attribution partial are kept here -- ESA WorldCover,
Copernicus HRL, and Sentinel-2 L2A rows are trimmed since this deck never
touches those sources. TESSERA's row is intentionally omitted from this
CC-BY attribution slide because its embedding-data license is unstated,
not because it is CC BY -- see the Provider Comparison table above for
that gap instead of implying attribution requirements this course cannot
confirm.
-->

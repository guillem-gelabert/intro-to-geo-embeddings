# Research Summary

**Project:** Introduction to Geospatial Embeddings — Udemy course materials
**Synthesized:** 2026-09-03
**Sources:** STACK.md, FEATURES.md, ARCHITECTURE.md, PITFALLS.md (four parallel researchers, all verifying against live sources on 2026-09-03)
**Confidence:** HIGH for stack versions, data access and pitfalls (verified live from this machine); MEDIUM for Udemy platform rules and repo conventions.

---

## The finding that reshapes the plan

**The frozen-dataset pipeline needs no Earth Engine account.** Every input for the first deliverable is publicly readable without credentials, and each was verified end-to-end on 2026-09-03:

| Input | Public source | Verified |
|---|---|---|
| AlphaEarth 64-D embeddings, 2017–2025 | Google GCS `alphaearth_foundations` (provider-pays since July 2026) and the Source Cooperative mirror | Anonymous rasterio reads from both hosts return byte-identical int8; dequantized norm 0.9963 |
| Tile lookup | `aef_index.parquet` (77.8 MB GeoParquet) | DuckDB httpfs + spatial point-in-polygon; Bern resolves to zone 32N tiles for 2018/2021/2024 |
| Land-cover labels | ESA WorldCover 2021 v200, CC BY 4.0, anonymous S3 | Bern old town returns built-up, Bremgartenwald returns tree cover |
| Independent artificial-surface reference | EEA ImageServer, imperviousness density 2018 | `identify` and `exportImage` both work anonymously; Bern 100%, forest 0% |
| Sentinel-2 bands for the baseline | Earth Search STAC, per-band COGs | Summer 2021 Bern scene found, scale/offset metadata present |

Three independent products agree at the same coordinates, which also proves point sampling on Google's unusual bottom-up COGs is geographically correct.

Earth Engine remains optional and is needed only for the live path in the access module, Dynamic World labels, and Sentinel-2 harmonized composites. This removes the credential blocker recorded in PROJECT.md from the critical path.

---

## Corrections to the design report

Four premises in `docs/research/course-design-research-2026-08.md` are stale. Fix them before they reach slides and scripts.

| Report says | Verified state (2026-09-03) |
|---|---|
| The GCS bucket is requester-pays, budget for egress | Provider-pays since July 2026; students incur no cost. Teach it as "currently provider-pays, policy can change, the frozen dataset is your insurance" |
| LGND open Clay corpus is 15.2 B embeddings, monthly 2017–2026 | True only for `source.coop/clay/lgnd-embeddings`. The similarly named `clay/lgnd-clay-v1-5-sentinel-2-l2a` has just two time steps, June 2024 and June 2025. Pin the exact product path and partition |
| System Python 3.14 is likely too new for the geo stack | The full stack resolves and imports on both 3.12 and 3.14. Standardize on 3.12 anyway because Colab runs 3.12.13 and geemap, geotessera, rasterio and rioxarray all declare `>=3.12` |
| Earth Engine catalog through 2024, GCS 2017–2025 | Confirmed. Also: dataset version 1.1 (2025-11-17) regenerated the 2017 layer with extra Sentinel-1 acquisitions |

One further correction from the architecture work, absent from the report: **Google's COGs are bottom-up** (positive `transform.e`). `rasterio.windows.from_bounds` raises on the raw dataset; wrap in `WarpedVRT` and round window offsets and lengths, or sampled values shift.

---

## Recommended stack

| Question | Decision |
|---|---|
| Python | 3.12 via uv, `requires-python = ">=3.12,<3.14"`; 3.13 as the CI-tested secondary; never ship 3.14 |
| Environment | uv 0.12.9, `uv.lock` as the single source of truth, `uv export` produces the Colab requirements file. No conda, no Docker-first |
| Flagship notebook stack | numpy 2.5, pandas 3.0, pyarrow 25, geopandas 1.1.4, scikit-learn 1.9, matplotlib 3.11, folium plus mapclassify. Nothing cloud-related |
| AlphaEarth access | Path A is earthengine-api plus geemap; Path A-prime is anonymous rasterio on the GCS COGs; Path B is frozen GeoParquet |
| Spatial CV | `GroupKFold(n_splits, shuffle=True, random_state)`, `StratifiedGroupKFold`, `LeaveOneGroupOut`. No third-party spatial-CV package |
| Exercise derivation | Custom nbformat script driven by cell tags plus nbgrader-style solution markers. Not nbgrader, not nbdev |
| Headless execution | `jupyter execute` in a Makefile; pytest for the shared helper module only |
| Slides | Quarto 1.10.18 revealjs, embedding figures straight from the solution notebooks, speaker notes seeding the narration. Marp is the fallback |
| Frozen data format | GeoParquet 1.1.0, zstd, covering bbox, 64 wide float32 columns, provenance in Parquet key-value metadata plus a sidecar data card |

Colab runs Python 3.12.13, numpy 2.0.2 today, with a 3.13 upgrade announced. Write to the numpy 2.x surface and pandas Copy-on-Write-safe code so local and Colab behave identically. Guard `GroupKFold(shuffle=True)`, which needs scikit-learn 1.6 or newer.

---

## Architecture

One schema contract is the boundary. Source adapters (live readers used by both the author-only pipeline and the notebooks' Path A cells) and the frozen-data loader both return a GeoDataFrame that passes the same validation, so every cell after the source cell is path-agnostic and provider-agnostic.

```
public sources ──> pipeline/ (author, once per release) ──> data/*.parquet + DATA_CARD.md + manifest.json
                        │                                            │
                        └──> course.live.* adapters <────────────────┘
                                     │
                     notebooks/solutions/*.ipynb ──tags──> notebooks/exercises/*.ipynb
                                     │
                              figures/ ──> slides/ (Quarto) ──> scripts/
```

Key boundaries: helper functions live in an importable `course` package, never copy-pasted between notebooks; exercises are generated one-way from solutions and CI-diffed; slides embed tagged figure cells rather than screenshots; the Clay/torch environment is fully separate.

**What must exist before the flagship notebook runs end-to-end:** the pinned environment, the `course` package minimum (schema, loader, embeddings, spatial, evaluation, provenance, plotting) with green unit tests, the live readers the pipeline needs, two frozen region tables with labels and Sentinel-2 bands, and a passing headless execution. No credentials, no exercises, no slides.

---

## Feature landscape

The comparables were read cell by cell. The ISPRS 2026 tutorial is the right structural model: Colab detection, local-first fetch with remote fallback, sub-megabyte parquet tables, edit-me knobs, takeaway cells, a raw-band baseline with the same probe, and a transfer region with an error map.

**Nobody evaluates honestly.** Google's supervised-classification tutorial has no train/test split and reports no metrics; its regression tutorial reports R-squared on training data; Spatial Thoughts validates qualitatively; Clay tests on five hand-picked chips; ISPRS uses a plain random split within region. The random vs spatial-block vs leave-region-out comparison is the course's single biggest differentiator.

**Similarity search in every comparable is a hand-picked threshold between 0.90 and 0.97 validated by eye.** A query-design ladder (single pixel, polygon mean, positive minus negative) scored with precision@k is untaken ground.

Exercise conventions are well established across Kaggle learntools, nbgrader, Carpentries and fastbook: consistent stubs, checkpoint asserts with friendly messages, expected-output hints, hidden solutions that running all cells never spoils, and single-source generation from tags.

Udemy specifics are medium-to-low confidence because support pages are gated: 2–6 minute lectures with codealong exceptions, multiple-choice quizzes plus assignments as the right item types, and a browser coding-exercise runner that is not Jupyter and must be validated before being relied on.

---

## Pitfalls that shape the plan

Fourteen critical pitfalls were documented with warning signs, prevention and phase mapping. The ones that change what gets built:

- **Raw int8 values are not the embedding.** Dequantize with the square-root formula, mask `-128` nodata, then renormalize. Ship float32, never int8, or students will average int8 and break unit norm.
- **Spatial leakage, and its over-correction.** Random splits on neighbouring pixels measure interpolation. But spatial CV can be pessimistically biased for map accuracy (Wadoux et al. 2021); the honest lesson is that the CV geometry must match the question being asked, interpolation versus transfer. Teach both sides.
- **Blocks built wrongly** are as bad as no blocks: use a projected CRS, ensure at least as many groups as folds, keep every class present per fold, and precompute `block_id` in the frozen data so the lesson reproduces.
- **Change is not transition.** Cosine distance measures representation movement. Calibrate a threshold against independent labels and build a class-transition matrix. Google's own April 2026 analysis found dot-product-only change produces speckled false positives and baseline-aware features performed best.
- **Year alignment for the change lab:** imperviousness has a 2015-to-2018 series break and the change product covers 2018–2021, so use AlphaEarth 2018 versus 2021, not 2020 versus 2024 as the report suggests.
- **Validation independence:** `validation_source` must differ from `label_source`. Swiss Arealstatistik is an independent, redistributable label source the report never mentions.
- **Licensing:** per-source attribution strings, not one blanket line. Copernicus Global Embeddings have no stated license and the portal terms prohibit redistribution, so they are live-only and never bundled.
- **Notebook rot:** hidden state, author-only paths, Colab divergence, exercise drift. Prevented by headless CI execution, a pinned lock, a Colab requirements export, and one-way exercise generation.

---

## Implications for the roadmap

The build order the author fixed (flagship notebook first, then backtrack, then forward, then derived artifacts) survives contact with the research, with two scaffolding phases in front of it that the notebook cannot run without.

| Phase | Deliverable | Why here |
|---|---|---|
| 1 | Repo scaffold: pyproject and uv lock, `course` package skeleton with the schema contract and tests, Makefile, README banner | Establishes the contract everything else targets |
| 2 | Frozen-data pipeline for two regions, three years, public sources only, with data card, manifest and integrity tests | The notebook's two headline features are impossible without a two-region table carrying Sentinel-2 bands |
| 3 | The similarity-search and classification solution notebook | The first deliverable and the core value; every later notebook reuses its helpers |
| 4 | Backtrack: refresher, foundations inspection, AlphaEarth access and visualization with its three tiers | Reuse phase 3's helpers and frozen table |
| 5 | Forward: change detection and validation, embedding ecosystems, capstone, provenance checklist | Extend the same table with more years and label columns |
| 6 | Per module: exercise generator, exercises, figures, slides, narration, quizzes | Each depends on its solution notebook being frozen |
| 7 | Release: tag, data mirror, per-lecture bundles | |

Design the schema backwards from the notebook blueprint, then build forwards: outline the notebook, then the schema, then the pipeline.

**Decisions the roadmap should surface early:** which transfer and change areas to use (bounds, imperviousness coverage, class balance); whether the author creates a free EU Login for the 2021 Copernicus products; whether to register an Earth Engine noncommercial project for the live path; and verification of TESSERA coverage and the actual Clay corpus partitions before the ecosystems module.

---
*Synthesized from four parallel research agents, 2026-09-03*

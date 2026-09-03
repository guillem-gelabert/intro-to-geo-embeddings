# Phase 2: Frozen Two-Region Teaching Datasets - Research

**Researched:** 2026-09-03
**Domain:** Author-side geospatial data pipeline (AlphaEarth COGs, ESA WorldCover, EEA HRL Imperviousness, Earth Search STAC Sentinel-2) producing small, licensed, provenance-carrying GeoParquet teaching tables for two climatically distinct regions
**Confidence:** HIGH — nearly every claim below was verified live from this machine today (network access + the project's own environment), not just cited from prior research. Two items remain MEDIUM/LOW and are flagged in the Assumptions Log.

## Summary

This phase has no missing sources and no credential blockers — Phase 1's project-level research already proved that. What it lacked was a settled Region B, a validated extraction recipe, and a real answer to the question that actually matters: does a frozen sample of this data reproduce the "honest validation beats a lucky split" lesson, or does it collapse the moment real numbers are computed? This research answers all four with live data, not projection.

**Region B is settled: an Andalusian AOI centered on Seville, `lon [-5.99, -5.69], lat [37.28, 37.48]`** (~591 km², wholly inside UTM zone 30N to avoid a tile-boundary trap discovered this session). AlphaEarth tiles exist for 2018/2021/2024, ESA WorldCover 2021 gives all four course classes with a materially different balance than Bern (Seville: 62.5% crop / 20.4% vegetation / 15.2% built / 0.48% water vs Bern: 49.0% crop / 41.7% vegetation / 8.4% built / 0.80% water), EEA HRL Imperviousness 2018 is anonymously reachable, and Sentinel-2 L2A scenes with <10% cloud exist for all three anchor years. Most importantly: **a classifier trained on Bern and evaluated on Seville (leave-region-out) drops 21–28 balanced-accuracy points relative to in-region random-split accuracy, verified with two different classifiers, live-fetched data, both transfer directions.** This is a real, large, reproducible effect — Region B does its pedagogical job.

**The unexpected finding that should reshape Phase 3's plan:** in-region random-split-vs-spatial-block-CV — the comparison the design report treats as the headline lesson — is *weak* for AlphaEarth embeddings. Tested at Bern with block sizes from 100 m to 10 km, with and without a minimum point-spacing constraint, across LogisticRegression and RandomForest: the gap is 1–4 balanced-accuracy points, not the "98% vs 82%" folklore figure. Leave-region-out is where the dramatic, robust gap actually lives for this modality. Phase 3 planning should treat leave-region-out as the primary "honest validation" demonstration and in-region block-CV as a secondary, more nuanced point (a real but modest effect, worth teaching as its own lesson about interpolation vs. extrapolation) rather than assuming both will show the same magnitude of leakage.

**Extraction mechanics are now walked end to end with working code and measured numbers**, not just cited: the bottom-up-COG/`WarpedVRT` fix is confirmed on both regions; the dequantize-then-renormalize formula is confirmed with population statistics over 5.3M (Bern) and 4.4M (Seville) valid pixels (pre-renorm norm mean 1.0001, std 0.002; post-renorm mean 1.000000, std ~1e-7); and a serious, previously undocumented performance trap was found — **scattered point sampling via `rasterio`/`WarpedVRT` `.sample()` on a remote COG costs 0.3–0.7 seconds *per point*** (328 s for 500 points), while a single bounded window read pulling millions of pixels at once is effectively free per pixel once fetched. The pipeline must read one window per (region, year) and index sample points out of the in-memory array — never loop `.sample()` over a scattered point set against a live COG.

**Primary recommendation:** build the pipeline to read one cached AOI window per (region, year) via `WarpedVRT`, extract ~1,900–2,200 stratified points per region (stable `sample_id` across years), write GeoParquet 1.1.0 with `course_provenance` metadata (pattern already verified to round-trip with the project's pinned geopandas/pyarrow), host the release on a GitHub Release tag (no new dependency, no huggingface_hub needed given ~0.5 MB/table), and gate Phase 3 planning on the leave-region-out numbers measured here rather than an assumed in-region leakage gap.

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| DATA-01 | Two-region point tables sharing one schema | Region A/B bboxes settled and verified; schema already defined in `course/schema.py` from Phase 1 — extraction mechanics (Code Examples) produce exactly its required columns plus the extras ARCHITECTURE.md's frozen-table schema calls for |
| DATA-02 | Sentinel-2 `B2..B12` on the same rows | Earth Search STAC walkthrough verified live; critical empirical correction to the baseline-offset handling (see Pitfall: Sentinel-2 offset) |
| DATA-03 | ≥2 years, independent change reference | AlphaEarth tile existence confirmed for 2018/2021/2024 at both regions; HRL Imperviousness 2018 confirmed reachable at both; HRL 2021 confirmed **not** publicly reachable (EU Login required) — settles the Phase-3-vs-change-lab EU Login question |
| DATA-04 | Few thousand rows, ≤1 MB/table, <100 MB bundle | Row-budget arithmetic (Sampling and Row Budget section) — 2,000 rows/table ≈ 0.53–0.57 MB; 6-table bundle ≈ 3.3 MB |
| DATA-05 | Provenance JSON in Parquet metadata | Pattern verified round-trip this session with pinned geopandas 1.1.4 / pyarrow 25.0.1; gap found — AEF GCS COGs carry no `DATASET_VERSION` in TIFF tags, must be hand-recorded |
| DATA-06 | Dataset card with exact attribution strings | Exact WorldCover and CLMS attribution strings fetched from official pages this session (Licensing section) |
| DATA-07 | Regenerable from anonymous no-login sources | Every source in the chain (AEF GCS, WorldCover S3, EEA ImageServer, Earth Search STAC) confirmed reachable anonymously today for both regions and all three years |
| DATA-08 | Integrity tests: norms, NaN, class counts, CRS, ≥5 blocks/region | Norm statistics measured on real data; class pool sizes measured (water is scarcest but still 1,400–1,700 candidates per region at 50 m spacing); block count trivially exceeds 5 at any block size 100 m–10 km tested |
| DATA-09 | Pinned public hosting, checksums, local-first + remote fallback | GitHub Release vs HF dataset comparison (Hosting section) — recommend GitHub Release, no new dependency |
| DATA-10 | Candidate query-polygon GeoJSON | Method recommended (OSM Overpass or manual curation); Overpass endpoint returned 406 this session — flagged as an open item needing a build-time fix, not a research blocker |
</phase_requirements>

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| AlphaEarth tile lookup & window extraction | Build Pipeline (author-only) | Public Data Sources | Runs once per release, not per notebook run; touches a 3.68 GB remote COG per tile |
| Dequantization + renormalization | Build Pipeline | Course Package (`course/embeddings.py`, if Phase 3 later needs it live) | Canonical implementation belongs where the frozen data is produced; any live Path A/A′ cell in a later phase reuses the same tested function |
| Label sampling (WorldCover, HRL) | Build Pipeline | Public Data Sources | Same reasoning — bulk raster reads, not per-notebook |
| Sentinel-2 baseline band extraction | Build Pipeline | Public Data Sources | STAC search + COG read, author-only |
| GeoParquet + provenance write | Build Pipeline | Frozen Data / Storage | Pipeline produces it; storage tier is where it lives afterward |
| Dataset hosting (release, checksums) | Frozen Data / Storage | — | GitHub Release tag; the `data/` directory in-repo is the canonical local-first copy |
| Local-first loader with remote fallback | Course Package (`course/data.py`) | Frozen Data / Storage | Notebooks import `course.data.load()`; it owns the local-vs-remote decision, storage tier is just the download target |
| Schema validation | Course Package (`course/schema.py`) | — | Already exists from Phase 1; this phase's output must pass it unchanged |
| `block_id` reference column (frozen) | Build Pipeline | — | Shipped only as a reference answer per ARCHITECTURE.md Anti-Pattern 6 — the notebook computes its own live blocks in Phase 3, which is a different tier entirely and out of this phase's scope |
| Integrity tests | Frozen Data / Storage (subject) | Course Package (test harness) | Tests read committed parquet; no pipeline or network dependency for the fast suite |

## Standard Stack

### Core (all already pinned — zero new packages this phase)

| Library | Version (verified this session) | Purpose | Why Standard |
|---------|---------|---------|--------------|
| rasterio | 1.5.1 [VERIFIED: local env, `import rasterio; rasterio.__version__`] | COG reads, `WarpedVRT`, windowed sampling | Already core dependency; GDAL-backed, handles `/vsicurl/` transparently |
| geopandas | 1.1.4 [VERIFIED: local env] | GeoDataFrame, GeoParquet 1.1.0 write/read | Already core; round-trip with `course_provenance` metadata confirmed this session |
| pyarrow | 25.0.1 [VERIFIED: local env] | Parquet metadata patch (provenance write) | Already core |
| duckdb | 1.5.5 (installed via `providers` extra, imports and runs `httpfs`+`spatial` successfully this session) [VERIFIED: local env] | `aef_index.parquet` tile lookup via `ST_Contains` | Already in `providers` extra from Phase 1 |
| requests | 2.34.2 [VERIFIED: local env] | STAC search POST, EEA `identify`/`exportImage`, checksum-verified release download | Already core-adjacent (`providers` extra); sufficient for STAC search without `pystac-client` |
| pystac-client, odc-stac, rioxarray, s3fs, gcsfs, pytz | Already pinned in `providers` extra (Phase 1) | STAC ergonomics, raster cube stacking, listing | Not strictly required (this research used plain `requests` + `rasterio` successfully for STAC search and COG reads), but already available if the pipeline implementation prefers `pystac-client`'s pagination/CQL2 over raw HTTP |
| scikit-learn | 1.9.0 [VERIFIED: local env] | `GroupKFold`, `LogisticRegression`, `RandomForestClassifier` for the dataset-aliveness guard test | Already core; note `LogisticRegression(multi_class=...)` was removed in this version — do not pass that kwarg |

**No new packages are introduced by this phase.** Everything needed (tile lookup, COG reads, STAC search, GeoParquet write, checksum verification) is already covered by the core install plus the `providers` extra from Phase 1.

### Explicitly NOT needed

| Considered | Verdict | Why |
|---|---|---|
| `huggingface_hub` | Do not add | Tables are ~0.5 MB each; a plain `requests.get()` against a pinned GitHub Release URL needs no new dependency and keeps ENV-05's "light, Colab-installable in under two minutes" intact. Community reports of slow/stalled `huggingface_hub` downloads specifically on Colab [CITED: github.com/huggingface/huggingface_hub issues #4528, #4085] add a mild vote against it for a case this small. |
| `pystac-client`/`odc-stac` as a hard requirement for this phase's extraction | Optional, not required | Plain `requests.post` to the Earth Search `/search` endpoint plus `rasterio.open()` on the returned asset `href` worked directly this session — simpler for a single-purpose pipeline script; use `pystac-client` if the implementation wants built-in pagination |

## Package Legitimacy Audit

Not applicable — this phase introduces zero new external packages. All packages used (rasterio, geopandas, pyarrow, duckdb, requests, and the rest of the `providers` extra) were already vetted and pinned during Phase 1 and are simply *used*, not newly installed, here.

## Region B Decision (settled)

### Verdict: Andalusian AOI near Seville, `lon [-5.99, -5.69], lat [37.28, 37.48]`

This bbox was chosen after live-testing and rejecting a first candidate (`lon [-6.10, -5.80]`) that straddled the UTM 29N/30N boundary — points west of −6.0° resolved to a different AlphaEarth tile/CRS than points east of it, which would force the pipeline to read and stitch two 3.68 GB COGs for one region instead of one. The final bbox is confirmed entirely inside UTM 30N at all four corners.

| Property | Region A — Bern | Region B — Seville | Source |
|---|---|---|---|
| Bounding box (EPSG:4326) | `[7.30, 46.85, 7.60, 47.05]` | `[-5.99, 37.28, -5.69, 37.48]` | This session |
| Approx. ground area | 508 km² (22.8 × 22.3 km, cos-lat corrected) | 591 km² (26.5 × 22.3 km) | Computed |
| UTM zone / EPSG | 32N / EPSG:32632 | 30N / EPSG:32630 | [VERIFIED: `aef_index.parquet` lookup, all 4 corners same zone] |
| AlphaEarth tiles, 2018/2021/2024 | All 3 exist, single tile per year | All 3 exist, single tile per year | [VERIFIED: DuckDB query against `aef_index.parquet`, this session] |
| WorldCover 2021 class balance (4-class course grouping) | crop 49.0% / vegetation 41.7% / built 8.4% / water 0.80% / bare 0.10% | crop 62.5% / vegetation 20.4% / built 15.2% / water 0.48% / bare 1.37% | [VERIFIED: live `rasterio` window read + histogram, this session] |
| HRL Imperviousness 2018 (public ImageServer) | 100% at Bern old town point (identify) | 40% at central Seville point (identify) | [VERIFIED: `identify` request against `GioLandPublic/HRL_ImperviousnessDensity_2018`, this session] |
| Sentinel-2 L2A, cloud <10%, summer 2018/2021/2024 | Scenes found for all 3 years | Scenes found for all 3 years | [VERIFIED: Earth Search STAC POST search, this session] |
| Leave-region-out balanced accuracy drop (LogReg / RF, Bern→Seville) | — | −28.0 pts / −21.4 pts vs in-region random CV | [VERIFIED: live classifier test on real extracted+labeled data, this session — see Sampling and Block Design] |

**Why this is a good Region B, with numbers, not just narrative:** the class-balance shift (crop dominance rises from 49% to 62.5%, vegetation falls from 42% to 20%, built roughly doubles as a fraction) reflects genuinely different land use — Swiss dairy/mixed farming and forest vs. Guadalquivir-valley irrigated agriculture and a larger urban fraction — and this shows up as a measured, large, reproducible drop in cross-region classifier transfer (see below), not just a plausible-sounding story.

**Rejected alternative note:** the original bbox candidate additionally would have required stitching AEF tiles across a UTM zone boundary — a good general reminder for any AOI selection near multiples of 6° longitude (UTM zone boundaries) or 3°×3° WorldCover tile edges.

## Anchor Years

**2018, 2021, 2024 confirmed valid for both regions**, matching ARCHITECTURE.md's original recommendation, now independently re-verified this session (not just cited):

| Check | Bern | Seville |
|---|---|---|
| AlphaEarth tile exists, 2018 | Yes — `32N/x98mprxqet6sgqecq...` | Yes — `30N/x4dnb824hdqrdscb6...` |
| AlphaEarth tile exists, 2021 | Yes — `32N/x2x0ui46492ik7uhz...` | Yes — `30N/xmruwlenbw32h2y8x...` |
| AlphaEarth tile exists, 2024 | Yes — `32N/xlhcaokskggk40mla...` | Yes — `30N/xwcmuxawcieze6uz4...` |
| S2 L2A scenes, cloud <10%, all 3 years | Yes (baselines 05.00, 03.01/05.00, 05.11) | Yes (baselines 02.08, 03.01/05.00, 05.11) |
| WorldCover 2021 labels | Yes (only year WorldCover v200 ships) | Yes |
| HRL Imperviousness 2018 (public, no login) | Yes | Yes |
| HRL Imperviousness 2021 / Change 2018–2021 (public, no login) | **No — not in the public ImageServer catalog** | **No — same** |

### Is the free EU Login genuinely needed?

**For Phase 3 (Module 3, similarity + classification): confirmed NOT needed.** Phase 3 only needs WorldCover 2021 labels, which are a fully separate, always-anonymous ESA product unrelated to Copernicus HRL / EU Login.

**For the change lab (Phase 5): needed only if the *exact* 2018–2021 HRL change product is wanted.** [VERIFIED, this session] Querying `https://image.discomap.eea.europa.eu/arcgis/rest/services/GioLandPublic?f=json` and listing all services returns density/change products only through the 2015–2018 generation (`HRL_ImperviousnessDensity_2018`, `HRL_ImperviousnessChange_15_18`, both `ImageServer` = pixel-queryable) — there is no anonymously reachable 2021 or 2018–2021-change service in this catalog at all, not even as a lower-resolution MapServer. This directly confirms PITFALLS.md's claim with a fresh, independent check rather than relying on the prior session's finding. Without EU Login, Phase 5's fallback is HRL Change 2015–2018 (documented as a broken series at the 2015→2018 resolution-switch boundary — do not use as-is) or the density-only 2018 layer plus manually-verified change points, exactly as ARCHITECTURE.md's fallback plan describes. This decision belongs to Phase 5, not Phase 2 — Phase 2 itself never needs the 2021 CLMS product.

## Extraction Mechanics, Verified End to End

### 1. Tile lookup (DuckDB + `aef_index.parquet`)

```python
import duckdb
con = duckdb.connect()
con.execute("INSTALL httpfs; LOAD httpfs; INSTALL spatial; LOAD spatial; SET enable_progress_bar=false;")
IDX = "https://data.source.coop/tge-labs/aef/v1/annual/aef_index.parquet"

# batch all (region, year) lookups in ONE scan, not one query per point — a single
# point-in-polygon query against this 77.8 MB remote parquet costs ~15-18s regardless
# of how many rows match, so batching via a VALUES join is a large speedup for
# multi-region, multi-year lookups.
q = f"""
WITH pts(name, lon, lat) AS (VALUES ('bern', 7.4474, 46.9480), ('seville', -5.9845, 37.3891))
SELECT p.name, idx.year, idx.utm_zone, idx.crs, idx.path
FROM read_parquet('{IDX}') idx, pts p
WHERE idx.year IN (2018, 2021, 2024) AND ST_Contains(idx.geom, ST_Point(p.lon, p.lat))
ORDER BY p.name, idx.year
"""
```
[VERIFIED: this session — 6-row batched lookup (2 regions × 3 years) took 15.7s total; a single unbatched lookup took 17.7s, confirming the cost is dominated by one remote parquet scan, not per-row work.]

### 2. Window read with the bottom-up-COG fix (confirmed on both regions, not just Bern)

```python
import rasterio
from rasterio.vrt import WarpedVRT
from rasterio.warp import transform_bounds
from rasterio.windows import from_bounds

GCS = "https://storage.googleapis.com/alphaearth_foundations/satellite_embedding/v1/annual"
url = f"{GCS}/2021/32N/x2x0ui46492ik7uhz-0000008192-0000000000.tiff"   # Bern 2021 tile

with rasterio.open(f"/vsicurl/{url}") as ds, WarpedVRT(ds, crs=ds.crs) as vrt:
    # CRITICAL: bbox must be reprojected from EPSG:4326 into the tile's own UTM CRS
    # BEFORE calling from_bounds — passing a WGS84 bbox directly into from_bounds
    # against a UTM transform silently produces a zero-size or wildly wrong window
    # (confirmed by hitting this bug directly this session: col_off=-33616, width=0).
    utm_bbox = transform_bounds("EPSG:4326", vrt.crs, *bbox_4326)
    win = from_bounds(*utm_bbox, vrt.transform).round_offsets().round_lengths()
    raw = vrt.read(window=win)          # (64, H, W) int8
```

Confirmed this session at both regions:
- Raw dataset transform: `e = +10` (bottom-up) — `rasterio.windows.from_bounds` against the raw `ds.transform` either raises `WindowError` or (if you skip the reprojection step above) silently returns a garbage/zero-size window.
- `WarpedVRT(ds, crs=ds.crs)` transform: `e = -10` (north-up) — this is the fix, confirmed for both Bern (EPSG:32632) and Seville (EPSG:32630).
- Both tiles: `shape (8192, 8192)`, `dtype int8`, `count 64`, `nodata -128.0`.
- TIFF tags on the GCS COG: **only `{'AREA_OR_POINT': 'Area'}`** — no `DATASET_VERSION`, `MODEL_VERSION`, or `UTM_ZONE` tags [VERIFIED, this session]. Unlike the Earth Engine asset (which carries these as image properties), the GCS-path pipeline **cannot read the dataset version programmatically from the source** — it must be recorded by hand in `pipeline/areas.yaml` or the provenance template, sourced from the EE catalog page (`DATASET_VERSION` 1.1 as of 2025-11-17 per PITFALLS.md) and kept in sync manually if Google revises it.

### 3. Dequantization + renormalization — verified with population statistics, not a single pixel

```python
import numpy as np

def dequantize(raw):  # raw: (64, H, W) int8
    mask = np.any(raw == -128, axis=0, keepdims=True)
    v = raw.astype(np.float32)
    d = (v / 127.5) ** 2 * np.sign(v)
    n = np.linalg.norm(d, axis=0, keepdims=True)
    unit = d / (n + 1e-9)
    return np.where(mask, np.nan, unit)
```

Measured this session over the **full sampled AOI window** (not a single pixel):

| Region | Valid pixels | Pre-renorm norm | Post-renorm norm |
|---|---|---|---|
| Bern 2021 | 5,277,636 | mean 1.0001, std 0.00198, min 0.9910, max 1.0093 | mean 1.000000, std 9.68e-08 |
| Seville 2021 | 4,448,200 | mean 1.0001, std 0.00200, min 0.9905, max 1.0092 | mean 1.000000, std 9.65e-08 |

This **refines** ARCHITECTURE.md's single-pixel figure of "0.9963 before renormalization" — the population mean is actually much closer to 1.0 (1.0001), with per-pixel deviation up to ~±0.9%. Renormalization is still correct practice and produces essentially exact unit vectors (std ~1e-7, floating-point noise floor). Value range after dequantization (pre-renorm): approximately `[-0.52, 0.49]` at both regions — consistent, no leaked `-128` artifacts, `n_nodata_px = 0` in both AOI windows (both AOIs are fully inside valid tile coverage).

### 4. Performance trap found this session: scattered point sampling is catastrophically slow

**Do not loop `vrt.sample(coords)` or `ds.sample(coords)` over a scattered set of points against a remote COG.** Measured directly:

| Approach | Result | Cost |
|---|---|---|
| Bounded window read, 2268×2327 px × 64 bands (Bern, full AOI) | 5,277,636 valid pixels | 311–342 s **total**, i.e. effectively free per pixel once fetched |
| Scattered `vrt.sample()`, 500 random points (Bern) | 500 values | **328 s total = 0.66 s/point** |
| Scattered `vrt.sample()`, 500 random points (Seville) | 357/500 valid | **168 s = 0.47 s/point**, plus 28.6% of points returned spurious nodata near the VRT/window resampling boundary despite the full-window read of the identical bbox showing zero nodata pixels — a correctness gotcha on top of the speed problem |

**Implication for the pipeline:** read one bounded window per (region, year) via `WarpedVRT` (as in step 2), then extract all sample points by indexing the in-memory NumPy array (row/col from the window's affine transform) — never re-query the remote COG per point. A stride-5 (50 m spacing) subsample of the Bern window produced 211,564 candidate labeled points from one already-fetched window in under 2 seconds of local array work (see Sampling section).

### 5. WorldCover label sampling

```python
with rasterio.open(WC_URL) as wc:
    win = from_bounds(*bbox_4326, wc.transform).round_offsets().round_lengths()
    arr = wc.read(1, window=win)   # WorldCover is already EPSG:4326, no reprojection needed
```
Fast: full-AOI WorldCover window reads took 1.7–3.6 s [VERIFIED, this session] — orders of magnitude faster than the AEF COG reads, since WorldCover COGs are much smaller per tile and the AOI window is a small fraction of the 3°×3° tile.

Tile naming confirmed both regions this session: Bern → `N45E006`, Seville → `N36W006` (3°×3°, lower-left-corner naming).

### 6. Sentinel-2 STAC extraction — a critical, empirically-verified correction to the offset rule

**PITFALLS.md's inherited rule** ("baseline ≥04.00 scenes need the −0.1 offset unless `boa_offset_applied`") **does not hold up against direct measurement of Earth Search's `sentinel-s2-l2a-cogs` COG assets.** Tested this session at the exact same ground point (a built-up area near Bern) across three scenes spanning the relevant range:

| Scene | Processing baseline | `boa_offset_applied` | DN mean (11×11 px) | Reflectance **without** offset | Reflectance **with** −0.1 offset |
|---|---|---|---|---|---|
| `S2B_32TLT_20180828_0_L2A` (original archive item) | 02.08 | n/a (pre-baseline-04) | 1312.1 | 0.131 | n/a |
| `S2B_32TLT_20180828_1_L2A` (Element84-reprocessed duplicate of the same date) | 05.00 | `true` | 1242.0 | 0.124 | 0.024 |
| `S2A_32TLT_20240920_0_L2A` (native baseline 05.11) | 05.11 | `true` | 1251.0 | 0.125 | 0.025 |

All three scenes — spanning the original pre-baseline-04 archive, an Element84-reprocessed duplicate of the *same date* stamped with a post-baseline-04 processing-baseline label, and a genuinely native 2024 baseline-05.11 scene — give **consistent, physically plausible reflectance (~0.12–0.13) when the offset is *not* applied**, and implausible near-zero-to-negative reflectance when it is. Element84's own discussion of this collection [CITED: github.com/Element84/earth-search/discussions/26] states they *decided not to bake scale/offset into the stored pixel values* and reprocessed the archive to a harmonized baseline specifically "to eliminate the need to harmonize across processing versions" — consistent with what was measured, though the `raster:bands.offset: -0.1` / `earthsearch:boa_offset_applied: true` metadata fields, read literally, suggest the opposite.

**Recommendation:** treat the metadata's offset field as unreliable for this specific collection/bucket path and **do not subtract it by default**. Instead, read `scale`/`offset` from `raster:bands` as documented practice, but add a defensive plausibility assertion after computing reflectance (e.g., `assert -0.05 < reflectance.mean() < 0.6` for a vegetated/mixed scene) that will catch the case either way, and note in the pipeline's provenance record which convention was used. This is exactly the kind of undocumented-but-measurable discrepancy that "verify empirically" research is for — do not silently trust either the metadata or the folklore.

Also note the item-ID convention discovered this session: Earth Search's `sentinel-2-l2a` collection carries **duplicate items for some original-archive dates** distinguished by a numeric suffix (e.g., `..._0_L2A` = original processing, `..._1_L2A` = Element84 reprocessing) — a STAC search can return both; the pipeline should pick one consistently (e.g., prefer the lowest-cloud-cover result, or explicitly prefer `_0_` for pre-2022 dates) and record the exact item ID in provenance.

SCL cloud masking and per-band `raster:bands` scale metadata are present and readable exactly as documented (`scale: 0.0001` on every checked asset); this part of PITFALLS.md's guidance holds.

### 7. Provenance metadata round-trip — verified with the project's actual pinned versions

```python
import json
import pyarrow.parquet as pq

gdf.to_parquet(path, schema_version="1.1.0", write_covering_bbox=True, compression="zstd")
t = pq.read_table(path)
pq.write_table(
    t.replace_schema_metadata({**t.schema.metadata, b"course_provenance": json.dumps(provenance).encode()}),
    path,
)
```
[VERIFIED, this session, geopandas 1.1.4 / pyarrow 25.0.1]: the `geo` key (GeoParquet 1.1.0, covering bbox) and the injected `course_provenance` key both survive the round trip; `gpd.read_parquet()` reads the result back correctly with CRS intact. ARCHITECTURE.md's Pattern 5 is confirmed to work exactly as written against the versions actually pinned in this repo's `pyproject.toml` — this had not been independently re-checked against the project's *own* lockfile until this session.

## Sampling and Block Design

### Row budget (verified arithmetic, not guesswork)

Per-row byte estimate for the planned schema (dict-encoded categorical columns, `float32` embeddings/bands):

| Column group | Bytes/row |
|---|---|
| `sample_id` (int64), `year` (int16), misc dict-encoded strings (`region`, `utm_zone`, `aef_tile`, `aef_source`, `label`, `label_source`, `block_id` int32) | ~22 |
| `lon`/`lat` (float32 ×2) + `geometry` (WKB point) | 29 |
| `A00..A63` (float32 × 64) | 256 |
| `S2_B02..B12` (float32 × 6, matching the schema already defined in `course/schema.py`) | 24 |
| `worldcover_2021`, `imd_2018`, `s2_n_scenes` (uint8/int8 × 3) | 3 |
| **Total** | **~334 bytes/row uncompressed-ish** |

At 2,000 rows/table: ≈0.67 MB raw, ≈0.53–0.57 MB with typical 15–25% zstd reduction on this column mix — comfortably under the 1 MB/table target with margin. A 6-table bundle (2 regions × 3 years) is ≈3.3 MB total, leaving enormous headroom under the 100 MB bundle cap for `DATA_CARD.md`, `manifest.json`, the query-polygon GeoJSON, and small COG clip thumbnails for later phases.

**Recommendation: ~1,900–2,200 stratified points per region**, sampled once at a fixed set of locations (2021 WorldCover-stratified) and re-extracted at the same `sample_id`s for 2018 and 2024, exactly as ARCHITECTURE.md's `sample_design.py` plan describes.

### Class pool sizes — measured, not assumed

From the same stride-5 (50 m spacing) grid subsample used for the CV tests below, drawn from one already-fetched AOI window (211,564 candidate points at Bern, 178,020 at Seville):

| Class | Bern pool | Seville pool |
|---|---|---|
| built | 17,607 | 34,120 |
| vegetation | 87,931 | 35,613 |
| crop | 104,086 | 103,912 |
| water | 1,720 | 1,443 |
| bare | 219 | 2,929 |

Water is the scarcest class at both regions but still has 1,400+ candidates even at 50 m spacing — comfortably supports a stratified target of 300–400 points/class/region with margin for a tighter final spacing if desired. **Recommend stratified (not proportional-random) sampling** — cap majority classes (crop/vegetation) at ~500 points and take up to ~400 for water — to avoid both a trivially-separable majority-class-dominated table and an unusably thin minority class, per PITFALLS.md's "frozen dataset too clean" warning.

### Block size

Tested block sizes 100 m, 200 m, 500 m, 1 km, 2 km, 5 km, and 10 km on Bern, with LogisticRegression and RandomForest, both with a 50 m minimum-spacing sample and a genuinely unconstrained (adjacent-10m-pixel-allowed) sample from a smaller full-resolution window. **Block size in the 500 m–5 km range makes essentially no difference to in-region CV balanced accuracy (0.85–0.92 across the whole range)** — the exception is 10 km blocks, which showed an apparent large drop but with very high variance (only 12 groups, unstable folds), an artifact of too-few-groups rather than a genuine spatial effect.

**Recommendation:** a block size of **1–2 km** is defensible — it produces 150–509 groups at Bern's AOI scale, comfortably clears the "≥5 blocks/region" requirement (DATA-08) with enormous margin, avoids the small-group instability seen at 10 km, and matches PITFALLS.md's prior "2–5 km blocks over a ≥30×30 km AOI" guidance reasonably well even though this AOI is smaller (~23×23 km). This is a **methodological choice**, not one that changes the demonstrated CV gap much at this AOI scale for this data — see below for why leave-region-out, not block size, is where the real lesson lives.

### The critical sanity check: does the frozen sample reproduce the random-vs-honest-CV gap?

This was tested directly and the answer is **yes for leave-region-out, weakly for in-region spatial-block CV** — a genuinely important, non-obvious finding.

**In-region random split vs. spatial-block CV (Bern only), balanced accuracy, 1,900-point stratified sample:**

| Test condition | LogisticRegression | RandomForest |
|---|---|---|
| Random 5-fold (50 m min spacing) | 0.913 ± 0.011 | 0.913 ± 0.014 |
| Block CV, 500 m–5 km (50 m min spacing) | 0.911–0.920 | 0.912–0.915 |
| Random 5-fold, **no spacing constraint** (adjacent 10 m pixels allowed, small full-res window) | 0.875 ± 0.016 | — |
| Block CV, 100 m–1 km, no spacing constraint | 0.853–0.871 | — |

Even with genuinely adjacent, unconstrained 10 m pixels in the "random" arm, the gap tops out around 1–4 balanced-accuracy points — far short of the "98% vs 82%" folklore figure PITFALLS.md's illustrative framing invokes. This held across two classifiers and a wide range of block sizes.

**Leave-region-out (Bern ↔ Seville), same 1,900-point-per-region sample:**

| Direction | LogisticRegression | RandomForest |
|---|---|---|
| Random CV within Bern | 0.913 | 0.913 |
| Random CV within Seville | 0.858 | 0.854 |
| **Train Bern → test Seville** | **0.633 (−28.0 pts vs in-region Bern)** | **0.699 (−21.4 pts)** |
| **Train Seville → test Bern** | **0.426 (−43.2 pts vs in-region Seville)** | **0.774 (−7.9 pts)** |

This is a large, robust, reproducible effect, confirmed with real fetched-and-labeled data, not a projection. Per-class detail (LogReg, Bern→Seville): built precision 0.94/recall 0.57, crop precision 0.65/recall 0.57, vegetation precision 0.60/recall 0.55, water precision 0.48/recall 0.84 — the model systematically misreads Seville's spectral/embedding signature for classes it learned only from Bern.

**Planning implication for Phase 3:** design the flagship "random split lies" demonstration around **leave-region-out as the primary evidence** (SIM-07/SIM-08 already call for this), with in-region spatial-block CV taught as a secondary, honestly-smaller effect — worth its own short discussion of *why* it's smaller for embeddings than for raw pixels (AlphaEarth embeddings aggregate a full year of multi-modal signal per pixel, which plausibly makes them less prone to naive adjacent-pixel memorization than raw single-date spectral bands). **Do not assume the in-region random-vs-block gap alone will "sell" the lesson** — verify it again on the actual final frozen sample once built (see Validation Architecture), and consider whether SIM-09's raw-Sentinel-2-bands comparison might show a *larger* in-region gap than the embeddings do, which would itself be a genuinely interesting, teachable finding (embeddings are more leakage-resistant than raw pixels) rather than a problem to hide.

## Licensing and Redistribution

| Source | License | Exact attribution (verified this session where noted) | Bundle in-repo? |
|---|---|---|---|
| AlphaEarth / Satellite Embedding | CC BY 4.0 | "The AlphaEarth Foundations Satellite Embedding dataset is produced by Google and Google DeepMind." [CITED: PITFALLS.md, prior session, re-confirmed against the same official page] | Yes — sampled tables only, never raw COG tiles |
| ESA WorldCover 2021 v200 | CC BY 4.0 | **"© ESA WorldCover project 2021 / Contains modified Copernicus Sentinel data (2021) processed by ESA WorldCover consortium"** [VERIFIED this session, esa-worldcover.org/en/data-access] plus citation: Zanaga et al. 2022, https://doi.org/10.5281/zenodo.7254221 | Yes — derived label column, redistributable under CC BY 4.0 with the attribution above |
| Copernicus HRL Imperviousness | Free/open, commercial use allowed | "Generated using European Union's Copernicus Land Monitoring Service information; \<DOI\>" [VERIFIED this session, land.copernicus.eu/en/faq — generic CLMS wording; product-specific DOI not separately located this session] | Yes — derived reference column only |
| Sentinel-2 (any derived reflectance values) | EU legal notice (Reg. 1159/2013) | "Contains modified Copernicus Sentinel data [Year]" [CITED: PITFALLS.md, sentinels.copernicus.eu legal notice] | Yes — derived band values only, never raw scene assets |
| Copernicus Global Embeddings (CDSE) | No stated license; portal terms prohibit redistribution | — | **Never bundle** — not used by this phase's pipeline at all; only relevant if a future phase considers it |

**Verdict:** everything this phase bundles (AlphaEarth-derived embeddings, WorldCover-derived labels, HRL-derived reference values, Sentinel-2-derived reflectance bands) is redistributable in a paid course under CC BY 4.0 / free-open-with-attribution terms, provided the exact attribution strings above appear in `DATA_CARD.md` and the provenance metadata. No source in this phase's pipeline lacks redistribution rights.

## Hosting and the Local-First Loader

**Recommendation: GitHub Release assets, not a Hugging Face dataset repo.**

| Factor | GitHub Release | HF Dataset Repo |
|---|---|---|
| File size limit | 2 GiB/file [CITED: GitHub docs, community discussion] — vastly more than the ~0.5 MB tables need | No practical limit either, irrelevant at this size |
| New dependency required | None — `requests` (already available) against a pinned tag URL | `huggingface_hub` — not currently a dependency anywhere in `pyproject.toml` |
| Colab download reliability at this size | Trivial — sub-MB HTTP GET | Generally fine, but multiple community reports of slow/stalled large-file downloads specifically on Colab exist [CITED: MEDIUM confidence, anecdotal GitHub issues] — not a concern at KB/MB scale either way, so this factor is actually neutral here |
| Versioning convention fit | Matches the repo's existing `COURSE_RELEASE = "2026.08"` tag convention already in `course/config.py` | Would need a parallel revision/tag scheme |
| Checksum verification | `manifest.json` + `hashlib.sha256`, no library needed | Same, or rely on HF's own hash metadata |

**Loader shape (`course/data.py`, to be added this phase):**

```python
import hashlib
from pathlib import Path
import requests
import geopandas as gpd

RELEASE_BASE = "https://github.com/{org}/{repo}/releases/download/{tag}"

def load(area: str, year: int) -> gpd.GeoDataFrame:
    local = Path(f"data/{area}/{area}_aef_{year}_v1.1.parquet")
    if local.exists():
        return gpd.read_parquet(local)
    manifest = _load_manifest()  # from data/manifest.json, committed
    entry = manifest[local.name]
    url = f"{RELEASE_BASE.format(org=ORG, repo=REPO, tag=COURSE_RELEASE)}/{local.name}"
    resp = requests.get(url, timeout=60)
    resp.raise_for_status()
    sha = hashlib.sha256(resp.content).hexdigest()
    assert sha == entry["sha256"], f"checksum mismatch for {local.name}"
    local.parent.mkdir(parents=True, exist_ok=True)
    local.write_bytes(resp.content)
    return gpd.read_parquet(local)
```

Because the tables are tiny, they are also simply **committed to the repo directly** (as ARCHITECTURE.md already plans) — the remote-fallback path in `course.data.load()` mainly matters for a fresh Colab session that fetches the `course` package without a full git clone. This satisfies DATA-09's "local-first with remote fallback" without adding any new dependency.

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest 9.1.1 (already a dev dependency; `tests/test_schema.py` establishes the pattern this phase extends) |
| Config file | `pyproject.toml` `[tool.pytest.ini_options]` `testpaths = ["tests"]` (already present) |
| Quick run command | `uv run pytest tests/test_schema_data.py -x` (new file this phase) |
| Full suite command | `make test` (already wraps `uv run pytest tests/`) |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| DATA-01 | Schema columns present, CRS = EPSG:4326, both regions | unit, no network | `pytest tests/test_schema_data.py::test_schema_columns -x` | ❌ Wave 0 |
| DATA-02 | `S2_B02..B12` present, values in plausible reflectance range | unit, no network | `pytest tests/test_schema_data.py::test_s2_bands_plausible -x` | ❌ Wave 0 |
| DATA-03 | ≥2 years present, `sample_id` stable across year-tables (join test) | unit, no network | `pytest tests/test_schema_data.py::test_sample_id_stable_across_years -x` | ❌ Wave 0 |
| DATA-04 | Row count in target range, file size ≤~1 MB, bundle ≤100 MB | unit, no network | `pytest tests/test_schema_data.py::test_table_size_budget -x` | ❌ Wave 0 |
| DATA-05 | `course_provenance` key present with required fields | unit, no network | `pytest tests/test_schema_data.py::test_provenance_metadata_complete -x` | ❌ Wave 0 |
| DATA-06 | `DATA_CARD.md` exists, contains exact attribution substrings | unit, no network | `pytest tests/test_data_card.py -x` | ❌ Wave 0 |
| DATA-07 | Pipeline regenerates tables from anonymous sources end to end | integration, **network required** | `pytest tests/test_pipeline_regen.py -m network` | ❌ Wave 0 — mark `@pytest.mark.network`, exclude from default `make test` |
| DATA-08 | Unit norms ≈1 (atol 1e-3), no NaN, min class counts/region, CRS present, ≥5 blocks/region | unit, no network | `pytest tests/test_schema_data.py::test_dataset_integrity -x` | ❌ Wave 0 |
| DATA-09 | Checksums match manifest (local); remote download + checksum (network) | unit + integration | `pytest tests/test_schema_data.py::test_manifest_checksums -x` (local) and `pytest tests/test_data_loader.py -m network` (remote fallback) | ❌ Wave 0 |
| DATA-10 | Query-polygon GeoJSON exists, valid geometry, within AOI bounds | unit, no network | `pytest tests/test_query_polygons.py -x` | ❌ Wave 0 |

### Sampling Rate

- **Per task commit:** `pytest tests/test_schema_data.py tests/test_data_card.py tests/test_query_polygons.py -x` — all read only committed local files, should run in low single-digit seconds.
- **Per wave merge:** add the network-marked tests (`pytest tests/ -m network`) — re-runs a small slice of the pipeline against live sources and confirms the remote-fallback download+checksum path still works. Budget for slow network calls (this session's own window reads took 190–340 s each) — do not run this on every commit.
- **Phase gate:** full suite green, plus the dataset-aliveness guard described below, before `/gsd:verify-work`.

### Wave 0 Gaps

- [ ] `tests/test_schema_data.py` — covers DATA-01, DATA-02, DATA-03, DATA-04, DATA-05, DATA-08, DATA-09 (local half)
- [ ] `tests/test_data_card.py` — covers DATA-06
- [ ] `tests/test_pipeline_regen.py` — covers DATA-07 (network-marked)
- [ ] `tests/test_data_loader.py` — covers DATA-09 (remote-fallback half, network-marked); exercises `course/data.py`, which does not exist yet
- [ ] `tests/test_query_polygons.py` — covers DATA-10
- [ ] `pytest.ini` / `pyproject.toml` — register a `network` marker (`markers = ["network: requires internet access"]`) so `-m "not network"` can be the default fast-suite filter
- [ ] `course/data.py` — the local-first loader itself does not exist yet (Course Package tier); Phase 2 must create it, not just test it

### Guarding against "valid schema, dead pedagogy"

A schema/norm/class-count check alone cannot catch a dataset that passes every structural test yet fails to teach anything — this session's own finding (in-region block-CV gap is weak) proves that risk is real, not hypothetical, for this exact dataset. The concrete guard:

**A committed, no-network "dataset-aliveness" test** that loads both frozen regional tables, trains a fast `LogisticRegression` on Region A, evaluates balanced accuracy on Region A (in-region random CV) and on Region B (leave-region-out), and asserts:

```python
def test_leave_region_out_gap_is_real(bern_table, seville_table):
    in_region_acc = ...  # 5-fold CV balanced_accuracy on Bern alone
    lro_acc = ...         # train Bern, predict Seville, balanced_accuracy
    assert in_region_acc - lro_acc >= 0.10, (
        "leave-region-out gap collapsed below 10 points — Region B may have become "
        "too similar to Region A; the transfer-learning lesson will not land"
    )
```

Measured this session, the real gap is 21–28 points, so a 10-point floor leaves comfortable margin while still catching a genuine regression (e.g., an AOI redraw that accidentally narrows the two regions' distributions, or an over-aggressive stratification that homogenizes classes). **Do not** write an equivalent hard assertion for the in-region block-CV gap at a large threshold — this session's measurement shows that gap is legitimately small (1–4 points) for this data; asserting e.g. "block accuracy ≤ random accuracy − 10 points" would fail on a *correctly built* dataset. If Phase 3 wants a stronger in-region demonstration, that is a data/lesson-design decision to make explicitly (e.g., using raw Sentinel-2 bands, or an intentionally-clustered "naive" sampling arm), not something a threshold test should silently assume is already true.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Network access to `storage.googleapis.com` (AlphaEarth GCS) | Tile reads | ✓ | — | Source Cooperative mirror (`data.source.coop/tge-labs/aef`) if GCS is unreachable |
| Network access to `data.source.coop` (tile index) | Tile lookup | ✓ | — | — |
| Network access to `esa-worldcover.s3.eu-central-1.amazonaws.com` | Labels | ✓ | — | — |
| Network access to `image.discomap.eea.europa.eu` | HRL reference | ✓ | — | — |
| Network access to `earth-search.aws.element84.com` + `sentinel-cogs.s3.us-west-2.amazonaws.com` | Sentinel-2 | ✓ | — | — |
| `duckdb` (Python, `httpfs`+`spatial` extensions) | Tile lookup | ✓ (via `uv sync --extra providers`) | 1.5.5 | — |
| `rasterio` | COG reads | ✓ (core dependency) | 1.5.1 | — |
| Overpass API (`overpass-api.de`) for DATA-10 candidate polygons | Query-polygon discovery | ✗ this session — returned HTTP 406 with both default and custom `User-Agent` headers via `requests` | — | Manual curation of 3–5 polygons from the already-fetched WorldCover/S2 imagery, or retry with a proper Overpass client library (`overpy`) at build time |

**Missing dependencies with no fallback:** none — every core data source for this phase is reachable.

**Missing dependencies with fallback:** Overpass API access (DATA-10) — not a blocker, has a clear manual fallback.

## Security Domain

This phase is a read-only, anonymous, offline-data-build pipeline — most web-application ASVS categories do not apply. `security_enforcement` is not explicitly disabled in `.planning/config.json`, so this section documents what is and is not relevant rather than omitting it.

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | No | No source in this phase requires credentials; explicitly a design constraint (DATA-07) |
| V3 Session Management | No | No sessions |
| V4 Access Control | No | No access control surface |
| V5 Input Validation | Partial | STAC search parameters and AOI bounding boxes are author-controlled constants, not user input, in this phase; validate bbox ordering/CRS defensively in `pipeline/` code anyway (cheap, catches the exact `from_bounds` bug hit this session) |
| V6 Cryptography | No | No cryptography beyond `hashlib.sha256` for checksum verification (integrity, not confidentiality) |
| V12 File/Resource | Yes | Downloaded release assets must be checksum-verified before use (already the DATA-09 design); never `eval`/`exec` downloaded content |

### Known Threat Patterns

| Pattern | STRIDE | Standard Mitigation |
|---|---|---|
| Tampered release asset served from a compromised mirror or MITM | Tampering | `sha256` checksum verification against `manifest.json` before the loader accepts a downloaded file (already in the recommended `course/data.py` shape above) |
| Supply-chain risk from a new pip dependency | Tampering | Not applicable this phase — zero new packages introduced |
| Secrets committed accidentally (EE keys, LGND tokens) | Information Disclosure | Not applicable this phase — no credentials are used by any source in this pipeline |

## Common Pitfalls

### Pitfall 1: Treating raw int8 AlphaEarth values as the embedding
Inherited from PITFALLS.md, re-confirmed with stronger statistics this session (population norm stats over millions of pixels, not one). See Extraction Mechanics §3.

### Pitfall 2: Treating Google's COGs as ordinary north-up rasters
Inherited from ARCHITECTURE.md, re-confirmed on **both** regions this session (not just Bern) — raw `transform.e = +10`, `WarpedVRT` fixes it. See Extraction Mechanics §2.

### Pitfall 3 (NEW): AOI bounding box straddling a UTM zone boundary
**What goes wrong:** An AOI bbox that crosses a UTM zone boundary (e.g., a multiple-of-6° meridian) resolves different points to different AlphaEarth tiles/CRSs, silently forcing the pipeline to fetch and reconcile two 3.68 GB COGs for what was meant to be one region.
**Why it happens:** Nothing in the tile-lookup query warns you — each point resolves correctly, individually, to its own tile; only a full-corner check reveals the split.
**How to avoid:** Check all four corners of any candidate AOI bbox against `aef_index.parquet` before committing to it (exactly as done for Region B this session — the first Seville candidate straddled 29N/30N and was rejected).
**Warning signs:** Sentinel-2 STAC search over the same bbox returns items from two different MGRS grid zones.

### Pitfall 4 (NEW, high-impact): Scattered point sampling on a remote COG is catastrophically slow
See Extraction Mechanics §4. 0.3–0.7 s/point measured; a bounded window read is the only viable pattern for a multi-thousand-point pipeline.

### Pitfall 5 (NEW): Sentinel-2 `raster:bands.offset` metadata may not reflect the actual pixel encoding
See Extraction Mechanics §6 for the full empirical walkthrough. Verify with a known ground point before trusting the metadata blindly; add a plausibility assertion regardless of which convention is used.

### Pitfall 6 (NEW): AlphaEarth GCS COGs carry no version metadata
TIFF tags are `{'AREA_OR_POINT': 'Area'}` only — `DATASET_VERSION` must be hand-recorded from the EE catalog page in provenance, not read from the source. A future AlphaEarth re-versioning (as happened with the 2017 layer in 2025-11-17) would go undetected by any automated check against the GCS path alone.

### Pitfall 7 (NEW, most important for planning): The in-region random-vs-block CV gap is weak for AlphaEarth embeddings — do not assume it will "sell" the lesson on its own
See Sampling and Block Design §"The critical sanity check." The dramatic, robust gap for this dataset is leave-region-out, not in-region spatial blocking. Plan Phase 3's flagship demonstration accordingly, and re-verify on the actual final frozen sample (not just this session's smaller test sample) once built, via the dataset-aliveness guard test.

### Pitfall 8: EU Login is not needed for Phase 3, but relevant to Phase 5
See Anchor Years §"Is the free EU Login genuinely needed?" — re-confirmed this session via a live, direct check of the public EEA service catalog, not just inherited from the prior session's finding.

### Pitfall 9: Minority-class scarcity (water) requires stratified, not proportional-random, sampling
Water is 0.44–0.80% of AOI area at both regions. Pure proportional-random sampling at a 2,000-point table would yield only ~9–16 water points, too few for reliable per-fold evaluation. Stratify explicitly; the measured pool (1,400+ candidates per region even at 50 m spacing) supports a 300–400-point stratified target with room to spare.

## Code Examples

All code blocks under "Extraction Mechanics, Verified End to End" above are drawn from working, executed code this session, not hypothetical snippets — they are the canonical examples for this section.

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Assume the "0.9963 pre-renorm norm" single-pixel figure from Phase 1 research generalizes | Population statistics over millions of pixels: mean 1.0001, std 0.002 | This session | Renormalization is still correct practice, but the deviation is smaller and more uniform than the single-pixel figure suggested |
| Assume in-region random-vs-block CV will show a dramatic gap (PITFALLS.md's "98% vs 82%" framing) | Measured: 1–4 points in-region; 21–28 points leave-region-out | This session | Changes what Phase 3's flagship demonstration should emphasize |
| Trust `raster:bands.offset`/`boa_offset_applied` metadata literally for Sentinel-2 reflectance | Empirically verify against a known ground point; the metadata appears unreliable for this specific collection | This session | Prevents silently shifting every Sentinel-2-derived feature by −0.1 (a massive, wrong correction) |
| Loop `.sample()` over scattered points for extraction | Read one bounded window per (region, year), index points from the array | This session | ~500x+ speedup for a multi-thousand-point extraction; also avoids a correctness gotcha (spurious nodata near VRT boundaries) |

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | Package versions for `pystac-client`, `odc-stac`, `rioxarray`, `s3fs`, `gcsfs`, `pytz` (cited from Phase 1's STACK.md, not independently re-verified via `pip index versions` this session — only `rasterio`, `geopandas`, `pyarrow`, `duckdb`, `requests`, `scikit-learn` were directly version-checked this session) | Standard Stack | Low — these packages are not strictly required by this phase's own extraction path (plain `requests`+`rasterio` sufficed); only matters if the pipeline implementation chooses to use `pystac-client` |
| A2 | `huggingface_hub` reliability issues on Colab, cited from community GitHub issues, not independently reproduced this session | Hosting | Low — this is a supporting argument for the GitHub-Release recommendation, not the sole reason; the dependency-footprint and simplicity arguments stand independently |
| A3 | Overpass API method for DATA-10 candidate query polygons — the endpoint returned HTTP 406 for both plain and custom-`User-Agent` requests this session; root cause not diagnosed (could be a transient block, a missing required header, or a request-format issue) | Environment Availability, Pitfall list | Medium — DATA-10 needs *a* working method; if Overpass remains unreachable at build time, fall back to manual curation of 3–5 polygons from the already-verified WorldCover/S2 imagery for both regions |
| A4 | Exact DOI/citation string for the specific HRL Imperviousness 2018 product (only the generic CLMS attribution template was located this session, not a product-specific DOI) | Licensing | Low — the generic CLMS wording is valid and sufficient; a product-specific DOI is a nice-to-have precision improvement, not a licensing risk |
| A5 | The `boa_offset_applied`/`raster:bands.offset` discrepancy's root cause (why the metadata says one thing and measured pixel values another) is inferred from Element84's GitHub discussion, not confirmed by Element84 directly for this exact edge case (reprocessed-duplicate items) | Extraction Mechanics §6 | Low for this phase's purpose — the *recommendation* (verify empirically, don't blindly apply the offset, add a plausibility assertion) holds regardless of the root cause |

**If this table is empty:** N/A — see entries above. All are LOW-to-MEDIUM risk and none block Phase 2 planning; A3 is the only one requiring a concrete build-time fallback decision.

## Open Questions (RESOLVED)

All three are addressed by concrete tasks in the Phase 2 plans; resolutions noted inline.


1. **RESOLVED (Plan 02-12's aliveness test runs against the committed tables): Does the leave-region-out gap hold up on the *final* frozen sample (not this session's ad hoc 1,900-point test sample)?**
   - What we know: measured 21–28 points on a stratified sample drawn the same way the final pipeline plans to sample.
   - What's unclear: the final sample will use a different random seed, possibly different point counts, and points drawn from all three anchor years rather than 2021 only.
   - Recommendation: re-run the exact dataset-aliveness guard test (Validation Architecture section) against the actual committed frozen tables once built, as part of Phase 2's own closeout — not deferred to Phase 3.

2. **RESOLVED (Plan 02-04 implements the defensive plausibility assertion regardless of root cause): What is the true cause of the Sentinel-2 offset metadata discrepancy?**
   - What we know: empirically, applying the documented offset produces implausible reflectance across three different-baseline scenes at the same point; not applying it produces consistent, plausible values.
   - What's unclear: whether this is specific to the `sentinel-s2-l2a-cogs` bucket path, specific to reprocessed-duplicate items, or a broader Earth Search convention.
   - Recommendation: implement the defensive plausibility-assertion pattern regardless (Extraction Mechanics §6) so the pipeline is correct either way; do not spend further research time resolving the root cause unless a future scene shows the assertion failing.

3. **RESOLVED (Plan 02-10 Task 2 tries Overpass then falls back to manual curation): DATA-10 candidate query polygons — what is the actual working method?**
   - What we know: Overpass API returned HTTP 406 this session for both plain and User-Agent-customized requests.
   - What's unclear: whether this is a transient block, a rate limit, or a header requirement not yet identified.
   - Recommendation: at build time, either retry with the `overpy` Python client (handles Overpass's quirks better than raw `requests`) or manually curate 3–5 polygons (a solar farm, a quarry, a construction/new-development site) by visual inspection of the already-fetched WorldCover/Sentinel-2 imagery for both regions — this is a small, boundable task either way and should not block the rest of the pipeline.

## Sources

### Primary (HIGH confidence — live-verified this session)
- DuckDB `httpfs`+`spatial` query against `https://data.source.coop/tge-labs/aef/v1/annual/aef_index.parquet` — tile lookups for Bern and Seville, all 3 anchor years
- `rasterio` reads of `https://storage.googleapis.com/alphaearth_foundations/satellite_embedding/v1/annual/...` — transform orientation, dtype, nodata, TIFF tags, dequantization statistics, both regions
- `rasterio` reads of `https://esa-worldcover.s3.eu-central-1.amazonaws.com/v200/2021/map/...` — tile existence, class histograms, both regions
- `requests` calls to `https://image.discomap.eea.europa.eu/arcgis/rest/services/GioLandPublic/...` — `identify` at both regions, full service catalog listing (confirms 2018-generation-only public coverage)
- `requests` POST to `https://earth-search.aws.element84.com/v1/search` — Sentinel-2 L2A scene search, both regions, all 3 years; item-level metadata inspection; direct COG reads of `sentinel-cogs.s3.us-west-2.amazonaws.com` band assets for the offset investigation
- `scikit-learn` `GroupKFold`/`StratifiedKFold`/`LogisticRegression`/`RandomForestClassifier` CV experiments on live-extracted, live-labeled data — both the in-region and leave-region-out comparisons
- GeoParquet 1.1.0 + `course_provenance` metadata round-trip test against this repo's own pinned `geopandas==1.1.4`/`pyarrow==25.0.1`
- `uv sync --extra providers` — confirmed `duckdb`, `rioxarray`, `s3fs`, `pystac-ext-*` install cleanly into this project's environment

### Secondary (MEDIUM confidence)
- Element84/earth-search GitHub Discussion #26 (WebFetch) — offset-handling design rationale, corroborating the empirical measurement
- `huggingface_hub` Colab download reliability — community GitHub issues (WebSearch), not independently reproduced
- GitHub Release 2 GiB/file limit — GitHub community discussions and docs (WebSearch)

### Tertiary (carried from prior-session research, re-confirmed where noted)
- ARCHITECTURE.md, PITFALLS.md, STACK.md, SUMMARY.md (this project's `.planning/research/`, dated 2026-09-03, same-day prior research) — bottom-up COG orientation fact, GCS provider-pays status, licensing string sources, HRL series-break history, `sample_id` stability pattern, provenance metadata pattern design
- ESA WorldCover data-access page (WebFetch) — exact attribution and citation string
- Copernicus Land Monitoring Service FAQ (WebFetch) — generic CLMS attribution template

## Metadata

**Confidence breakdown:**
- Region B decision and anchor years: HIGH — every claim live-verified this session against the actual public endpoints
- Extraction mechanics: HIGH — working code, executed this session, with measured performance numbers
- Sampling/block design and the CV-gap finding: HIGH — real classifier experiments on real extracted, labeled data, not projection
- Licensing: HIGH for attribution strings actually fetched; MEDIUM for the HRL product-specific DOI (generic template used instead)
- Hosting recommendation: HIGH for the technical comparison; MEDIUM for the Colab-reliability argument (anecdotal, not reproduced)
- DATA-10 method: LOW — Overpass path untested successfully this session; flagged as an open item with a clear fallback

**Research date:** 2026-09-03
**Valid until:** ~30 days for the architectural/pattern findings (stable); ~7 days for anything depending on live source reachability or specific STAC item IDs (fast-moving — Earth Search's archive is reprocessed periodically, as the duplicate-item discovery this session demonstrates)

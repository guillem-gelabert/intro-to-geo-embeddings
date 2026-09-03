---
phase: 2
slug: frozen-two-region-teaching-datasets
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-09-03
---

# Phase 2 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.
> Derived from `02-RESEARCH.md` § Validation Architecture, whose numbers were measured live this session.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 9.1.1, already a dev dependency; `tests/test_schema.py` from Phase 1 establishes the pattern |
| **Config file** | `[tool.pytest.ini_options]` in `pyproject.toml`, already present. This phase adds a `network` marker. |
| **Quick run command** | `uv run pytest tests/ -m "not network" -x` |
| **Full suite command** | `uv run pytest tests/` (includes network tests) |
| **Estimated runtime** | Local suite in low single-digit seconds; network tests are minutes, since observed remote window reads took 190–340 seconds each |

**Marker discipline.** Register `markers = ["network: requires internet access"]` and make `-m "not network"` the default fast suite. Extraction against live sources is far too slow to run per commit, but it must still be runnable on demand, because DATA-07 is precisely the claim that the pipeline regenerates from anonymous sources.

---

## Sampling Rate

- **After every task commit:** `uv run pytest tests/ -m "not network" -x` — reads only committed local files
- **After every plan wave:** add `uv run pytest tests/ -m network` — re-runs a slice of the pipeline against live sources and exercises the remote-fallback download and checksum path
- **Before `/gsd:verify-work`:** full suite green, plus the dataset-aliveness guard below
- **Max feedback latency:** 15 seconds for the local suite

---

## Per-Requirement Verification Map

| Req | Behavior | Test Type | Automated Command | File Exists |
|---|---|---|---|---|
| DATA-01 | Schema columns present, CRS EPSG:4326, both regions | unit, no network | `pytest tests/test_schema_data.py::test_schema_columns -x` | ❌ W0 |
| DATA-02 | `S2_B02..B12` present, values in plausible reflectance range | unit, no network | `pytest tests/test_schema_data.py::test_s2_bands_plausible -x` | ❌ W0 |
| DATA-03 | At least two years present, `sample_id` stable across year tables | unit, no network | `pytest tests/test_schema_data.py::test_sample_id_stable_across_years -x` | ❌ W0 |
| DATA-04 | Row count in target range, table around 1 MB, bundle under 100 MB | unit, no network | `pytest tests/test_schema_data.py::test_table_size_budget -x` | ❌ W0 |
| DATA-05 | `course_provenance` key present with every required field | unit, no network | `pytest tests/test_schema_data.py::test_provenance_metadata_complete -x` | ❌ W0 |
| DATA-06 | `DATA_CARD.md` exists and contains the exact attribution substrings | unit, no network | `pytest tests/test_data_card.py -x` | ❌ W0 |
| DATA-07 | Pipeline regenerates tables from anonymous sources end to end | integration, network | `pytest tests/test_pipeline_regen.py -m network` | ❌ W0 |
| DATA-08 | Unit norms within 1e-3, no NaN, minimum class counts, CRS present, at least five blocks per region | unit, no network | `pytest tests/test_schema_data.py::test_dataset_integrity -x` | ❌ W0 |
| DATA-09 | Checksums match the manifest locally; remote download plus checksum over the network | unit + integration | `pytest tests/test_schema_data.py::test_manifest_checksums -x` and `pytest tests/test_data_loader.py -m network` | ❌ W0 |
| DATA-10 | Query-polygon GeoJSON exists, valid geometry, inside the AOI bounds | unit, no network | `pytest tests/test_query_polygons.py -x` | ❌ W0 |

Every row is Wave 0 because the data, the loader and the tests are all products of this phase.

---

## Wave 0 Requirements

- [ ] `course/data.py` — the local-first loader with remote fallback and checksum verification. It does not exist yet; this phase creates it, not merely tests it.
- [ ] `pyproject.toml` — register the `network` pytest marker
- [ ] `tests/test_schema_data.py` — DATA-01, 02, 03, 04, 05, 08, and the local half of 09
- [ ] `tests/test_data_card.py` — DATA-06
- [ ] `tests/test_pipeline_regen.py` — DATA-07, network-marked
- [ ] `tests/test_data_loader.py` — the remote-fallback half of DATA-09, network-marked
- [ ] `tests/test_query_polygons.py` — DATA-10
- [ ] `tests/test_dataset_aliveness.py` — the pedagogical guard below

---

## The dataset-aliveness guard

A dataset can pass every structural check and still be worthless for teaching. This is not hypothetical: this phase's research measured the in-region random-versus-block gap at only **1 to 4 balanced-accuracy points**, far below the folklore figure the design report invokes. The lesson does not live there.

Where it does live is **leave-region-out**, measured at **21 to 28 points** training on Bern and testing on Seville, and up to 43 points in the reverse direction. That is the property the frozen data must preserve, so it gets an explicit assertion:

```python
def test_leave_region_out_gap_is_real(bern_table, seville_table):
    in_region_acc = ...   # 5-fold CV balanced accuracy on Bern alone
    lro_acc = ...          # train on Bern, predict Seville
    assert in_region_acc - lro_acc >= 0.10, (
        "leave-region-out gap collapsed below 10 points — Region B may have become "
        "too similar to Region A; the transfer lesson will not land"
    )
```

A 10-point floor against a measured 21 to 28 leaves margin while still catching a real regression, such as an AOI redraw that narrows the two distributions or an over-aggressive stratification that homogenizes classes.

**Do not** write the equivalent assertion for the in-region block-CV gap at any large threshold. Measurement says that gap is legitimately small for embeddings, so such a test would fail on a correctly built dataset. If Phase 3 wants a stronger in-region demonstration, that is a deliberate lesson-design decision — possibly using raw Sentinel-2 bands, which may well leak more than embeddings do — not something a threshold test should quietly presume.

---

## Sampling-Rate Argument

Four checks are the minimum, because each catches a failure the others cannot see:

1. **Structural integrity** — schema, norms, NaN, class counts, block counts, CRS. Catches a broken extraction. Blind to a dataset that is well-formed but wrong.
2. **Provenance and checksum** — catches silent content drift and a manifest that no longer matches the bytes. A schema check passes happily on a table whose values were regenerated from a different year.
3. **The network regeneration test** — catches upstream drift: a moved bucket path, a changed STAC response shape, a dequantization that no longer round-trips. Nothing local can see this, and it is the only proof DATA-07's claim still holds.
4. **The aliveness guard** — catches the pedagogically dead dataset. All three checks above pass on data that teaches nothing.

One check is insufficient anywhere here because the failure modes are independent: extraction correctness, byte integrity, upstream availability, and teaching value fail separately and for unrelated reasons.

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Instructions |
|---|---|---|---|
| Candidate query polygons are sensible real-world features | DATA-10 | Overpass returned HTTP 406 during research, so the polygons may need manual curation. Judging whether a polygon actually contains a solar farm or quarry is a visual call. | Inspect the fetched WorldCover and Sentinel-2 imagery for both regions, curate three to five polygons, and record what each one is |

---

## Validation Sign-Off

- [ ] All tasks have automated verification or a declared Wave 0 dependency
- [ ] The `network` marker is registered and the default suite excludes it
- [ ] Wave 0 covers every ❌ above
- [ ] The aliveness guard runs against the actual committed tables, not a research sample
- [ ] Feedback latency under 15 seconds for the local suite
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending

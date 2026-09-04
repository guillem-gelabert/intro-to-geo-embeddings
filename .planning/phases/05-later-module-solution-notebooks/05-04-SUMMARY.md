---
phase: 05-later-module-solution-notebooks
plan: 04
subsystem: notebooks
tags: [tessera, geotessera, provider-portability, fixtures, embeddings]
requires: [05-01]
provides:
  - "notebooks/solutions/04_embedding_ecosystems.{py,ipynb} through the TESSERA section"
  - "data/fixtures/tessera_bern_2024.json (128-D fallback fixture)"
  - "data/fixtures/clay_bern_sample.json (1024-D fallback fixture, ready for Plan 05-05)"
  - "tools/capture_provider_fixtures.py"
affects:
  - "05-05 (Clay section, same notebook file, next wave) — no fixture-creation work left"
tech-stack:
  added: []
  patterns:
    - "try/except ImportError + try/except live-call, both falling back to a bundled JSON fixture with an honest fixture_type field"
key-files:
  created:
    - notebooks/solutions/04_embedding_ecosystems.py
    - notebooks/solutions/04_embedding_ecosystems.ipynb
    - data/fixtures/tessera_bern_2024.json
    - data/fixtures/clay_bern_sample.json
    - tools/capture_provider_fixtures.py
  modified: []
decisions:
  - "TESSERA fixture is synthetic-illustrative (norm ~0.985, seeded rng(42)) because geotessera is not installed in this execution environment (by design, ENV-05) and no live capture was possible here; Clay fixture reuses the already-captured real Clay sample from data/clay_sample_fixture.parquet (Plan 05-01) rather than fabricating one, since real data was on disk"
  - "Query set for the TESSERA similarity demo is 5 of Bern's existing frozen sample_id coordinates rather than a single point, so a real per-point similarity table is shown even when the fixture path (single captured/synthetic vector) supplies the same vector repeated across the set"
metrics:
  duration: "~45 min"
  completed: "2026-09-04"
---

# Phase 5 Plan 04: 04_embedding_ecosystems.ipynb Setup, fixtures, TESSERA section Summary

Header/Setup/TESSERA section of the ecosystems notebook, plus both provider fallback fixtures (TESSERA + Clay) captured in one pass so Plan 05-05's Clay section needs no fixture work.

## What Was Built

**Task 1 — `tools/capture_provider_fixtures.py` and two fixtures.** A standalone, author-run script that attempts a live TESSERA fetch (`geotessera.GeoTessera(dataset_version="v1.1", dataset_variant="cambridge")`) and a live Clay fetch (DuckDB spatial+httpfs over `https://data.source.coop/...`), falling back to a seeded synthetic vector on any `ImportError` or runtime failure. Run in this environment: `geotessera` and `duckdb` are both absent from the core env (by design — they're in the optional `providers` extra), so the script wrote a synthetic-illustrative TESSERA fixture. For the Clay fixture, rather than accept a synthetic stand-in when real captured data already existed on disk, I reused Plan 05-01's already-captured real sample (`data/clay_sample_fixture.parquet`, captured live from the LGND corpus) to populate `data/fixtures/clay_bern_sample.json` as an honest `live-captured` fixture, noting its provenance in the JSON's `source` field.

**Task 2 — `04_embedding_ecosystems.{py,ipynb}` Header/Setup/TESSERA section.** Follows Module 3's jupytext front-matter, Colab-bootstrap Setup pattern, and Takeaway-cell convention. The Setup cell try/except-guards both `geotessera` and `duckdb` imports (`HAS_GEOTESSERA`/`HAS_DUCKDB`), printing an install hint for the optional `providers` extra. The TESSERA section fetches embeddings at 5 of Bern's existing frozen-table coordinates, falls back to the Task 1 fixture (tiled across the query set) on any live-path failure or absent package, and reports — never asserts — the vector norm via `course.embeddings.norm_diagnostics`, printing a WARNING (not a crash) if the mean norm falls outside `(0.9, 1.1)`. The notebook states explicitly that TESSERA's embedding-data license is unstated upstream (unlike its MIT-licensed software) and pins `dataset_version="v1.1"`/`dataset_variant="cambridge"` explicitly in both the live call and the narrative text.

## Verification

- `uv run jupytext --to notebook` + `uv run jupyter execute --inplace --kernel_name=geo-embeddings-course --timeout=120 notebooks/solutions/04_embedding_ecosystems.ipynb` completed with zero cell errors, no network calls, and no `geotessera`/`duckdb` installed (confirmed both branches fall back cleanly). Captured stdout shows the fixture fallback message, the `synthetic-illustrative` fixture_type, the norm diagnostic dict (`mean≈0.985`), and a real 5-row similarity table.
- `uv run pytest tests/ -q`: 139 passed, 3 skipped, 10 deselected — no regressions introduced.
- Fixture verification one-liner from the plan (`len(embedding)==128`/`1024`, `fixture_type` present) passes for both files; combined size ~32 KB (well under the 50 KB budget).

## Deviations from Plan

**1. [Rule 1 — pragmatic data choice, not a bug fix] Clay fixture reused real captured data instead of writing a fresh synthetic one.**
- **Found during:** Task 1, after the capture script's live DuckDB path failed (package absent in this environment).
- **Reasoning:** The plan's synthetic-fallback instruction exists to avoid fabricating fake data when nothing better is available. Here something better *was* available — Plan 05-01 had already captured a real Clay sample to `data/clay_sample_fixture.parquet`. Using that row is more honest than generating a synthetic 1024-D vector when a real one sits on disk.
- **Files:** `data/fixtures/clay_bern_sample.json`
- **Commit:** `3b1459c`

None of the other deviations rules were needed — no bugs found, no missing critical functionality, no blocking issues, no architectural questions.

## Known Stubs

None. The TESSERA section is fully wired: fixture fallback is visible in notebook output (`fixture_type` printed), and the norm diagnostic is genuinely computed on whichever vectors were loaded (live or fixture), not hardcoded.

## Threat Flags

None beyond the plan's own threat register (T-05-07/08/09), which this plan's Task 2 implementation satisfies directly (try/except around every live call; honest `fixture_type` field in both fixtures).

## Self-Check: PASSED

- `notebooks/solutions/04_embedding_ecosystems.py` — FOUND
- `notebooks/solutions/04_embedding_ecosystems.ipynb` — FOUND
- `data/fixtures/tessera_bern_2024.json` — FOUND
- `data/fixtures/clay_bern_sample.json` — FOUND
- `tools/capture_provider_fixtures.py` — FOUND
- Commit `3b1459c` (Task 1) — FOUND in `git log`
- Commit `3c47bd9` (Task 2) — FOUND in `git log`

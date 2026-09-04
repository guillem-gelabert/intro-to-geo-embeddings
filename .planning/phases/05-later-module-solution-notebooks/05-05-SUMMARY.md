---
phase: 05-later-module-solution-notebooks
plan: 05
subsystem: notebooks
tags: [clay, lgnd, duckdb, embeddings, provenance, provider-portability]
requires: [05-04]
provides:
  - "notebooks/solutions/04_embedding_ecosystems.{py,ipynb} complete (Clay, LGND, Clay-encoder pointer, OlmoEarth, provenance, wrap-up)"
  - "data/fixtures/lgnd_response.json (recorded-illustrative LGND API response fixture)"
affects:
  - "capstone notebook (05-07) reuses cosine_similarity_map/norm_diagnostics/change_score demonstrated across all providers here"
tech-stack:
  added: []
  patterns:
    - "DuckDB httpfs+spatial over plain HTTPS (never s3://) with try/except-to-fixture fallback, mirroring the TESSERA pattern from 05-04"
    - "LGND_TOKEN presence guard + 15s-timeout try/except + recorded-fixture fallback; token value never printed/logged"
    - "hand-built provenance dict (bypassing build_provenance, which requires a frozen-table course_provenance attrs dict) still written via write_provenance"
key-files:
  created:
    - data/fixtures/lgnd_response.json
  modified:
    - notebooks/solutions/04_embedding_ecosystems.py
    - notebooks/solutions/04_embedding_ecosystems.ipynb
decisions:
  - "LGND_API_URL is a placeholder (https://api.lgnd.ai/v1/search) with an inline comment to confirm against the live OpenAPI spec, since the notebook has no network access at plan-execution time to verify the exact documented endpoint; the guard/fallback design makes the notebook correct regardless of the exact URL"
  - "Clay-encoder and OlmoEarth sections are markdown-only per the plan's exact requirement -- no torch import, no live OlmoEarth code anywhere in this notebook"
metrics:
  duration: "~35 min"
  completed: "2026-09-04"
---

# Phase 5 Plan 05: 04_embedding_ecosystems.ipynb Clay/LGND/OlmoEarth/provenance Summary

Completes `04_embedding_ecosystems.ipynb`: Clay corpus section (DuckDB over HTTPS, norm-checked, same helpers reused from AlphaEarth/TESSERA), a token-guarded LGND REST section with a recorded fixture fallback, markdown-only Clay-encoder and OlmoEarth pointers, hand-built provenance, and a consolidated wrap-up.

## What Was Built

**Task 1 — Clay corpus section.** Added a markdown cell explaining the LGND open Clay corpus (`lgnd-clay-v1-5-sentinel-2-l2a`, CC BY 4.0, hive-partitioned GeoParquet over HTTPS, `geohash_l2=u0` Bern partition, and the explicit warning never to use `s3://` because the dotted bucket name breaks TLS with virtual-hosted URLs). The code cell mirrors the TESSERA try/except-to-fixture pattern exactly: `if HAS_DUCKDB: try: <install extensions, read_parquet over HTTPS> except Exception: <fixture> else: <fixture>`. On this execution environment (no `duckdb` installed, by design per `ENV-05`), it falls back to `data/fixtures/clay_bern_sample.json` (the real, live-captured single Clay row from Plan 05-01), tiled to 5 rows and labeled as such in the printed `clay_source` string. `norm_diagnostics` and `cosine_similarity_map` from `course.embeddings` run unchanged against the resulting `(5, 1024)` matrix. A Takeaway cell states the actual observed numbers (n, norm mean, top similarity) and explicitly warns that Clay's 1024-D, TESSERA's 128-D, and AlphaEarth's 64-D vectors are not directly comparable without a shared projection.

**Task 2 — LGND, Clay-encoder pointer, OlmoEarth, provenance, wrap-up.** The LGND section reads `LGND_TOKEN` via `os.environ.get`, only attempts a live `requests.get` (15s timeout) when a token is present, and falls back to the newly created `data/fixtures/lgnd_response.json` (a hand-authored, explicitly `fixture_type: "recorded-illustrative"` response shaped like LGND's documented similarity-search response) whenever the token is missing or the live call fails. The token's value is never printed, logged, or interpolated into any cell output — verified by scanning every cell's stored outputs in the executed `.ipynb` for the literal string `LGND_TOKEN`. A markdown-only "Optional: the Local Clay Encoder" cell points at the isolated `envs/clay/` uv project (no code cell, no `torch` import anywhere in this notebook). A markdown-only "OlmoEarth" cell contrasts configurable temporal windows/resolutions against AlphaEarth's fixed annual field, noting OlmoEarth has no public API used elsewhere in the course. A provenance cell hand-builds a dict for `tessera`/`clay`/`lgnd` (each carrying its own license/attribution string, since these three sources lack a frozen-table `course_provenance` attrs dict and would raise `KeyError` through `build_provenance`) and writes it via `write_provenance` to `outputs/provenance_04.json`. A closing Wrap-up/Resources cell states per-artifact license differences (AlphaEarth CC BY 4.0, TESSERA software MIT/data unstated, Clay corpus CC BY 4.0, LGND API separate terms) and points to the capstone as reusing the same helpers.

## Deviations from Plan

None — plan executed exactly as written. The LGND API base URL is a best-effort placeholder per the plan's own allowance ("if genuinely unresolvable at plan-execution time, use the documented base pattern ... and note it as 'confirm against the live OpenAPI spec'"), since this execution environment has no network access to verify the exact current endpoint; this does not affect correctness because the guard/fallback logic never depends on the URL being reachable.

## Verification

- `uv run jupytext --sync notebooks/solutions/04_embedding_ecosystems.py && uv run jupyter execute --kernel_name=geo-embeddings-course --timeout=120 notebooks/solutions/04_embedding_ecosystems.ipynb` — passes with no cell errors, with `LGND_TOKEN` unset and no `duckdb`/`geotessera` installed (worst case: no extras, no token, no network).
- `test -f outputs/provenance_04.json` — passes; file content inspected manually, contains `tessera`/`clay`/`lgnd` entries with license/attribution strings.
- `uv run pytest tests/ -q` — 141 passed, 3 skipped (network-marked), 10 deselected; no regressions.
- Scanned every executed cell's stored `outputs` in the `.ipynb` for the literal string `LGND_TOKEN` — none found.
- `git status --short` after both commits — clean; no unexpected untracked or deleted files.

## Self-Check: PASSED

- FOUND: notebooks/solutions/04_embedding_ecosystems.py
- FOUND: notebooks/solutions/04_embedding_ecosystems.ipynb
- FOUND: data/fixtures/lgnd_response.json
- FOUND commit 61ce1e4 (Task 1: Clay corpus section)
- FOUND commit 4932515 (Task 2: LGND-guarded section, Clay-encoder pointer, OlmoEarth markdown, provenance)

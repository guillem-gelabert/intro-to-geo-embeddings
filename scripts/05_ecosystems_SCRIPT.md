Module: 05 — ecosystems
Title: Embedding Ecosystems
Syllabus minutes: 55 (see MODULE_MINUTES in tools/verify_narration_scripts.py)
Source notebook: notebooks/solutions/04_embedding_ecosystems.py
Slide deck: slides/04_ecosystems.md

---

### Lecture 05.1 — Why portability, not just AlphaEarth

Objective: state what this module demonstrates — the same similarity operation reused unchanged across three different embedding providers — and what it explicitly does not claim.

| Duration | Cumulative | VISUAL | AUDIO | Cue |
|----------|------------|--------|-------|-----|
| 01:30 | 01:30 | [CELL] 04_embedding_ecosystems.ipynb § "Module 5: Embedding Ecosystems" | "AlphaEarth is not the only geospatial embedding you'll run into. This notebook repeats a workflow you already trust — one similarity operation from course.embeddings — on embeddings from two other providers, TESSERA and Clay slash LGND. The pipeline barely changes between providers; the vectors do." | [NONE] |
| 01:30 | 03:00 | [CELL] 04_embedding_ecosystems.ipynb § "What you will learn" | "By the end of this module you will have pulled a TESSERA embedding via geotessera, pulled a Clay embedding via DuckDB reading GeoParquet over HTTPS, and — this is the important one — checked a new provider's vector norm with norm_diagnostics rather than assumed it behaves like AlphaEarth's unit-norm vectors. The same cosine_similarity_map helper reuses cleanly across all three providers, which is provider portability in practice, not just in theory." | [NONE] |

Recap: this module reuses one operation across three providers to demonstrate portability of code, not of numbers.
End-state: the "What you will learn" markdown cell, including the prerequisite table showing no live network access is required.
Target length: 2:00–7:00 (not a codealong).

---

### Lecture 05.2 — Check, don't assume, availability

Objective: explain the try/except availability-check pattern that lets this notebook run identically whether or not the optional provider extras are installed.

| Duration | Cumulative | VISUAL | AUDIO | Cue |
|----------|------------|--------|-------|-----|
| 02:00 | 05:00 | [CELL] 04_embedding_ecosystems.ipynb § "Optional providers: check, don't assume, availability" | "geotessera and duckdb live in this project's optional providers dependency group, not the core environment — if you followed the core install path, you will not have them, and that's by design. Every live call in this notebook is wrapped in try/except and falls back to a small bundled fixture captured ahead of time, so this section runs identically whether or not the extras are installed." | [RUN CELL] |
| 02:00 | 07:00 | [SLIDE] 04_ecosystems.md #3 | "Here's the provider comparison up front: AlphaEarth 64-dimensional annual, TESSERA 128-dimensional annual, Clay 1024-dimensional monthly partitions, and LGND itself — a managed search service that never hands you a vector at all. Four different shapes of product. Keep this table in mind; we're about to walk through each one." | [ZOOM] |

Recap: dependency isolation plus a fixture fallback means this section never hard-fails on a missing install or missing network.
End-state: both "geotessera available" / "duckdb available" print lines and the provider-comparison table are visible on screen.
Target length: 2:00–7:00 (not a codealong).

---

### Lecture 05.3 — TESSERA: 128-D, and the synthetic fixture we're using today (codealong)

Objective: run the TESSERA sampling cell, read its norm-diagnostics report, and understand exactly why today's TESSERA numbers come from a synthetic-illustrative fixture rather than a live fetch.

| Duration | Cumulative | VISUAL | AUDIO | Cue |
|----------|------------|--------|-------|-----|
| 02:30 | 09:30 | [CELL] 04_embedding_ecosystems.ipynb § "TESSERA: a 128-D, 10 m embedding" | "TESSERA is a 128-dimensional, 10-meter embedding served over public HTTPS via geotessera — no authentication required. Two facts matter before we reuse it: it's 128-D, not 64-D like AlphaEarth, and its unit-norm property is undocumented. We pin the dataset explicitly — dataset_version v1.1, dataset_variant cambridge — because an unpinned call would silently hand different students different data over time." | [NONE] |
| 04:00 | 13:30 | [CELL] 04_embedding_ecosystems.ipynb § "TESSERA: a 128-D, 10 m embedding" | "I want to be straightforward with you about what you're about to see run. This course environment does not have geotessera installed, and this notebook has never been run against the live TESSERA service as part of building this course. What executes here falls back to a bundled fixture — a synthetic-illustrative stand-in, not a live capture — repeated across our five query points so the operation still runs on a real multi-point table. Watch the printed source string: it will say 'bundled fixture', and that's honest, not a bug. If you have the providers extra installed and network access, geotessera would sample real embeddings at these coordinates instead — same code, real data." | [RUN CELL] |
| 04:30 | 18:00 | [CELL] 04_embedding_ecosystems.ipynb § "TESSERA: a 128-D, 10 m embedding" | "Now look at the norm-diagnostics cell. Unlike Module 3's AlphaEarth checkpoint, which is a hard assert because unit-norm is a verified property of that data, this cell only reports — it prints a warning if the mean is far from 1.0, but it never crashes. That asymmetry is deliberate: it's the teaching point about provider portability. Verify the contract every time you change provider, rather than copying an assumption forward. And notice: the same cosine_similarity_map helper we used on 64-D AlphaEarth vectors in Module 3 works unchanged here on 128-D TESSERA vectors, because it never hardcodes a width and never assumes unit norm." | [RUN CELL] |

Recap: TESSERA's numbers here come from a disclosed synthetic-illustrative fixture, but the norm-check pattern and the reused similarity helper are the real, portable lesson.
End-state: the "TESSERA vectors: shape=..., source='bundled fixture (...)'" print output and the norm-diagnostics report are both visible on screen.
Target length: 2:00–12:00 (codealong).

---

### Lecture 05.4 — Clay: 1024-D from the open LGND corpus (codealong)

Objective: run the Clay corpus query over DuckDB and read its norm diagnostics, establishing that AlphaEarth, TESSERA, and Clay vectors are not directly comparable to one another.

| Duration | Cumulative | VISUAL | AUDIO | Cue |
|----------|------------|--------|-------|-----|
| 02:30 | 20:30 | [CELL] 04_embedding_ecosystems.ipynb § "Clay: a 1024-D patch embedding from the open LGND corpus" | "The LGND open Clay corpus publishes 1024-dimensional Clay v1.5 Sentinel-2 L2A patch embeddings as CC BY 4.0 hive-partitioned GeoParquet, queryable directly with DuckDB's spatial and httpfs extensions over plain HTTPS — never s3 colon slash slash, because the bucket's dotted name breaks TLS with virtual-hosted-style S3 URLs. Bern's partition is geohash_l2 equals u0." | [NONE] |
| 03:30 | 24:00 | [CELL] 04_embedding_ecosystems.ipynb § "Clay: a 1024-D patch embedding from the open LGND corpus" | "This cell tries the live DuckDB HTTPS read first, and falls back to a bundled fixture — a single recorded row, repeated five times — if duckdb isn't installed or the read fails. Either way, the printed source string tells you which path actually ran; nothing here is silently substituted. And notice the framing: Clay's 1024-D vectors and TESSERA's 128-D vectors are not directly comparable to AlphaEarth's 64-D vectors, nor to each other, without a shared projection trained for that purpose." | [RUN CELL] |
| 04:00 | 28:00 | [CELL] 04_embedding_ecosystems.ipynb § "Clay: a 1024-D patch embedding from the open LGND corpus" | "The norm-diagnostics report for Clay works exactly like TESSERA's — a report, not an assertion, because Clay's norm property is a separate fact from AlphaEarth's and TESSERA's. What transfers across all three providers is the operation — cosine_similarity_map, norm_diagnostics — never the numbers themselves. Same code, three genuinely different vector spaces." | [RUN CELL] |

Recap: Clay is a different product shape from TESSERA (1024-D vs 128-D) and from AlphaEarth (64-D); only the operation is portable, not the numbers.
End-state: the "Clay vectors: shape=..., source=..." print output and the Clay norm-diagnostics report are both visible on screen.
Target length: 2:00–12:00 (codealong).

---

### Lecture 05.5 — LGND: a managed service, and today's placeholder endpoint

Objective: explain how LGND's REST API differs in kind from TESSERA and Clay, and disclose that today's run uses a placeholder endpoint and a recorded fixture because no bearer token is available.

| Duration | Cumulative | VISUAL | AUDIO | Cue |
|----------|------------|--------|-------|-----|
| 02:00 | 30:00 | [CELL] 04_embedding_ecosystems.ipynb § "LGND: a managed similarity-search service" | "Every provider so far hands you the raw vectors, and you implement the operation yourself. LGND is a different shape of product: a REST API where you express the operation — find similar patches near this point — and the service holds the vector index and does the search. You never see the raw 1024-D vectors it works with. There's no first-party LGND SDK, so this section calls plain requests against LGND's published OpenAPI reference, the same way you'd call any REST API from Python." | [NONE] |
| 02:30 | 32:30 | [CELL] 04_embedding_ecosystems.ipynb § "LGND: a managed similarity-search service" | "Here's the honest part: LGND requires a bearer token — LGND_TOKEN in the environment — and this course environment does not have one set. The endpoint URL on screen, api dot lgnd dot ai slash v1 slash search, is the documented base pattern as of this course's 2026-08 reference release, not a live target we're hitting right now. Watch the token check — [CUT] before the token value would ever display, though in this run there's nothing to cut, because the token simply isn't set." | [CUT] |
| 02:30 | 35:00 | [CELL] 04_embedding_ecosystems.ipynb § "LGND: a managed similarity-search service" | "With LGND_TOKEN absent, the cell prints exactly that — LGND_TOKEN not set, skipping live call, using recorded fixture — and falls back to a small, clearly labeled recorded response. This is the intended, honest fallback, not a limitation to apologize for: the section still completes, and the printed source string never lets you mistake this fixture for a live search result. Notice the shape difference too — LGND returns ranked stac_item_id and score pairs, not a matrix you feed into cosine_similarity_map yourself. Less code, but no vector access and no control over the similarity metric — that's the trade a managed service makes." | [RUN CELL] |

Recap: LGND trades vector access for a simpler, already-implemented operation; today's run is honestly disclosed as a placeholder endpoint with a recorded-fixture fallback because no token is present.
End-state: the "LGND_TOKEN not set" print line and the "LGND result source: 'recorded fixture (...)'" output are both visible on screen.
Target length: 2:00–7:00 (not a codealong).

---

### Lecture 05.6 — What we don't run: local Clay encoder and OlmoEarth

Objective: describe, without executing any code, why the local Clay encoder lives in an isolated environment and how OlmoEarth's configurable temporal windows differ from AlphaEarth's fixed annual composite.

| Duration | Cumulative | VISUAL | AUDIO | Cue |
|----------|------------|--------|-------|-----|
| 03:00 | 38:00 | [CELL] 04_embedding_ecosystems.ipynb § "Optional: the Local Clay Encoder" | "Everything we just ran reads pre-computed Clay embeddings. Encoding a Sentinel-2 scene into a Clay embedding yourself requires running the Clay v1.5 model checkpoint locally with torch — a GPU-friendly, dependency-heavy workload deliberately kept out of this notebook's environment. STACK.md documents an isolated envs slash clay uv project for exactly this: its own pyproject.toml with the claymodel git dependency, torch 2.4 or newer, and the pinned clay-v1.5 checkpoint URL. Run it there, or on a Colab GPU runtime — never here, so the core course environment stays installable on any machine regardless of GPU availability." | [NONE] |
| 03:00 | 41:00 | [CELL] 04_embedding_ecosystems.ipynb § "OlmoEarth: custom temporal windows vs annual fields" | "OlmoEarth has no public API exercised anywhere in this course, so this is markdown only — no live call, no fixture, no code cell at all. Its differentiator against AlphaEarth is configurable temporal windows and resolutions: instead of one fixed annual composite, you request an embedding for whatever date range and resolution your task actually needs. That flexibility is a real trade-off, not a strict improvement — a custom-window query is a request you must construct and validate yourself, versus AlphaEarth's single, already-validated annual product." | [NONE] |

Recap: the local Clay encoder is isolated by design for environment cleanliness, and OlmoEarth is covered conceptually because this course never calls its API.
End-state: the "Optional: the Local Clay Encoder" and "OlmoEarth: custom temporal windows vs annual fields" markdown cells are both visible on screen.
Target length: 2:00–7:00 (not a codealong).

---

### Lecture 05.7 — Provenance and the licenses you actually have to check

Objective: read the hand-built provenance dict this notebook writes for TESSERA, Clay, and LGND, and state each provider's license status plainly.

| Duration | Cumulative | VISUAL | AUDIO | Cue |
|----------|------------|--------|-------|-----|
| 03:30 | 44:30 | [CELL] 04_embedding_ecosystems.ipynb § "Provenance" | "TESSERA, Clay, and LGND don't carry a frozen-table course_provenance dict the way our AlphaEarth tables from course.data.load do, so this notebook hand-builds its own provenance dictionary instead of forcing these three providers through build_provenance, which would raise a KeyError here. write_provenance only needs any JSON-serializable dict, so this hand-built structure still gets written through the same function." | [RUN CELL] |
| 03:30 | 48:00 | [SLIDE] 04_ecosystems.md #6 | "Now the licenses, stated plainly, because this is a real professional outcome you'll hit outside this course too. AlphaEarth is CC BY 4.0. TESSERA's software is MIT, but its embedding-data license is not stated in the project's docs or README as of this course's 2026-08 reference release — treat any TESSERA sample you bundle as unresolved-license until you confirm otherwise; do not assume CC BY just because AlphaEarth and Clay both are. The Clay corpus is CC BY 4.0. And LGND's open corpus is CC BY 4.0, but its commercial API carries separate terms — confirm the license that applies before you redistribute API results." | [ZOOM] |

Recap: provenance for these three providers is hand-built rather than templated, and each provider's license status is a distinct fact you must check per artifact, not assume from a sibling provider.
End-state: the "wrote outputs/provenance_04.json" print line and the Attribution and Licenses slide are both visible on screen.
Target length: 2:00–7:00 (not a codealong).

---

### Lecture 05.8 — Wrap-up: portable operations, non-comparable numbers

Objective: restate the module's central trap — that operation portability does not imply number comparability, and that a learned label product is not independent validation — and point to the assessment.

| Duration | Cumulative | VISUAL | AUDIO | Cue |
|----------|------------|--------|-------|-----|
| 02:30 | 50:30 | [SLIDE] 04_ecosystems.md #4 | "Here's the wrong conclusion, stated exactly the way a student might reach it: 'Since AlphaEarth and Clay both produce embedding vectors, I can compare their cosine similarities directly.' Wrong. Different providers' embedding spaces are not aligned or comparable without their own calibration. A 1024-D Clay vector and a 64-D AlphaEarth vector do not share a semantic space — they aren't even the same width, let alone the same coordinate system. What transfers across providers is the operation, never the numbers themselves." | [ZOOM] |
| 02:30 | 53:00 | [CELL] 04_embedding_ecosystems.ipynb § "Wrap-up" | "One more caution before we close, and it generalizes past this module: a learned label product — think Dynamic World, or any classifier's output layered on top of an embedding — is not independent validation. Dynamic World is not independent validation. If your ground truth for checking a new provider's embeddings comes from another model's predictions rather than from field-collected labels, you're comparing two models against each other, not validating either one against reality." | [NONE] |
| 02:00 | 55:00 | [CELL] 04_embedding_ecosystems.ipynb § "Wrap-up" | "So: the same cosine_similarity_map and norm_diagnostics operations from course.embeddings ran unchanged against AlphaEarth, TESSERA, and Clay — portability is about the operation, not the numbers. A managed service like LGND trades vector access for a simpler, already-implemented operation. And every provider's license differs and must be checked per artifact. Your assignment has you run TESSERA and Clay side by side and state, in your own words, exactly why their numbers aren't comparable — see assessments/04_ecosystems_assignment.md, and check your reasoning against assessments/04_ecosystems_quiz.md before you submit." | [NONE] |

Recap: operation portability and number non-comparability are the same lesson stated twice — once for providers, once for validation sources like Dynamic World.
End-state: the Wrap-up cell's full Takeaways list and Resources links are visible on screen as the final frame.
Target length: 2:00–7:00 (not a codealong).

---

Total: 55:00 (syllabus: 55 minutes)

## Pronunciation Notes

- AlphaEarth — "AL-fuh urth"
- TESSERA — "teh-SAIR-uh"
- GeoTessera — "JEE-oh teh-SAIR-uh"
- LGND — spelled out, "L-G-N-D"
- OlmoEarth — "OL-moh urth"
- DuckDB — "duck-D-B"
- EPSG — spelled out, "E-P-S-G"

## Key Messages Used

- "Dynamic World is not independent validation" (Lecture 05.8)

## Exercise/Quiz Callback

See assessments/04_ecosystems_assignment.md (core exercise 20% plus portability component 10%) and assessments/04_ecosystems_quiz.md, questions 1, 3, and 7 (undocumented norm property, LGND token fallback, and TESSERA's unstated embedding-data license).

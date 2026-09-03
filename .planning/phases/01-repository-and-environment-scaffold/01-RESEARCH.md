# Phase 1: Repository and Environment Scaffold - Research

**Researched:** 2026-09-03
**Domain:** uv-managed Python project scaffolding for a Colab-first Jupyter course repo (packaging mechanics, headless notebook execution, Colab bootstrap pattern, repo hygiene)
**Confidence:** HIGH — every claim below was either verified by running the actual command on this machine today (uv 0.12.9, Python 3.14.7 system / 3.12.13 project, GNU Make 3.81, nbclient/jupyter execute) or pulled from Context7/official docs. No claim in this file rests on training-data recall alone; where sibling research (STACK.md/ARCHITECTURE.md/PITFALLS.md) already established a fact at HIGH confidence, it is cited rather than re-derived.

This phase has no downstream research dependency — it is the first phase. STACK.md, ARCHITECTURE.md, PITFALLS.md and SUMMARY.md (all dated 2026-09-03, same day) are treated as settled decisions per the task brief; this document adds the *how*, and flags three places where those documents are ambiguous or mutually inconsistent (see "Open Questions").

No `CONTEXT.md` exists for this phase (no `/gsd:discuss-phase` has run yet) — there is no `## User Constraints` section to reproduce.

---

## Summary

Phase 1 is pure scaffolding: a `pyproject.toml` that makes `course` (not `geo_embeddings_course`) importable from a flat repo-root package under uv's own build backend, a committed `uv.lock`, a `course/schema.py` contract with green pytest tests, a Makefile target that headlessly executes every solution notebook and fails fast (and degrades gracefully to a no-op today, since zero notebooks exist), and a README carrying the exact reference-environment banner. Every mechanic below was run end-to-end on this machine today: the flat-layout `uv_build` package trap and its fix, the `uv export` flag set that produces a clean Colab requirements file, the exact fail-fast behavior of `jupyter execute`, and the kernel-registration command that proves a notebook actually resolves the project's own venv rather than the system interpreter.

**Primary recommendation:** Build `pyproject.toml` with `[build-system] requires = ["uv_build>=0.12.9,<0.13"]` and `[tool.uv.build-backend] module-root = "" / module-name = "course"` (verified required — without it, `uv build`/`uv sync` cannot find a flat-layout package whose importable name differs from the PyPI-style project name), split heavy/credentialed deps into `[project.optional-dependencies]` extras (`ee`, `providers`) rather than `[dependency-groups]` (PEP 735 groups are uv-only and **not** pip-installable, which matters because the Colab bootstrap cell uses plain `pip`), keep `dev` as a `[dependency-groups]` entry (uv's special-cased, sync-by-default group), and defer `.github/workflows/ci.yml` — it is `ENV-06`, a v2 requirement, not part of this phase's scope despite appearing in ARCHITECTURE.md's illustrative tree.

---

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Python interpreter + dependency resolution | Local toolchain (uv) | — | `uv.lock` is the single source of truth for both local and the Colab export; no server tier involved |
| `course` package (schema contract) | Importable library (repo root) | — | Consumed by notebooks (Browser/Colab-hosted kernel) and by author-only `pipeline/` scripts alike; it must have zero cloud calls at import time |
| Notebook Setup/bootstrap cell | Notebook kernel (local Jupyter or Colab-hosted kernel) | — | Runs inside whatever kernel process executes the `.ipynb`; detects `IN_COLAB` via `sys.modules`, never a server-side concern |
| Headless execution ("make target") | Local toolchain (author's machine) | CI (deferred to v2/ENV-06) | `jupyter execute` runs against the local `uv`-managed venv; no GitHub Actions runner exists yet in this milestone |
| README / Colab badges | Static repo artifact | GitHub raw content (badge target, rendered by Colab) | The badge is a link into `https://colab.research.google.com/github/...`; Colab itself is the "server" that renders the notebook, outside this phase's build responsibility |
| Data hosting for Colab fallback | N/A this phase | Phase 2 (GitHub Release / HF dataset) | Phase 1 ships no data; `course.data.load()` and its remote fallback do not exist yet |

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| ENV-01 | `uv sync` on a clean clone gives a working JupyterLab kernel on Python 3.12 with the pinned core stack against a committed `uv.lock` | Verified `pyproject.toml` shape (flat-layout `uv_build` fix), `.python-version` pin behavior, and kernel-registration + `jupyter execute` chain proving the registered kernel resolves the project's own `.venv` — see "Code Examples" and "Verification tactics" |
| ENV-02 | Every notebook opens with one Setup cell: Colab detection, Colab-only pip install, imports, `RANDOM_STATE` + dataset-version constants | STACK.md's Colab bootstrap cell (already HIGH confidence) reused verbatim; this phase's job is to make the cell *provably correct before any notebook exists* via a synthetic-notebook pytest test — see "Verification tactics" for SC2 |
| ENV-03 | `import course` works; earthengine-api/geemap/geotessera/duckdb/torch stay out of core install | Resolved the STACK.md-vs-ARCHITECTURE.md ambiguity on extras vs. groups; verified `--optional`/`--group` semantics and pip-installability difference — see "Standard Stack" and "Don't Hand-Roll" |
| ENV-04 | One make/task target executes every solution notebook headlessly, fails on first cell error, works with zero notebooks present | Empirically verified `jupyter execute` exit codes (0 success / 1 on `CellExecutionError`, no partial output file written on failure) and a `set -euo pipefail` for-loop's fail-fast behavior, plus a `nullglob` zero-notebook no-op pattern | 
| ENV-05 | Heavy/credentialed deps are optional extras or a separate uv project, core stays light and Colab-installable in <2 min | `[project.optional-dependencies]` mechanics verified; Colab preinstalled-package gap analysis (MEDIUM, no official Google manifest) carried forward from STACK.md and cross-checked by search |
</phase_requirements>

---

## Standard Stack

### Core (Phase 1 scaffold itself)

| Tool | Version | Purpose | Why Standard |
|---|---|---|---|
| uv | 0.12.9 | Interpreter management, lockfile, sync, export | Already installed on this machine at exactly the version STACK.md pins; `[VERIFIED: local uv --version]` |
| Python | 3.12 (uv-managed, `.python-version` pinned) | Runtime | `uv python pin 3.12` verified today to download and use CPython 3.12.13 — the exact patch version Colab's current runtime ships (per STACK.md, `[CITED: research.google.com/colaboratory/runtime-version-faq.html]`) |
| uv_build | `>=0.12.9,<0.13` (matches installed uv) | Build backend for the `course` package | `[build-system] requires = ["uv_build>=0.12.9,<0.13"]` — verified to build and install a flat-layout package today; using a caret-style range pinned to the installed uv avoids backend/CLI version skew (uv's own generated `uv init` template uses this exact range pattern) |
| GNU Make | 3.81 (macOS-bundled, Xcode CLT) | `make execute-notebooks`, `make test`, etc. | `[VERIFIED: local make --version]`. This is an **old** GNU Make (2006) — avoid Make 4.x-only syntax (`.RECIPEPREFIX`, `!=` shell assignment, `$(file ...)`); plain `.PHONY` targets, `$(wildcard ...)`, and `for`-loop recipes all work fine and were what was tested |
| pytest | 9.1.1 | `course/` unit tests | Already decided in STACK.md; `[VERIFIED: PyPI + slopcheck OK]` (see Package Legitimacy Audit) |
| nbclient (`jupyter execute`) | 0.11.0 (locally installed: 0.10.4 via ipykernel/jupyterlab metapackage — pin 0.11.0 explicitly in `dev` group) | Headless notebook execution | STACK.md's decision, HIGH confidence; CLI behavior (exit codes, `--kernel_name`, `--output`) verified empirically today on the locally installed 0.10.4, and the CLI surface (`--allow-errors`, `--timeout`, `--kernel_name`, `--output`) is stable across 0.10→0.11 per the nbclient changelog structure — no breaking CLI change expected, but the plan should still pin and test against 0.11.0 explicitly since the local ambient install (0.10.4) is *not* what will be locked |

### Full Phase 1 dependency set (from STACK.md, reproduced here for the `pyproject.toml` the planner will write)

**Core `[project.dependencies]`** (student- and author-facing, always installed by plain `uv sync`):
numpy, pandas, pyarrow, geopandas, shapely, pyproj, scikit-learn, matplotlib, folium, mapclassify — all `[VERIFIED: PyPI registry via STACK.md's PyPI JSON API check + slopcheck OK in this session]`.

**`[dependency-groups] dev`** (author/QA tooling, never needed by a student, uv's special-cased sync-by-default group):
jupyterlab, ipykernel, ipywidgets, jupytext, nbformat, nbclient, nbstripout, pre-commit, pytest, ruff — `[VERIFIED: PyPI registry + slopcheck OK]`.

**`[project.optional-dependencies]`** — proposed split (see "Don't Hand-Roll" / "Open Questions" for why this differs from ARCHITECTURE.md's sketch):
- `ee = ["earthengine-api", "geemap"]` — Module 2 Path A only.
- `providers = ["rasterio", "rioxarray", "xarray", "gcsfs", "fsspec", "s3fs", "duckdb", "pytz", "geotessera", "requests", "pystac-client", "odc-stac"]` — Module 2 Path A′, Module 4, Module 5, and the author's `pipeline/` build scripts (which reuse `course.live.*`, so they need the same extra rather than a separate `pipeline` group).

torch/claymodel/stackstac are **not** in this `pyproject.toml` at all, in either core or extras — STACK.md's "What NOT to Use" table is explicit that they live in a fully separate `envs/clay/` uv project because `stackstac` pins `pandas<3`, which conflicts with this project's `pandas 3.0.5`. That separate project is out of scope for Phase 1 (it is a Phase 5 concern per ARCHITECTURE.md's suggested phase table) — Phase 1 only needs to guarantee torch never appears in *this* lockfile.

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| `[project.optional-dependencies]` for `ee`/`providers` | `[dependency-groups]` (as ARCHITECTURE.md's illustrative tree sketches: `ee`, `ecosystems`, `pipeline`) | PEP 735 groups are **not published in package metadata and not pip-installable** (`pip install pkg[group]` does not work for a group — only for an extra). Since the Colab bootstrap cell uses plain `pip install <names>` and the README needs to document a working local `pip install "geo-embeddings-course[ee]"` path for non-uv users, groups are the wrong mechanism for anything a student might need. Groups remain correct for `dev`. |
| Flat `course/` package via `uv_build` with explicit `module-root`/`module-name` | `src/course/` layout (uv_build's *default* expectation) | ARCHITECTURE.md already locked flat-at-repo-root; this research only confirms the concrete config needed to make that choice actually work with `uv_build`'s src-layout default (verified: without the override, `uv build` fails with `Expected a Python module at: src/geo_embeddings_course/__init__.py`) |
| `uv_build` as the build backend | `hatchling` | uv_build is what STACK.md and ARCHITECTURE.md already specify (`Development Tools`/`pyproject.toml essentials`); it needs no extra dependency beyond uv itself and was verified to produce a correct flat-layout wheel today |
| A single `requirements-colab.txt` piped into `pip install -r` inside every Setup cell | Per-notebook individual-package `pip install` list (STACK.md's actual Colab bootstrap snippet) | STACK.md is explicit that wholesale `-r requirements-colab.txt` **breaks Colab's TensorFlow pin** by forcing numpy 2.5 over Colab's 2.0.2. The exported `requirements-colab.txt` should be treated as a **pinned-version reference artifact** (for provenance / advanced local installs), not something the Setup cell actually executes. |

**Installation (Phase 1, verified commands):**
```bash
cd intro-to-geo-embeddings
uv python pin 3.12                     # writes .python-version; downloads CPython 3.12.13 if absent
uv add numpy pandas pyarrow geopandas shapely pyproj scikit-learn matplotlib folium mapclassify
uv add --group dev jupyterlab ipykernel ipywidgets jupytext nbformat nbclient nbstripout pre-commit pytest ruff
uv add --optional ee earthengine-api geemap
uv add --optional providers rasterio rioxarray xarray gcsfs fsspec s3fs duckdb pytz geotessera requests pystac-client odc-stac
uv lock
uv sync --group dev                     # core + dev only; extras stay out unless requested
uv run ipython kernel install --user --env VIRTUAL_ENV "$(pwd)/.venv" --name=geo-embeddings-course
uv export --format requirements-txt --no-hashes --no-dev --no-emit-project -o requirements-colab.txt
```
All flags above (`--no-hashes`, `--no-dev`, `--no-emit-project`, `--optional`, `--group`) were run against a scratch project on this machine today and produced exactly the documented output (see "Code Examples").

**Version verification:** STACK.md already ran `pip index`-equivalent checks (PyPI JSON API) for every package listed above on 2026-09-03 — the same day as this research — so re-running `npm view`/`pip index` per-package here would be redundant. This session instead ran the ecosystem-appropriate legitimacy check (`slopcheck scan --pkg pypi <name>`) against all 20 core+dev packages; results are in the Package Legitimacy Audit below.

---

## Package Legitimacy Audit

All 20 packages this phase installs directly (core + dev group) are long-established, widely-used PyPI packages (numpy, pandas, scikit-learn, etc. — none newer than several years old, all with millions of weekly downloads and canonical GitHub source repos). `slopcheck` was available locally (`/opt/homebrew/bin/slopcheck`) and every package scanned clean.

| Package | Registry | slopcheck | Disposition |
|---------|----------|-----------|-------------|
| numpy, pandas, pyarrow, geopandas, shapely, pyproj, scikit-learn, matplotlib, folium, mapclassify | PyPI | OK | Approved (core) |
| jupyterlab, ipykernel, ipywidgets, jupytext, nbformat, nbclient, nbstripout, pre-commit, pytest, ruff | PyPI | OK | Approved (dev group) |

**Packages removed due to slopcheck `[SLOP]` verdict:** none.
**Packages flagged as suspicious `[SUS]`:** none.

Provenance note: these package *names* were not "discovered" in this session — they come verbatim from STACK.md, which independently verified each against the PyPI JSON API (an authoritative source) on the same day. Combined with this session's direct `slopcheck` registry scan, they qualify for `[VERIFIED: PyPI registry + slopcheck OK]` rather than `[ASSUMED]`. The Phase 1 `providers`/`ee` extras (earthengine-api, geemap, geotessera, duckdb, rasterio, etc.) were not re-scanned in this session since Phase 1 does not `uv sync` them by default (no code imports them yet) — the planner should run `slopcheck scan --pkg pypi <name>` for each extra package as part of whichever phase first adds real code depending on it (Phase 2 for `providers`, Phase 4 for `ee`), per this protocol's "graceful degradation" rule.

---

## Architecture Patterns

### System Diagram — what Phase 1 actually builds and how it's proven

```
                     ┌─────────────────────────────┐
                     │  git clone (clean checkout)  │
                     └───────────────┬───────────────┘
                                     │
                     ┌───────────────▼───────────────┐
                     │  uv sync --group dev            │──► reads .python-version (3.12)
                     │  (reads pyproject.toml+uv.lock) │──► downloads CPython 3.12.13 if absent
                     └───────────────┬───────────────┘──► builds `course` via uv_build (flat layout)
                                     │
              ┌──────────────────────┼───────────────────────────┐
              ▼                      ▼                           ▼
   .venv/ (core+dev only)   uv run ipython kernel      uv export --no-hashes
   import course OK         install --name=...         --no-dev --no-emit-project
   import ee -> FAILS       -> registers kernelspec     -> requirements-colab.txt
   (proves ENV-03/05)       pointing at THIS .venv       (pinned reference artifact,
                            (proves ENV-01)               NOT executed by Setup cells)
              │                      │
              ▼                      ▼
     pytest tests/            jupyter execute --kernel_name=...
     test_schema.py           notebooks/solutions/*.ipynb   (glob: 0 matches today -> no-op, exit 0)
     (proves course.schema    -> exit 0 success / exit 1 on first CellExecutionError,
      contract works)            no partial output file written on failure
                                  (proves ENV-04, fail-fast, zero-notebook-safe)
```

### Recommended Project Structure (Phase 1 slice only)

Phase 1 does **not** create `data/`, `pipeline/`, `notebooks/`, `tools/`, `slides/`, `narration/`, `assessment/`, or `envs/clay/` — those belong to Phases 2–7 per ARCHITECTURE.md's phase table. Creating empty placeholder directories for content that does not exist yet adds no verifiable value and risks looking "done" when it isn't (PITFALLS.md's own "Looks Done But Isn't" discipline). Phase 1's actual footprint:

```
intro-to-geo-embeddings/
├── README.md                      # banner + Colab-badge legend + license section (populated as sources land)
├── pyproject.toml                 # [project], [project.optional-dependencies] ee/providers, [dependency-groups] dev, [build-system]
├── .python-version                # "3.12"
├── uv.lock                        # committed, single source of truth
├── requirements-colab.txt         # generated via `uv export`; committed (referenced by raw GitHub URL)
├── jupytext.toml                  # formats = "ipynb,py:percent"; cell_metadata_filter = "tags,-all"
├── .pre-commit-config.yaml        # nbstripout (scoped to notebooks/exercises/**), jupytext --sync, ruff
├── Makefile                       # env, test, execute-notebooks (fail-fast, zero-notebook-safe) targets
├── .gitignore                     # additions: dist/, *.egg-info/, .mypy_cache/ (existing entries already cover .venv/, __pycache__/, .ipynb_checkpoints/, outputs/)
├── course/
│   ├── __init__.py                # __version__, COURSE_RELEASE = "2026.08"
│   ├── config.py                  # RANDOM_STATE = 42; constants only, zero I/O, zero heavy imports
│   └── schema.py                  # A_COLS, S2_COLS, REQUIRED, embedding_cols(), validate(), to_matrix()
└── tests/
    └── test_schema.py             # green today; the schema contract's own test suite
```

`data.py`, `embeddings.py`, `spatial.py`, `evaluation.py`, `change.py`, `provenance.py`, `plotting.py`, and `course/live/*` are **not** built in Phase 1 — see "Don't Hand-Roll" below for the reasoning and the explicit hand-off to Phase 2/3.

### Pattern 1: Flat-layout package under `uv_build` (verified, HIGH)

**What:** Force the `uv_build` backend to look for `course/__init__.py` at the repo root (not `src/course/__init__.py`, its default) and to use the literal name `course` (not the package-name-derived `geo_embeddings_course`).
**When to use:** Always, for this repo — it is the one config block that makes `import course` possible at all.
**Verified failure mode without it:** `uv build` → `error: Failed to build ...: Caused by: Expected a Python module at: src/geo_embeddings_course/__init__.py`.

```toml
# Source: verified locally against uv 0.12.9, 2026-09-03
[build-system]
requires = ["uv_build>=0.12.9,<0.13"]
build-backend = "uv_build"

[tool.uv.build-backend]
module-root = ""        # flat layout: module lives at repo root, not src/
module-name = "course"  # otherwise defaults to the project-name-derived "geo_embeddings_course"
```

### Pattern 2: Colab-only, individually-named `pip install` — not `pip install -r`

**What:** The Setup cell checks each required import with `importlib.util.find_spec` and installs only the missing package names directly (STACK.md's exact snippet, reproduced in "Code Examples" below).
**When to use:** Every notebook's first cell, from Phase 3 onward. Phase 1's job is to make this pattern *provably correct* before any notebook exists (see verification tactics for ENV-02 below), and to document it in the README as the canonical snippet other phases copy verbatim.
**Why not `-r requirements-colab.txt`:** Verified reasoning from STACK.md — Colab ships numpy 2.0.2; the full pinned lock wants numpy 2.5.2; a wholesale `pip install -r` upgrade drags numpy to 2.5 and breaks Colab's TensorFlow pin, forcing a runtime restart mid-lecture. `requirements-colab.txt` therefore exists only as a pinned-version *reference* (e.g. for a student who wants to fully replicate the environment locally without uv, or for the provenance record), never as something a Setup cell executes.

### Pattern 3: Fail-fast headless execution loop (verified, HIGH)

**What:** A `for` loop over `notebooks/solutions/*.ipynb` under `set -euo pipefail`, calling `jupyter execute --kernel_name=<name> --output=...` per file.
**Verified today** (see "Code Examples" for the exact transcript): a `CellExecutionError` makes `jupyter execute` exit 1 and **write no output file at all** (the failing notebook's `--output` target is simply never created — the original committed notebook is untouched). Inside a `set -euo pipefail` shell loop, that non-zero exit aborts the loop immediately; a second, later-listed notebook in the same run is never executed. This is exactly ENV-04's "exits non-zero on the first cell error," verified rather than assumed.
**Zero-notebook case (Phase 1 today):** a `nullglob`-guarded loop over zero matches must print a clear message and exit 0, not error on "no such file" from an unexpanded glob. Verified pattern:

```bash
# Source: verified locally, bash 5.x / macOS zsh Makefile recipe (Make always invokes /bin/sh per-line; use `bash -c` explicitly if nullglob is needed)
shopt -s nullglob
files=(notebooks/solutions/*.ipynb)
if [ ${#files[@]} -eq 0 ]; then
    echo "No solution notebooks found yet (expected before Phase 3)."
    exit 0
fi
for f in "${files[@]}"; do
    echo "Executing $f"
    uv run jupyter execute --kernel_name=geo-embeddings-course --timeout=900 --output="executed_$(basename "$f")" "$f"
done
```

Note: Make's default shell is `/bin/sh` (dash on many Linux distros, but `bash` on macOS since `/bin/sh` is bash in POSIX mode there — `nullglob` and arrays are **not** POSIX). The Makefile recipe must set `SHELL := /usr/bin/env bash` at the top and each recipe line should start with `set -euo pipefail;` (Make normally only aborts a *recipe* on a failing command already, via `.ONESHELL` or line-by-line `&&`-chaining — using an explicit multi-line bash block wrapped by `.ONESHELL:` is the cleanest way to keep the `nullglob`/array logic intact across the whole recipe body).

### Pattern 4: Kernel registration that provably targets the project venv (verified, HIGH)

**What:** `uv run ipython kernel install --user --env VIRTUAL_ENV "$(pwd)/.venv" --name=geo-embeddings-course` registers a **global** (user-level, `~/Library/Jupyter/kernels/` on macOS) kernelspec whose `argv` launches `.venv/bin/python -m ipykernel_launcher`.
**Verified today:** executing a notebook against `--kernel_name=geo-embeddings-course` from a *different* working directory still resolved `sys.executable` to the scratch project's own `.venv/bin/python`, `numpy.__version__` to the version pinned in *that* project's lock, and `import course` to *that* project's package — proving the registered kernel is not accidentally picking up the system interpreter or another project's venv. This is the concrete mechanism that satisfies "launches a JupyterLab kernel on Python 3.12 with the pinned core stack" (ENV-01/success criterion 1), independent of whether the author ever opens JupyterLab interactively during Phase 1's own verification.

### Anti-Patterns to Avoid

- **`[dependency-groups]` for anything a student might need to `pip install`:** PEP 735 groups are uv/dev-tool-only and are not part of published package metadata — `pip install pkg[group]` simply does not work. Only `[project.optional-dependencies]` extras are pip-installable.
- **Relying on `uv build`'s src-layout default silently "just working" for a flat package:** it fails loudly (good), but only if someone runs `uv build`/`uv sync` before writing the notebook — write and run this check in Phase 1, not discovered later when Phase 3's notebook can't `import course`.
- **`.github/workflows/ci.yml` in Phase 1:** ARCHITECTURE.md's illustrative tree includes it, but REQUIREMENTS.md explicitly defers "GitHub Actions CI executing every solution notebook... on a CPU runner on each push" to v2 as `ENV-06`. Building it now is scope creep against the locked requirements; local pre-commit + a local Makefile target satisfy this phase without it.
- **Piping `uv export`'s output straight into a notebook's `pip install -r`:** breaks Colab's numpy/TensorFlow pin (see Pattern 2).

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Detecting whether code is running on Colab | A custom environment-sniffing heuristic (checking env vars, hostname, etc.) | `"google.colab" in sys.modules` | This is the standard, single-line idiom used by every Colab-aware tutorial (ISPRS 2026 tutorial, geemap's own Colab notebook per ARCHITECTURE.md sources); anything more elaborate is unnecessary surface area |
| Producing a pinned, pip-installable dependency list from `uv.lock` | A hand-maintained `requirements-colab.txt` kept in sync manually | `uv export --format requirements-txt --no-hashes --no-dev --no-emit-project` | Verified today to produce exactly the intended output (core deps only, no hashes, no `-e .` self-reference, no dev-group noise); hand-maintaining this file invites exactly the version-drift PITFALLS.md Pitfall 10 warns about |
| Notebook execution / cell-error detection | A custom subprocess wrapper around `jupyter nbconvert --execute` parsing stdout for tracebacks | `jupyter execute` (nbclient CLI), whose exit code alone is the fail-fast signal | Verified today: exit 0/1 is unambiguous and no output file is written on failure — no output-parsing needed at all |
| The `course` package's schema validation | Ad hoc `assert` scattered across every notebook cell that loads data | `course.schema.validate(gdf)` — one tested function, imported everywhere | This *is* ARCHITECTURE.md's stated "one schema contract... the boundary between sources and notebooks" (Pattern 2); Phase 1's entire job is to make this the first real, tested piece of that contract |

**Key insight:** Phase 1 has essentially zero domain-specific "don't hand-roll" traps of its own (those arrive with the geospatial data pipeline in Phase 2) — its hand-roll risk is almost entirely in **packaging and CI-adjacent tooling**, where uv/nbclient/pre-commit already solve every problem this phase has, and the temptation is to write custom shell glue instead of the flags those tools already expose.

---

## Common Pitfalls

### Pitfall 1: Flat package name mismatch under `uv_build`

**What goes wrong:** `uv sync` "succeeds" (installs *something* called `geo-embeddings-course`) but `import course` raises `ModuleNotFoundError`, because the backend built a wheel containing `geo_embeddings_course/`, not `course/`.
**Why it happens:** `uv_build`'s default `module-name` is derived from the *project* name (dashes/dots → underscores), not the literal package directory name — this only matches by coincidence when the two happen to be the same string.
**How to avoid:** Set `module-name = "course"` explicitly (see Pattern 1). Verify with `uv run python -c "import course"` immediately after the first `uv sync`, before writing anything else.
**Warning signs:** `uv build` succeeds with no error but produces `dist/geo_embeddings_course-*.whl` instead of a wheel containing `course/`.

### Pitfall 2: Make's default shell breaks `nullglob`/array-based fail-fast logic

**What goes wrong:** A Makefile recipe using bash-only syntax (`shopt -s nullglob`, `"${files[@]}"`) silently misbehaves or errors under a non-bash `SHELL`.
**Why it happens:** GNU Make invokes each recipe line with `/bin/sh` by default unless `SHELL := ...` is set; `/bin/sh` is not guaranteed to be bash-compatible (and even where it is bash, it is *not* run in POSIX-array-supporting mode unless invoked as `bash`, not `sh`).
**How to avoid:** `SHELL := /usr/bin/env bash` at the top of the Makefile, and wrap multi-line recipes needing shared state (like the nullglob check) in `.ONESHELL:` so the whole recipe body runs as one bash invocation rather than line-by-line.
**Warning signs:** The "zero notebooks" case prints nothing and exits nonzero instead of the intended graceful no-op message.

### Pitfall 3: `dev` group leaking into the Colab requirements export

**What goes wrong:** A student's Setup cell (if it were ever changed to reference `requirements-colab.txt`) pulls in `jupyterlab`, `pre-commit`, `ruff` — multi-hundred-MB of authoring tooling irrelevant to running a notebook, blowing the two-minute budget.
**Why it happens:** `uv export`'s default behavior *includes* the dev group (verified today: a plain `uv export --format requirements-txt` with no flags included `pytest`, `pluggy`, `iniconfig`, `pygments`, `packaging`, `colorama` alongside the real runtime deps).
**How to avoid:** Always pass `--no-dev` explicitly when generating `requirements-colab.txt`; treat this as a Makefile target (`make requirements-colab.txt`) rather than a manual step, so the flag is never forgotten.
**Warning signs:** `requirements-colab.txt` line count is much larger than the ~6-8 core runtime packages + their transitive deps.

### Pitfall 4: Registering the kernel with a name that collides across projects

**What goes wrong:** `ipython kernel install --name=python3` (the ipykernel default) silently overwrites or is overwritten by another project's default-named kernel on the same machine, and a notebook picks up the wrong interpreter without any error.
**Why it happens:** Kernel registration is **global** per-user (`~/Library/Jupyter/kernels/` on macOS), not scoped to the repo.
**How to avoid:** Always pass an explicit, project-specific `--name=geo-embeddings-course` (verified pattern above) and store that exact name as `course.config.KERNEL_NAME` or a Makefile variable so `jupyter execute --kernel_name=...` and the interactive JupyterLab kernel picker always agree.
**Warning signs:** `jupyter kernelspec list` shows a generically-named `python3` kernel whose `resource_dir` doesn't point into this repo's `.venv`.

---

## Code Examples

Verified transcripts from this machine, 2026-09-03 (uv 0.12.9, macOS arm64):

### Flat-layout `course` package (fails without the override, succeeds with it)
```toml
# Source: verified locally
[project]
name = "geo-embeddings-course"
version = "2026.8.0"
requires-python = ">=3.12,<3.14"
dependencies = []

[build-system]
requires = ["uv_build>=0.12.9,<0.13"]
build-backend = "uv_build"

[tool.uv.build-backend]
module-root = ""
module-name = "course"
```
```
$ uv build     # WITHOUT the [tool.uv.build-backend] block
error: Failed to build ...
  Caused by: Expected a Python module at: src/geo_embeddings_course/__init__.py

$ uv build     # WITH it
Successfully built dist/geo_embeddings_course-0.0.1.tar.gz
Successfully built dist/geo_embeddings_course-0.0.1-py3-none-any.whl

$ uv sync && uv run python -c "import course; print(course.__version__)"
Using CPython 3.12.13
import course OK, version 0.0.1
```

### `jupyter execute` exit-code behavior (the ENV-04 mechanism)
```
$ jupyter execute --kernel_name=python3 err.ipynb --output=err_executed.ipynb
[NbClientApp] Executing err.ipynb
nbclient.exceptions.CellExecutionError: An error occurred while executing the following cell:
------------------
raise ValueError('boom')
------------------
$ echo $?
1
$ ls err_executed.ipynb
ls: err_executed.ipynb: No such file or directory      # confirmed: no partial output on failure

$ jupyter execute --kernel_name=python3 ok.ipynb --output=ok_executed.ipynb
[NbClientApp] Save executed results to ok_executed.ipynb
$ echo $?
0
```
```bash
# fail-fast under set -euo pipefail: second notebook never runs after the first fails
$ for f in err.ipynb ok.ipynb; do
    jupyter execute --kernel_name=python3 "$f" --output="executed_${f}" >/dev/null
    touch "RAN_${f%.ipynb}"
  done
# script exits 1 after err.ipynb; `RAN_err` and `RAN_ok` are BOTH absent (ok.ipynb never reached)
```

### `uv export` flag behavior (the Colab requirements-file mechanism)
```
$ uv export --format requirements-txt                     # DEFAULT: includes -e ., hashes, and the dev group
-e .
certifi==2026.7.22 \
    --hash=sha256:...
...
pytest==9.1.1 \                                            # dev-group leakage — see Pitfall 3
    --hash=sha256:...

$ uv export --format requirements-txt --no-hashes --no-dev --no-emit-project
certifi==2026.7.22
charset-normalizer==3.5.1
idna==3.19
requests==2.34.2
    # via geo-embeddings-course
urllib3==2.7.0
    # via requests
# clean: no -e ., no hashes, no dev group

$ uv export --format requirements-txt --no-hashes --no-dev --no-emit-project --extra ee
# adds the `ee` extra's packages to the same clean export — proves per-module selective export works
```

### `course/schema.py` — the Phase 1 contract (ARCHITECTURE.md Pattern 2, reproduced for direct use)
```python
# course/schema.py
# Source: ARCHITECTURE.md Pattern 2 (HIGH confidence, sibling research)
import numpy as np

A_COLS = [f"A{i:02d}" for i in range(64)]
S2_COLS = ["S2_B02", "S2_B03", "S2_B04", "S2_B08", "S2_B11", "S2_B12"]
REQUIRED = ["sample_id", "lon", "lat", "year", "label", "label_source"]


def embedding_cols(gdf, prefix: str = "A") -> list[str]:
    return [c for c in gdf.columns if c.startswith(prefix) and c[len(prefix):].isdigit()]


def validate(gdf, embedding_prefix: str = "A"):
    missing = [c for c in REQUIRED if c not in gdf]
    assert not missing, f"missing columns: {missing}"
    assert gdf.crs is not None and gdf.crs.to_epsg() == 4326, (
        "points must be EPSG:4326; reproject inside the notebook"
    )
    cols = embedding_cols(gdf, embedding_prefix)
    assert cols, f"no embedding columns found with prefix {embedding_prefix!r}"
    norms = np.linalg.norm(gdf[cols].to_numpy(np.float32), axis=1)
    assert np.allclose(norms, 1.0, atol=1e-3), "embeddings must be unit length"
    return gdf


def to_matrix(gdf, embedding_prefix: str = "A") -> np.ndarray:
    return gdf[embedding_cols(gdf, embedding_prefix)].to_numpy(np.float32)
```

### Colab Setup cell (STACK.md's exact pattern, HIGH confidence — reproduced here as the artifact Phase 1's synthetic-notebook test must exercise)
```python
# %% tags=["setup"]
import importlib.util, subprocess, sys
IN_COLAB = "google.colab" in sys.modules
REQUIRED = {"geopandas": "geopandas", "pyarrow": "pyarrow", "mapclassify": "mapclassify"}
if IN_COLAB:
    missing = [pip for mod, pip in REQUIRED.items() if importlib.util.find_spec(mod) is None]
    if missing:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-q", *missing])

from course.config import RANDOM_STATE, COURSE_RELEASE
import numpy as np
np.random.seed(RANDOM_STATE)
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|---------------|--------|
| `setup.py` / `setuptools` src-layout as the default Python packaging story | uv-native `uv_build` backend, project-managed via `pyproject.toml` + `uv.lock` | uv 0.4.0 (`uv init` stopped creating `src/`/`[build-system]` by default) through the current 0.12.x line | Flat-layout packages now need an *explicit* `module-root = ""` — this is a genuinely new failure mode relative to older setuptools-based flat packages, which discovered top-level packages automatically |
| `nbgrader`/manual notebook execution for CI-style checks | `jupyter execute` (nbclient CLI) as a standalone headless runner | nbclient's CLI has been stable for several releases; STACK.md already chose it over nbmake (last release 2024-12) | Simpler dependency footprint; exit-code-only signaling (verified today) needs no output parsing |
| Requester-pays framing for cloud data egress budgeting | N/A to this phase directly, but relevant to why Phase 1's `providers` extra matters early | Google's GCS AlphaEarth bucket switched to provider-pays, July 2026 (STACK.md/ARCHITECTURE.md, HIGH) | Not a Phase 1 mechanic, noted only because it justifies *why* `providers` extra exists this early — Module 2/4/5 will need it without any cost-budgeting ceremony |

**Deprecated/outdated:** `uv add` without `--optional`/`--group` puts a dependency straight into `[project.dependencies]` (core) — the STACK.md installation walkthrough's step "3. Later phases — cloud / providers" (`uv add earthengine-api geemap rasterio ...` with no flag) would, if followed literally, put every heavy/credentialed package into the *core* install and violate ENV-05. That step needs to be read as shorthand, not copied verbatim — the planner must add `--optional ee` / `--optional providers` to those `uv add` invocations.

---

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | The extras should be named `ee` and `providers` (grouping earthengine-api+geemap separately from the rasterio/duckdb/geotessera/pystac-client "no-EE-account" cluster) | Standard Stack, Installation | Low — this is purely a naming/grouping choice; renaming later is a `pyproject.toml` edit only, no code depends on the string today. If the user (via a future `/gsd:discuss-phase`) wants different extra names or a single combined extra, it does not invalidate any other finding in this document. |
| A2 | Colab's runtime does **not** preinstall geopandas/pyarrow/shapely/pyproj/mapclassify (only inferred via WebSearch community sources, no official Google-published package manifest exists) | Standard Stack / Don't Hand-Roll (Pattern 2) | Medium — if Colab *does* preinstall one of these (e.g., pyarrow, which many data-science-oriented Colab images do carry), the Setup cell's `find_spec` check already handles it gracefully (skips installing what's present) — so this assumption is self-correcting at runtime even if wrong, but the "<2 minute" budget estimate could be optimistic or pessimistic depending on the true baseline. Carried forward from STACK.md at MEDIUM confidence there too. |
| A3 | `nbclient` 0.11.0's CLI exit-code/no-partial-output behavior (verified against the locally installed 0.10.4) holds unchanged at 0.11.0 | Code Examples, Common Pitfalls | Low — nbclient's CLI surface (`jupyter execute`, `--kernel_name`, `--output`, exit codes) has been stable across recent minor versions; still, the planner should re-run the exact verification transcript once 0.11.0 is actually locked, rather than trusting this extrapolation blindly. |

---

## Open Questions

1. **Should `.github/workflows/ci.yml` exist at all in Phase 1, even as a stub?**
   - What we know: REQUIREMENTS.md lists GitHub Actions CI as `ENV-06`, explicitly v2/deferred. ARCHITECTURE.md's illustrative repo tree includes it anyway, and Anti-Pattern 2 in ARCHITECTURE.md references "CI" enforcement of the exercise-drift check.
   - What's unclear: whether "CI" in ARCHITECTURE.md's prose means "a GitHub Actions workflow" (deferred) or "the same checks, run locally via pre-commit/Makefile, that could *later* be lifted into a workflow" (in scope now).
   - Recommendation: build the checks as local pre-commit hooks + Makefile targets now (satisfies the *substance* of ARCHITECTURE.md's enforcement intent), and explicitly do not create `.github/workflows/`. Flag `ENV-06` as the natural home for wiring the exact same commands into a GitHub Actions runner later.

2. **Does Phase 1's README "list every notebook with an Open-in-Colab badge" success criterion (SC5) apply vacuously (zero notebooks) or does it require a populated stub table?**
   - What we know: Phase 1 ships zero notebooks (Phase 3 ships the first one). ENV-03's literal wording assumes notebooks already exist ("The README lists every notebook...").
   - What's unclear: whether the plan-checker/verifier will treat "table exists with a header row and zero data rows, ready for Phase 3+ to append to" as satisfying SC5, or whether it expects something more.
   - Recommendation: Phase 1 should deliver the banner (exact text, verified verbatim per ENV-03), the license section pre-populated with what's already known today (AlphaEarth CC BY 4.0 + exact attribution sentence, per PITFALLS.md Pitfall 13 — these facts don't depend on data existing yet), local run instructions, and an empty "Notebooks" table with the Colab badge URL pattern documented as a comment/template row. Each later phase's plan should include a task to append its notebook's row — this should be called out explicitly as a recurring task in Phases 3–5's future plans, not assumed automatic.

3. **Exact `RANDOM_STATE`/`COURSE_RELEASE` constant values** — `RANDOM_STATE = 42` and `COURSE_RELEASE = "2026.08"` are used consistently across STACK.md/ARCHITECTURE.md's snippets; treat as settled (not actually open) but flagging that Phase 1's `course/config.py` is the single place these get defined, and every later phase's Setup cell must import them from there rather than re-hardcoding.

---

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| uv | Entire phase | ✓ | 0.12.9 | — |
| Python 3.12 (via uv) | Runtime pin | ✓ (downloadable via `uv python pin 3.12`) | 3.12.13 | — |
| GNU Make | ENV-04 headless target | ✓ | 3.81 (old — avoid Make 4.x-only syntax) | — |
| git | Clean-clone verification | ✓ | 2.55.0 | — |
| jupyter/nbclient (`jupyter execute`) | ENV-04 | ✓ (ambient) / will be pinned via `dev` group | 0.10.4 ambient, 0.11.0 to be locked | — |
| slopcheck | Package Legitimacy Audit | ✓ | (Homebrew install) | — |
| GitHub Actions runner | Deferred `ENV-06` | N/A this phase | — | Local pre-commit + Makefile substitute for now |
| A live Colab session | Manually verifying the <2-minute Setup-cell install budget on real Colab infra | ✗ (no browser/Colab API access from this environment) | — | Documented as a manual, one-time human-verification step; cannot be automated from this research session or from the author's local machine alone |

**Missing dependencies with no fallback:** none block Phase 1's buildable scope.
**Missing dependencies with fallback:** live Colab timing verification — flagged as a manual checkpoint the plan should schedule (see Validation Architecture below).

---

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 9.1.1 (for `course/`), `jupyter execute`/nbclient (for notebook-shaped checks — no notebooks exist yet in Phase 1, so this framework is exercised only via synthetic/temporary notebooks built with `nbformat` inside pytest tests) |
| Config file | none yet — Wave 0 creates `pyproject.toml`'s `[tool.pytest.ini_options]` (or a bare `pytest.ini`) alongside the package itself |
| Quick run command | `uv run pytest tests/ -x` |
| Full suite command | `uv run pytest tests/` (Phase 1 has no slow tests — the whole suite *is* the quick run at this phase) |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| ENV-01 | `uv sync` on clean clone gives Python 3.12 kernel with pinned stack, `uv.lock` committed and reproducible | integration | `rm -rf .venv && uv sync --group dev && uv run python --version` (expect substring `Python 3.12.`) then `git diff --exit-code uv.lock` (expect exit 0 — lockfile unchanged by sync) | ❌ Wave 0 — needs `pyproject.toml` to exist first, chicken-and-egg with this phase's own deliverable |
| ENV-01 (kernel proof) | Registered kernel resolves THIS project's venv, not system/another project | integration | `uv run ipython kernel install --user --env VIRTUAL_ENV "$(pwd)/.venv" --name=geo-embeddings-course && uv run jupyter execute --kernel_name=geo-embeddings-course <tmp notebook printing sys.executable>` (assert output path contains `.venv`) | ❌ Wave 0 |
| ENV-02 | Setup cell's Colab-detection + import + RANDOM_STATE pattern is syntactically and semantically correct before any real notebook exists | unit (via synthetic notebook) | `uv run pytest tests/test_bootstrap.py -x` — builds an in-memory notebook with `nbformat`, writes the exact Setup-cell source from Code Examples, executes it via `nbclient.NotebookClient`, asserts `RANDOM_STATE == 42` and no exception | ❌ Wave 0 |
| ENV-03 | `import course` succeeds; `import ee`/`geemap`/`geotessera`/`duckdb`/`torch` all fail in the core (no-extras) env | unit | `uv run python -c "import course"` (exit 0) and `uv run python -c "import ee"` (expect exit 1, `ModuleNotFoundError`) — repeat per heavy package; wrap as `tests/test_core_env_isolation.py` using `subprocess.run` with `sys.executable` pointed at `.venv` and asserting each returncode | ❌ Wave 0 |
| ENV-04 | Headless execution target fails fast on first cell error; no-ops cleanly with zero notebooks | integration (shell-level) | `tests/test_execute_target.py`: with zero notebooks present, run the Makefile's execution recipe and assert exit 0 + expected "No solution notebooks found" substring; then, in a `tmp_path` fixture, drop a synthetic two-notebook pair (first raises, second would print a sentinel) and assert exit 1 and that the sentinel never appears in output | ❌ Wave 0 |
| ENV-05 | Heavy/credentialed deps installable via `--extra` but excluded from default `uv sync` | unit | `uv sync --group dev` (no extras) then assert `import ee` fails; `uv sync --group dev --extra ee` then assert `import ee` succeeds; revert to `uv sync --group dev` afterward so the working tree returns to its default state | ❌ Wave 0 |

### Sampling Rate
- **Per task commit:** `uv run pytest tests/ -x` (fast — Phase 1 has no I/O-heavy tests; sub-second).
- **Per wave merge:** the full command sequence above (`uv sync` clean-clone rebuild + kernel registration + extras toggle) — this is the phase's only wave, so "wave merge" and "phase gate" are the same checkpoint here.
- **Phase gate:** all five rows above green, **plus** one manual, human-run checkpoint: open a fresh Colab notebook, paste the Setup-cell snippet, and time the install (target: under two minutes). This cannot be scripted from this environment or from the author's local machine — flag as `checkpoint:human-verify` in the plan. A single automated check is insufficient here specifically because the "<2 minutes on Colab" claim is about Colab's actual infrastructure and preinstalled-package set (MEDIUM confidence, no official manifest — see Assumption A2), which no amount of local testing can substitute for.

### Wave 0 Gaps
- [ ] `tests/test_schema.py` — covers the `course.schema` contract (validate/embedding_cols/to_matrix, happy path + each assertion failure mode)
- [ ] `tests/test_bootstrap.py` — covers ENV-02 via a synthetic in-memory notebook (no real `.ipynb` artifact needed or committed)
- [ ] `tests/test_core_env_isolation.py` — covers ENV-03/ENV-05 (core vs. `--extra ee`/`--extra providers` import isolation)
- [ ] `tests/test_execute_target.py` — covers ENV-04 (zero-notebook no-op + fail-fast on synthetic error notebook)
- [ ] `tests/conftest.py` — shared fixtures: a valid synthetic GeoDataFrame builder (5 rows, unit-norm `A00..A63`, EPSG:4326) for `test_schema.py`; a temp-project or `tmp_path`-scoped notebook-writer helper for the other three
- [ ] Framework install: `uv add --group dev pytest` (already covered by the `dev` group install command above — no separate action needed)

---

## Security Domain

`security_enforcement` is absent from `.planning/config.json`'s `workflow` block, which per the enforcement default means **enabled**. This is a docs/notebook-authoring repository with no server, no user accounts, and no runtime auth boundary — most ASVS categories genuinely do not apply. The real security surface here is narrower: credential hygiene (this repo will later hold Earth Engine/LGND-adjacent code) and supply-chain hygiene (unpinned installs, the exact failure mode PITFALLS.md Pitfall 10 already documents at length).

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | No | No login system exists anywhere in this project; Earth Engine/LGND auth (Phase 4/5) is out-of-band, credential-optional, and not this phase's concern |
| V3 Session Management | No | N/A — no server, no sessions |
| V4 Access Control | No | N/A — public, static repo content |
| V5 Input Validation | Yes (narrow) | `course.schema.validate()` is the one real "trust boundary" this phase creates — it is the gate every downstream cell relies on before treating a GeoDataFrame as safe to use (correct columns, correct CRS, unit-norm embeddings). Not classic web input validation, but the same *principle*: validate at the boundary, fail loudly, never silently coerce. |
| V6 Cryptography | Marginal | No secrets or crypto in Phase 1. Later phases' `manifest.json` sha256 checksums (Phase 2) are data-integrity hashing, not cryptographic security per se — noted here only so the planner doesn't need to re-derive this distinction later. |

### Known Threat Patterns for this stack

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Committing a service-account JSON or `LGND_TOKEN` literal (PITFALLS.md Pitfall 9's documented "Security Mistakes" table) | Information Disclosure | `.gitignore` entry for any `*.json` credential file pattern the author might create locally, `getpass`/env-var-only credential loading (already the STACK.md/ARCHITECTURE.md pattern for later phases) — Phase 1's concrete contribution is making sure `.gitignore` is broad enough *now*, before any credential-adjacent code exists, rather than reactively after a leak |
| Unpinned `pip install` in a Setup cell (`pip install geopandas` with no version) | Tampering (supply-chain: a compromised or yanked release silently changes what every student runs) | The Setup cell installs by bare name deliberately (Pattern 2) for Colab-preinstalled-package compatibility, but the *pinned* record of exactly what versions the course was authored/recorded against lives in `uv.lock` / `requirements-colab.txt` — the mitigation is provenance-through-the-lockfile, not per-cell pinning, which is why `uv.lock` being committed and `git diff --exit-code`-verified (ENV-01's test) matters as a security control, not just a reproducibility one |
| `jupyter execute` kernel running "over TCP without encryption" (verified warning emitted locally: `[IPKernelApp] WARNING | Kernel is running over TCP without encryption...`) | Information Disclosure (theoretical) | Non-issue for local, single-machine headless execution (no network exposure); worth a one-line note in the Makefile/README so a future contributor doesn't mistake the benign default warning for a real finding |
| slopsquatted / typo-squatted package names in a future `uv add` (e.g., a contributor fat-fingering `geo-tessera` instead of `geotessera`) | Tampering (supply chain) | `slopcheck scan --pkg pypi <name>` before adding any new dependency — already run for all 20 Phase 1 packages in this session; the plan should make this an explicit step for every future `uv add` of a new package name, not just a one-time Phase 1 audit |

---

## Sources

### Primary (HIGH confidence — verified by running the command on this machine, 2026-09-03)
- `uv --version`, `uv init --bare`, `uv build`, `uv sync`, `uv lock`, `uv export --format requirements-txt [--no-hashes|--no-dev|--no-emit-project|--extra|--group]`, `uv python pin 3.12`, `uv add --optional`/`--group` — all run against scratch projects in this session
- `jupyter execute --kernel_name=... --output=... --allow-errors --timeout=... --help` — exit-code and no-partial-output-on-failure behavior verified against synthetic notebooks built with `nbformat`
- `uv run ipython kernel install --user --env VIRTUAL_ENV ... --name=...` + `jupyter kernelspec list` + `jupyter kernelspec uninstall` — full registration/execution/cleanup cycle verified
- `slopcheck scan --pkg pypi <name>` for all 20 Phase 1 core+dev packages
- `make --version` (GNU Make 3.81), `git --version` (2.55.0) — local toolchain audit
- Context7 `/astral-sh/uv` — `[dependency-groups]` (PEP 735) vs `[project.optional-dependencies]` semantics, `uv add --optional`/`--group`, `uv sync --extra`/`--group`/`--all-extras`/`--all-groups`, `[tool.uv] default-groups`, `uv_build` `module-root`/`module-name` settings struct
- Context7 `/kynan/nbstripout` — pre-commit hook config, `keep_output` tag/metadata mechanism (note: nbstripout's native tag is `keep_output`, underscore — differs from ARCHITECTURE.md's hyphenated `keep-output` tag vocabulary; flagged for the planner)
- Context7 `/mwouts/jupytext` — pre-commit `--sync` hook, `jupytext.toml` `cell_metadata_filter` semantics (confirms `"tags,-all"` ≠ the docs' generic `"-all"` example — deliberate divergence to preserve tags for `tools/make_exercise.py`, Phase 6)
- `/websites/astral_sh_ruff` (Context7) — `.ipynb` linted by default (no `extend-include` needed), `[tool.ruff.format] exclude` / `[tool.ruff] extend-exclude` for opting notebooks *out* if desired
- docs.astral.sh/uv/concepts/projects/dependencies/ (WebFetch) — extras-vs-groups pip-installability distinction stated explicitly: "extras... installable by end users via `pip install package[extra]`" vs. groups "will not be included in the project requirements when published to PyPI"
- docs.astral.sh/uv/reference/cli/#uv-export (WebFetch) — full flag list and default-value semantics for every `uv export` flag used in this document

### Secondary (MEDIUM confidence)
- WebSearch, "Google Colab preinstalled packages list geopandas pyarrow shapely pyproj mapclassify" — no official Google-published manifest found; community consensus (Medium/GitHub issue threads) supports STACK.md's existing MEDIUM-confidence claim that geopandas/pyarrow/shapely/pyproj/mapclassify are not preinstalled — corroborates rather than newly establishes this fact (see Assumption A2)

### Tertiary (LOW confidence)
- None used without corroboration in this document.

### Carried forward at HIGH confidence from sibling research (not re-verified here, cited by document)
- STACK.md — exact package versions, PyPI JSON API checks, Colab runtime FAQ (Python 3.12.13, numpy 2.0.2), "provider pays" GCS bucket status, `jupyter execute`/nbclient choice over papermill/nbmake, jupytext/nbstripout/pre-commit tool choices
- ARCHITECTURE.md — flat `course/` layout decision, schema-contract Pattern 2 (reproduced verbatim in Code Examples), `course/live/` vs `pipeline/` boundary, project structure tree, phase sequencing table
- PITFALLS.md — Pitfall 9 (credential hard-dependence), Pitfall 10 (version rot), Pitfall 11 (hidden state / Colab divergence, including the exact env-detection snippet this document's Pattern 2 extends), Pitfall 12 (exercise drift), Pitfall 13's exact AlphaEarth attribution sentence (reused in Open Question 2's README recommendation)

---

## Metadata

**Confidence breakdown:**
- Standard stack (package list/versions): HIGH — inherited from STACK.md's same-day PyPI verification, cross-checked with slopcheck in this session
- Packaging mechanics (`uv_build` flat-layout fix, extras-vs-groups pip-installability): HIGH — directly verified by building and importing a real package on this machine
- Headless execution behavior (`jupyter execute` exit codes, fail-fast, zero-notebook handling): HIGH — directly verified with real transcripts
- Colab-specific claims (preinstalled packages, <2-minute budget): MEDIUM — no official Google manifest exists; corroborated by community sources only, and the actual timing claim needs one manual human-run Colab session to confirm (flagged in Validation Architecture)
- Security domain: MEDIUM — most controls are "keep doing what PITFALLS.md already established," not new findings; ASVS mapping is a reasonable-effort fit for a non-web-app repo, not a rigorous audit

**Research date:** 2026-09-03
**Valid until:** ~30 days for the packaging/tooling mechanics (uv is fast-moving but its project/build-backend semantics have been stable across recent 0.12.x releases); ~7 days for anything Colab-runtime-specific (numpy/pandas versions, preinstalled-package set) given Colab's own stated intent to move to Python 3.13 "very soon" per STACK.md's cited GitHub issue

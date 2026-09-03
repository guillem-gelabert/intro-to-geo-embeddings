---
phase: 1
slug: repository-and-environment-scaffold
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-09-03
---

# Phase 1 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.
> Derived from `01-RESEARCH.md` § Validation Architecture.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 9.1.1 for the `course` package; `jupyter execute` / nbclient for notebook-shaped checks. No notebooks exist in this phase, so the notebook path is exercised only through synthetic notebooks built with `nbformat` inside pytest. |
| **Config file** | none yet — Wave 0 creates `[tool.pytest.ini_options]` in `pyproject.toml` alongside the package itself |
| **Quick run command** | `uv run pytest tests/ -x` |
| **Full suite command** | `uv run pytest tests/` |
| **Estimated runtime** | ~10 seconds for the pytest suite; the clean-clone `uv sync` rebuild is minutes and runs at the phase gate, not per task |

**Chicken-and-egg note.** This phase builds the very test infrastructure it is validated by. Every row below is marked Wave 0 because `pyproject.toml` and `tests/` do not exist at phase start. Wave 0 must therefore land the packaging skeleton and the test harness before any other task can be verified.

---

## Sampling Rate

- **After every task commit:** `uv run pytest tests/ -x` — sub-second to a few seconds, no I/O-heavy tests in this phase
- **After every plan wave:** full sequence — clean-clone `uv sync` rebuild, kernel registration proof, extras toggle
- **Before `/gsd:verify-work`:** full suite green plus the manual Colab checkpoint below
- **Max feedback latency:** 15 seconds for the automated suite

---

## Per-Task Verification Map

Task IDs are assigned by the planner. Rows are keyed by requirement until plans exist, then the executor refines them.

| Requirement | Behavior | Test Type | Automated Command | Expected | File Exists |
|---|---|---|---|---|---|
| ENV-01 | Clean-clone `uv sync` yields a Python 3.12 interpreter against a committed, reproducible `uv.lock` | integration | `rm -rf .venv && uv sync --group dev && uv run python --version` then `git diff --exit-code uv.lock` | version output contains `Python 3.12.`; lockfile diff exits 0 | ❌ W0 |
| ENV-01 | The registered Jupyter kernel resolves this project's venv, not a system or sibling-project interpreter | integration | register the kernel, then `uv run jupyter execute` a temp notebook that prints `sys.executable` | printed path contains `.venv` | ❌ W0 |
| ENV-02 | The Setup cell's Colab detection, imports and constants are correct before any real notebook exists | unit via synthetic notebook | `uv run pytest tests/test_bootstrap.py -x` — builds the notebook in memory with `nbformat`, executes via `NotebookClient` | `RANDOM_STATE == 42`, no exception raised | ❌ W0 |
| ENV-03 | `import course` succeeds in the core environment | unit | `uv run python -c "import course"` | exit 0 | ❌ W0 |
| ENV-04 | The headless execution target no-ops cleanly when zero notebooks exist | integration | run the Makefile execution recipe with no notebooks present | exit 0 and a "no solution notebooks found" message | ❌ W0 |
| ENV-04 | The same target fails fast on the first cell error | integration | drop a synthetic two-notebook pair in `tmp_path` where the first raises and the second prints a sentinel | exit 1, sentinel absent from output | ❌ W0 |
| ENV-05 | Heavy and credentialed dependencies are absent from the default install and installable on demand | unit | `uv sync --group dev` then `python -c "import ee"`; then `uv sync --group dev --extra ee` and repeat | first invocation exits non-zero with `ModuleNotFoundError`; second exits 0; working tree restored afterwards | ❌ W0 |

*Status legend: ⬜ pending · ✅ green · ❌ red or Wave 0 dependency · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `pyproject.toml` with `[tool.pytest.ini_options]` — the packaging skeleton every other check depends on
- [ ] `tests/conftest.py` — shared fixtures: a synthetic unit-norm GeoDataFrame builder (5 rows, `A00..A63`, EPSG:4326) and a `tmp_path`-scoped notebook-writer helper
- [ ] `tests/test_schema.py` — the `course.schema` contract: happy path plus each assertion failure mode
- [ ] `tests/test_bootstrap.py` — ENV-02 through a synthetic in-memory notebook, no committed `.ipynb`
- [ ] `tests/test_core_env_isolation.py` — ENV-03 and ENV-05 core-versus-extras import isolation
- [ ] `tests/test_execute_target.py` — ENV-04 zero-notebook no-op and fail-fast on a synthetic error notebook

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|---|---|---|---|
| The Colab bootstrap install completes in under two minutes | ENV-02, ENV-05 | The claim is about Colab's live infrastructure and its preinstalled package set. Research rates this MEDIUM confidence with no official Google manifest, and no local test can substitute for it. | Open a fresh Colab CPU runtime, paste the Setup cell, time the install, and record the observed `numpy`, `pandas` and `scikit-learn` versions for the version-skew note |

Flag the corresponding plan task `checkpoint:human-verify`. It is the one gate in this phase that cannot be automated from this machine.

---

## Sampling-Rate Argument

The minimum set that would catch a regression in this scaffold is four checks, because each covers a failure mode invisible to the others:

1. **Clean-clone rebuild** catches lockfile drift and a `requires-python` that no longer resolves. A passing test suite in an already-built venv cannot see this.
2. **`import course` in a fresh interpreter** catches the `uv_build` module-discovery trap the research found empirically: without an explicit `module-root`/`module-name` override the backend derives the wrong module name, and the package silently fails to expose `course`.
3. **The extras-toggle pair** catches dependency creep into the core install. One half is insufficient: proving `import ee` fails says nothing about whether the extra still works, and proving it succeeds says nothing about core weight.
4. **The fail-fast pair for the execution target** catches both degenerate directions — a target that silently passes on error, and a target that errors on an empty notebook set. A single check cannot distinguish them.

A single aggregate check is insufficient anywhere in this phase because the failure modes are independent: packaging, isolation and execution semantics fail separately and for unrelated reasons.

---

## Validation Sign-Off

- [ ] All tasks have automated verification or a declared Wave 0 dependency
- [ ] Sampling continuity: no three consecutive tasks without an automated verify
- [ ] Wave 0 covers every ❌ reference above
- [ ] No watch-mode flags in any command
- [ ] Feedback latency under 15 seconds for the automated suite
- [ ] Manual Colab checkpoint recorded with observed versions
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending

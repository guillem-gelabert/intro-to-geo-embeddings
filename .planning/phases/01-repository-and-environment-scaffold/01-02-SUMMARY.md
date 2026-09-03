---
phase: 01-repository-and-environment-scaffold
plan: 02
subsystem: infra
tags: [readme, jupytext, pre-commit, nbstripout, ruff, gitignore, documentation]

# Dependency graph
requires:
  - phase: 01-repository-and-environment-scaffold (plan 01)
    provides: "pyproject.toml core/extras dependency layout, the placeholder README.md this plan replaces, .python-version, uv.lock"
provides:
  - "README.md front door: verbatim reference-environment banner, local setup instructions, empty Notebooks table with Colab badge URL template, AlphaEarth CC BY 4.0 license/attribution section, accurate Extras (ee/providers) documentation, requirements-colab.txt explainer"
  - "jupytext.toml pairing config (ipynb/py:percent, cell_metadata_filter=tags,-all) for future solution notebooks"
  - ".pre-commit-config.yaml with four verified-resolvable hook repos (pre-commit-hooks v5.0.0, nbstripout 0.9.1, jupytext v1.19.5 --sync, ruff-pre-commit v0.16.5)"
  - "Broadened .gitignore: packaging-artifact patterns (dist/, *.egg-info/, .mypy_cache/) and credential-shaped-file patterns (.env, .env.*, *-key.json, *service-account*.json, *.pem), preemptive per phase threat model T-01-04"
affects: [01-03, 01-04, phase-2, phase-3, phase-6]

# Tech tracking
tech-stack:
  added: [jupytext 1.19.5, pre-commit 4.6.2, nbstripout 0.9.1, ruff-pre-commit v0.16.5]
  patterns: ["jupytext cell_metadata_filter=tags,-all (deliberate divergence from jupytext's -all default, preserving tags for Phase 6 exercise-derivation tooling)", "Pre-commit hooks pinned to explicit tagged revs, never floating branches"]

key-files:
  created: [jupytext.toml, .pre-commit-config.yaml]
  modified: [README.md, .gitignore]

key-decisions:
  - "ruff-pre-commit pinned to v0.16.5, matching the installed uv-managed ruff 0.16.5 exactly (queried via `uv run ruff --version` per the plan's instruction, rather than guessed)"
  - "Reverted all file modifications made by `uv run pre-commit run --all-files` outside this plan's declared files_modified scope (01-RESEARCH.md, ARCHITECTURE.md, PITFALLS.md, STACK.md, course/schema.py, docs/research/course-design-research-2026-08.md) via `git checkout -- <file>` after confirming the four hook repos resolved without error — the verification command's job was to prove hook-repo resolvability, not to reformat unrelated files in this task's commit"

patterns-established:
  - "Pattern: plan-level `<verify>` commands that run repo-wide tools (pre-commit --all-files) are read-only proof-of-resolution checks in a parallel-worktree context; any side-effect file modifications outside files_modified must be reverted with `git checkout -- <file>`, never committed"

requirements-completed: [ENV-03]

# Metrics
duration: ~2min (commit timestamps 17:58:12 -> 17:59:58 local; excludes file-read/context-gathering time)
completed: 2026-09-03
---

# Phase 1 Plan 02: Repository and Environment Scaffold Summary

**Full README front door (verbatim banner, local setup, AlphaEarth CC BY 4.0 attribution, empty Notebooks table with Colab badge template, accurate ee/providers Extras section) plus jupytext/pre-commit/gitignore repo hygiene scaffolding, with all four pre-commit hook repos verified resolvable at their pinned revs.**

## Performance

- **Duration:** ~2 min per commit timestamps (17:58:12 → 17:59:58 local)
- **Started:** 2026-09-03T15:58:12Z
- **Completed:** 2026-09-03T15:59:58Z
- **Tasks:** 2/2
- **Files modified:** 4 (README.md, .gitignore modified; jupytext.toml, .pre-commit-config.yaml created)

## Accomplishments
- README.md replaced its Plan 01 placeholder with the full front door: verbatim banner sentence, Local setup section (uv python pin, uv sync --group dev, kernel registration command, make test, make execute-notebooks with its documented current no-op behavior), empty Notebooks table plus Colab badge URL template as an HTML comment, Data sources and licenses section with the exact AlphaEarth attribution and CC BY 4.0, and an Extras section that correctly keeps rasterio/xarray out of the `providers` extra (they ship in core per ENV-01)
- jupytext.toml scaffolded with the Phase 6-required `cell_metadata_filter = "tags,-all"` divergence from jupytext's own docs default
- .pre-commit-config.yaml scaffolded with all four hook repos (pre-commit-hooks, nbstripout, jupytext, ruff-pre-commit) verified to resolve and install cleanly under `uv run pre-commit run --all-files` — no repo- or revision-resolution error; ruff-pre-commit's rev was queried from the actually-installed `ruff --version` (0.16.5) rather than guessed
- .gitignore extended with packaging-artifact and credential-shaped-file patterns (T-01-04 preemptive mitigation), confirmed to be a strict superset of its pre-existing content including both re-include rules (`!.planning/REQUIREMENTS.md`, `!.planning/**/*-PLAN.md`)

## Task Commits

Each task was committed atomically:

1. **Task 1: README with banner, run instructions, license section, and notebook table skeleton** - `edb00f4` (docs)
2. **Task 2: Repo hygiene scaffolding: jupytext pairing, pre-commit hooks, broadened .gitignore** - `d6027b5` (chore)

**Plan metadata:** committed with this SUMMARY.md (see below)

## Files Created/Modified
- `README.md` - full front door content (banner, local setup, Notebooks table skeleton, license/attribution, Extras, requirements-colab.txt explainer), replacing Plan 01's placeholder
- `jupytext.toml` - `formats = "ipynb,py:percent"`, `cell_metadata_filter = "tags,-all"`
- `.pre-commit-config.yaml` - pre-commit-hooks v5.0.0, nbstripout 0.9.1, jupytext v1.19.5 (`--sync`), ruff-pre-commit v0.16.5
- `.gitignore` - added packaging-artifact block (`dist/`, `*.egg-info/`, `.mypy_cache/`) and credential-shaped-file block (`.env`, `.env.*`, `*-key.json`, `*service-account*.json`, `*.pem`), all pre-existing lines preserved unchanged

## Decisions Made
- Queried the installed ruff version (`uv run ruff --version` → 0.16.5) rather than guessing the ruff-pre-commit tag, per the plan's explicit instruction; the pin resolved cleanly on the first `pre-commit run --all-files` attempt, so `pre-commit autoupdate` was not needed
- After running `uv run pre-commit run --all-files` for verification, several existing files outside this plan's `files_modified` scope were reformatted as a side effect (trailing-whitespace/end-of-file-fixer on two `.planning`/`docs` files, ruff-format on `course/schema.py` and others). These were reverted with `git checkout -- <file>` before staging Task 2's commit — the verification's purpose was to prove the four hook repos resolve without a repo/revision error (which they did), not to reformat files this plan does not own. Committing those reformats would have collided with sibling worktree agents' declared file scopes.

## Deviations from Plan

None - plan executed exactly as written. (The pre-commit side-effect revert above is process hygiene during verification, not a deviation from the plan's specified content — the plan's own acceptance criteria only require the four hook repos to resolve without a repo/revision error, which was confirmed.)

## Issues Encountered
- `uv run pre-commit run --all-files` modified files outside this plan's scope as a side effect of running `trailing-whitespace`, `end-of-file-fixer`, and `ruff-format` repo-wide. Resolved by reverting each out-of-scope file individually with `git checkout -- <file>` (never a blanket reset/clean, per the destructive-git prohibition) and confirming `git status --short` showed only the four intended files before staging Task 2's commit.

## User Setup Required
None - no external service configuration required. All four pre-commit hook repos are public GitHub repos pinned to tagged revs; no credentials or manual installation steps needed. Note: `pre-commit install` (to wire hooks into `git commit`) was not run as part of this plan's scope — hooks were exercised via `uv run pre-commit run --all-files` for verification only, per the plan's `<verify>` block.

## Next Phase Readiness
- README.md, jupytext.toml, and .pre-commit-config.yaml are in place for Phase 3+ to build on: future phases append rows to the Notebooks table, and the jupytext/nbstripout hooks are ready before the first notebook is authored.
- No blockers for the remaining plans in this phase (01-03, 01-04), which own disjoint files (Makefile, requirements-colab.txt, tests/) per the parallel-execution file-scope contract.

---
*Phase: 01-repository-and-environment-scaffold*
*Completed: 2026-09-03*

## Self-Check: PASSED

All 5 files verified present on disk (README.md, jupytext.toml, .pre-commit-config.yaml, .gitignore, 01-02-SUMMARY.md). All 3 commits verified present in git history (edb00f4, d6027b5, 04713a3).

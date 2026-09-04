---
phase: 07-slide-decks
plan: 01
subsystem: slides
tags: [marp-cli, slides, revealjs-fallback, makefile, toolchain-decision]

requires: []
provides:
  - "Slide toolchain decision (Marp CLI 4.5.0, not Quarto) recorded unambiguously for sibling plans"
  - "slides/_metadata.yml: shared 16:9 Marp front-matter reference block"
  - "slides/custom.scss: shared minimal theme"
  - "slides/_partials/version-banner.qmd and attribution.qmd: copy-paste-ready reusable slide content"
  - "make slides / make slides-pdf Makefile targets"
affects: [07-02-deck-authoring, 07-03-deck-authoring, 07-04-deck-authoring, 07-05-deck-smoke-render]

tech-stack:
  added: ["@marp-team/marp-cli@4.5.0 (via npx, pinned)"]
  patterns:
    - "Marp CLI on-demand via npx, never a global install, version always pinned in the Makefile MARP variable"
    - "Partials are copy-pasted into each deck (not included) because Marp lacks Quarto's {{< include >}}"

key-files:
  created:
    - slides/_metadata.yml
    - slides/custom.scss
    - slides/_partials/version-banner.qmd
    - slides/_partials/attribution.qmd
    - slides/_partials/README.md
  modified:
    - Makefile

key-decisions:
  - "Quarto is NOT usable on this machine: brew install --cask quarto fetches the cask but its .pkg installer requires interactive sudo (no TTY, no askpass helper available to the agent) and fails non-interactively."
  - "Marp CLI is the toolchain for the rest of phase 07, invoked via `npx --yes @marp-team/marp-cli@4.5.0` (pinned, never @latest per the plan's threat model T-07-01)."
  - "Because Marp has no shared-metadata-include mechanism, slides/_metadata.yml is a documented reference block; every deck's own front-matter must repeat marp: true / theme: default / size: 16:9 / paginate: true verbatim."
  - "Partials (version-banner.qmd, attribution.qmd) are copy-pasted into each of the eight decks rather than included, per the same Marp limitation; slides/_partials/README.md documents the trim-only-never-reword convention."
  - "npx decktape is not used for PDF; Marp's own --pdf flag is used directly in make slides-pdf."

patterns-established:
  - "Deck-authoring plans (07-02/03/04) must copy slides/_metadata.yml's three front-matter keys and copy-paste (not include) the two partials, trimming irrelevant attribution rows only."

requirements-completed: [SLIDE-01, SLIDE-03]

duration: ~25min
completed: 2026-09-04
---

# Phase 07 Plan 01: Slide Toolchain and Shared Deck Scaffold Summary

**Marp CLI (pinned 4.5.0, via npx) replaces the planned Quarto toolchain after Quarto's cask installer proved impossible to run non-interactively on this machine; shared 16:9 theme, reusable version-banner/attribution partials, and `make slides`/`make slides-pdf` targets are in place for the remaining deck-authoring plans.**

## Performance

- **Duration:** ~25 min
- **Started:** 2026-09-04T02:00Z (approx)
- **Completed:** 2026-09-04T02:19:48Z
- **Tasks:** 3
- **Files modified:** 6 (5 created, 1 modified)

## Accomplishments
- Verified Quarto cannot be installed non-interactively (`brew install --cask quarto` fails with `sudo: a password is required`); confirmed Marp CLI 4.5.0 resolves and runs via `npx --yes @marp-team/marp-cli@4.5.0 --version`.
- Created the shared 16:9 Marp configuration reference (`slides/_metadata.yml`) and minimal theme (`slides/custom.scss`).
- Created reusable, copy-paste-ready partials for the version banner and the DATA_CARD.md attribution table, plus a README documenting the Marp copy-paste convention (no `{{< include >}}` equivalent exists in Marp).
- Added `make slides` and `make slides-pdf` Makefile targets that render every `slides/*.md` deck via the pinned Marp CLI, following this repo's existing nullglob recipe style.

## Task Commits

Each task was committed atomically:

1. **Task 1: Verify or install Quarto, decide the real fallback** - no file changes (verification-only); decision recorded in Task 2's commit message and files
2. **Task 2: Shared revealjs project config and theme** - `e519234` (feat)
3. **Task 3: Reusable version-banner and attribution partials, Makefile targets** - `5d1283c` (feat)

**Plan metadata:** (final SUMMARY commit, this file)

## Files Created/Modified
- `slides/_metadata.yml` - Marp front-matter reference block (16:9, theme, paginate); documents the toolchain decision inline
- `slides/custom.scss` - Minimal legible-font Marp theme
- `slides/_partials/version-banner.qmd` - Course-reference-environment slide content (copy-paste target)
- `slides/_partials/attribution.qmd` - Verbatim DATA_CARD.md licensing/attribution slide content (copy-paste target)
- `slides/_partials/README.md` - Documents the Marp copy-paste (not include) convention and trim-only-never-reword rule
- `Makefile` - Adds `MARP` variable and `slides` / `slides-pdf` targets

## Decisions Made
- **Toolchain: Marp CLI 4.5.0, not Quarto.** Quarto's `.pkg` installer requires interactive `sudo`; this agent has no TTY/askpass. Marp CLI resolves cleanly via pinned `npx`. This is the deciding fact for 07-02/03/04: those plans must author decks as plain Marp-flavoured Markdown (`slides/NN_*.md`) with Marp front-matter, not `.qmd` files with Quarto revealjs syntax.
- **Partials are copy-pasted, not included**, because Marp has no project-level include mechanism equivalent to Quarto's `{{< include >}}` or `_metadata.yml` auto-pickup. `slides/_partials/README.md` is the canonical instruction sibling plans should follow.
- **No decktape**: Marp's native `--pdf` flag is simpler and sufficient; `make slides-pdf` calls it directly rather than rendering HTML then post-processing with decktape.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Fallback to Marp required (not a bug fix, but a required toolchain substitution anticipated by the plan itself)**
- **Found during:** Task 1 (Quarto verification)
- **Issue:** `brew install --cask quarto` fetched the cask successfully but its underlying installer step (`sudo installer -pkg ... -target /`) failed with `sudo: a password is required` — no interactive terminal is available to this agent to supply a password or configure an askpass helper.
- **Fix:** Followed the plan's own explicit fallback instruction (Task 1's `<action>`): verified `npx --yes @marp-team/marp-cli@4.5.0 --version` resolves, and used Marp CLI for all of this plan's Task 2/3 deliverables (front-matter reference block instead of Quarto's shared metadata, copy-paste partials instead of `{{< include >}}`, Marp's `--pdf` instead of decktape).
- **Files modified:** `slides/_metadata.yml`, `slides/_partials/README.md` (documents the substitution); no code files affected.
- **Verification:** `npx --yes @marp-team/marp-cli@4.5.0 --version` printed `@marp-team/marp-cli v4.5.0 (w/ @marp-team/marp-core v4.4.0)`; `make slides` and `make slides-pdf` both run cleanly (print "no decks found yet" since no decks exist before 07-02).
- **Committed in:** `e519234`, `5d1283c`

---

**Total deviations:** 1 (an explicitly plan-sanctioned fallback path, not an unplanned deviation in the usual sense).
**Impact on plan:** None beyond what the plan itself anticipated. No scope creep — Task 1's acceptance criteria explicitly allowed "the SUMMARY documents the Marp fallback explicitly."

## Issues Encountered
None beyond the Quarto/sudo issue documented above, which the plan had already anticipated and given explicit fallback instructions for.

## User Setup Required
None - no external service configuration required. (Note for the user: if Quarto is ever desired instead of Marp, it must be installed manually via an interactive terminal session — `brew install --cask quarto` and answer the sudo prompt — before any future phase re-attempts the Quarto path.)

## Next Phase Readiness
- Plans 07-02, 07-03, and 07-04 must author decks as Marp Markdown (`slides/NN_*.md`), not Quarto `.qmd`, and must copy-paste (not include) the two partials per `slides/_partials/README.md`.
- `make slides` / `make slides-pdf` are ready to render decks the moment they exist; both currently no-op cleanly with "No decks found yet" since `slides/*.md` is empty.
- `uv run pytest tests/ -q` still passes (167 passed, 3 skipped, 10 deselected) — this plan touched no Python code.

---
*Phase: 07-slide-decks*
*Completed: 2026-09-04*
## Self-Check: PASSED

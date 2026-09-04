---
phase: 07-slide-decks
plan: 04
subsystem: slides
tags: [marp-cli, slides, provenance, capstone, ecosystems]

requires: ["07-01"]
provides:
  - "slides/04_ecosystems.md: Module 5 deck, sourced Provider Comparison table"
  - "slides/05_capstone.md: Module 6/capstone deck with figures and rubric recap"
  - "slides/06_provenance_licensing.md: eighth deck (no source notebook), built from DATA_CARD.md/PROVENANCE_CHECKLIST.md"
affects: []

tech-stack:
  added: []
  patterns:
    - "Decks authored as plain Marp Markdown (.md, not .qmd) per 07-01's toolchain decision"
    - "Partials copy-pasted (version-banner + trimmed attribution) into each deck, per slides/_partials/README.md"

key-files:
  created:
    - slides/04_ecosystems.md
    - slides/05_capstone.md
    - slides/06_provenance_licensing.md
  modified: []

key-decisions:
  - "Deck files are slides/NN_*.md, not the .qmd extension named in the plan's files_modified list, because 07-01 already established Marp as the toolchain for the whole phase (Quarto is not installable non-interactively on this machine)."
  - "05_capstone's WRONG-conclusion slide cites the notebook's own stated range ('roughly 17-19 balanced-accuracy points') rather than the constraint brief's rounded '23', since notebooks/solutions/05_capstone_artificialization.py/.ipynb carries no stored cell output to read an exact number from and the notebook's own prose is the closest sourced figure."
  - "06_provenance_licensing has no WRONG-conclusion slide by design (per the plan); a licensing-caution slide sourced directly from data/DATA_CARD.md's licensing table substitutes for it."

requirements-completed: [SLIDE-01, SLIDE-02, SLIDE-03, SLIDE-04, SLIDE-05]

duration: ~35min
completed: 2026-09-04
---

# Phase 07 Plan 04: Final Three Slide Decks (Ecosystems, Capstone, Provenance/Licensing) Summary

**Authored the last three of the course's eight decks as Marp Markdown — 04_ecosystems with a sourced provider-comparison table, 05_capstone embedding both capstone figures with a rubric recap, and the notebook-less eighth deck 06_provenance_licensing built directly from data/DATA_CARD.md and templates/PROVENANCE_CHECKLIST.md.**

## Performance

- **Duration:** ~35 min
- **Completed:** 2026-09-04
- **Tasks:** 3
- **Files modified:** 3 (all created)

## Accomplishments
- `slides/04_ecosystems.md`: objectives slide, a "Provider Comparison" table populated only with sourced facts (AlphaEarth, TESSERA, Clay/LGND corpus, LGND API measured from the notebook/CLAUDE.md; OlmoEarth and SatCLIP explicitly marked "portability awareness only, not exercised in this course's notebooks"), a WRONG-conclusion slide on cross-provider cosine incomparability, recap, and both shared partials trimmed to AlphaEarth + LGND Clay attribution rows.
- `slides/05_capstone.md`: objectives slide, both `figures/05_prediction_map.png` and `figures/05_uncertainty_margin_hist.png` embedded with captions, a WRONG-conclusion slide citing the notebook's own reported "roughly 17-19 balanced-accuracy points" leave-region-out cost, a recap naming all six capstone rubric dimensions from `assessments/05_capstone_rubric.md` (validation design 30%, reproducibility/provenance 15%, CRS/alignment 15%, interpretation/uncertainty 15%, representation choice 15%, licensing/ethics 10%), and both shared partials trimmed to AlphaEarth + ESA WorldCover + Copernicus HRL.
- `slides/06_provenance_licensing.md`: the eighth deck, with no corresponding solution notebook. Reproduces the DATA_CARD.md provenance field list verbatim, a worked checklist example applying all eight `templates/PROVENANCE_CHECKLIST.md` items to the AlphaEarth table, a licensing-caution slide (CC BY 4.0 attribution obligations) stating the three honest unresolved/notable license findings (TESSERA data license unstated, Copernicus Global Embeddings never bundled due to CDSE portal terms, Clay's four separate licenses across code/weights/docs/embeddings), recap, and the full untrimmed attribution partial plus version-banner partial.

## Task Commits

Each task was committed atomically:

1. **Task 1: 04_ecosystems.md (provider comparison table)** - `05d2712` (feat)
2. **Task 2: 05_capstone.md** - `f29d1e9` (feat)
3. **Task 3: 06_provenance_licensing.md (the eighth deck, no source notebook)** - `add8860` (feat)

**Plan metadata:** (final SUMMARY commit, this file)

## Files Created/Modified
- `slides/04_ecosystems.md` - Module 5 deck (embedding ecosystems)
- `slides/05_capstone.md` - Module 6 deck (capstone artificialization)
- `slides/06_provenance_licensing.md` - Module 7 deck (provenance/licensing, no source notebook)

## Decisions Made
- **File extension: `.md`, not `.qmd`.** The plan's `files_modified` frontmatter listed `.qmd` paths, but 07-01 (a dependency of this plan) already established that Quarto cannot be installed non-interactively on this machine and pinned Marp CLI 4.5.0 as the phase's toolchain. Marp decks are plain Markdown, so all three files were authored as `slides/NN_*.md`. This is consistent with `slides/_partials/README.md`'s explicit instruction to 07-02/03/04 to author decks this way, and with the shared `slides/_metadata.yml` reference block.
- **05_capstone leave-region-out number sourced from notebook prose, not a hardcoded run.** Neither the `.py` nor the `.ipynb` copy of `05_capstone_artificialization` carries stored cell output (notebooks are stripped by the `nbstripout` pre-commit hook per STACK.md), so there is no literal printed number to read. The notebook's own markdown states the measured pattern as "roughly 17-19 balanced-accuracy points" (Module 3's measurement, reused here) — this is the figure the deck cites, deliberately not the constraint brief's rounded "23".
- **06_provenance_licensing has no WRONG-conclusion slide.** Per the plan's explicit instruction, a licensing-caution slide (CC BY 4.0's verbatim-attribution requirement, TESSERA/CDSE/Clay's unresolved or multi-part license findings) substitutes for it, since there is no notebook trap cell to mirror.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Deck files authored as `.md`, not the `.qmd` extension in the plan's frontmatter**
- **Found during:** Task 1 setup (reading `07-01-SUMMARY.md` and `slides/_partials/README.md` before writing any deck)
- **Issue:** The plan's `files_modified` frontmatter names `slides/04_ecosystems.qmd`, `slides/05_capstone.qmd`, `slides/06_provenance_licensing.qmd`, but the plan itself depends on `07-01`, whose SUMMARY documents that Quarto cannot be installed non-interactively on this machine and that Marp CLI (plain Markdown, no `.qmd`) is the toolchain for the rest of the phase.
- **Fix:** Authored all three decks as `slides/NN_*.md` Marp Markdown, following `slides/_metadata.yml`'s front-matter reference block and copy-pasting (not `{{< include >}}`-ing) the two shared partials, per `slides/_partials/README.md`'s explicit instruction to 07-02/03/04.
- **Files modified:** `slides/04_ecosystems.md`, `slides/05_capstone.md`, `slides/06_provenance_licensing.md`
- **Verification:** `make slides` rendered all three decks successfully via the pinned Marp CLI (`slides/*.md => slides/*.html`); the generated HTML build artifacts were removed after verification since no `.gitignore` rule yet exists for them and they are not part of this plan's committed deliverable.
- **Committed in:** `05d2712`, `f29d1e9`, `add8860`

---

**Total deviations:** 1 (a plan-frontmatter/toolchain-decision mismatch, already anticipated and resolved by the dependency plan 07-01).
**Impact on plan:** None on scope or content — only the file extension and Markdown flavor changed, matching the toolchain already in force for sibling plans 07-02 and 07-03.

## Issues Encountered
None beyond the extension deviation documented above.

## User Setup Required
None.

## Verification
- `grep -c "Provider Comparison" slides/04_ecosystems.md` → 2 (heading + reference in recap)
- `grep -c "figures/05_" slides/05_capstone.md` → 2 (both figure embeds)
- `grep -c "course_release" slides/06_provenance_licensing.md` → 1 (provenance field list)
- `make slides` rendered all three decks to HTML without error via the pinned Marp CLI
- `uv run pytest tests/ -q` → 167 passed, 3 skipped, 10 deselected (unchanged from the 07-01 baseline; this plan touched no Python code)

## Next Phase Readiness
All eight decks in the phase's deck set are now assigned across 07-02, 07-03, and this plan (07-04); this plan's three files close out the deck set with the eighth (notebook-less) provenance/licensing deck explicitly present rather than silently dropped.

---
*Phase: 07-slide-decks*
*Completed: 2026-09-04*
## Self-Check: PASSED

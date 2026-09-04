# Narration Script Template

Format contract for every module's `scripts/{NN}_{slug}_SCRIPT.md`. Every
Wave-2 narration-script plan copies this structure verbatim so all eight
scripts are structurally identical and machine-checkable by
`tools/verify_narration_scripts.py`.

**Anchors are re-verified against the live notebook source at check time,
not against a snapshot taken while writing the script.**
`tools/verify_narration_scripts.py` re-derives the current set of markdown
cell headings from `notebooks/solutions/{stem}.py` every time it runs. A
script referencing a heading that does not exist -- because the cell was
reordered, renamed, or deleted after the script was written -- fails the
check. This is intentional: it converts a silent failure that would
otherwise surface mid-recording into a loud one caught by
`uv run pytest tests/test_narration_scripts.py -x`.

**Toolchain note:** decks are Marp-flavoured Markdown
(`slides/NN_*.md`, per the Phase 7 pivot away from Quarto), and speaker
notes there are plain HTML comments (`<!-- ... -->`), not `::: {.notes}`
blocks. This template's `[SLIDE]` anchor syntax targets that real format.

---

## Header block

Every script opens with this block, filled in per module:

```
Module: {module number} — {module slug}
Title: {human-readable module title}
Syllabus minutes: {NN} (see MODULE_MINUTES in tools/verify_narration_scripts.py)
Source notebook: notebooks/solutions/{stem}.py (or "no dedicated notebook" for module 06)
Slide deck: slides/{NN}_{slug}.md
```

If the Phase 7 deck for this module has not been produced yet, search
`.planning/phases/07-slide-decks/*-SUMMARY.md` for its path before writing
this script. If no deck exists yet, write:

```
Slide deck: Phase 7 deck not yet available — script drafted from
notebook/assessments directly.
```

Do not invent a deck path.

**Worked example (module 03):**

```
Module: 03 — similarity_classification
Title: Similarity Search and Classification
Syllabus minutes: 65
Source notebook: notebooks/solutions/02_similarity_and_classification.py
Slide deck: slides/02_similarity_classification.md
```

---

## Per-lecture structure

Each lecture within the module gets a heading, an objective line, a
two-column AV table, a recap line, an end-state line, and a target-length
note.

```
### Lecture {module}.{n} — {title}

Objective: {one sentence: what the student can do after this lecture}

| Duration | Cumulative | VISUAL | AUDIO | Cue |
|----------|------------|--------|-------|-----|
| mm:ss    | mm:ss      | ...    | ...   | ... |

Recap: {one sentence tying back to the objective}
End-state: {what must be on screen at the last frame of this lecture}
```

**Column definitions:**

- **Duration** — `mm:ss`, this row's spoken/on-screen time only.
- **Cumulative** — `mm:ss`, running total since the start of the whole
  module script (not just this lecture). Used to keep the recording on
  pace against the syllabus minutes.
- **VISUAL** — what is on screen, using exactly one of two anchor
  syntaxes:
  - `[CELL] {notebook_stem}.ipynb § "{exact heading text as it appears in the notebook's markdown headings}"`
    for notebook-anchored rows. The heading text must be copied verbatim
    from the notebook's own markdown cell heading (e.g. `# ## Data`
    becomes `"Data"`) — the verifier re-derives the live heading set with
    `grep -n '^# #\{1,3\} '` equivalent logic and fails if the quoted text
    does not match exactly.
  - `[SLIDE] {deck_stem}.md #{n}` for slide-anchored rows, where `{n}` is
    the 1-indexed position of the `---`-delimited slide in the deck
    (counting the title slide as `#1`).
- **AUDIO** — verbatim narration prose: what the narrator reads aloud, not
  a paraphrase instruction or stage direction.
- **Cue** — exactly one of `[RUN CELL]`, `[ZOOM]`, `[PAUSE]`, `[CUT]`,
  `[NONE]`. Any cell or slide that would display a secret value (an env
  var like `LGND_TOKEN`, an Earth Engine project ID) must use `[CUT]`
  immediately before the value is typed or displayed — never `[ZOOM]`
  (see the threat model in `08-01-PLAN.md`, T-08-01).

**Target length:** lectures run 2:00–7:00. Lectures whose heading is
suffixed literally with the text `(codealong)` may run up to 12:00.

**Worked example lecture (module 03, first lecture):**

```
### Lecture 03.1 — Search by example

Objective: run a cosine-similarity search over the frozen AlphaEarth
embedding table and read the resulting similarity distribution honestly.

| Duration | Cumulative | VISUAL | AUDIO | Cue |
|----------|------------|--------|-------|-----|
| 00:45 | 00:45 | [SLIDE] 02_similarity_classification.md #4 | "Every point in this region has a 64-dimensional AlphaEarth vector. Cosine similarity to a single query point gives us this distribution — most of the mass sits well below 1.0, with a tail above 0.90 we're about to probe." | [NONE] |
| 02:30 | 03:15 | [CELL] 02_similarity_and_classification.ipynb § "Similarity 1: Search by example" | "Here's the cell that computes it. We pick one query point, take the dot product against every other embedding in the region — and because AlphaEarth vectors are unit-norm, dot product equals cosine similarity, so no separate normalization step is needed." | [RUN CELL] |
| 01:00 | 04:15 | [CELL] 02_similarity_and_classification.ipynb § "Why this is wrong" | "Before we celebrate a 0.90 cutoff: pick 0.85 or 0.95 instead and the apparent agreement rate changes, even though nothing about the underlying data changed. That's the trap — ranking, plus precision@k, is the honest replacement for an arbitrary threshold." | [ZOOM] |

Recap: cosine similarity ranks candidates; a fixed threshold like 0.90 does
not generalize.
End-state: the similarity histogram and the "why this is wrong" markdown
cell are both visible on screen.
Target length: 2:00–7:00 (not a codealong).
```

---

## Module footer

Every script closes with these four sections, in order:

**1. Totals line** — sums every lecture's Duration column and must equal
the module's syllabus minutes exactly (checked by `check_module_total`):

```
Total: 65:00 (syllabus: 65 minutes)
```

**2. Pronunciation Notes** — bullet list, `term — phonetic guide`. Seeded
list every module starts from (add module-specific terms as needed):

```
## Pronunciation Notes

- AlphaEarth — "AL-fuh urth"
- TESSERA — "teh-SAIR-uh"
- GeoTessera — "JEE-oh teh-SAIR-uh"
- Guadalquivir — "gwah-dahl-kee-VEER"
- EPSG — spelled out, "E-P-S-G"
- precision@k — "precision at k"
```

**3. Key Messages Used** — which of the five canonical verbatim messages
(from `KEY_MESSAGES` in `tools/verify_narration_scripts.py`) this module's
script quotes. Assign per module in each Wave-2 plan, not here; module 03
must carry the unit-norm/cosine message and the leave-region-out cost
numbers:

```
## Key Messages Used

- "AlphaEarth vectors are unit-norm, so dot product equals cosine" (Lecture 03.1)
- "17-19 points" (Lecture 03.4, leave-region-out cost)
```

**4. Exercise/Quiz Callback** — the exact `assessments/*.md` file(s) this
module's script references (SCRIPT-05):

```
## Exercise/Quiz Callback

See assessments/03_similarity_classification_quiz.md, question 2
(random-split vs. leave-region-out).
```

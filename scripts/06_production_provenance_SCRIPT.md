Module: 06 — production_provenance
Title: Production, Provenance and Licensing
Syllabus minutes: 45 (see MODULE_MINUTES in tools/verify_narration_scripts.py)
Source notebook: no dedicated notebook -- extends `templates/MODEL_DATA_CARD_TEMPLATE.md`,
  `templates/PROVENANCE_CHECKLIST.md`, and prior modules' own "Provenance" cells.
  `[DOC]` anchors below are re-checked by `tools/verify_narration_scripts.py`'s
  `check_anchors_exist` the same way `[CELL]` anchors are, but load headings
  directly from the named file path (any file) rather than from
  `notebooks/solutions/{stem}.py`.
Slide deck: slides/06_provenance_licensing.md

---

### Lecture 06.1 — Why this module has no notebook

Objective: explain that provenance and licensing are a documentation and
judgment discipline this course teaches through the artifacts it already
ships, not a code exercise.

| Duration | Cumulative | VISUAL | AUDIO | Cue |
|----------|------------|--------|-------|-----|
| 00:45 | 00:45 | [SLIDE] 06_provenance_licensing.md #1 | "Every other module in this course opens with a solution notebook. This one doesn't -- because provenance and licensing aren't a cell you run, they're a habit you check before you ship anything. We're going to build that habit against artifacts this course already produced: a real data card and a reusable checklist." | [NONE] |
| 02:15 | 03:00 | [SLIDE] 06_provenance_licensing.md #2 | "By the end you'll know exactly what provenance a frozen teaching dataset must carry, where it physically lives -- twice, not once -- and which licenses require which attribution string verbatim. You'll also see what happens when a license check comes back unclear instead of clean, because that outcome is going to happen to you, and it is a valid outcome, not a failure of the checklist." | [NONE] |

Recap: this module trades a notebook for two real artifacts -- the data
card and the checklist -- because the skill being taught is judgment, not
syntax.
End-state: the "What you will learn" slide is on screen with both learning
outcomes visible.
Target length: 2:00-7:00 (not a codealong).

---

### Lecture 06.2 — Provenance lives in two places

Objective: locate provenance metadata in both its machine-readable and
human-readable homes for a real course table.

| Duration | Cumulative | VISUAL | AUDIO | Cue |
|----------|------------|--------|-------|-----|
| 02:00 | 05:00 | [DOC] templates/MODEL_DATA_CARD_TEMPLATE.md § "Provenance" | "Provenance for any artifact in this course lives in two places at once, and both are required. First: inside the Parquet file itself, as a `course_provenance` JSON dict in the schema's key-value metadata -- source URL, dataset version, extraction date, CRS, label source, license, attribution, creator. Read it back with `pyarrow.parquet.read_table(path).schema.metadata`." | [NONE] |
| 03:00 | 08:00 | [CELL] 02_similarity_and_classification.ipynb § "Provenance" | "Here's that pattern in a module you've already seen run. This cell writes the same provenance dict this course's own frozen tables carry -- so the metadata survives even if a student loses the accompanying markdown file or copies the table somewhere else. Notice it's built by `build_provenance`, never hand-typed." | [ZOOM] |
| 02:00 | 10:00 | [DOC] data/DATA_CARD.md § "Provenance" | "Second: the human-readable side, `DATA_CARD.md`, sitting right next to the data. This project's own card documents six frozen tables across Bern and Seville, a clip raster, and a Clay corpus fixture -- with a sibling `manifest.json` carrying the sha256 checksum, row count, and builder git SHA for every table. Neither copy substitutes for the other." | [NONE] |

Recap: the same provenance facts are recorded twice -- inside the file's
own metadata, and in a human-readable card next to it.
End-state: `data/DATA_CARD.md`'s Provenance section is visible on screen.
Target length: 2:00-7:00 (not a codealong).

---

### Lecture 06.3 — The eight-item checklist, worked

Objective: apply the provenance checklist to a real, completed artifact
rather than a template still full of placeholders.

| Duration | Cumulative | VISUAL | AUDIO | Cue |
|----------|------------|--------|-------|-----|
| 02:00 | 12:00 | [DOC] templates/PROVENANCE_CHECKLIST.md § "Provenance Checklist" | "Eight yes/no questions, applied to one artifact at a time: is the source documented, is the license identified, is attribution copied verbatim, are `label_source` and `validation_source` two genuinely distinct strings, is the CRS recorded, is a version or checksum recorded, is the representation trade-off stated, and is there a false-positive-cost statement." | [NONE] |
| 03:00 | 15:00 | [SLIDE] 06_provenance_licensing.md #4 | "Here it is applied, fully, to this course's own AlphaEarth table: source is `GOOGLE/SATELLITE_EMBEDDING/V1/ANNUAL` at `DATASET_VERSION` 1.1; license is CC BY 4.0; attribution is copied character-for-character; `label_source` is `esa_worldcover_2021` and `validation_source` is `eea_hrl_imperviousness_2018` -- two independently derived products, never the same one twice." | [ZOOM] |
| 02:00 | 17:00 | [DOC] templates/PROVENANCE_CHECKLIST.md § "Pitfall 6: label_source vs validation_source" | "That last distinction matters enough to name as its own pitfall: validating a learned product against another learned product derived from the same upstream classifier isn't independent validation, no matter how good the agreement looks. `label_source` and `validation_source` must always name two distinct upstream products." | [NONE] |

Recap: every checklist item must be answerable yes or no for one specific
artifact -- "probably" or "assumed from a similar dataset" doesn't count.
End-state: the completed eight-row checklist table for the AlphaEarth
table is visible.
Target length: 2:00-7:00 (not a codealong).

---

### Lecture 06.4 — Representation choice and worked provenance callbacks

Objective: connect the model/data-card template's representation-choice
section to how each prior module actually recorded its own provenance.

| Duration | Cumulative | VISUAL | AUDIO | Cue |
|----------|------------|--------|-------|-----|
| 02:00 | 19:00 | [DOC] templates/MODEL_DATA_CARD_TEMPLATE.md § "Representation Choice" | "The card template asks you to name the embedding representation used, the alternatives you considered, and why -- dimensionality, coverage, license, cost, latency -- plus the known trade-off you accepted. This is the same trade-off framing you saw argued live in Module 5's TESSERA-versus-AlphaEarth comparison." | [NONE] |
| 02:30 | 21:30 | [CELL] 03_change_detection_and_validation.ipynb § "Provenance" | "Module 3's own Provenance cell is another worked example: same `course_provenance` dict shape, same `build_provenance`/`write_provenance` helpers, applied to the change-detection tables instead of the similarity ones. The pattern doesn't change between modules -- only the data does." | [ZOOM] |
| 02:30 | 24:00 | [CELL] 04_embedding_ecosystems.ipynb § "Provenance" | "And Module 5's Provenance cell closes the loop again for the Clay and TESSERA fixtures. Three modules, three different embedding products, one identical provenance discipline -- that repetition is the point: provenance isn't optional polish added at the end, it's built the same way every single time." | [ZOOM] |

Recap: the representation-choice question and the provenance-recording
pattern repeat identically across every module -- only the underlying
product changes.
End-state: Module 5's Provenance cell is on screen, ecosystems fixtures
visible.
Target length: 2:00-7:00 (not a codealong).

---

### Lecture 06.5 — Licensing caution: when a check does not resolve cleanly

Objective: treat an unresolved or restrictive license finding as a valid,
reportable outcome rather than a failure of the checklist.

| Duration | Cumulative | VISUAL | AUDIO | Cue |
|----------|------------|--------|-------|-----|
| 01:00 | 25:00 | [SLIDE] 06_provenance_licensing.md #5 | "CC BY 4.0 permits redistribution and adaptation, but the verbatim attribution string is still required -- omitting it is a license violation even if the data itself is untouched. Now the harder cases: three licensing checks in this course genuinely did not resolve cleanly." | [NONE] |
| 02:00 | 27:00 | [DOC] templates/PROVENANCE_CHECKLIST.md § "Reference table: exact verbatim attribution strings" | "TESSERA's software -- `geotessera` and `tessera` -- is MIT-licensed, but the embedding data itself has no stated license anywhere in the docs or README. This course does not invent one. It reports the gap and withholds redistribution of TESSERA-derived samples until the maintainers confirm terms." | [ZOOM] |
| 02:00 | 29:00 | [DOC] templates/PROVENANCE_CHECKLIST.md § "Reference table: exact verbatim attribution strings" | "Copernicus Global Embeddings via CDSE have no stated license, and CDSE's own portal terms prohibit redistributing portal material outright. This course never bundles them -- no frozen column anywhere in `data/` comes from CDSE. Any future use has to be a live, opt-in notebook cell under the student's own credentials, never a frozen artifact. That's a licence check correctly returning 'do not redistribute' -- a real outcome, not a failure." | [NONE] |
| 02:00 | 31:00 | [SLIDE] 06_provenance_licensing.md #5 | "And Clay -- code, weights, docs, and released embeddings -- carries four different licenses across those four artifact types. Asking 'is Clay open' isn't one question. It's four, and you have to check all four before you reuse any of it." | [NONE] |

Recap: a license check that returns "unstated" or "do not redistribute" is
a successful, honest checklist outcome, not a gap to paper over.
End-state: the licensing-caution slide with all three unresolved findings
is visible.
Target length: 2:00-7:00 (not a codealong).

---

### Lecture 06.6 — Ethics: naming who bears the cost

Objective: state, concretely, who bears the cost of an error from this
course's downstream classification use, and how sensitive inferred labels
compare to the imagery they came from.

| Duration | Cumulative | VISUAL | AUDIO | Cue |
|----------|------------|--------|-------|-----|
| 03:30 | 34:30 | [DOC] templates/MODEL_DATA_CARD_TEMPLATE.md § "Ethics Statement" | "The card template's last section asks two questions directly: who bears the cost of a false positive from this artifact's downstream use, and is the inferred information more sensitive than the underlying imagery. Answer both concretely -- 'consider the impact' is not an acceptable answer, and neither is silence." | [NONE] |
| 03:30 | 38:00 | [SLIDE] 06_provenance_licensing.md #4 | "For this course's own artifacts: a false 'artificialized' flag on someone's land can trigger real regulatory or compliance consequences for that landowner -- that's who bears the cost, named specifically, not abstractly. And the inferred label itself -- 'this parcel became built-up' -- is more sensitive than the raw pixels it came from, because it implies a judgment the imagery alone does not make. This is exactly the ethics row the capstone rubric grades, and it isn't generic -- it names who is affected and why." | [ZOOM] |

Recap: ethics content in this course names a specific harmed party and a
specific sensitivity gap, never a generic "be careful" disclaimer.
End-state: the ethics answer for the AlphaEarth-derived classification use
is visible on screen.
Target length: 2:00-7:00 (not a codealong).

---

### Lecture 06.7 — Recap and version pinning

Objective: tie the module's checklist discipline back to why this course
pins dataset and library versions at all.

| Duration | Cumulative | VISUAL | AUDIO | Cue |
|----------|------------|--------|-------|-----|
| 02:30 | 40:30 | [SLIDE] 06_provenance_licensing.md #6 | "Provenance lives in two places, neither substitutes for the other. The checklist applies one artifact at a time, every item answered yes or no. License checks sometimes resolve cleanly -- AlphaEarth, WorldCover, Clay's open corpus -- and sometimes they don't -- TESSERA's data license, CDSE. Both outcomes are valid, provided you report them honestly." | [NONE] |
| 02:30 | 43:00 | [SLIDE] 06_provenance_licensing.md #7 | "Course reference environment: 2026-08 release. AlphaEarth's `DATASET_VERSION` 1.1 and GeoTessera's `v1.1`/`cambridge` variant are recorded here so a student re-running these notebooks a year from now gets the exact same embeddings we used to build every figure and label in this course -- not a newer revision that silently changed underneath them." | [NONE] |
| 02:00 | 45:00 | [SLIDE] 06_provenance_licensing.md #8 | "This is deliberately the one deck in the course where every attribution row is kept, untrimmed -- all five licensed sources this project bundles, plus the two it explicitly declines to. Every quantitative and visual claim across every other module traces back to one of these rows via `data/DATA_CARD.md`." | [ZOOM] |

Recap: version pinning and honest license reporting are the same
discipline applied at different scales -- both protect a student's future
re-run from silently changing underneath them.
End-state: the full attribution-and-licenses slide is on screen.
Target length: 2:00-7:00 (not a codealong).

---

Total: 45:00 (syllabus: 45 minutes)

## Pronunciation Notes

- AlphaEarth — "AL-fuh urth"
- TESSERA — "teh-SAIR-uh"
- GeoTessera — "JEE-oh teh-SAIR-uh"
- Guadalquivir — "gwah-dahl-kee-VEER"
- EPSG — spelled out, "E-P-S-G"
- precision@k — "precision at k"
- CDSE — spelled out, "C-D-S-E"
- WorldCover — "WORLD-cover", one compound word

## Key Messages Used

None of the five canonical KEY_MESSAGES are specific to this module's
content; this module's callbacks (Lecture 06.4) instead cite prior
modules' own Provenance cells by anchor.

## Exercise/Quiz Callback

See `assessments/05_capstone_rubric.md`'s Licensing and ethics criterion
(10% weight) — this module's checklist and ethics-statement discipline is
exactly what that rubric row grades against.

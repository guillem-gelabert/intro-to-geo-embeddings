Module: 01 — foundations
Title: Representations — Pixel, Patch and Location Embeddings
Syllabus minutes: 35 (see MODULE_MINUTES in tools/verify_narration_scripts.py)
Source notebook: notebooks/solutions/00b_representation_inspection.py
Slide deck: slides/00b_representation_inspection.md

---

### Lecture 01.1 — Welcome and the taxonomy of embedding shapes

Objective: name the three embedding "shapes" this module compares — pixel, patch, and location — and confirm no Earth Engine account or torch install is required.

| Duration | Cumulative | VISUAL | AUDIO | Cue |
|----------|------------|--------|-------|-----|
| 01:30 | 01:30 | [SLIDE] 00b_representation_inspection.md #1 | "This notebook inspects the same real-world location through three different embedding shapes before we go deeper into any single one. AlphaEarth, Clay, and SatCLIP are not competing brands of the same thing — they describe different spatial units and different temporal support, and mixing them up is the easiest way to draw a wrong conclusion from an embedding." | [NONE] |
| 01:30 | 03:00 | [SLIDE] 00b_representation_inspection.md #2 | "Four things by the end: load a 64-dimensional AlphaEarth pixel embedding for one point, load a 1024-dimensional Clay patch embedding for a nearby location, compare shape, spatial unit, temporal support and metadata side by side, and optionally load a SatCLIP location embedding if torch happens to be installed." | [NONE] |
| 02:00 | 05:00 | [CELL] 00b_representation_inspection.ipynb § "What you will learn" | "No Earth Engine account is needed for this notebook, and torch is optional — only the last, clearly marked section touches it, and it degrades gracefully when torch is absent, which is the default in this course's reference environment." | [NONE] |

Recap: this module compares pixel, patch, and location embeddings, and needs neither an Earth Engine account nor torch to run.
End-state: the four numbered objectives and the prerequisite table are visible on screen.
Target length: 2:00–7:00 (not a codealong).

---

### Lecture 01.2 — The AlphaEarth pixel vector

Objective: load one real AlphaEarth pixel embedding and state its shape, spatial unit, and temporal support precisely.

| Duration | Cumulative | VISUAL | AUDIO | Cue |
|----------|------------|--------|-------|-----|
| 01:00 | 01:00 | [SLIDE] 00b_representation_inspection.md #3 | "AlphaEarth, also called Google Satellite Embedding, produces one 64-dimensional vector per 10-metre pixel, per calendar year. It is a pixel embedding — the smallest spatial unit we'll see in this module, and the only one with a fixed annual cadence." | [NONE] |
| 05:00 | 06:00 | [CELL] 00b_representation_inspection.ipynb § "The AlphaEarth pixel vector" | "This loads one row from the frozen Bern sample for 2024 and pulls out its 64 AlphaEarth columns. Shape: 64. The L2 norm printed here is close to 1 because these vectors ship unit-normalized. Spatial unit: one 10-metre pixel. Temporal support: one calendar-year composite, 2024 — a single number describing an entire year at that pixel, not a snapshot of one day. And to be precise about what this vector is not: it's a single point in a 64-dimensional space with no independently interpretable axis — that's the subject of the next notebook." | [RUN CELL] |

Recap: an AlphaEarth vector is a 64-D, unit-norm, per-pixel, per-calendar-year embedding with no independently interpretable axis.
End-state: the printed vector shape, L2 norm, spatial unit, and temporal support lines are all visible on screen.
Target length: 2:00–7:00 (not a codealong).

---

### Lecture 01.3 — The Clay patch embedding

Objective: load one real Clay patch embedding from the frozen fixture and contrast its spatial unit and temporal support with the AlphaEarth pixel vector.

| Duration | Cumulative | VISUAL | AUDIO | Cue |
|----------|------------|--------|-------|-----|
| 01:00 | 01:00 | [SLIDE] 00b_representation_inspection.md #4 | "Clay, distributed through the open LGND corpus, produces one 1024-dimensional vector per Sentinel-2 L2A scene, per MajorTOM patch. It's a patch embedding: a much larger footprint than a single AlphaEarth pixel, and tied to one observation rather than a yearly composite." | [NONE] |
| 06:00 | 07:00 | [CELL] 00b_representation_inspection.ipynb § "The Clay patch embedding" | "This reads a frozen Clay sample fixture — not a live query — and pulls its embedding column. Shape: 1024, roughly sixteen times wider than the AlphaEarth vector. Spatial unit: one Sentinel-2 patch, a MajorTOM cell, about 2,560 metres on a side. Temporal support: one Sentinel-2 L2A scene at a specific timestamp, not a yearly composite. The provenance JSON alongside the fixture records exactly where this sample came from, which we always keep next to frozen course data. The takeaway: 'the same location' means something different for a pixel vector than for a patch embedding." | [RUN CELL] |

Recap: a Clay patch embedding is 1024-D, covers a much wider footprint, and describes one scene, not one year.
End-state: the printed Clay embedding shape, L2 norm, spatial unit, temporal support, and the provenance JSON block are all visible on screen.
Target length: 2:00–7:00 (not a codealong).

---

### Lecture 01.4 — Side-by-side comparison

Objective: read a comparison table of dims, spatial unit, temporal support, and source across AlphaEarth and Clay, and state the central conceptual trap of this module.

| Duration | Cumulative | VISUAL | AUDIO | Cue |
|----------|------------|--------|-------|-----|
| 01:00 | 01:00 | [SLIDE] 00b_representation_inspection.md #5 | "Here's the central trap of this module: a latent axis does not measure a physical quantity. Component 17 of an AlphaEarth vector is not NDVI, and no single axis in any of these embeddings is 'the vegetation axis' or 'the moisture axis.' What we can say is narrower and more honest: this axis, or this component, separates these landscape types in this sample." | [NONE] |
| 05:00 | 06:00 | [CELL] 00b_representation_inspection.ipynb § "Side-by-side comparison" | "This table puts AlphaEarth and Clay next to each other: dims — 64 versus 1024; spatial unit — one 10-metre pixel versus one 2,560-metre MajorTOM patch; temporal support — a calendar-year composite versus a single scene timestamp; and source. Shape and spatial unit are the first two things to check before you combine or compare embeddings from different providers — Module 5 revisits this same question with TESSERA and OlmoEarth." | [RUN CELL] |

Recap: shape and spatial unit must be checked before comparing embeddings across providers; a latent axis is never a named physical quantity.
End-state: the four-column comparison table (dims, spatial unit, temporal support, source) for both AlphaEarth and Clay is visible on screen.
Target length: 2:00–7:00 (not a codealong).

---

### Lecture 01.5 — Optional: SatCLIP location embedding

Objective: describe what a location embedding is and why this section does not execute a live SatCLIP model in the reference environment.

| Duration | Cumulative | VISUAL | AUDIO | Cue |
|----------|------------|--------|-------|-----|
| 02:00 | 02:00 | [SLIDE] 00b_representation_inspection.md #6 | "SatCLIP, pronounced 'sat-clip,' produces a location embedding: derived from coordinates alone — longitude and latitude, sometimes with a target resolution — with no observation date at all. It knows nothing about what happened at a place this year. That's the tradeoff for needing no imagery at all to query it." | [NONE] |
| 03:00 | 05:00 | [CELL] 00b_representation_inspection.ipynb § "Optional: SatCLIP location embedding" | "torch is intentionally kept out of this course's core install, so in this reference environment this cell prints a skip message rather than loading a model — that's expected, not a bug. Even in an environment where torch is installed, this branch is illustrative only: no SatCLIP weights ship with this course, so what you'd see is a placeholder shape, not a real forward pass through a real checkpoint. A genuine walkthrough lives in the separate, torch-enabled environment referenced in the technology-stack docs." | [RUN CELL] |

Recap: a location embedding needs only coordinates and no imagery; this section's torch branch is optional and, when it runs at all, illustrative rather than a real model pass.
End-state: the "torch is not installed — skipping the SatCLIP section" message (or, if torch is present, the placeholder-shape message) is visible on screen.
Target length: 2:00–7:00 (not a codealong).

---

### Lecture 01.6 — Wrap-up

Objective: recap the three representation takeaways and point to the quiz for self-check.

| Duration | Cumulative | VISUAL | AUDIO | Cue |
|----------|------------|--------|-------|-----|
| 02:00 | 02:00 | [CELL] 00b_representation_inspection.ipynb § "Wrap-up" | "Three takeaways: the AlphaEarth vector is a single point in a 64-D space describing one 10-metre pixel for one calendar year, with no independently interpretable axis; a Clay patch embedding covers a much larger area and a single scene, so 'the same location' means something different for a pixel vector than for a patch embedding; and shape plus spatial unit are the first two things to check before combining or comparing embeddings from different providers." | [NONE] |
| 02:00 | 04:00 | [SLIDE] 00b_representation_inspection.md #7 | "Same version-pin discipline as every module: we record the exact AlphaEarth DATASET_VERSION and GeoTessera dataset_version and variant used to build every figure here, because unpinned datasets and libraries rot." | [NONE] |
| 02:00 | 06:00 | [SLIDE] 00b_representation_inspection.md #8 | "The AlphaEarth Foundations Satellite Embedding dataset is produced by Google and Google DeepMind, licensed CC BY 4.0; the Clay v1.5 Sentinel-2 L2A corpus is distributed by LGND on Source Cooperative, also CC BY 4.0. Next up: `01_alphaearth_access_visualize.ipynb` goes deeper on the AlphaEarth pixel embedding alone. If you want to check your understanding first, work through the representation quiz." | [NONE] |

Recap: pixel, patch, and location embeddings differ in shape, spatial unit, and temporal support, and none of their axes is a named physical quantity.
End-state: the wrap-up takeaway list, the version-pin note, and the attribution/forward-pointer slide are all visible on screen.
Target length: 2:00–7:00 (not a codealong).

---

Total: 35:00 (syllabus: 35 minutes)

## Pronunciation Notes

- AlphaEarth — "AL-fuh urth"
- Clay — as spelled, "clay" (one syllable; not an acronym)
- SatCLIP — "sat-clip"
- EPSG — spelled out, "E-P-S-G" (used only in passing when describing coordinate systems shared with other modules)

## Key Messages Used

None of the five canonical messages apply to this module — it compares embedding shapes (pixel/patch/location) and does not touch cosine/unit-norm search, leave-region-out costs, 1-minus-cosine distance, or Dynamic World validation.

## Exercise/Quiz Callback

See assessments/00b_representation_quiz.md.

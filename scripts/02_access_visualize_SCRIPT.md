Module: 02 — access_visualize
Title: Accessing and Visualizing AlphaEarth
Syllabus minutes: 50
Source notebook: notebooks/solutions/01_alphaearth_access_visualize.py
Slide deck: slides/01_access_visualize.md

---

### Lecture 02.1 — Two paths to the same data

Objective: state which two access paths reach AlphaEarth in this module and pick the right one before touching any code.

| Duration | Cumulative | VISUAL | AUDIO | Cue |
|----------|------------|--------|-------|-----|
| 00:45 | 00:45 | [SLIDE] 01_access_visualize.md #1 | "Module 2 is about getting AlphaEarth — the Google Satellite Embedding product — onto your screen two different ways: directly from Earth Engine if you have a registered project, or with zero credentials from a small bundled file. Every cloud step in this course has an offline fallback, and this is the notebook where that pattern is introduced." | [NONE] |
| 01:15 | 02:00 | [SLIDE] 01_access_visualize.md #2 | "By the end of this module you'll be able to load the AlphaEarth image collection from Earth Engine, read the same embedding anonymously straight off the underlying cloud raster with no Earth Engine account at all, dequantize the int8-quantized values correctly, and build a pseudo-RGB and a PCA composite from them. The Earth Engine account is explicitly optional — everything conceptual in this module is reachable through the offline path alone." | [NONE] |
| 02:00 | 04:00 | [SLIDE] 01_access_visualize.md #3 | "Here's the decision flowchart. If you have a registered Earth Engine project, that's Path A — live `ee.Initialize`. If you don't, but you still want pixel-level windows rather than the full Earth Engine API, there's Path A-prime: an anonymous `rasterio` read straight off the public cloud bucket, no account needed. And if you just want the frozen course data with zero network access at all, that's Path B — the bundled clip this notebook actually runs by default. All three reach the same underlying AlphaEarth values." | [ZOOM] |

Recap: three access paths exist for the same AlphaEarth product, and only one of them — Path B — is required to follow the rest of this course.
End-state: the decision flowchart is on screen with all three paths visible.
Target length: 2:00–7:00 (not a codealong).

---

### Lecture 02.2 — Path A: the live Earth Engine walkthrough (illustrative only) (codealong)

Objective: read the Path A code as a reference for students with a registered Earth Engine project, without claiming it was run live on camera.

| Duration | Cumulative | VISUAL | AUDIO | Cue |
|----------|------------|--------|-------|-----|
| 00:30 | 04:30 | [CELL] 01_alphaearth_access_visualize.ipynb § "Path A: Live Earth Engine access (optional, requires a registered project)" | "Here is what Path A looks like if you have registered an Earth Engine project. To be clear up front: this cell is shown but not executed on camera — it's tagged `skip-execution` in the notebook itself, because this course's own automated checks don't hold an Earth Engine account either. Treat this as a reference walkthrough, not a live demo." | [NONE] |
| 03:00 | 07:30 | [CELL] 01_alphaearth_access_visualize.ipynb § "Path A: Live Earth Engine access (optional, requires a registered project)" | "The first block authenticates with `ee.Initialize(project=...)`, wrapped in a try/except so a missing account fails loudly and clearly rather than crashing the notebook. Then it builds the AlphaEarth image collection, filters it to the Bern area of interest and the 2024 date range, and takes the first image. Printing `bandNames()` should show sixty-four bands named A00 through A63, and the `DATASET_VERSION` property should read 1.1 — that's the same version pin used throughout this course." | [ZOOM] |
| 01:00 | 08:30 | [CELL] 01_alphaearth_access_visualize.ipynb § "Path A: Live Earth Engine access (optional, requires a registered project)" | "The project ID itself comes from an environment variable, never a hardcoded string — the notebook's own comment is explicit that you should never hardcode a real project ID or credential here. We're cutting away before that value would ever be typed or displayed on screen." | [CUT] |
| 04:00 | 12:30 | [CELL] 01_alphaearth_access_visualize.ipynb § "Path A: Live Earth Engine access (optional, requires a registered project)" | "Next, `geemap` builds an interactive map and adds the AlphaEarth image with three chosen bands as a display composite — A01, A16, A09, stretched to minus-0.3 to 0.3. That range is a display stretch for visualization only, not a physical reflectance range, and the notebook is careful to say these bands are illustrative only — it makes no claim about what any single axis means. Finally, `sampleRegions` pulls a table of embedding values at a single point, deliberately small, because Earth Engine's `getInfo` aborts past five thousand elements." | [ZOOM] |
| 03:30 | 16:00 | [CELL] 01_alphaearth_access_visualize.ipynb § "Path A: Live Earth Engine access (optional, requires a registered project)" | "For a real export at scale, the notebook shows — but again does not run — a batch export task rather than `getInfo`, since `getInfo` is meant for small interactive results, not production exports. That's the entire Path A reference. If you don't have a registered project, none of this blocks you — everything from here forward runs on Path B instead." | [NONE] |

Recap: Path A is a real, working access pattern for students with a registered Earth Engine project, but it is narrated, not executed, in this recording.
End-state: the Path A code cell is on screen with the export-task comment visible, no credential ever shown.
Target length: 2:00–12:00 (codealong).

---

### Lecture 02.3 — Path B: offline access from the bundled clip

Objective: read AlphaEarth data from a checked-in file with zero network access and zero credentials.

| Duration | Cumulative | VISUAL | AUDIO | Cue |
|----------|------------|--------|-------|-----|
| 01:00 | 17:00 | [CELL] 01_alphaearth_access_visualize.ipynb § "Path B: Offline access from the bundled clip (no credentials needed)" | "Path B reaches the identical conclusions as Path A — sixty-four band embeddings, dequantized to unit-norm vectors, displayed as pseudo-RGB, explored with PCA — using only a small raw int8 COG GeoTIFF that's checked directly into this repository. No network access, no account, no quota. This is the path this notebook actually runs by default, and it's the one every student can run regardless of their Earth Engine status." | [NONE] |
| 02:30 | 19:30 | [CELL] 01_alphaearth_access_visualize.ipynb § "Path B: Offline access from the bundled clip (no credentials needed)" | "`rasterio.open` reads the clip directly off disk — no GCS, no signed request, nothing. `ds.read()` gives us a band-first array, sixty-four bands by height by width, still in raw int8. We also read the CRS and the nodata value, which is minus 128 for this product — that's the sentinel this dataset uses for masked-out pixels, and we'll need to exclude it before any of the later math." | [RUN CELL] |
| 02:30 | 22:00 | [CELL] 01_alphaearth_access_visualize.ipynb § "Path B: Offline access from the bundled clip (no credentials needed)" | "Alongside the raster sits a provenance JSON file, and we load it here rather than retype anything by hand — dataset version, source license, and the exact attribution string all come from that file, not from memory. That habit of reusing the recorded provenance instead of re-deriving it shows up throughout this course." | [ZOOM] |

Recap: Path B is the credential-free, network-free default this notebook actually runs, and it reaches the same conclusions as Path A.
End-state: the printed `raw.shape`, `raw.dtype`, `crs`, `nodata`, and provenance dictionary are all visible on screen.
Target length: 2:00–7:00 (not a codealong).

---

### Lecture 02.4 — The int8 dequantization formula

Objective: convert AlphaEarth's raw int8 storage into a real embedding vector without silently corrupting it.

| Duration | Cumulative | VISUAL | AUDIO | Cue |
|----------|------------|--------|-------|-----|
| 01:30 | 23:30 | [CELL] 01_alphaearth_access_visualize.ipynb § "The int8 dequantization formula" | "AlphaEarth ships each band as a signed 8-bit integer — not a float, and not a linear encoding either. Recovering the real embedding value requires this formula: divide by 127.5, square it, then multiply by the sign of the original value. Skip this step, or average the raw int8 values directly, and the quantization's non-linearity silently corrupts the data — there's no error message, just a wrong number." | [NONE] |
| 03:00 | 26:30 | [CELL] 01_alphaearth_access_visualize.ipynb § "The int8 dequantization formula" | "`dequantize_aef` is the one place this formula lives in the whole course — everything else imports it rather than reimplementing it. Below that, the notebook walks the formula by hand on a single real pixel: raw int8 values, then divided by 127.5, then squared, then signed, then the pre-renormalization L2 norm, then the final unit-norm result — and it asserts that hand-rolled result matches what `dequantize_aef` produces at that exact pixel. Seeing the intermediate numbers, not just the final call, is the point of this cell." | [RUN CELL] |
| 01:30 | 28:00 | [CELL] 01_alphaearth_access_visualize.ipynb § "The int8 dequantization formula" | "One habit to take away here: whenever you see raw AlphaEarth int8 values in any notebook or script, dequantize first — this formula, then an L2 renormalization along the band axis — before doing any arithmetic on them at all." | [ZOOM] |

Recap: AlphaEarth's int8 storage requires a specific non-linear formula, not a simple divide, to recover a usable embedding vector.
End-state: the by-hand walkthrough's printed intermediate values and the final `np.allclose` match assertion are visible on screen.
Target length: 2:00–7:00 (not a codealong).

---

### Lecture 02.5 — Unit-norm check

Objective: confirm every valid dequantized pixel is a unit vector, and state why that property matters later in the course.

| Duration | Cumulative | VISUAL | AUDIO | Cue |
|----------|------------|--------|-------|-----|
| 01:30 | 29:30 | [CELL] 01_alphaearth_access_visualize.ipynb § "Unit-norm check" | "Now we check something that isn't obvious just from looking at the numbers: after dequantization, is every pixel actually a unit vector? We compute the L2 norm along the band axis for every pixel, then separate out the valid ones — the ones that aren't nodata — before asserting anything." | [NONE] |
| 02:30 | 32:00 | [CELL] 01_alphaearth_access_visualize.ipynb § "Unit-norm check" | "The assertion passes: every valid pixel in this clip is a unit vector once dequantized, exactly like the point tables `02_similarity_and_classification.ipynb` uses. And here's why that matters beyond this one notebook — AlphaEarth vectors are unit-norm, so dot product equals cosine, which is exactly the shortcut the similarity-search module relies on. It also means averaging raw, pre-dequantization int8 values instead of these unit vectors would silently corrupt the result, because the quantization step is non-linear." | [RUN CELL] |

Recap: unit-norm holds for every valid dequantized pixel, and that property is what lets dot product substitute for cosine similarity later in the course.
End-state: the "valid pixels: N / total" print and the passed assertion are both visible on screen.
Target length: 2:00–7:00 (not a codealong).

---

### Lecture 02.6 — Static pseudo-RGB

Objective: build a pseudo-RGB composite from three embedding axes and state plainly why it is not a true-color image.

| Duration | Cumulative | VISUAL | AUDIO | Cue |
|----------|------------|--------|-------|-----|
| 01:30 | 33:30 | [CELL] 01_alphaearth_access_visualize.ipynb § "Static pseudo-RGB" | "We're reusing the same illustrative band triple as Path A — A01, A16, A09 — stretched to minus-0.3 to 0.3 for display only. That range is a display stretch, not a physical reflectance range, and these three channels carry no RGB meaning; they're just three of the embedding's sixty-four axes, chosen because they happen to display well, not because they correspond to red, green, and blue light." | [NONE] |
| 02:30 | 36:00 | [CELL] 01_alphaearth_access_visualize.ipynb § "Static pseudo-RGB" | "The code selects those three bands, transposes into height-by-width-by-channel order for matplotlib, clips the stretched range into zero-to-one, and renders it. Ask yourself the question the notebook poses here: why does this map look geographically structured at all, if the three axes have no assigned RGB meaning?" | [RUN CELL] |
| 02:00 | 38:00 | [SLIDE] 01_access_visualize.md #4 | "Here's that same pseudo-RGB composite on the slide. Roads, fields, and built-up areas are visually distinguishable — but hold that observation, because the next section explains exactly why that structure appears without any single band carrying a labeled physical meaning." | [ZOOM] |

Recap: a pseudo-RGB composite is a display convenience over three chosen embedding axes, never a true-color or physically-labeled image.
End-state: the pseudo-RGB figure is on screen, framed as a display stretch rather than a reflectance image.
Target length: 2:00–7:00 (not a codealong).

---

### Lecture 02.7 — PCA on the clip and the labeling trap

Objective: run PCA on the clip's embeddings and state the labeling trap the notebook and quiz both test explicitly.

| Duration | Cumulative | VISUAL | AUDIO | Cue |
|----------|------------|--------|-------|-----|
| 01:30 | 39:30 | [CELL] 01_alphaearth_access_visualize.ipynb § "PCA on the clip" | "This section fits PCA on all sixty-four bands of the clip's embeddings, not just the three we picked for the pseudo-RGB. We reshape to height-times-width rows by sixty-four columns, drop the invalid pixels, and fit three components." | [NONE] |
| 02:00 | 41:30 | [CELL] 01_alphaearth_access_visualize.ipynb § "PCA on the clip" | "The first principal component is mapped back over the valid pixels and plotted. And here's the caption exactly as the notebook states it: this component separates built-up, denser pixels from open, vegetated pixels in this sample — never 'measures vegetation' or 'is built-up.' A component is a direction in sixty-four-dimensional embedding space fit to this one clip, not a labeled physical variable. That phrasing is deliberate, and it's the one to repeat verbatim, not paraphrase into something stronger." | [RUN CELL] |
| 02:00 | 43:30 | [SLIDE] 01_access_visualize.md #5 | "Here's that first component on the slide. The takeaway underneath it in the notebook makes the connection explicit: this map looks geographically structured because nearby pixels tend to share similar land cover and therefore similar embeddings — not because any single axis or component has an assigned physical meaning. It's the same underlying structure the pseudo-RGB composite showed, viewed a different way." | [ZOOM] |
| 01:30 | 45:00 | [SLIDE] 01_access_visualize.md #6 | "This is exactly the trap the module's quiz tests. A student sees a PCA composite that visually correlates with land cover and concludes 'so this component measures vegetation' — that's the wrong conclusion. The correct framing: PCA components are unlabeled directions of maximum variance in this particular sample, and the same color in a different scene, a different date, or a different PCA fit is not guaranteed to mean the same thing. Turning colors into labels requires an actual trained classifier on labeled data — that's later modules, not a visual read of a PCA composite." | [PAUSE] |

Recap: a PCA component separates landscape types observed in this sample; it never measures or represents a fixed physical quantity.
End-state: the "WRONG conclusion" slide is on screen with the PCA figure still fresh in view.
Target length: 2:00–7:00 (not a codealong).

---

### Lecture 02.8 — Wrap-up and quiz callback

Objective: recap what Path B alone proves, and point students to the module quiz that tests these exact conceptual traps.

| Duration | Cumulative | VISUAL | AUDIO | Cue |
|----------|------------|--------|-------|-----|
| 01:30 | 46:30 | [CELL] 01_alphaearth_access_visualize.ipynb § "Wrap-up" | "To recap the takeaways: AlphaEarth ships sixty-four-band embeddings as quantized int8, and recovering a real vector requires that dequantization formula — never average raw int8 values directly. Every valid pixel in the bundled clip dequantizes to a unit-norm vector, exactly like the point tables the next notebook uses — that's what makes dot product equal cosine similarity there. A pseudo-RGB composite is always a display stretch over three illustrative axes, and a PCA component separates landscape types observed in this sample — neither one measures or is a physical quantity." | [NONE] |
| 01:30 | 48:00 | [SLIDE] 01_access_visualize.md #7 | "And the promise this whole module keeps: Path B reaches every one of these conclusions with zero credentials, using only the checked-in bundled clip — proving the course's central rule that no notebook hard-depends on an Earth Engine account. This offline path is also the one this course's own automated checks actually execute, which is why we could stand behind every number in this recording." | [NONE] |
| 01:00 | 49:00 | [SLIDE] 01_access_visualize.md #8 | "One housekeeping note before we move on: this module was built against AlphaEarth's `DATASET_VERSION` 1.1, and every figure and dequantization step you just saw was verified against that pin. If a future release changes the dataset version, expect the exact pixel values to shift even though the workflow itself stays the same." | [NONE] |
| 01:00 | 50:00 | [SLIDE] 01_access_visualize.md #9 | "Attribution, as always: the AlphaEarth Foundations Satellite Embedding dataset is produced by Google and Google DeepMind, licensed CC BY 4.0. Before you move to the next notebook, work through the Module 2 quiz — it tests exactly the PCA-labeling trap we just walked through, along with the dequantization and unit-norm reasoning from this module." | [NONE] |

Recap: Path B alone proves every conceptual claim this module makes, with the attribution and quiz callback closing out the recording.
End-state: the attribution slide is on screen as the module ends.
Target length: 2:00–7:00 (not a codealong).

---

Total: 50:00 (syllabus: 50 minutes)

## Pronunciation Notes

- AlphaEarth — "AL-fuh urth"
- TESSERA — "teh-SAIR-uh"
- GeoTessera — "JEE-oh teh-SAIR-uh"
- Guadalquivir — "gwah-dahl-kee-VEER"
- EPSG — spelled out, "E-P-S-G"
- precision@k — "precision at k"
- geemap — "gee-map"

## Key Messages Used

- "AlphaEarth vectors are unit-norm, so dot product equals cosine" (Lecture 02.5)

## Exercise/Quiz Callback

See assessments/01_access_visualize_quiz.md, question 1 (PCA component labeling trap) and question 5 (geographic structure without physical band meaning).

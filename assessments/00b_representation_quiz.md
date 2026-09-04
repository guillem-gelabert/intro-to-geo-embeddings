# Module 1 Quiz: Pixel, Patch and Location Embeddings

Conceptual-error quiz for `00b_representation_inspection.ipynb`. Every option's explanation
names the specific heading, print output, or Takeaway that proves the answer.

---

#### Q1. You have a 64-D AlphaEarth vector for one point and a 1024-D Clay embedding for the same coordinates. Can you concatenate them into a single 1088-D vector and run cosine similarity against another such concatenated pair, expecting a meaningful result?

- A. Yes, since both are embeddings, concatenation is always safe.
  *Incorrect — the "Side-by-side comparison" section's Takeaway is explicit: "shape and spatial unit are the first two things to check before combining or comparing embeddings from different providers." A 10 m pixel and a 2,560 m patch describe physically different footprints; naive concatenation mixes incompatible spatial units.*
- B. No — not without first checking that the two embeddings describe the same spatial unit and temporal support, which for AlphaEarth (one 10 m pixel, one calendar-year composite) and Clay (one ~2,560 m MajorTOM patch, one Sentinel-2 scene) they do not.
  *Correct — this is exactly the comparison table in "Side-by-side comparison": `dims`, `spatial_unit`, and `temporal_support` differ, and the Takeaway names checking shape and spatial unit as the mandatory first step before combining providers.*
- C. Yes, because concatenating any two float32 arrays of any length is always mathematically valid.
  *Incorrect — being programmatically possible (numpy will happily concatenate arrays) is not the same as being meaningful; the section's whole point is that shape compatibility does not imply semantic compatibility.*
- D. No, because Clay embeddings cannot be represented as numpy arrays.
  *Incorrect — the notebook does exactly that: `clay_vector = np.array(clay_row["embedding"], dtype="float32")` under "The Clay patch embedding" section, printing its shape as a normal array.*

---

#### Q2. The AlphaEarth pixel vector print output shows shape `(64,)`. What does this "one 10 m pixel" spatial unit mean when comparing two AlphaEarth vectors from points 5 meters apart?

- A. They are almost certainly the same underlying 10 m pixel or immediately adjacent pixels, so high similarity between them says little beyond spatial adjacency.
  *Correct — "The AlphaEarth pixel vector" section states AlphaEarth is "the smallest spatial unit in this notebook" at "one 10 m pixel." Two points 5 m apart likely fall in the same or a neighboring pixel, so any similarity result mostly reflects that adjacency, not an independent land-cover judgment — the same adjacent-pixel leakage concern raised again in Module 3's spatial-CV section.*
- B. They must belong to different MajorTOM cells.
  *Incorrect — MajorTOM cells are a Clay/LGND concept (2,560 m), described in "The Clay patch embedding" section, not an AlphaEarth pixel-level concept at all.*
- C. Their temporal support automatically differs, since AlphaEarth timestamps are pixel-specific.
  *Incorrect — "The AlphaEarth pixel vector" section states AlphaEarth's temporal support is "one calendar-year composite (2024)," identical for every pixel drawn from the same year, not pixel-specific.*
- D. This has no bearing on interpretation; only the vector shape matters.
  *Incorrect — the section's Takeaway explicitly says the vector "with no independently interpretable axis" and points to spatial unit info printed alongside the shape, i.e., shape alone is insufficient.*

---

#### Q3. The Clay patch embedding print output reports shape `(1024,)` and "Spatial unit: one Sentinel-2 patch (MajorTOM cell, 2,560 m)". A student claims: "since Clay's vector is bigger (1024 vs 64), it must describe a smaller, more precise spatial area than AlphaEarth." Is this correct?

- A. Yes, higher dimensionality always implies finer spatial resolution.
  *Incorrect — dimensionality and spatial footprint are unrelated axes of comparison. The "Side-by-side comparison" table lists them as two separate columns (`dims` and `spatial_unit`) precisely because one does not determine the other.*
- B. No — the comparison table shows Clay's spatial unit is a 2,560 m MajorTOM cell, which is a much *larger* footprint than AlphaEarth's 10 m pixel, despite Clay's vector having many more dimensions.
  *Correct — this is stated directly in the "Side-by-side comparison" table and its Takeaway: Clay's `spatial_unit` is "one Sentinel-2 patch (MajorTOM cell, 2,560 m)" versus AlphaEarth's "one 10 m pixel" — the larger vector describes the larger area, the opposite of the student's claim.*
- C. Yes, because Clay is described as a "patch" embedding and patches are always smaller than pixels.
  *Incorrect — "patch" in this course's vocabulary (see "The Clay patch embedding" heading) refers to a fixed MajorTOM tile, 2,560 m, larger than an AlphaEarth "pixel" (10 m), not smaller — the terms name spatial units, not implied sizes.*
- D. This cannot be determined from the notebook's output.
  *Incorrect — the "Side-by-side comparison" table prints exactly this information (`spatial_unit` column) for both providers.*

---

#### Q4. What does the "Temporal support" field printed for AlphaEarth ("one calendar-year composite (2024)") versus Clay ("one Sentinel-2 L2A scene at [datetime]") tell you about matching them to the "same" point in time?

- A. Both describe an identical, single-instant satellite pass, so temporal matching is straightforward.
  *Incorrect — the AlphaEarth vector is explicitly a "calendar-year composite," an aggregate over the whole year, not a single pass; the Clay vector is tied to "a single scene," a specific acquisition datetime — these are structurally different temporal supports, as the "The Clay patch embedding" Takeaway states directly: "means something different for a pixel vector than for a patch embedding."*
- B. AlphaEarth's yearly composite smooths over intra-year variation (e.g. seasonal change), while Clay's single-scene embedding reflects one specific date's conditions — so "the same year" does not mean "the same moment" across the two providers.
  *Correct — this is the direct reading of the two printed Temporal support lines and the section's Takeaway that "the same location" means something different for a pixel vector versus a patch embedding once you also account for time.*
- C. Temporal support is irrelevant to embedding comparison; only spatial unit matters.
  *Incorrect — the notebook prints both spatial unit and temporal support side by side in the comparison table specifically because both matter together, not just one.*
- D. Clay embeddings have no temporal information at all.
  *Incorrect — the print output explicitly shows `clay_row["datetime"]`, a specific acquisition date, directly contradicting this option.*

---

#### Q5. The "Optional: SatCLIP location embedding" section describes SatCLIP as a "location" embedding derived from coordinates alone, with no observation date. What is the key conceptual difference between a location embedding and the pixel/patch embeddings covered earlier?

- A. Location embeddings require the most recent satellite pass to be computed.
  *Incorrect — the section states the opposite: SatCLIP "knows nothing about what happened at a place this year — that is the tradeoff for needing no imagery to query it," meaning it needs no recent (or any) imagery at query time.*
- B. A location embedding is derived purely from where a place is (lon/lat), not from what was observed there at any specific time — unlike AlphaEarth (annual composite) or Clay (single scene), both of which are grounded in actual satellite imagery.
  *Correct — this matches the section text directly: SatCLIP "is derived from coordinates alone... with no observation date at all," in contrast to the imagery-grounded pixel and patch embeddings covered in the earlier sections.*
- C. SatCLIP embeddings are always exactly 64-D, matching AlphaEarth.
  *Incorrect — the section's placeholder code explicitly uses `np.zeros(256, dtype="float32")` with the comment "placeholder shape only," and states real SatCLIP embeddings are "typically a few hundred dimensions" — not 64.*
- D. Location embeddings cannot be compared to pixel or patch embeddings under any circumstances.
  *Incorrect — the section doesn't make this absolute claim; it flags a conceptual tradeoff (no temporal grounding) rather than declaring comparison categorically impossible.*

---

#### Q6. Why does the "Optional: SatCLIP location embedding" section wrap its demonstration in a `try/except ImportError` check for `torch`, rather than importing it unconditionally?

- A. Because torch is intentionally kept out of this course's core/providers install, so the section must degrade gracefully when it is absent.
  *Correct — the section text states this directly: "SatCLIP requires `torch`, which is intentionally kept out of this course's core/providers install (ENV-05), so this section degrades gracefully when torch is absent."*
- B. Because torch is not a real Python package and the import would always fail.
  *Incorrect — torch is a real, installable package; the code path that runs when `TORCH_AVAILABLE` is true demonstrates handling the case where it *is* installed.*
- C. Because SatCLIP cannot be described without running a live model.
  *Incorrect — the section explicitly states the torch-available branch "is illustrative only... not expected to execute in the reference environment... does not need a real model checkpoint," i.e., no live model run is required either way.*
- D. Because import errors in Jupyter notebooks always crash the entire kernel.
  *Incorrect — Python's `try/except ImportError` is a standard, safe pattern precisely because it prevents a crash; that is the point of using it here.*

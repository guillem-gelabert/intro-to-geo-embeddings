# Module 2 Quiz: Accessing and Visualizing AlphaEarth

Conceptual-error quiz for `01_alphaearth_access_visualize.ipynb`. Every option's explanation
names the specific heading, print output, or Takeaway/Caption that proves the answer.

---

#### Q1. The notebook's "PCA on the clip" section captions its first-principal-component map as separating "built-up, denser pixels from open, vegetated pixels." A student concludes: "so PC1 is a vegetation index." Is this correct?

- A. Yes, since the map visually correlates with vegetation, PC1 must be measuring vegetation as a physical quantity.
  *Incorrect — the "Caption" directly under the PCA figure forbids exactly this reading: "never 'measures vegetation' or 'is built-up': a component is a direction in 64-D embedding space fit to this one clip, not a labeled physical variable."*
- B. No — PC1 is a direction of maximum variance fit to this specific clip's 64-D embeddings; it happens to separate built-up from vegetated pixels in this sample, but it is not a labeled, physically-defined vegetation index like NDVI.
  *Correct — this is the exact wording of the Caption: the component "separates built-up, denser pixels from open, vegetated pixels in this sample," phrased deliberately as a this-sample observation, not a general physical measurement, and the section explicitly warns against naming the axis "vegetation."*
- C. Yes, because AlphaEarth's band A16 (used in the pseudo-RGB) is specifically designed to encode vegetation.
  *Incorrect — the pseudo-RGB section states the three chosen bands (A01, A16, A09) are "just three of the embedding's 64 axes" carrying "no RGB meaning," not a bespoke vegetation-sensitive band; the same "no assigned physical meaning" rule the PCA Caption states applies to individual bands too.*
- D. No, because PCA cannot be run on embedding vectors at all.
  *Incorrect — the "PCA on the clip" section runs `PCA(n_components=3).fit_transform(...)` directly on the dequantized embedding matrix; PCA on embeddings is exactly what the section demonstrates.*

---

#### Q2. Why does the "Static pseudo-RGB" visualization stretch band values to `[-0.3, 0.3]` before display, and what does that stretch represent?

- A. It represents the true physical reflectance range of the underlying satellite bands.
  *Incorrect — the section states explicitly: "this range is a DISPLAY STRETCH, not a physical reflectance range" — it is a visualization convenience, not a physical unit.*
- B. It is a display-only contrast stretch chosen to make the chosen embedding axes visible as an image; the three channels (A01, A16, A09) carry no RGB meaning regardless of the stretch applied.
  *Correct — this matches the section text directly: "stretched to `[-0.3, 0.3]` for display only... the three channels carry no RGB meaning; they are just three of the embedding's 64 axes."*
- C. It converts the int8 AlphaEarth values into true-color RGB imagery.
  *Incorrect — the section is explicit that the three bands used "carry no RGB meaning"; the visualization is called "pseudo-RGB" precisely because it borrows the RGB display convention without the bands actually being red/green/blue reflectance.*
- D. It is the dequantization formula applied a second time for display purposes.
  *Incorrect — dequantization (`(v/127.5)**2 * sign(v)`) is a separate, earlier step described under "The int8 dequantization formula"; the `[-0.3, 0.3]` stretch in "Static pseudo-RGB" is a distinct display-only rescaling applied after dequantization.*

---

#### Q3. The "Unit-norm check" section asserts `np.allclose(norms[valid], 1.0, atol=1e-3)` after dequantization. Why does this matter for anything you might do later, like averaging several nearby pixels?

- A. It doesn't matter; unit-norm is just a cosmetic property of AlphaEarth.
  *Incorrect — the section's Takeaway states this directly matters because it's "what makes dot product equal cosine similarity" in `02_similarity_and_classification.ipynb`; averaging raw int8 values instead of dequantized unit vectors "silently corrupts the data" per the "int8 dequantization formula" section's Pitfall reference.*
- B. Because every valid dequantized pixel is confirmed to be a unit vector, dot products between dequantized pixels equal cosine similarities directly, and any subsequent averaging of raw (pre-dequantization) int8 values would silently corrupt the result since quantization is non-linear.
  *Correct — the Takeaway states pixels are "unit vector[s] once dequantized, exactly like the point tables `02_similarity_and_classification.ipynb` uses. That is what makes dot product equal cosine similarity there," and the earlier "int8 dequantization formula" section warns that "averaging raw int8 values directly... silently corrupts the data, because the quantization is non-linear."*
- C. It confirms that the AlphaEarth data has no missing/nodata pixels.
  *Incorrect — the same code explicitly separates `valid = ~np.isnan(norms)` before asserting unit-norm only on valid pixels, meaning nodata pixels are expected and excluded, not disproven.*
- D. It only applies to this specific Bern clip, not to any other AlphaEarth tile.
  *Incorrect — the Takeaway generalizes this property ("exactly like the point tables `02_similarity_and_classification.ipynb` uses"), tying it to the dequantization formula itself, which is provider-wide, not clip-specific.*

---

#### Q4. Path A (live Earth Engine) and Path B (the bundled offline clip) both let you inspect AlphaEarth data. If a student only ever runs Path B, do they still reach the same core conclusions about the data (unit-norm, dequantization, PCA structure)?

- A. No — Path A and Path B use fundamentally different embedding products, so their outputs cannot be compared.
  *Incorrect — the notebook is structured so both paths inspect the same AlphaEarth Google Satellite Embedding product; Path B ("offline access from the bundled clip") is explicitly the credential-free fallback for the same data, per "Path B: Offline access from the bundled clip (no credentials needed)."*
- B. Yes — Path B works from the same int8-quantized AlphaEarth clip and applies the identical `dequantize_aef` formula, unit-norm check, pseudo-RGB, and PCA steps, so the conceptual conclusions (dequantization matters, unit-norm holds, PCA components aren't labeled variables) hold regardless of which path supplied the raw bytes.
  *Correct — Path B's section header states it needs "no credentials," and every subsequent subsection ("The int8 dequantization formula," "Unit-norm check," "Static pseudo-RGB," "PCA on the clip") operates on `raw`/`embedded` arrays without reference to which path produced them — the conclusions are about the data's properties, not the access method.*
- C. No — only Path A's live Earth Engine data is dequantized; Path B's offline clip is already float and skips that step.
  *Incorrect — the "int8 dequantization formula" section explicitly operates on `raw` read from the bundled clip and calls `dequantize_aef(raw)`, meaning the offline clip is also delivered as int8 and requires the same dequantization step.*
- D. This cannot be determined without running Path A, which requires a registered Earth Engine project.
  *Incorrect — Path B is designed precisely so the offline path can be run and reasoned about without ever touching Path A or needing a project; the notebook's own structure treats it as self-sufficient for these conclusions.*

---

#### Q5. A student sees the pseudo-RGB image looks "geographically structured" — roads, fields, and buildings are visually distinguishable — and concludes the three chosen bands (A01, A16, A09) must individually encode meaningful physical categories like "roads" or "vegetation." What does the notebook's own explanation say instead?

- A. The visual structure exists because nearby pixels tend to share similar land cover and therefore similar embeddings overall — not because any single axis or component has an assigned physical meaning; the same underlying structure also shows up in the unrelated PC1 map.
  *Correct — this is the exact wording of the PCA section's Takeaway: "the pseudo-RGB map above looks geographically structured because nearby pixels tend to share similar land cover and therefore have similar embeddings, not because any single axis or component has an assigned physical meaning... two different views of the same underlying structure, neither of which names what the axes 'are'."*
- B. The bands were specifically engineered by Google to represent roads, vegetation, and buildings as separate RGB channels.
  *Incorrect — the pseudo-RGB section states the three bands "carry no RGB meaning; they are just three of the embedding's 64 axes," directly contradicting any claim of engineered physical-category channels.*
- C. This structure is a rendering artifact of the `[-0.3, 0.3]` stretch and would disappear with a different stretch range.
  *Incorrect — the stretch only affects contrast/display range, not the underlying spatial correlation of nearby pixels' embeddings; the Takeaway attributes the structure to shared land cover producing similar embeddings, a property of the data, not the display stretch.*
- D. It confirms component 3 of the PCA specifically measures vegetation, since the pseudo-RGB uses band A16.
  *Incorrect — this conflates the pseudo-RGB band selection (A01, A16, A09, chosen for display) with the separate PCA computation (fit on all 64 bands via `PCA(n_components=3)`); neither is captioned as measuring vegetation, per the PCA Caption's explicit warning.*

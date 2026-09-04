# Module 5 Quiz: Embedding Ecosystems

This quiz tests conceptual errors, not terminology. Every option below is
explained by quoting the specific cell, heading, or Takeaway in
`notebooks/solutions/04_embedding_ecosystems.py` that demonstrates the
correct reasoning.

---

#### Q1. The notebook computes `norm_diagnostics` on TESSERA vectors and
only prints a warning if the mean is far from 1.0, rather than a hard
`assert` like Module 3 used for AlphaEarth. Why the different treatment?

- A) TESSERA's unit-norm property is undocumented, so a crashing assert
  would make the notebook fragile to a legitimate provider property; a
  report is the honest response to an unverified contract.
  **Correct.** Quoted verbatim: "unlike Module 3's AlphaEarth checkpoint
  (a hard `assert` because unit-norm is a verified property of that
  data), this cell only *reports*. That asymmetry is deliberate: it is
  the teaching point about provider portability — verify the contract
  every time you change provider, rather than copying an assumption
  forward."
- B) TESSERA vectors are always unit-norm, so the check is redundant and
  only kept for symmetry with AlphaEarth's code.
  **Incorrect.** The section states directly: "Its unit-norm property is
  undocumented ... The right response is not to assume either way — it
  is to *check*."
- C) Hard asserts are computationally too expensive for 128-D vectors.
  **Incorrect.** Cost is never given as the reason; the reason stated is
  epistemic (undocumented property), not performance.
- D) TESSERA and AlphaEarth use identical normalization, so no check is
  actually needed.
  **Incorrect.** This is the opposite of the stated reasoning — the
  section exists specifically because AlphaEarth's unit-norm is a
  *verified* property and TESSERA's is not, so they cannot be assumed
  identical.

---

#### Q2. What must you check before reusing `cosine_similarity_map` on a
new embedding provider you have not used before?

- A) The provider's vector norm, using `norm_diagnostics` — never assume
  it behaves like AlphaEarth's unit-norm vectors.
  **Correct.** Header "What you will learn," item 3: "Why you must
  *check* a new provider's vector norm with
  `course.embeddings.norm_diagnostics` rather than assume it behaves
  like AlphaEarth's unit-norm vectors."
- B) The provider's embedding dimensionality must be padded or truncated
  to exactly 64-D to match AlphaEarth.
  **Incorrect.** The notebook states the opposite: "`course.embeddings.
  cosine_similarity_map` does not hardcode a width, so it works
  unchanged" against 128-D TESSERA and 1024-D Clay vectors directly.
- C) Whether the provider's API requires an Earth Engine account.
  **Incorrect.** None of TESSERA, Clay, or LGND require an Earth Engine
  account in this notebook; the "Prerequisite" table marks Earth Engine
  as not needed throughout this module.
- D) The provider's exact release date.
  **Incorrect.** Release date is never checked in the norm-diagnostics
  section or elsewhere as a precondition for reusing the similarity
  helper.

---

#### Q3. `LGND_TOKEN` is not set in the environment. What does the
notebook do?

- A) It prints that `LGND_TOKEN` is not set, skips the live call, and
  falls back to a recorded fixture — the section still completes.
  **Correct.** Quoted verbatim: "LGND_TOKEN not set; skipping live call,
  using recorded fixture" is printed, and the section's own framing
  states "This notebook never hard-depends on it: no token means no live
  call, and the section still completes using a small, clearly labeled
  recorded fixture."
- B) It raises an exception and halts the entire notebook.
  **Incorrect.** The code wraps the live call in `if LGND_TOKEN:` /
  `else:` with a fixture fallback specifically to avoid this outcome —
  see the "check, don't assume, availability" design repeated for every
  provider in this module.
- C) It silently substitutes a different provider's data without telling
  the reader.
  **Incorrect.** The fixture path is explicitly printed
  (`f"recorded fixture ({lgnd_result['fixture_type']})"`) so the source
  is always visible, never silent.
- D) It prompts the student interactively to enter a token before
  continuing.
  **Incorrect.** No interactive prompt exists in the notebook; the
  fallback is fully automatic.

---

#### Q4. How do TESSERA and Clay differ in how you access their
embeddings?

- A) TESSERA is 128-D and sampled directly at points/rasters via
  `geotessera` (`sample_embeddings_at_points`, `fetch_embedding`), while
  Clay is a 1024-D patch embedding queried from a hive-partitioned
  GeoParquet corpus via DuckDB over HTTPS.
  **Correct.** Quoted from the respective section headers: "TESSERA: a
  128-D, 10 m embedding" describes direct point/raster sampling via
  `geotessera`; "Clay: a 1024-D patch embedding from the open LGND
  corpus" describes DuckDB `read_parquet` over the hive-partitioned
  GeoParquet corpus at `geohash_l2=u0`.
- B) Both TESSERA and Clay are accessed the exact same way, through
  `geotessera`.
  **Incorrect.** Clay is accessed via DuckDB reading GeoParquet
  (`duckdb.sql("... read_parquet(...)")`), not via `geotessera`, which
  is TESSERA-specific.
- C) TESSERA requires a bearer token; Clay does not.
  **Incorrect.** Bearer-token auth belongs to the LGND REST API section,
  not TESSERA (served "over public HTTPS via `geotessera` — no
  authentication required") or the open Clay corpus (public GeoParquet,
  no token).
- D) TESSERA and Clay produce vectors of the same dimensionality, so
  they can be directly compared without transformation.
  **Incorrect.** The notebook states plainly: "Clay's 1024-D vectors and
  TESSERA's 128-D vectors are NOT directly comparable to AlphaEarth's
  64-D vectors, nor to each other, without a shared projection trained
  for that purpose."

---

#### Q5. "Provider portability" as demonstrated across AlphaEarth,
TESSERA, and Clay in this notebook means:

- A) The same operations (`cosine_similarity_map`, `norm_diagnostics`)
  run unchanged across providers — it does NOT mean the similarity
  numbers themselves are comparable across providers.
  **Correct.** Wrap-up Takeaway, quoted verbatim: "The same
  `cosine_similarity_map`/`norm_diagnostics` operations from
  `course.embeddings` ran unchanged against AlphaEarth (64-D), TESSERA
  (128-D), and Clay (1024-D) vectors — provider portability is about the
  operation, not the numbers, which are NOT comparable across
  providers."
- B) A similarity score of 0.9 from Clay means the same thing as a 0.9
  score from AlphaEarth.
  **Incorrect.** This is precisely the confusion the same Takeaway warns
  against: numbers "are NOT comparable across providers" without a
  shared projection.
- C) All three providers must be converted to the same dimensionality
  before any operation can be reused.
  **Incorrect.** The notebook reuses the operations unchanged at their
  native dimensionalities (64-D, 128-D, 1024-D) — no dimensionality
  conversion step exists in this notebook.
- D) Portability means only that the notebook's code is short.
  **Incorrect.** The Takeaway's point is about operation reuse across
  genuinely different vector spaces, not code brevity.

---

#### Q6. How does querying LGND differ in kind from querying TESSERA or
Clay in this notebook?

- A) LGND is a managed service: you express the operation via a REST API
  call and the service returns ranked results (`stac_item_id`/`score`
  pairs) — you never see the raw vectors it works with, unlike TESSERA
  and Clay where you hold the vectors and compute similarity yourself.
  **Correct.** Quoted verbatim: "LGND is a different shape of product: a
  REST API where you express the operation ... and the service holds the
  vector index and does the search — you never see the raw 1024-D
  vectors it works with," and the Takeaway: "LGND returns ranked
  `stac_item_id`/`score` pairs, not a matrix you feed into
  `cosine_similarity_map` yourself."
- B) LGND is strictly better than TESSERA and Clay because it requires
  less code.
  **Incorrect.** The Takeaway frames this as "a trade" (less code, but no
  vector access or metric control), explicitly not a strict
  improvement.
- C) LGND, TESSERA, and Clay all return the identical response shape.
  **Incorrect.** The Takeaway explicitly calls out "the API shape
  difference from every other provider in this notebook."
- D) LGND requires no authentication at all, unlike TESSERA and Clay.
  **Incorrect.** LGND "requires a bearer token (`LGND_TOKEN` in the
  environment; a trial tier exists)" — the reverse of TESSERA/Clay, both
  of which are public/no-auth in this notebook.

---

#### Q7. Regarding TESSERA's embedding-data license, the notebook says:

- A) Treat any TESSERA sample you bundle as unresolved-license until
  confirmed otherwise — the software is MIT, but the embedding data's
  license is not stated in the docs or README.
  **Correct.** Quoted verbatim: "`geotessera`'s **software** is
  MIT-licensed. Its **embedding data** license is not stated in the
  project's docs or README ... Treat any TESSERA sample you bundle as
  unresolved-license until you can confirm otherwise; do not assume CC
  BY just because AlphaEarth and Clay both are."
- B) TESSERA embedding data is CC BY 4.0, same as AlphaEarth and Clay.
  **Incorrect.** This is the exact assumption the notebook warns
  against: "do not assume CC BY just because AlphaEarth and Clay both
  are."
- C) TESSERA embedding data is public domain since the software is MIT.
  **Incorrect.** A software license (MIT) and a data license are
  explicitly treated as two separate facts in this notebook; MIT
  software licensing says nothing about the data license, which remains
  unstated.
- D) TESSERA's license question was resolved by this course's research
  and is documented in `data/DATA_CARD.md`.
  **Incorrect.** The notebook calls this "an open question this course
  does not resolve for you," not a resolved one.

# [DATASET / ARTIFACT NAME] -- Model / Data Card

Fill every `[PLACEHOLDER]`. Do not leave a placeholder unresolved in a
submitted card -- an unresolved placeholder means the checklist in
`PROVENANCE_CHECKLIST.md` has not been satisfied for this artifact.

## Description

[One paragraph: what this artifact is, what embedding product(s) and/or
raw bands it contains, what region(s) and year(s) it covers, how many
rows/tiles, and how it was built (script/notebook name) or where it was
obtained.]

## Representation Choice

Which embedding representation does this artifact use, and why?

| Question | Answer |
|---|---|
| Representation used | [AlphaEarth / TESSERA / Clay / SatCLIP / raw Sentinel-2 bands / other] |
| Alternatives considered | [list] |
| Why this one (dimensionality, coverage, license, cost, latency) | [answer] |
| Known tradeoff accepted | [e.g. "TESSERA gives 10 m resolution but the embedding-data license is unstated, so this artifact is not redistributed outside the author's own analysis"] |

## Licenses and Attribution (verbatim -- do not paraphrase)

| Source | License | Attribution |
|---|---|---|
| [source name] | [license identifier, e.g. CC BY 4.0] | [exact attribution sentence, copied character-for-character from the provider's own documentation -- never paraphrased] |

If any source's license is unstated, unclear, or its terms prohibit
redistribution, say so explicitly here rather than inventing a license.
State the resulting decision (e.g. "not bundled", "author's private use
only", "opt-in live fetch, never frozen").

## Sampling Method / Model Details

[If a sampled dataset: sampling strategy, class balancing, spacing,
random seed, row budget derivation. If a model output: model name,
version, checkpoint, inference parameters.]

`label_source`: [exact string, e.g. `esa_worldcover_2021`]
`validation_source`: [exact string -- MUST differ from `label_source`;
validating one learned product against another learned product is not
independent validation (see Pitfall 6 in PROVENANCE_CHECKLIST.md)]

## Structure

[Table of files/tables, rows, CRS, columns/bands, dtypes.]

| File/Table | Rows | CRS | Notes |
|---|---|---|---|
| [path] | [n] | [EPSG:xxxx] | [notes] |

## Limitations

[What this artifact does NOT support -- e.g. scale at which conclusions
hold, known validation gaps, geographic/temporal coverage limits, known
class imbalance.]

## Citation

If you use this artifact, cite the underlying sources above using their
exact attribution strings, plus:

> [course/project citation line, release date]

## Provenance

- Source URL(s) / bucket path(s) / scene IDs: [list]
- Dataset version: [exact version string, e.g. EE `DATASET_VERSION`]
- Extraction / build date: [ISO date]
- CRS: [EPSG code]
- Checksum (sha256) of the artifact: [hash, if applicable]
- Builder script/notebook + git SHA: [reference]
- Created by: [name/role]

## Ethics Statement

- Who bears the cost of a false positive from this artifact's downstream
  use? [answer concretely -- not "consider the impact"]
- Is any inferred information (e.g. land-use change, built-up
  artificialization) more sensitive than the underlying imagery itself?
  [answer]

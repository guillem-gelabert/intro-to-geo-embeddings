# Provenance Checklist

Apply this checklist to one specific artifact at a time (one dataset
table, one raster, one model output). Every item must be answerable
yes/no about that artifact -- if you cannot answer yes/no, the item is
not done yet.

1. **Data source documented** -- is the exact source (bucket path,
   collection ID, API endpoint, or STAC item) recorded, not just a
   provider name?
2. **License identified** -- is a specific license (CC BY 4.0, "free/open
   commercial use allowed", "unstated -- do not redistribute", etc.)
   recorded for this artifact, rather than assumed from a similar
   dataset?
3. **Attribution copied verbatim** -- is the attribution sentence an
   exact character-for-character copy of the provider's own wording,
   not a paraphrase or summary?
4. **`label_source` and `validation_source` are distinct strings** --
   are they recorded separately and do they name two independently
   derived products (see Pitfall 6 below), never the same product
   twice?
5. **CRS recorded** -- is the EPSG code of every geometry/raster in this
   artifact written down, not left implicit?
6. **Version / checksum recorded** -- is a dataset version string (e.g.
   `DATASET_VERSION`) and/or a sha256 checksum recorded so a later
   reader can confirm they have the same bytes?
7. **Representation-choice tradeoff stated** -- is there a written reason
   for choosing this embedding representation over the alternatives,
   including any known gap (e.g. an unstated data license)?
8. **False-positive-cost / ethics statement present** -- does the card
   name who bears the cost of an error from this artifact's downstream
   use, and whether the inferred output is more sensitive than the
   underlying imagery?

If any answer is "no", the card is not finished -- fix the card, don't
relax the checklist.

## Pitfall 6: label_source vs validation_source

Validating one learned product (e.g. a land-cover classification) against
another learned product derived independently is legitimate. Validating
it against itself, or against a product derived from the same upstream
classifier, is not independent validation and must not be called
"validation" in a card. `label_source` and `validation_source` must
always be recorded as two distinct strings naming two distinct upstream
products.

## Reference table: exact verbatim attribution strings

Copied character-for-character from `data/DATA_CARD.md`. Do not edit
these strings when reusing them in a new card -- copy them exactly.

| Source | License | Attribution |
|---|---|---|
| AlphaEarth / Satellite Embedding | CC BY 4.0 | The AlphaEarth Foundations Satellite Embedding dataset is produced by Google and Google DeepMind. |
| ESA WorldCover 2021 v200 | CC BY 4.0 | © ESA WorldCover project 2021 / Contains modified Copernicus Sentinel data (2021) processed by ESA WorldCover consortium (citation: Zanaga et al. 2022, https://doi.org/10.5281/zenodo.7254221) |
| Copernicus HRL Imperviousness Density 2018 | Free/open, commercial use allowed | Generated using European Union's Copernicus Land Monitoring Service information |
| Sentinel-2 L2A (derived reflectance bands) | EU legal notice (Reg. 1159/2013) | Contains modified Copernicus Sentinel data [Year] (the actual year is recorded per-table in that table's own `course_provenance`) |
| LGND Clay v1.5 Sentinel-2 L2A (fixture) | CC BY 4.0 | LGND Clay v1.5 Sentinel-2 L2A embeddings, Source Cooperative, CC BY 4.0 |
| TESSERA (software: `geotessera`/`tessera`) | MIT (software license only) | No stated attribution string -- the geotessera/tessera repositories license the software as MIT, but **the embedding data itself has no stated license** in the docs or README. Do not invent one; confirm with the maintainers before redistributing TESSERA-derived samples. |

## Worked "do not redistribute" example: Copernicus Global Embeddings (CDSE)

Copernicus Global Embeddings, accessed via the Copernicus Data Space
Ecosystem (CDSE), have no stated license and CDSE's own portal terms
prohibit redistribution of portal material. This course never bundles
them: no frozen column in `data/` is derived from CDSE, and any future
use must be a live, opt-in notebook cell that fetches data at run time
under the student's own CDSE credentials, never a frozen artifact
shipped in this repository. This is the worked example of a license
check correctly reaching a "do not redistribute" conclusion rather than
bundling data under an assumed-permissive license.

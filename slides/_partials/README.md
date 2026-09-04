# Slide partials

## Toolchain in use: Marp CLI (not Quarto)

Decided in `07-01`: `brew install --cask quarto` fetches the cask but its
`.pkg` installer requires an interactive `sudo` prompt (no askpass helper,
no TTY), so Quarto cannot be installed non-interactively on this machine.
The phase falls back to **Marp CLI, pinned at `4.5.0`**, invoked on demand
via `npx --yes @marp-team/marp-cli@4.5.0` — never `@latest` (see the
threat model in `07-01-PLAN.md`, T-07-01). `npx decktape` is not used;
Marp's own `--pdf` flag produces PDFs directly (see `make slides-pdf`).

This changes how partials are consumed compared to the Quarto plan this
phase was originally scoped against:

- Quarto has `{{< include >}}`, so a shared partial file is included
  verbatim into every deck at render time.
- **Marp has no include mechanism.** Every one of the eight module decks
  (`slides/NN_*.md`) must **copy-paste** the body of
  `version-banner.qmd` and `attribution.qmd` directly into its own
  Markdown file, immediately after its own front-matter.

## Convention for the deck-authoring plans (07-02, 07-03, 07-04)

- Copy both partials into every deck: `version-banner.qmd` first, then
  `attribution.qmd` (or wherever they fit that module's narrative --
  typically banner near the top, attribution near the end).
- **Trim rows** in the attribution slide that are irrelevant to that
  specific module's data sources (e.g. a module that never touches LGND
  Clay drops that row entirely).
- **Never reword a row you keep.** The remaining license/attribution
  strings must stay byte-for-byte identical to `data/DATA_CARD.md` and to
  `attribution.qmd` here.
- Repeat the three Marp front-matter keys from `slides/_metadata.yml`
  (`marp: true`, `theme: default`, `size: "16:9"`, `paginate: true`) in
  each deck's own front-matter -- Marp does not pick these up from a
  shared project file.
- Use the shared theme with
  `npx --yes @marp-team/marp-cli@4.5.0 --theme slides/custom.scss ...`
  (wired into `make slides` / `make slides-pdf`; do not hand-invoke marp
  with different flags).

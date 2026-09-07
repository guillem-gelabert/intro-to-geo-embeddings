# Introduction to Geospatial Embeddings — course reference environment Makefile.
# GNU Make on the reference machine is 3.81 (macOS-bundled, pre-.ONESHELL) — every
# recipe below is written to be portable to that version: no .ONESHELL, no `!=`
# shell assignment, no $(file ...). Recipes needing shared shell state (arrays,
# nullglob) use backslash-newline continuation so Make passes them to a single
# shell invocation instead of one-shell-per-line.
SHELL := /usr/bin/env bash

# Must match course.config.KERNEL_NAME exactly — jupyter execute and the
# interactive JupyterLab kernel picker both key off this literal string.
KERNEL_NAME := geo-embeddings-course

# Overridable from the command line, e.g. `make execute-notebooks NOTEBOOKS_DIR=/tmp/x`.
# Defaults to notebooks/solutions, which does not exist yet in this repo (Phase 3).
NOTEBOOKS_DIR ?= notebooks/solutions

.PHONY: env kernel test test-network execute-notebooks exercises slides slides-pdf web-content web-serve

# Marp CLI is the slide toolchain (07-01): `brew install --cask quarto`'s
# .pkg installer requires interactive sudo on this machine, so Quarto is
# unavailable. Marp is invoked on demand via npx, pinned to 4.5.0 (never
# @latest -- see 07-01-PLAN.md threat model T-07-01).
MARP := npx --yes @marp-team/marp-cli@4.5.0

# Solution-notebook stems the exercise generator loops over (Phase 6).
EXERCISE_STEMS := 00_embedding_refresher 00b_representation_inspection \
	01_alphaearth_access_visualize 02_similarity_and_classification \
	03_change_detection_and_validation 04_embedding_ecosystems \
	05_capstone_artificialization

env:
	uv sync --group dev

kernel:
	uv run ipython kernel install --user --env VIRTUAL_ENV "$(CURDIR)/.venv" --name=$(KERNEL_NAME)

test:
	uv run pytest tests/

# Network-marked tests are excluded from `test`'s default addopts
# (-m "not network" in pyproject.toml). Live AlphaEarth window reads
# measured at 190-340s each (02-RESEARCH.md) — run this on demand only.
test-network:
	uv run pytest tests/ -m network

# nbclient's underlying kernel process emits a benign "Kernel is running over TCP
# without encryption" warning during local, single-machine headless execution —
# this is expected and not a real finding (no network exposure); see 01-RESEARCH.md
# Security Domain, Known Threat Patterns.
execute-notebooks:
	@shopt -s nullglob; \
	files=(); \
	for f in $(NOTEBOOKS_DIR)/*.ipynb; do \
		case "$$(basename "$$f")" in executed_*) continue;; esac; \
		files+=("$$f"); \
	done; \
	if [ $${#files[@]} -eq 0 ]; then \
		echo "No solution notebooks found yet (expected before Phase 3)."; \
		exit 0; \
	fi; \
	set -euo pipefail; \
	for f in "$${files[@]}"; do \
		echo "Executing $$f"; \
		uv run jupyter execute --kernel_name=$(KERNEL_NAME) --timeout=900 --output="executed_$$(basename "$$f")" "$$f"; \
	done

# Derives all seven exercise notebooks from their tagged solution notebooks
# (tools/derive_exercise.py, plan 06-06), then pairs each output with a
# jupytext py:percent twin for reviewable diffs, matching the solutions'
# pairing convention.
exercises:
	@set -euo pipefail; \
	mkdir -p notebooks/exercises; \
	for stem in $(EXERCISE_STEMS); do \
		echo "Deriving notebooks/exercises/$$stem.ipynb"; \
		uv run python tools/derive_exercise.py \
			notebooks/solutions/$$stem.ipynb notebooks/exercises/$$stem.ipynb \
			--appendix tools/exercise_appendix.yaml; \
		uv run jupytext --set-formats ipynb,py:percent notebooks/exercises/$$stem.ipynb; \
	done

# Renders every module deck (slides/NN_*.md) to self-contained HTML via
# Marp CLI, skipping the shared slides/_partials/ reference files (those
# are copy-pasted into decks, not rendered standalone; see
# slides/_partials/README.md for why Marp has no include mechanism).
slides:
	@shopt -s nullglob; \
	files=(); \
	for f in slides/*.md; do \
		files+=("$$f"); \
	done; \
	if [ $${#files[@]} -eq 0 ]; then \
		echo "No decks found yet under slides/ (expected before 07-02)."; \
		exit 0; \
	fi; \
	set -euo pipefail; \
	for f in "$${files[@]}"; do \
		echo "Rendering $$f"; \
		$(MARP) --theme slides/custom.scss --html "$$f"; \
	done

# Renders every module deck straight to PDF via Marp's own --pdf flag
# (no decktape needed -- Marp is not Quarto's browser-print workflow).
slides-pdf:
	@shopt -s nullglob; \
	mkdir -p slides/pdf; \
	files=(); \
	for f in slides/*.md; do \
		files+=("$$f"); \
	done; \
	if [ $${#files[@]} -eq 0 ]; then \
		echo "No decks found yet under slides/ (expected before 07-02)."; \
		exit 0; \
	fi; \
	set -euo pipefail; \
	for f in "$${files[@]}"; do \
		stem="$$(basename "$$f" .md)"; \
		echo "Rendering slides/pdf/$$stem.pdf"; \
		$(MARP) --theme slides/custom.scss --pdf --allow-local-files -o "slides/pdf/$$stem.pdf" "$$f"; \
	done

# Generated, pinned, no-dev, no-hash Colab reference requirements file. Never
# hand-edit this file — it is only ever produced by `uv export` with these flags.
requirements-colab.txt: pyproject.toml uv.lock
	uv export --format requirements-txt --no-hashes --no-dev --no-emit-project -o requirements-colab.txt

# --- mobile web companion -------------------------------------------------
# The bundle is committed so the container image needs neither the notebooks nor
# the geo stack. Regenerate it whenever a solution notebook is re-executed.
web-content:
	uv run --extra web python tools/build_web_course.py

web-serve: web-content
	uv run --extra web uvicorn webapp.app:app --reload --host 0.0.0.0 --port 8000

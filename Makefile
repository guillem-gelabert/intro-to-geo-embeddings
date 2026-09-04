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

.PHONY: env kernel test test-network execute-notebooks exercises

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

# Generated, pinned, no-dev, no-hash Colab reference requirements file. Never
# hand-edit this file — it is only ever produced by `uv export` with these flags.
requirements-colab.txt: pyproject.toml uv.lock
	uv export --format requirements-txt --no-hashes --no-dev --no-emit-project -o requirements-colab.txt

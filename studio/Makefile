# reveal-studio: every target runs from studio/ with uv's venv (studio/.venv); the main venv (../.venv) is only ever
# the python the runner starts for loop_seq.py, never this Makefile's interpreter.
UV ?= uv
# PyPI for every uv call, whatever the shell exports (this laptop's shell names a work mirror;
# the lock of 2026-11-05 carried its URLs once and the GitHub runner could not reach it).
export UV_DEFAULT_INDEX := https://pypi.org/simple
unexport UV_INDEX_URL PIP_INDEX_URL
RUN := $(UV) run
PORT ?= 8390

.PHONY: help install run test test-fast test-cov acceptance draft-check lint fix typecheck audit prose qa detector

help:  ## list the targets
	@grep -E '^[a-z-]+:.*## ' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*## "}; {printf "  %-11s %s\n", $$1, $$2}'

install:  ## create or update studio/.venv from uv.lock
	$(UV) sync

run:  ## serve the studio on 127.0.0.1:8380 (pass flags with: uv run reveal-studio serve --port ...)
	$(RUN) reveal-studio serve

test:  ## unit and integration tests (the integration ones skip without ../.venv)
	$(RUN) pytest tests -m "not acceptance"

test-fast:  ## unit tests only (the fake loop_seq.py, no main venv)
	$(RUN) pytest tests -m "not integration and not acceptance"

test-cov:  ## unit and integration tests with line and branch coverage
	$(RUN) pytest tests -m "not acceptance" --cov --cov-report=term-missing

acceptance:  ## the A1 and A2 loop-flow drives on the owner's stills (tests/acceptance; two new jobs under benchmarks/runs/<date>/studio/; about 3 min)
	$(RUN) pytest tests/acceptance -m acceptance -s

draft-check:  ## the 480 px draft of angel_a2 through the package into the job loop_angel_20261104-220719 (an 8 MB draft per run)
	$(RUN) pytest tests/integration/test_draft_render.py -m acceptance -s

lint:  ## ruff check and ruff format --check
	$(RUN) ruff check .
	$(RUN) ruff format --check .

fix:  ## apply ruff's fixes and formatting
	$(RUN) ruff check --fix .
	$(RUN) ruff format .

typecheck:  ## mypy --strict over src/
	$(RUN) mypy src

audit:  ## dead code, dependencies, known vulnerabilities, import contracts, complexity
	$(RUN) vulture src --min-confidence 80
	$(RUN) deptry .
	$(RUN) pip-audit --skip-editable --progress-spinner off --cache-dir .venv/pip-audit-cache
	$(RUN) lint-imports
	$(RUN) radon cc src -n C -s

prose:  ## the no-slop checker over the package's two documents
	python3 -I ../.claude/skills/no-slop/scripts/slop-check.py --profile file README.md ARCHITECTURE.md

qa: lint typecheck test-fast audit prose  ## every gate but the integration and acceptance tests

detector:  ## print the impeccable detector commands for a server on PORT (default 8390); the engine is the owner's clone (DECISIONS 2026-11-04 sixth line)
	@for v in 2560x1440 1440x900 1280x800; do echo "IMPECCABLE_BIN=/Users/yevhens/Projects/ai/impeccable/skill/scripts/bin/darwin-arm64/impeccable DO_NOT_TRACK=1 ../.claude/skills/impeccable/scripts/impeccable detect --no-advisory --viewport $$v http://127.0.0.1:$(PORT)/"; done

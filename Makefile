# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

# Entry points for development. Every target is a one-line wrapper around a command
# that also works on its own, so nothing here is required to use the project.
#
# Set PYTHON to run against an interpreter other than the first one on PATH:
#   make check PYTHON=/path/to/python

PYTHON ?= python
SCRIPTS := PYTHON=$(PYTHON) bash scripts

.DEFAULT_GOAL := help
.PHONY: help install lock lint format typecheck test test-cov check smoke \
        smoke-benchmarks smoke-oracles smoke-all package toolchains velvet \
        doctor catalog docs docs-serve clean distclean

help: ## Show this help
	@grep -hE '^[a-z-]+:.*?## ' $(MAKEFILE_LIST) \
		| awk -F ':.*?## ' '{printf "  \033[1m%-16s\033[0m %s\n", $$1, $$2}'

install: ## Install the project and its extras into the active environment
	$(SCRIPTS)/setup.sh

lock: ## Record the installed versions in constraints/
	$(SCRIPTS)/lock.sh

lint: ## Check formatting and lint rules
	$(PYTHON) -m ruff format --check .
	$(PYTHON) -m ruff check .

format: ## Reformat and apply the autofixable lint rules
	$(PYTHON) -m ruff format .
	$(PYTHON) -m ruff check --fix .

typecheck: ## Type-check the package
	$(PYTHON) -m mypy

test: ## Run the unit and integration tests
	$(PYTHON) -m pytest

test-cov: ## Run the tests with a coverage report
	$(PYTHON) -m pytest --cov --cov-report=term-missing

check: ## Everything continuous integration runs
	$(SCRIPTS)/check.sh

smoke: ## Exercise the pipeline end to end, offline
	$(SCRIPTS)/smoke.sh offline

smoke-benchmarks: ## Ingest a sample of every registered benchmark (needs network)
	$(SCRIPTS)/smoke.sh benchmarks

smoke-oracles: ## Judge with every oracle, SWE-bench included (needs network, Docker)
	$(SCRIPTS)/smoke.sh oracles

smoke-all: ## Every smoke case; what this machine cannot run is skipped
	$(SCRIPTS)/smoke.sh all

package: ## Build a wheel and run the offline suite from it, outside the checkout
	$(SCRIPTS)/package.sh

toolchains: ## Install the pinned prover toolchains locally (Dafny, Lean, Nagini)
	$(SCRIPTS)/install/dafny.sh
	$(SCRIPTS)/install/lean.sh
	$(SCRIPTS)/install/nagini.sh

velvet: ## Build the pinned Velvet workspace (tens of minutes, about 9 GB)
	$(SCRIPTS)/install/velvet.sh

doctor: ## Report the environment and which components are ready
	$(PYTHON) -m benchproofer doctor

catalog: ## List the benchmarks, backends, oracles, gates, and providers
	$(PYTHON) -m benchproofer catalog

docs: ## Build the documentation site into site/
	$(PYTHON) -m mkdocs build --strict

docs-serve: ## Serve the documentation with live reload
	$(PYTHON) -m mkdocs serve

clean: ## Remove caches and build output
	rm -rf .mypy_cache .pytest_cache .ruff_cache build dist site htmlcov .coverage
	find . -name '__pycache__' -type d -prune -exec rm -rf {} +

distclean: clean ## Also remove bundles, reports, and downloaded toolchains
	rm -rf bundles cassettes reports smoke-out .toolchains

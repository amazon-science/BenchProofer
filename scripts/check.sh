#!/usr/bin/env bash
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

# Run every check continuous integration runs, in the order that fails fastest.
#
#   bash scripts/check.sh                # format, lint, types, tests, offline smoke
#   bash scripts/check.sh --fix          # reformat and autofix first
#   bash scripts/check.sh --no-smoke     # stop after the unit and integration tests
#   bash scripts/check.sh --strict-smoke # also require that no smoke case was skipped
#
# The smoke step passes on a stock install: a case whose verifier is not installed is
# reported as skipped rather than as a failure, so a checkout without Dafny and Lean
# still gets a verdict on the work it can do. --strict-smoke turns a skip into a
# failure, which is the bar CI applies once it has installed the pinned toolchains:
#
#   make toolchains && bash scripts/check.sh --strict-smoke
#
# A failure prints the command that failed, so it can be rerun on its own.
set -euo pipefail

here="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=scripts/lib/common.sh
. "${here}/lib/common.sh"

fix=0
smoke=1
smoke_profile="offline"
while [ "$#" -gt 0 ]; do
  case "$1" in
    --fix) fix=1; shift ;;
    --no-smoke) smoke=0; shift ;;
    --strict-smoke) smoke_profile="ci"; shift ;;
    -h | --help) sed -n '5,19p' "${BASH_SOURCE[0]}" | cut -c 3-; exit 0 ;;
    *) die "unknown option: $1 (try --help)" ;;
  esac
done

require_python
cd "${REPO_ROOT}"

step() {
  info "$*"
  "$@" || die "failed: $*"
}

if [ "${fix}" -eq 1 ]; then
  step "${PYTHON}" -m ruff format .
  step "${PYTHON}" -m ruff check --fix .
else
  step "${PYTHON}" -m ruff format --check .
  step "${PYTHON}" -m ruff check .
fi

step "${PYTHON}" -m mypy
step "${PYTHON}" -m pytest

if [ "${smoke}" -eq 1 ]; then
  step bash "${here}/smoke.sh" "${smoke_profile}"
fi

info "all checks passed"

#!/usr/bin/env bash
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

# Install Benchproofer into the environment that is currently active.
#
#   conda env create -f environment.yml
#   conda activate benchproofer
#   bash scripts/setup.sh
#
# The install is editable, so a checkout is immediately runnable, and the plugin
# entry points declared in pyproject.toml are registered. When a version lock for
# this platform and interpreter ships in constraints/, it is applied, so the
# dependency tree is the one the project is tested against.
#
# Options:
#   --extras NAME   Extras to install (default: all). "" installs the runtime only.
#   --no-lock       Resolve dependencies freely, ignoring constraints/.
#   --no-doctor     Skip the environment report at the end.
set -euo pipefail

here="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=scripts/lib/common.sh
. "${here}/lib/common.sh"

extras="all"
use_lock=1
run_doctor=1

while [ "$#" -gt 0 ]; do
  case "$1" in
    --extras) extras="${2-}"; shift 2 ;;
    --extras=*) extras="${1#*=}"; shift ;;
    --no-lock) use_lock=0; shift ;;
    --no-doctor) run_doctor=0; shift ;;
    -h | --help) sed -n '5,19p' "${BASH_SOURCE[0]}" | cut -c 3-; exit 0 ;;
    *) die "unknown option: $1 (try --help)" ;;
  esac
done

require_python
python_version="$("${PYTHON}" -c 'import platform; print(platform.python_version())')"
info "installing into ${PYTHON} (Python ${python_version})"

target="${REPO_ROOT}"
if [ -n "${extras}" ]; then
  target="${REPO_ROOT}[${extras}]"
fi

pip_args=(--editable "${target}")
lock="$(lock_file)"
if [ "${use_lock}" -eq 1 ] && [ -f "${lock}" ]; then
  info "applying the version lock $(relative "${lock}")"
  pip_args+=(--constraint "${lock}")
elif [ "${use_lock}" -eq 1 ]; then
  warn "no version lock for $(platform_tag); dependencies will be resolved freely"
  warn "run scripts/lock.sh afterwards to record what was installed"
fi

"${PYTHON}" -m pip install "${pip_args[@]}"

if [ "${run_doctor}" -eq 1 ]; then
  echo
  info "what this installation can do:"
  "${PYTHON}" -m benchproofer doctor
  echo
  info "next: bash scripts/smoke.sh   # exercise the pipeline end to end, offline"
fi

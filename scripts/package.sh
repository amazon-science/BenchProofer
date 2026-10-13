#!/usr/bin/env bash
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

# Build a wheel and prove the installed package works with no checkout in sight.
#
#   bash scripts/package.sh
#
# `pip install -e .` runs out of a checkout, where every file is present whether or not
# the build declares it. A wheel is the opposite: it holds what the build put in it, and
# two of the things this tool needs are data rather than code -- the prompt templates it
# sends to a model, and the fixture corpus the offline smoke profile judges. So the
# wheel is built, checked for that data, installed into a throwaway environment, and run
# from a directory outside the repository, where an accidental import of src/ cannot
# rescue it.
#
# The two optional solver backends are installed with it, so the suite covers every
# backend here as it does in a checkout. The development extras are not: a wheel does
# not need a test runner to be worth installing.
#
# Options:
#   --out DIR     Where to write the wheel (default: dist/).
#   --extras NAME Extras to install with it (default: crosshair,smt). "" for none.
#   --no-lock     Resolve dependencies freely, ignoring constraints/.
#   --keep        Leave the throwaway environment behind, and say where it is.
set -euo pipefail

here="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=scripts/lib/common.sh
. "${here}/lib/common.sh"

out="${REPO_ROOT}/dist"
extras="crosshair,smt"
use_lock=1
keep=0

while [ "$#" -gt 0 ]; do
  case "$1" in
    --out) out="${2-}"; shift 2 ;;
    --out=*) out="${1#*=}"; shift ;;
    --extras) extras="${2-}"; shift 2 ;;
    --extras=*) extras="${1#*=}"; shift ;;
    --no-lock) use_lock=0; shift ;;
    --keep) keep=1; shift ;;
    -h | --help) sed -n '5,25p' "${BASH_SOURCE[0]}" | cut -c 3-; exit 0 ;;
    *) die "unknown option: $1 (try --help)" ;;
  esac
done

require_python
rm -rf "${out}"
info "building a wheel into $(relative "${out}")"
"${PYTHON}" -m pip wheel --no-deps --wheel-dir "${out}" "${REPO_ROOT}"

wheels=("${out}"/benchproofer-*.whl)
[ -f "${wheels[0]}" ] || die "no wheel was written to ${out}"
wheel="${wheels[0]}"

info "checking that $(basename "${wheel}") ships the data the tool reads"
"${PYTHON}" - "${wheel}" <<'EOF' || die "the wheel is incomplete; see pyproject.toml"
import sys
import zipfile

REQUIRED = (
    "benchproofer/formalize/templates/system.md",
    "benchproofer/smoke/fixtures/tasks.jsonl",
    "benchproofer/smoke/fixtures/bundles/coin-change-sound/solution.py",
)
held = set(zipfile.ZipFile(sys.argv[1]).namelist())
missing = [name for name in REQUIRED if name not in held]
for name in missing:
    print(f"missing from the wheel: {name}", file=sys.stderr)
sys.exit(1 if missing else 0)
EOF

scratch="$(mktemp -d)"
cleanup() {
  if [ "${keep}" -eq 1 ]; then
    info "the throwaway environment is at ${scratch}"
  else
    rm -rf "${scratch}"
  fi
}
trap cleanup EXIT

info "installing it into a throwaway environment"
"${PYTHON}" -m venv "${scratch}/venv"
pip_args=("${wheel}${extras:+[${extras}]}")
lock="$(lock_file)"
if [ "${use_lock}" -eq 1 ] && [ -f "${lock}" ]; then
  pip_args+=(--constraint "${lock}")
fi
"${scratch}/venv/bin/python" -m pip install --quiet "${pip_args[@]}"

# From here on, nothing may run inside the repository: the point is to use the
# installed package, and smoke output belongs in the throwaway directory anyway.
cd "${scratch}"
info "what the installed package reports"
"${scratch}/venv/bin/benchproofer" doctor
info "offline smoke, from the installed package"
"${scratch}/venv/bin/benchproofer" smoke offline

info "the wheel installs and runs on its own: $(relative "${wheel}")"

#!/usr/bin/env bash
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

# Install a pinned Nagini into the repository-local toolchain directory.
#
#   bash scripts/install/nagini.sh
#
# Nagini verifies Python against Viper, which runs on a JVM, so the toolchain is an
# interpreter, a JDK and one pinned package rather than a single archive. It gets a
# conda prefix of its own under .toolchains/: Nagini pins its own mypy and solver to
# exact versions, and installing those beside this project's would decide which mypy
# the project is developed against. Nothing is installed into the environment you
# work in, and nothing outside .toolchains/ is touched.
#
# The version below pins the whole toolchain, because Nagini's own metadata pins
# every dependency it has, Z3 included. An unpinned verifier is worse than a missing
# one: it silently changes what a verdict means.
#
# Options:
#   --dir DIR    Toolchain directory (default: $BENCHPROOFER_TOOLCHAIN_DIR
#                or .toolchains in the repository root).
#   --force      Reinstall even if the pinned version is already present.
set -euo pipefail

here="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=scripts/lib/common.sh
. "${here}/../lib/common.sh"

VERSION="1.3.1"
# Nagini 1.3.1 requires 3.12 or newer, and asking for one exact minor keeps two
# machines on the same interpreter rather than on whatever conda-forge ships today.
PYTHON_VERSION="3.12"
# Viper's Silicon backend ships inside the Nagini wheel; this is the JVM it runs on.
JDK_VERSION="17"

toolchain_dir="${BENCHPROOFER_TOOLCHAIN_DIR:-${REPO_ROOT}/.toolchains}"
force=0
while [ "$#" -gt 0 ]; do
  case "$1" in
    --dir) toolchain_dir="${2-}"; shift 2 ;;
    --dir=*) toolchain_dir="${1#*=}"; shift ;;
    --force) force=1; shift ;;
    -h | --help) sed -n '5,24p' "${BASH_SOURCE[0]}" | cut -c 3-; exit 0 ;;
    *) die "unknown option: $1 (try --help)" ;;
  esac
done

prefix="${toolchain_dir}/nagini"
executable="${prefix}/bin/nagini"
installed_version() {
  [ -x "${prefix}/bin/python" ] || return 0
  "${prefix}/bin/python" -m pip show nagini 2>/dev/null | sed -n 's/^Version: //p'
}

if [ "${force}" -eq 0 ] && [ -x "${executable}" ] &&
  [ "$(installed_version)" = "${VERSION}" ]; then
  info "Nagini ${VERSION} is already installed at $(relative "${prefix}")"
  exit 0
fi

# conda, found without assuming an activated shell: an activated environment exports
# CONDA_EXE even where the shell function is not defined.
conda="${BENCHPROOFER_CONDA:-${CONDA_EXE:-}}"
if [ -z "${conda}" ] && have conda; then
  conda="$(command -v conda)"
fi
[ -n "${conda}" ] && [ -x "${conda}" ] || die "no conda executable found
  This project's own environment comes from conda (see README.md), and Nagini needs
  a second one for its interpreter and JVM. Point at the executable directly if it
  is not on PATH:
    BENCHPROOFER_CONDA=/path/to/bin/conda bash scripts/install/nagini.sh
  Or install Nagini and a JDK another way and point the tool at the launcher:
    export BENCHPROOFER_NAGINI=/path/to/bin/nagini"

if [ "${force}" -eq 1 ] && [ -d "${prefix}" ]; then
  info "removing $(relative "${prefix}")"
  "${conda}" env remove --yes --prefix "${prefix}" >/dev/null 2>&1 || rm -rf "${prefix}"
fi

if [ ! -x "${prefix}/bin/python" ]; then
  info "creating a python ${PYTHON_VERSION} environment with a JDK at $(relative "${prefix}")"
  "${conda}" create --yes --quiet --prefix "${prefix}" \
    --channel conda-forge --override-channels \
    "python=${PYTHON_VERSION}" "openjdk=${JDK_VERSION}" ||
    die "conda could not create ${prefix}; nothing else was installed"
fi

info "installing nagini==${VERSION} (it pins its own mypy, jpype1 and z3-solver)"
"${prefix}/bin/python" -m pip install --quiet --no-input "nagini==${VERSION}" ||
  die "pip could not install nagini==${VERSION} into ${prefix}"

# Check each piece separately, so a gap in the install names itself rather than
# turning into a verifier that reaches no verdict on every file it is given.
[ -x "${executable}" ] || die "nagini reports as installed but ${executable} is missing"
[ -x "${prefix}/bin/z3" ] || die "no ${prefix}/bin/z3
  Nagini looks for Z3 beside its own launcher, so a Z3 on PATH is not enough."
[ -x "${prefix}/lib/jvm/bin/java" ] || die "no ${prefix}/lib/jvm/bin/java
  Viper cannot start without a JVM inside the environment:
    ${conda} install --yes --prefix ${prefix} -c conda-forge openjdk=${JDK_VERSION}"
backends="$("${prefix}/bin/python" -c 'import os.path as p, nagini_translation.resources as r
print(p.join(p.dirname(r.__file__), "backends"))')" ||
  die "${prefix}/bin/python cannot import nagini_translation, so the install is broken"
# Viper ships inside the wheel rather than as a separate install, so an empty
# backends directory means a wheel that cannot verify anything.
ls "${backends}"/*.jar >/dev/null 2>&1 ||
  die "no Viper backend under ${backends}; the wheel is incomplete"

# A verdict on a real module beats a file listing. It costs one JVM start, and it is
# the only check here that the pieces work together.
info "verifying a one-method module"
scratch="$(mktemp -d)"
trap 'rm -rf "${scratch}"' EXIT
cat >"${scratch}/smoke.py" <<'PY'
from nagini_contracts.contracts import *


def inc(n: int) -> int:
    Requires(n >= 0)
    Ensures(Result() == n + 1)
    return n + 1
PY
(
  cd "${scratch}"
  JAVA_HOME="${prefix}/lib/jvm" "${executable}" --ide-mode smoke.py
) | grep -q "Verification successful" ||
  die "the toolchain is complete and a trivially correct module did not verify
  Re-run it to read the whole complaint:
    cd $(mktemp -d) && JAVA_HOME=${prefix}/lib/jvm ${executable} --ide-mode <module.py>"

info "installed Nagini ${VERSION} at $(relative "${prefix}")"
info "next: benchproofer doctor   # nagini should now be ready"

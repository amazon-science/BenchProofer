# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

# Shared shell helpers. Sourced by the scripts in scripts/; not executable itself.
#
# Every script in this directory is a thin, readable wrapper around a command that
# is documented in the README. Anything with logic worth testing belongs in the
# Python package instead, where it is type-checked and covered by tests.

# shellcheck shell=bash

REPO_ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)"
export REPO_ROOT

_bold=""
_red=""
_yellow=""
_reset=""
if [ -t 2 ] && [ -z "${NO_COLOR-}" ]; then
  _bold="$(printf '\033[1m')"
  _red="$(printf '\033[31m')"
  _yellow="$(printf '\033[33m')"
  _reset="$(printf '\033[0m')"
fi

info() { printf '%s==>%s %s\n' "${_bold}" "${_reset}" "$*" >&2; }
warn() { printf '%swarning:%s %s\n' "${_yellow}" "${_reset}" "$*" >&2; }
die() {
  printf '%serror:%s %s\n' "${_red}" "${_reset}" "$*" >&2
  exit 1
}

# Print a path relative to the repository root when it is inside it.
relative() { printf '%s\n' "${1#"${REPO_ROOT}/"}"; }

have() { command -v "$1" >/dev/null 2>&1; }

need_tool() {
  have "$1" || die "$1 is required but was not found on PATH${2+; $2}"
}

# Resolve the interpreter to use and export it as PYTHON. Honours a preset PYTHON,
# so a caller can point at an interpreter that is not the first one on PATH.
require_python() {
  if [ -z "${PYTHON-}" ]; then
    for candidate in python3 python; do
      if have "${candidate}"; then
        PYTHON="$(command -v "${candidate}")"
        break
      fi
    done
  fi
  [ -n "${PYTHON-}" ] || die "no python interpreter on PATH; see README.md for setup"
  "${PYTHON}" - <<'EOF' || die "Benchproofer needs Python 3.10 or newer, and ${PYTHON} is older"
import sys

sys.exit(0 if sys.version_info >= (3, 10) else 1)
EOF
  export PYTHON
}

# A tag identifying the platform and interpreter a version lock was made on.
platform_tag() {
  local os
  case "$(uname -s)" in
    Linux) os="linux" ;;
    Darwin) os="macos" ;;
    *) os="$(uname -s | tr '[:upper:]' '[:lower:]')" ;;
  esac
  printf '%s-%s\n' "${os}" "$("${PYTHON}" -c 'import platform, sys
print(f"{platform.python_implementation().lower()}-{sys.version_info.major}{sys.version_info.minor}")')"
}

lock_file() { printf '%s\n' "${REPO_ROOT}/constraints/$(platform_tag).txt"; }

sha256_of() {
  if have sha256sum; then
    sha256sum "$1" | cut -d' ' -f1
  elif have shasum; then
    shasum -a 256 "$1" | cut -d' ' -f1
  else
    die "neither sha256sum nor shasum is available, so a download cannot be verified"
  fi
}

# Download a URL to a path and refuse to keep it unless it hashes as expected.
# An unverified toolchain is worse than a missing one: it silently changes what a
# verdict means.
fetch_verified() {
  local url="$1" expected="$2" destination="$3" actual scratch
  need_tool curl
  scratch="$(mktemp -d)"
  # shellcheck disable=SC2064
  trap "rm -rf '${scratch}'" RETURN
  info "downloading $(basename "${destination}")"
  curl --fail --location --retry 3 --retry-delay 2 --progress-bar \
    --output "${scratch}/download" "${url}"
  actual="$(sha256_of "${scratch}/download")"
  if [ "${actual}" != "${expected}" ]; then
    die "checksum mismatch for ${url}
  expected ${expected}
  received ${actual}"
  fi
  mkdir -p "$(dirname -- "${destination}")"
  mv -f "${scratch}/download" "${destination}"
}

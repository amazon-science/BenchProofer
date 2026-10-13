#!/usr/bin/env bash
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

# Install a pinned Lean 4 release into the repository-local toolchain directory.
#
#   bash scripts/install/lean.sh
#
# The archive and its checksum come from scripts/lib/lean.sh, which is also what the
# Velvet workspace is built with. The lean4 backend uses the Lean kernel alone and does
# not import Mathlib, so this is the whole dependency.
#
# Options:
#   --dir DIR    Toolchain directory (default: $BENCHPROOFER_TOOLCHAIN_DIR
#                or .toolchains in the repository root).
#   --force      Reinstall even if the pinned version is already present.
set -euo pipefail

here="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=scripts/lib/common.sh
. "${here}/../lib/common.sh"
# shellcheck source=scripts/lib/lean.sh
. "${here}/../lib/lean.sh"

VERSION="4.33.0"

toolchain_dir="${BENCHPROOFER_TOOLCHAIN_DIR:-${REPO_ROOT}/.toolchains}"
force=0
while [ "$#" -gt 0 ]; do
  case "$1" in
    --dir) toolchain_dir="${2-}"; shift 2 ;;
    --dir=*) toolchain_dir="${1#*=}"; shift ;;
    --force) force=1; shift ;;
    -h | --help) sed -n '5,16p' "${BASH_SOURCE[0]}" | cut -c 3-; exit 0 ;;
    *) die "unknown option: $1 (try --help)" ;;
  esac
done

executable="${toolchain_dir}/lean/bin/lean"
if [ "${force}" -eq 0 ] && [ -x "${executable}" ] &&
  "${executable}" --version 2>/dev/null | grep -q "${VERSION}"; then
  info "Lean ${VERSION} is already installed at $(relative "${executable}")"
  exit 0
fi

lean_install "${VERSION}" "${toolchain_dir}" ||
  die "Lean ${VERSION} publishes no release for $(uname -s)-$(uname -m)
  Install it another way and point the tool at it:
    export BENCHPROOFER_LEAN=/path/to/lean"

info "installed Lean $("${executable}" --version | head -1) at $(relative "${executable}")"
info "next: benchproofer doctor   # lean4 should now be ready"

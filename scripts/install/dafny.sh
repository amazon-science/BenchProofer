#!/usr/bin/env bash
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

# Install a pinned Dafny release into the repository-local toolchain directory.
#
#   bash scripts/install/dafny.sh
#
# The release archives are self-contained: they carry their own .NET runtime, so
# nothing else has to be installed. Every archive is checked against the SHA-256
# recorded below before it is unpacked, because an unverified verifier is worse
# than a missing one: it silently changes what a verdict means.
#
# Options:
#   --dir DIR    Toolchain directory (default: $BENCHPROOFER_TOOLCHAIN_DIR
#                or .toolchains in the repository root).
#   --force      Reinstall even if the pinned version is already present.
set -euo pipefail

here="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=scripts/lib/common.sh
. "${here}/../lib/common.sh"

VERSION="4.11.0"
BASE_URL="https://github.com/dafny-lang/dafny/releases/download/v${VERSION}"

toolchain_dir="${BENCHPROOFER_TOOLCHAIN_DIR:-${REPO_ROOT}/.toolchains}"
force=0
while [ "$#" -gt 0 ]; do
  case "$1" in
    --dir) toolchain_dir="${2-}"; shift 2 ;;
    --dir=*) toolchain_dir="${1#*=}"; shift ;;
    --force) force=1; shift ;;
    -h | --help) sed -n '5,18p' "${BASH_SOURCE[0]}" | cut -c 3-; exit 0 ;;
    *) die "unknown option: $1 (try --help)" ;;
  esac
done

case "$(uname -s)-$(uname -m)" in
  Linux-x86_64)
    archive="dafny-${VERSION}-x64-ubuntu-22.04.zip"
    sha256="a46a9ff7cdd720f7955854c78e95df13f4cfe6b80691b05f8654fe19e8267179"
    ;;
  Darwin-x86_64)
    archive="dafny-${VERSION}-x64-macos-13.zip"
    sha256="5fc0de946c5b2fad33f16bd22a5b06f4fd0dfa7f6d770284237e3f1f3ca9f73d"
    ;;
  Darwin-arm64)
    archive="dafny-${VERSION}-arm64-macos-13.zip"
    sha256="c90c75e7d5db9c6ccbb7127840dfe43f0ac938b039a7ebed146d8ead383a572f"
    ;;
  *)
    die "Dafny ${VERSION} publishes no release for $(uname -s)-$(uname -m)
  Install it another way and point the tool at it:
    export BENCHPROOFER_DAFNY=/path/to/dafny"
    ;;
esac

executable="${toolchain_dir}/dafny/dafny"
if [ "${force}" -eq 0 ] && [ -x "${executable}" ] &&
  "${executable}" --version 2>/dev/null | grep -q "${VERSION}"; then
  info "Dafny ${VERSION} is already installed at $(relative "${executable}")"
  exit 0
fi

need_tool unzip
scratch="$(mktemp -d)"
trap 'rm -rf "${scratch}"' EXIT

fetch_verified "${BASE_URL}/${archive}" "${sha256}" "${scratch}/${archive}"

info "unpacking into $(relative "${toolchain_dir}")"
mkdir -p "${toolchain_dir}"
rm -rf "${toolchain_dir}/dafny"
# The archive contains a single dafny/ directory holding the executable.
unzip -q "${scratch}/${archive}" -d "${toolchain_dir}"
chmod +x "${executable}"

info "installed $("${executable}" --version | head -1) at $(relative "${executable}")"
info "next: benchproofer doctor   # dafny should now be ready"

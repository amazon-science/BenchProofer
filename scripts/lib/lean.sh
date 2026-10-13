# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

# Fetching a pinned Lean 4 toolchain. Sourced, not executable.
#
# Two installs need one: the lean4 backend, which uses the kernel alone, and the
# Velvet workspace, which is pinned to the toolchain Velvet builds on. So the
# archives, their checksums and the unpacking live here rather than in either script,
# and the versions this repository pins sit side by side where a reader can see both.
#
# A release archive carries a complete toolchain, so no elan and no network access are
# needed once it is unpacked. Each one is checked against the SHA-256 below before it
# is used, because an unverified verifier is worse than a missing one: it silently
# changes what a verdict means. The checksums are of the published archives; recompute
# one with `curl -sL <url> | sha256sum` if you add a version.

# shellcheck shell=bash

#: Where the archives come from.
LEAN_RELEASES="https://github.com/leanprover/lean4/releases/download"

# Echo "<archive> <sha256>" for one version on this platform, or fail.
lean_archive() {
  local version="$1" platform archive sha
  case "$(uname -s)-$(uname -m)" in
    Linux-x86_64) platform="linux" ;;
    Linux-aarch64) platform="linux_aarch64" ;;
    Darwin-x86_64) platform="darwin" ;;
    Darwin-arm64) platform="darwin_aarch64" ;;
    *) return 1 ;;
  esac
  case "${version}-${platform}" in
    4.33.0-linux) sha="4b3fb03c29a1e0a253fb1d11f9bae3725f19a0dc6fc09b3ea16d2c9df3349e2c" ;;
    4.33.0-linux_aarch64) sha="f961a417cba10b6ea0a9d136712d5952813817ffd6680041f09a233526f803a9" ;;
    4.33.0-darwin) sha="18c4adfd2e4538c3668f7e070e88c7a21576dee9fbdf46de7df2ef16c97ffef3" ;;
    4.33.0-darwin_aarch64) sha="db5274b669be270af048b5e4f1e0ce571df6750e411956b3e1e6fcc2012410c2" ;;
    4.24.0-linux) sha="b14f5e5159219dd1a1956c3b806813319f5e94ccd5bdfd56f54520609a5bb5ec" ;;
    4.24.0-linux_aarch64) sha="237f8ef43fb40d16681871fb04b2c56f023afc02a5a3877831d35dd493823c23" ;;
    4.24.0-darwin) sha="a5ef0fb0e14645eaa0e60bc6ba39a07e7deeeec73dc93ce7195b837eb9de2c9f" ;;
    4.24.0-darwin_aarch64) sha="17ee554702c199fc03f37b1c3708245671c93f5d932dcff55a03fa6cdb5e5adf" ;;
    *) return 1 ;;
  esac
  archive="lean-${version}-${platform}.tar.zst"
  printf '%s %s\n' "${archive}" "${sha}"
}

# Unpack a pinned toolchain into <parent>/lean, replacing whatever is there.
lean_install() {
  local version="$1" parent="$2" archive sha scratch
  read -r archive sha < <(lean_archive "${version}") || return 1
  [ -n "${sha}" ] || return 1

  need_tool zstd "install it with conda, or use environment.yml which already lists it"
  need_tool tar
  scratch="$(mktemp -d)"
  # shellcheck disable=SC2064
  trap "rm -rf '${scratch}'" RETURN

  fetch_verified "${LEAN_RELEASES}/v${version}/${archive}" "${sha}" "${scratch}/${archive}"

  info "unpacking Lean ${version} into $(relative "${parent}") (about 2 GB unpacked)"
  mkdir -p "${scratch}/unpacked"
  zstd --decompress --stdout "${scratch}/${archive}" |
    tar --extract --directory "${scratch}/unpacked" --strip-components 1
  # Said out loud, because a caller writing `lean_install ... || die` turns errexit off
  # for this whole function: an unpack that produced nothing must not be allowed to
  # replace a toolchain that works.
  [ -x "${scratch}/unpacked/bin/lean" ] ||
    die "the Lean ${version} archive did not unpack into a toolchain"
  rm -rf "${parent}/lean"
  mkdir -p "${parent}"
  mv "${scratch}/unpacked" "${parent}/lean"
}

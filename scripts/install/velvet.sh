#!/usr/bin/env bash
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

# Build the pinned Velvet workspace in the repository-local toolchain directory.
#
#   bash scripts/install/velvet.sh
#
# Velvet is a Lean library, so its toolchain is a workspace: a pinned Lean release and a
# checkout of Velvet at one commit, built the way Velvet builds itself. Every Velvet
# bundle is then checked inside that workspace. The revisions Velvet's own manifest names
# are kept beside this script and compared against what was built, so a dependency that
# moved is a failure rather than a verifier that quietly became a different one.
#
# This is the largest install here: about 2 GB of toolchain and 7 GB of built libraries,
# and a first build takes tens of minutes even with Mathlib's prebuilt cache. Nothing
# outside the toolchain directory is touched and no elan is installed. The workspace is
# not relocatable, because Velvet finds its solvers through paths fixed when it was
# built: move the toolchain directory and this has to run again.
#
# Options:
#   --dir DIR    Toolchain directory (default: $BENCHPROOFER_TOOLCHAIN_DIR
#                or .toolchains in the repository root).
#   --force      Rebuild even if the pinned workspace is already built.
set -euo pipefail

here="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=scripts/lib/common.sh
. "${here}/../lib/common.sh"
# shellcheck source=scripts/lib/lean.sh
. "${here}/../lib/lean.sh"

VELVET_REPOSITORY="https://github.com/verse-lab/velvet.git"
VELVET_COMMIT="2cf0acb04c510848e597aa6214b7665fea86319d"
# The toolchain that commit builds on. Checked against the checkout below, so the two
# cannot drift apart silently.
LEAN_VERSION="4.24.0"

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

prefix="${toolchain_dir}/velvet"
workspace="${prefix}/workspace"
pins="${here}/velvet/lake-manifest.json"
# Written only once a real Velvet method has verified, so its presence means the
# workspace works rather than that some files arrived in the right place.
stamp="${prefix}/built.txt"

if [ "${force}" -eq 0 ] && [ -f "${stamp}" ] &&
  grep -qx "lean ${LEAN_VERSION}" "${stamp}" &&
  grep -qx "velvet ${VELVET_COMMIT}" "${stamp}"; then
  info "the pinned Velvet workspace is already built at $(relative "${workspace}")"
  exit 0
fi

require_python
need_tool git "the pinned Velvet commit is checked out with it"
need_tool curl "Mathlib's prebuilt libraries are downloaded with it"
need_tool unzip "Velvet unpacks its own solvers with it"

rm -f "${stamp}"
if [ ! -x "${prefix}/lean/bin/lean" ] ||
  ! "${prefix}/lean/bin/lean" --version 2>/dev/null | grep -q "${LEAN_VERSION}"; then
  lean_install "${LEAN_VERSION}" "${prefix}" ||
    die "Lean ${LEAN_VERSION} publishes no release for $(uname -s)-$(uname -m)
  Build the workspace another way and point the tool at it:
    export BENCHPROOFER_VELVET=/path/to/velvet-workspace"
fi
# Ahead of any elan or system Lean, so the pinned toolchain is the one that builds.
export PATH="${prefix}/lean/bin:${PATH}"

# A checkout already at the pinned commit is kept, which is what lets an interrupted
# build resume instead of downloading Mathlib again.
if [ "$(git -C "${workspace}" rev-parse HEAD 2>/dev/null)" = "${VELVET_COMMIT}" ]; then
  info "reusing the Velvet checkout at $(relative "${workspace}")"
else
  info "cloning Velvet into $(relative "${workspace}")"
  rm -rf "${workspace}"
  mkdir -p "${prefix}"
  git clone --quiet "${VELVET_REPOSITORY}" "${workspace}" ||
    die "could not clone ${VELVET_REPOSITORY}"
  git -C "${workspace}" checkout --quiet --detach "${VELVET_COMMIT}" ||
    die "${VELVET_REPOSITORY} has no commit ${VELVET_COMMIT}"
fi

# What is verified has to be the pinned commit and nothing else, so an edited checkout
# stops the install rather than becoming the verifier.
[ -z "$(git -C "${workspace}" status --porcelain)" ] ||
  die "the checkout at $(relative "${workspace}") has local modifications
  Nothing was built. Remove that directory and re-run to get the pinned commit back."

toolchain="$(tr -d '[:space:]' <"${workspace}/lean-toolchain")"
[ "${toolchain}" = "leanprover/lean4:v${LEAN_VERSION}" ] ||
  die "Velvet ${VELVET_COMMIT} builds on ${toolchain}, not the Lean ${LEAN_VERSION} installed here
  Update LEAN_VERSION in this script and the archive table in scripts/lib/lean.sh together."

# Lake resolves dependencies from the manifest in the checkout and rewrites it when it
# updates one, so comparing that file against the pins kept here is what catches a
# dependency that moved. Fail closed: other revisions are a different verifier.
compare_pins() {
  "${PYTHON}" - "${pins}" "${workspace}/lake-manifest.json" <<'PY'
import json
import sys


def pins(path: str) -> dict[str, str]:
    with open(path, encoding="utf-8") as handle:
        return {p["name"]: p["rev"] for p in json.load(handle)["packages"]}


pinned, built = (pins(path) for path in sys.argv[1:3])
report = [
    f"  {name}: pinned at {rev}, found {built.get(name, '(absent)')}"
    for name, rev in sorted(pinned.items())
    if built.get(name) != rev
]
report += [
    f"  {name}: {rev} is not pinned"
    for name, rev in sorted(built.items())
    if name not in pinned
]
print("\n".join(report))
sys.exit(1 if report else 0)
PY
}

drift="$(compare_pins)" || die "the checkout does not match $(relative "${pins}")
${drift}
  Nothing was built."

# Mathlib publishes its build products, so this turns hours of elaboration into a
# download. Velvet, Loom and lean-auto are not cached and are built from source below.
info "downloading Mathlib's prebuilt libraries (several GB, once)"
(cd "${workspace}" && lake exe cache get) ||
  die "lake could not fetch Mathlib's cache; re-run to resume the download"

# Velvet proves with Z3 and cvc5 and downloads both itself, into the directory its
# tactics look in. Building that target alone keeps the failure legible if it cannot.
info "downloading the solvers Velvet proves with"
(cd "${workspace}" && lake build downloadDependencies) ||
  die "lake could not download Velvet's solvers"
for solver in z3 cvc5; do
  executable="${workspace}/.lake/packages/Loom/.lake/build/${solver}"
  [ -x "${executable}" ] ||
    die "no ${solver} at ${executable}, which is where Velvet's tactics look for it"
done

info "building Velvet (tens of minutes on a first run)"
(cd "${workspace}" && lake build Velvet.Std) ||
  die "lake could not build Velvet in ${workspace}
  Read the whole complaint by re-running it there:
    cd ${workspace} && PATH=${prefix}/lean/bin:\$PATH lake build Velvet.Std"

drift="$(compare_pins)" || die "the build changed the pinned dependencies
${drift}
  The workspace is left in place, unstamped, so nothing will verify against it."

# A verdict on a real method beats a directory listing: it is the only check here that
# the toolchain, the libraries and the solvers work together.
info "verifying a one-method program"
scratch="$(mktemp -d)"
trap 'rm -rf "${scratch}"' EXIT
cat >"${scratch}/smoke.lean" <<'LEAN'
import Velvet.Std

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

method inc (n : Int) return (out : Int)
  require n ≥ 0
  ensures out = n + 1
  do
    return n + 1

prove_correct inc by
  loom_solve
LEAN
(cd "${workspace}" && lake env lean "${scratch}/smoke.lean") ||
  die "the workspace built and a trivially correct method did not verify
  Re-run it to read the whole complaint:
    cd ${workspace} && PATH=${prefix}/lean/bin:\$PATH lake env lean <file.lean>"

printf 'lean %s\nvelvet %s\n' "${LEAN_VERSION}" "${VELVET_COMMIT}" >"${stamp}"
info "built the pinned Velvet workspace at $(relative "${workspace}")"
info "next: benchproofer doctor   # velvet should now be ready"

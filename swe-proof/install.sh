#!/usr/bin/env bash
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

# Builds lean_shared/.lake once -- the single v4.24.0 workspace shared by the
# velvet AND lean backends (docs/reproducing.md section 4). Idempotent. The
# nagini verifier env is separate (conda; see scripts/nagini_verify.sh).
#
# The build honours the pins rather than re-resolving them. `lake build`
# materializes every dependency at the `rev` recorded in lake-manifest.json,
# which is the machine-readable form of PINS.md; the check at the end refuses a
# workspace whose revisions or toolchain have drifted from that table. Updating
# is deliberately not part of an install: 9 of the 12 dependencies are requested
# by branch (`inputRev` is `main` or `master`), so `lake update` moves them to
# whatever those branches point at today and rewrites lean-toolchain as well. A
# verdict is only meaningful relative to the prover that produced it, so moving
# the pins changes the artifact instead of refreshing it. SBU_LEAN_REPIN=1 asks
# for that explicitly.
set -euo pipefail

export PATH="$HOME/.elan/bin:$PATH"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SHARED="$ROOT/lean_shared"
PY="${SBU_PYTHON:-python3}"
cd "$SHARED"

if ! command -v elan >/dev/null 2>&1; then
  echo "[install] elan not found on PATH (\$HOME/.elan/bin is already searched)." >&2
  echo "[install] Install it, then re-run:" >&2
  echo "[install]   curl https://elan.lean-lang.org/elan-init.sh -sSf | sh -s -- -y" >&2
  exit 2
fi
if [[ ! -f lake-manifest.json ]]; then
  echo "[install] no lake-manifest.json in $SHARED: nothing pins the dependencies," >&2
  echo "[install] and a build would resolve them off moving branches. Restore it" >&2
  echo "[install] from the checkout before building." >&2
  exit 2
fi

echo "[install] elan: $(elan --version)"
echo "[install] toolchain: $(cat lean-toolchain)"

if [[ "${SBU_LEAN_REPIN:-0}" == "1" ]]; then
  echo "[install] SBU_LEAN_REPIN=1: re-resolving every dependency from its branch."
  echo "[install] This MOVES the pins in lake-manifest.json, so PINS.md has to be"
  echo "[install] updated to match and the recorded verdicts describe the old ones."
  # --keep-toolchain: an update otherwise also rewrites lean-toolchain, and the
  # SMT-backed library does not build on later toolchains.
  lake update --keep-toolchain -R 2>&1 | tail -20
fi

# prebuilt Mathlib oleans avoid a ~1h compile
echo "[install] lake exe cache get (Mathlib oleans)..."
lake exe cache get 2>&1 | tail -5 || echo "[install] WARN cache get failed; will compile Mathlib from source"

echo "[install] lake build (Velvet + local anchor; downloads z3/cvc5)..."
lake build 2>&1 | tail -40

# Fail closed on drift: a workspace built from other revisions elaborates
# against a different Mathlib and hands back verdicts that do not describe the
# artifact being shipped. Same argument as the fingerprint gate in
# scripts/lean_verify.sh, applied to the canonical workspace itself. The
# comparison lives in scripts/lean_pins.py so the test suite can make it too --
# reaching this line costs a full Mathlib build, so it is not where a drift
# committed to git gets caught.
echo "[install] checking the workspace against PINS.md..."
"$PY" "$ROOT/scripts/lean_pins.py" --shared "$SHARED" | sed 's/^/[install] /'

echo "[install] DONE. .lake size:"
du -sh .lake 2>/dev/null || true

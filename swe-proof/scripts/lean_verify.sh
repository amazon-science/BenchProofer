#!/usr/bin/env bash
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

# Single Lean verifier entry point (velvet + lean backends; the exit protocol is
# docs/adding_a_backend.md §1):
# `lake env lean <file>` against the shared workspace under a hard wall clock.
# Exit 0 iff the file elaborates with NO sorry/error; 124 = timeout (surfaced
# verbatim so the caller can record status="timeout"); default cap 300s,
# overridable per bundle via $2.
set -uo pipefail

FILE="${1:?usage: lean_verify.sh <file.lean> [timeout_seconds]}"
TIMEOUT="${2:-300}"

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SHARED="$ROOT/lean_shared"
export PATH="$HOME/.elan/bin:$PATH"

# Optional LOCAL-DISK mirror of the workspace ($SBU_LEAN_SHARED).
#
# If `lean_shared/.lake` lives on a NETWORK filesystem, this is the single
# largest cost in a build wave: elaborating one file re-opens the whole Mathlib
# olean tree, so the work is bound on filesystem metadata latency rather than on
# CPU, and cores sit idle while `import Mathlib` alone takes tens of seconds.
# Mirroring the workspace to local disk removes that cost. There is no tool to
# make one because there is nothing to it: after `install.sh` has built
# `lean_shared/.lake`, copy the tree and name the copy.
#
#     cp -a lean_shared/. "$SBU_LEAN_SHARED"/     # or the default path below
#
# `cp -a` rather than a fresh `lake build` on the local disk: the mirror has to
# be the SAME oleans, not an equivalent rebuild, or the fingerprint below
# attests to nothing.
#
# The mirror is used ONLY if its dependency PINS fingerprint-match the canonical
# workspace. A mirror built from different pins would elaborate against a
# different Mathlib and hand back verdicts that do not describe the artifact
# being shipped -- a silent corruption of every gate record it touches, which is
# far worse than being slow. So the check fails CLOSED: any mismatch, any
# missing file, and the canonical workspace is used, with the reason on stderr.
fingerprint() {
  # The four files that pin what the oleans are: dep revisions, toolchain, the
  # build's own targets, and the shared prelude every artifact imports.
  cat "$1/lake-manifest.json" "$1/lean-toolchain" "$1/lakefile.lean" \
      "$1/LeanShared.lean" 2>/dev/null | sha256sum | cut -d' ' -f1
}
# Defaulted, not opt-in: the two fleets spawn ~90 agent subprocesses that each
# invoke this script, and they read it fresh per build, so a default reaches
# work already in flight where an env var would need a relaunch (throwing away
# hours of unfinished agent work). The fingerprint check below is what makes a
# default safe -- an absent or mismatched mirror is simply not used.
MIRROR="${SBU_LEAN_SHARED-${TMPDIR:-/tmp}/lean_shared_local}"
if [[ -n "$MIRROR" && "$MIRROR" != "$SHARED" ]]; then
  if [[ ! -d "$MIRROR/.lake" ]]; then
    echo "lean_verify: mirror $MIRROR has no .lake; using $SHARED" >&2
  elif [[ "$(fingerprint "$MIRROR")" != "$(fingerprint "$SHARED")" ]]; then
    echo "lean_verify: mirror $MIRROR pins differ from $SHARED; using $SHARED" >&2
  else
    SHARED="$MIRROR"
  fi
fi

if [[ ! -f "$FILE" ]]; then
  echo "lean_verify: no such file: $FILE" >&2
  exit 2
fi
# absolute path before we cd into the shared workspace
FILE="$(cd "$(dirname "$FILE")" && pwd)/$(basename "$FILE")"

# Refuse a probe file sitting in the REPO ROOT. Both fleets tell their agents to
# keep scratch under /tmp, and prose has not been enough: agents have repeatedly
# written a rival next to the checkout and redirected its build log beside it, so
# `new__rival.lean` and `new__rival.log` end up staged into a commit and ship in
# the released artifacts. Refusing here is what actually stops it -- the agent's
# own inner loop fails immediately with the fix in the message, instead of the
# stray file surviving until someone reads `git status`. Bundle files, /tmp, and
# anything in a subdirectory are unaffected; only the root itself is refused.
if [[ "$(dirname "$FILE")" == "$ROOT" ]]; then
  echo "lean_verify: refusing to build $(basename "$FILE") in the repo root;" \
       "put scratch in a private dir, e.g. \$(mktemp -d /tmp/pbt.XXXXXX)" >&2
  exit 2
fi

# Optional HOST-WIDE concurrency cap ($SBU_LEAN_SLOTS). Every Lean build in the
# repo funnels through this script, so this is the only place a global bound can
# live: during a corpus-wide build the builds come from two uncoordinated sources
# — the gate's own worker pool AND each authoring agent iterating on its variants
# — and neither can see the other's load. Measured on a 96-core host:
# throughput rises to ~65 builds/min at 96-way and each build is ~200 MB private
# (the 5.3 GB RSS is shared mmap'd Mathlib oleans), so the cap exists to stop
# CPU thrash, not OOM. Unset = no cap, so single runs and the test suite are
# unaffected.
SLOTS="${SBU_LEAN_SLOTS:-0}"
if [[ "$SLOTS" =~ ^[0-9]+$ ]] && (( SLOTS > 0 )); then
  LOCKDIR="${SBU_LEAN_SLOT_DIR:-${TMPDIR:-/tmp}/sbu_lean_slots}"
  mkdir -p "$LOCKDIR"
  # Wait for a free slot: try each lock non-blockingly, then block on a random
  # one so waiters cannot livelock or stampede onto slot 0.
  while :; do
    for ((s = 0; s < SLOTS; s++)); do
      exec {SLOT_FD}>>"$LOCKDIR/$s.lock"
      if flock -n "$SLOT_FD"; then break 2; fi
      exec {SLOT_FD}>&-
    done
    exec {SLOT_FD}>>"$LOCKDIR/$((RANDOM % SLOTS)).lock"
    if flock -w 5 "$SLOT_FD"; then break; fi
    exec {SLOT_FD}>&-
  done
  # The lock is held for the lifetime of this shell: released on exit, including
  # a kill, so a slot can never leak.
fi

# Run from $SHARED so `lake env` resolves the right manifest and sees the
# prebuilt Velvet + Mathlib oleans.
cd "$SHARED"
OUT="$(timeout --signal=KILL "${TIMEOUT}s" \
  lake env lean "$FILE" 2>&1)"
CODE=$?

echo "$OUT"

if [[ $CODE -eq 137 || $CODE -eq 124 ]]; then
  echo "lean_verify: TIMEOUT after ${TIMEOUT}s" >&2
  exit 124
fi

# Exit 3 on sorry/admit warnings (defense in depth; G-HYGIENE is the
# authoritative sorry scan).
if [[ $CODE -ne 0 ]]; then
  exit "$CODE"
fi
if echo "$OUT" | grep -qiE "declaration uses 'sorry'|uses 'admit'"; then
  echo "lean_verify: file elaborates but uses sorry/admit" >&2
  exit 3
fi
exit 0

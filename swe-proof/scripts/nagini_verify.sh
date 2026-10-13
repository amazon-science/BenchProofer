#!/usr/bin/env bash
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

# Single Nagini verifier entry point (keeps JVM config + env selection
# uniform). Exit 0 iff verification succeeds.
#
# Enforces a HARD wall-clock timeout (default 300s, SBN_VERIFY_TIMEOUT):
# Nagini/Z3 can run for hours on a pathological obligation, hanging callers.
# On timeout the whole process group (JVM + Z3) is killed, exit 124 --
# distinguishable from a normal "Verification failed" (exit 1); treat 124 as
# "simplify the model/proof; it did not converge".
#
# Usage: bash scripts/nagini_verify.sh <module.py> [extra nagini args...]
#        SBN_VERIFY_TIMEOUT=600 bash scripts/nagini_verify.sh <module.py>
#        bash scripts/nagini_verify.sh --check-env   # resolve the env and stop
#
# The env itself is built and validated by scripts/setup_verifier_env.sh
# (`--check` there validates one without touching it); docs/reproducing.md
# section 4 has the prerequisites.
set -euo pipefail

ENV_NAME="${SWEBENCH_NAGINI_VERIFIER_ENV:-swebench-nagini-verifier}"
TIMEOUT="${SBN_VERIFY_TIMEOUT:-300}"

# Cap silicon's INTRA-verification parallelism: SBN_PARALLEL_VERIFIERS, default 1,
# 0 leaves silicon's own default (the core count, each verifier with its own Z3
# process, so one verification fans out across the whole machine and fights the
# outer per-cell parallelism).
#
# Keep the cap low. On a module that must be REFUTED a fanned-out solver can fail
# to converge where N=1 refutes, a non-convergence is recorded as "no verdict",
# and the gates that conclude from a rejection charge a missing verdict to the
# specification -- so a higher cap loses verdicts outright rather than trading
# them for speed.
PARALLEL_VERIFIERS="${SBN_PARALLEL_VERIFIERS:-1}"
VIPER_ARGS=()
if [ "$PARALLEL_VERIFIERS" != "0" ]; then
  # NOTE: --viper-arg takes ONE comma-separated string; repeating the flag makes
  # silicon's scallop parser throw ExcessArguments, which surfaces as a bogus
  # exit 1 that looks exactly like a real verification failure.
  VIPER_ARGS=("--viper-arg=--numberOfParallelVerifiers,$PARALLEL_VERIFIERS")
fi

# Locate the verifier env WITHOUT assuming conda is on PATH: a minimal PATH is
# normal for a non-interactive caller. Guessing one install directory is what
# makes this fragile: exit 2 is "no verdict", so every gate run under a PATH the
# guess misses stamps a real spec as unverified and overwrites the verdict that
# was there. Cheap filesystem probes come first and `conda info --base` last,
# because it starts a Python interpreter. Set SWEBENCH_NAGINI_VERIFIER_PREFIX to
# skip discovery entirely.
# NOTE: plain `[ ... ] && CANDIDATES+=(...)` would be a `set -e` landmine here --
# a false test makes the list exit 1 and kills the script, i.e. exactly the
# silent exit 2 this block exists to remove. Hence the `if`s.
CANDIDATES=()
if [ -n "${SWEBENCH_NAGINI_VERIFIER_PREFIX:-}" ]; then
  CANDIDATES+=("$SWEBENCH_NAGINI_VERIFIER_PREFIX")
fi
# An activated env exports CONDA_EXE=<base>/bin/conda even when PATH is bare.
if [ -n "${CONDA_EXE:-}" ]; then
  CANDIDATES+=("$(dirname "$(dirname "$CONDA_EXE")")/envs/$ENV_NAME")
fi
for base in "$HOME/miniconda3" "$HOME/anaconda3" "$HOME/miniforge3" \
            "$HOME/mambaforge" /opt/conda /usr/local/conda; do
  CANDIDATES+=("$base/envs/$ENV_NAME")
done
PREFIX=""
for cand in "${CANDIDATES[@]}"; do
  if [ -x "$cand/bin/nagini" ]; then PREFIX="$cand"; break; fi
done
if [ -z "$PREFIX" ] && command -v conda >/dev/null 2>&1; then
  base="$(conda info --base 2>/dev/null || true)"
  if [ -n "$base" ] && [ -x "$base/envs/$ENV_NAME/bin/nagini" ]; then
    PREFIX="$base/envs/$ENV_NAME"
  fi
  CANDIDATES+=("${base:-<conda info --base failed>}/envs/$ENV_NAME")
fi
if [ -z "$PREFIX" ]; then
  echo "[sbn] verifier env '$ENV_NAME' not found -- build it with:" \
       "bash scripts/setup_verifier_env.sh (or, if it exists elsewhere, set" \
       "SWEBENCH_NAGINI_VERIFIER_PREFIX to its prefix)" >&2
  printf '[sbn]   looked for bin/nagini under: %s\n' "${CANDIDATES[@]}" >&2
  exit 2
fi

# `--check-env` resolves the toolchain and stops, so a long-running caller can
# confirm at startup that verification is possible at all instead of learning it
# one gate stamp at a time: an unusable verifier reaches no verdict, and a
# no-verdict stamp overwrites a real one.
if [ "${1:-}" = "--check-env" ]; then
  echo "[sbn] verifier env: $PREFIX"
  exit 0
fi

# Nagini/Viper still spawns Z3 as OS children (fewer now, see the cap above);
# `timeout` reaps the group only on timeout, so on NORMAL completion the Z3
# children orphan and pile up -- fatal under parallelism. Fix: run in a fresh
# process group (setsid, foreground via `-w` so stdout + exit code pass
# through), and a trap kills that whole group on exit to reap any leftover Z3.
# `set -e` must be off around the run so a nonzero verifier code is captured,
# not fatal.
# Nagini's mypy layer keeps .mypy_cache_strict/_nonstrict in the CWD; a WARM
# cache nondeterministically crashes typeinfo.py:392 ('NoneType' has no
# attribute 'path'), surfacing as "verification failed in ~0.7s" on modules
# that verify in ~10s (measured 2026-08-19 on 9bdfd29f/nagini: cold pass 9.7s,
# warm fail 0.8s, repeatably). Shared root caches also raced parallel runs and
# left stray dirs that trip G-INTEGRITY. Fix: absolutize the module path, then
# run from a FRESH temp working dir so every verification gets a cold private
# cache; the temp dir is removed on exit.
MODULE_ARG="$1"; shift
case "$MODULE_ARG" in /*) : ;; *) MODULE_ARG="$PWD/$MODULE_ARG" ;; esac
SBN_WORKDIR="$(mktemp -d /tmp/sbn_verify.XXXXXX)"
cd "$SBN_WORKDIR"

set +e
setsid -w timeout --kill-after=10s --signal=TERM "$TIMEOUT" \
  env JAVA_HOME="$PREFIX/lib/jvm" PATH="$PREFIX/bin:$PATH" \
  "$PREFIX/bin/nagini" --ide-mode "${VIPER_ARGS[@]}" "$MODULE_ARG" "$@" &
verify_pid=$!
cleanup() { kill -KILL -"$verify_pid" 2>/dev/null; rm -rf "$SBN_WORKDIR"; }  # -pid = the setsid group
trap cleanup EXIT
wait "$verify_pid"; rc=$?
cleanup
if [ "$rc" -eq 124 ] || [ "$rc" -eq 137 ]; then
  echo "[sbn] Verification TIMED OUT after ${TIMEOUT}s (exit $rc) -- Nagini/Z3 did not converge." >&2
  echo "[sbn] Simplify the model or proof annotations; this is not a normal verification failure." >&2
  exit 124
fi
exit "$rc"

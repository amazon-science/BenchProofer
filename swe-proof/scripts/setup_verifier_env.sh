#!/usr/bin/env bash
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

# Build, repair or validate the conda env that scripts/nagini_verify.sh looks for.
#
# The imperative backend's verifier lives in its OWN env on purpose: nagini's
# dependencies are exact pins on tooling this project also installs -- nagini
# requires pytest==7.0.0, the `dev` extra requires pytest>=8.0 -- and its pinned
# typed-ast==1.5.4 caps the interpreter at 3.10 while the package itself requires
# >=3.10, so the two only ever overlap on one interpreter version. Nothing
# activates this env -- nagini_verify.sh finds it by name and runs
# <prefix>/bin/nagini out of it -- so this script only has to make that prefix
# exist and be complete.
#
# What "complete" means, and why each piece is needed:
#   <prefix>/bin/nagini        the pinned verifier (pyproject's `verifier-nagini`
#                              extra is the single source of the pin)
#   <prefix>/bin/z3            nagini resolves Z3 beside its own launcher and
#                              then beside its interpreter, never on PATH
#                              (nagini_translation/lib/config.py:_get_z3_path;
#                              Z3_EXE overrides). z3-solver is one of nagini's
#                              own pins, so a correct install already has it
#   <prefix>/lib/jvm/bin/java  nagini_verify.sh exports
#                              JAVA_HOME=<prefix>/lib/jvm, which is where the
#                              conda-forge `openjdk` package unpacks. A system
#                              JDK is NOT picked up: the JDK must be IN the env
#   silicon.jar & friends      Viper's backends ship inside the nagini wheel, so
#                              there is no separate Viper install to do
# Boogie and mono are deliberately absent: config.boogie_path is read only by the
# Carbon backend (nagini_translation/verifier.py, class Carbon), and
# nagini_verify.sh runs nagini's default backend, Silicon.
#
# This env holds the verifier ONLY. The project itself is not installed here;
# install that in your own env with `pip install -e ".[eval,dev]"`.
#
# Idempotent: re-running against a complete env checks it and changes nothing.
# It never half-builds -- each missing prerequisite is a loud exit naming the
# command that fixes it. `--check` is the same validation with every installing
# step refused instead of run, which is the form a driver or CI job wants at
# startup. Run with --help for the options.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ENV_NAME="${SWEBENCH_NAGINI_VERIFIER_ENV:-swebench-nagini-verifier}"
# 3.10 because nagini pins typed-ast==1.5.4, a C extension whose upstream support
# -- both its classifiers and its ABI-tagged wheels -- stops at 3.10.
PY_VERSION="${SBN_SETUP_PYTHON:-3.10}"
JDK_VERSION="${SBN_SETUP_JDK:-17}"
SMOKE="${SBN_SETUP_SMOKE:-1}"
DRY_RUN="${SBN_SETUP_DRY_RUN:-0}"
CHECK=0

say()  { printf '[setup] %s\n' "$*"; }
# die <what is wrong> [<what to do about it>...]
die()  {
  printf '[setup] ERROR: %s\n' "$1" >&2
  shift
  if [ "$#" -gt 0 ]; then printf '[setup]   %s\n' "$@" >&2; fi
  exit 1
}
# Every mutating step goes through run(), and every call to it is guarded by
# CHECK -- that is what makes `--check` a promise rather than an intention.
run()  {
  if [ "$DRY_RUN" = "1" ]; then printf '[setup] DRY RUN, would run: %s\n' "$*"; return 0; fi
  printf '[setup] + %s\n' "$*"
  "$@"
}
usage() {
  cat <<'EOF'
usage: bash scripts/setup_verifier_env.sh [--check]

Build, repair or validate the conda env that scripts/nagini_verify.sh runs the
Nagini/Viper verifier out of. Idempotent: anything already present at the pin is
left alone.

  --check     validate an existing env and install nothing. Each missing piece is
              an error naming the command that would supply it. Exit 0 means the
              wrapper resolves this env and -- unless SBN_SETUP_SMOKE=0 -- that a
              real verification reached a verdict in it.
  -h, --help  this text.

environment:
  SWEBENCH_NAGINI_VERIFIER_ENV     env name (default: swebench-nagini-verifier)
  SWEBENCH_NAGINI_VERIFIER_PREFIX  exact env location, instead of a name under
                                   the conda base. nagini_verify.sh reads this
                                   too, so export it if the env lives somewhere
                                   it does not search
  SBN_CONDA                        conda executable, when it is not on PATH and
                                   CONDA_EXE is unset
  SBN_SETUP_PYTHON                 interpreter for a NEW env (default: 3.10)
  SBN_SETUP_JDK                    conda-forge openjdk version (default: 17)
  SBN_SETUP_SMOKE=0                skip the closing end-to-end verification
  SBN_SETUP_DRY_RUN=1              print the build plan, install nothing
EOF
}

while [ "$#" -gt 0 ]; do
  case "$1" in
    --check)    CHECK=1 ;;
    -h|--help)  usage; exit 0 ;;
    *)          die "unknown argument: $1" "Run with --help for the options." ;;
  esac
  shift
done
if [ "$CHECK" = "1" ] && [ "$DRY_RUN" = "1" ]; then
  die "--check and SBN_SETUP_DRY_RUN=1 ask for opposite things: one inspects a real env, the other only prints what a build would do." \
      "Pick one:" \
      "  bash scripts/setup_verifier_env.sh --check" \
      "  SBN_SETUP_DRY_RUN=1 bash scripts/setup_verifier_env.sh"
fi
[ "$CHECK" = "0" ] || say "mode: --check (nothing will be installed)"

# ---- 1. a conda executable, found the same way nagini_verify.sh finds the env.
CONDA="${SBN_CONDA:-}"
if [ -n "$CONDA" ] && [ ! -x "$CONDA" ]; then
  die "SBN_CONDA=$CONDA is not an executable." \
      "Point it at the conda binary itself, e.g. \$HOME/miniforge3/bin/conda, or unset it."
fi
if [ -z "$CONDA" ] && [ -n "${CONDA_EXE:-}" ] && [ -x "$CONDA_EXE" ]; then
  CONDA="$CONDA_EXE"
fi
if [ -z "$CONDA" ] && command -v conda >/dev/null 2>&1; then
  CONDA="$(command -v conda)"
fi
if [ -z "$CONDA" ]; then
  for base in "$HOME/miniforge3" "$HOME/miniconda3" "$HOME/mambaforge" \
              "$HOME/anaconda3" /opt/conda /usr/local/conda; do
    if [ -x "$base/bin/conda" ]; then CONDA="$base/bin/conda"; break; fi
  done
fi
if [ -n "$CONDA" ]; then
  say "conda: $CONDA"
elif [ "$CHECK" = "1" ] && [ -n "${SWEBENCH_NAGINI_VERIFIER_PREFIX:-}" ]; then
  # A validation of a named env has to ask conda where the base is; a validation
  # of an explicit prefix does not need conda at all, and requiring it would fail
  # exactly the container/shared-install case the prefix variable exists for.
  say "no conda found; --check does not need one when the prefix is explicit"
else
  die "no conda executable found (tried \$SBN_CONDA, \$CONDA_EXE, PATH, and the usual install dirs)." \
      "Install Miniforge or Miniconda, or point at an existing one:" \
      "  SBN_CONDA=/path/to/bin/conda bash scripts/setup_verifier_env.sh"
fi

# The env is addressed by PREFIX throughout, so the same code path builds a
# named env under the conda base and an env at an explicit location.
if [ -n "${SWEBENCH_NAGINI_VERIFIER_PREFIX:-}" ]; then
  PREFIX="$SWEBENCH_NAGINI_VERIFIER_PREFIX"
else
  BASE="$("$CONDA" info --base 2>/dev/null || true)"
  [ -n "$BASE" ] || die \
    "\`$CONDA info --base\` produced nothing, so the env location is unknown." \
    "Give one explicitly:" \
    "  SWEBENCH_NAGINI_VERIFIER_PREFIX=/path/to/env bash scripts/setup_verifier_env.sh"
  PREFIX="$BASE/envs/$ENV_NAME"
fi
say "target env: $PREFIX"

# ---- 2. the interpreter.
if [ -x "$PREFIX/bin/python" ]; then
  HAVE_PY="$("$PREFIX/bin/python" -c 'import sys; print("%d.%d" % sys.version_info[:2])')"
  say "env exists, python $HAVE_PY (leaving it alone)"
  case "$HAVE_PY" in
    3.[0-9]|3.10) : ;;          # 3.10 and older: the cap typed-ast imposes
    *) die \
      "env $PREFIX has python $HAVE_PY, above the 3.10 where nagini's pinned typed-ast==1.5.4 stops." \
      "Either remove the env and let this script rebuild it:" \
      "  ${CONDA:-conda} env remove -y -p $PREFIX && bash scripts/setup_verifier_env.sh" \
      "or build a second one under a different name:" \
      "  SWEBENCH_NAGINI_VERIFIER_ENV=nagini-py310 bash scripts/setup_verifier_env.sh" ;;
  esac
else
  [ "$CHECK" = "0" ] || die \
    "no $PREFIX/bin/python: that env does not exist, and --check does not create it." \
    "Build it first:" \
    "  bash scripts/setup_verifier_env.sh"
  say "creating env with python $PY_VERSION"
  run "$CONDA" create -y -p "$PREFIX" -c conda-forge "python=$PY_VERSION" \
    || die "conda create failed for $PREFIX; nothing else was installed."
fi

# ---- 3. the JVM, inside the env (see the header: JAVA_HOME is <prefix>/lib/jvm).
if [ -x "$PREFIX/lib/jvm/bin/java" ]; then
  say "jvm present: $("$PREFIX/lib/jvm/bin/java" -version 2>&1 | head -1)"
else
  [ "$CHECK" = "0" ] || die \
    "no $PREFIX/lib/jvm/bin/java, and --check does not install it. Viper cannot start without it." \
    "  ${CONDA:-conda} install -y -p $PREFIX -c conda-forge openjdk=$JDK_VERSION"
  say "installing openjdk $JDK_VERSION into the env"
  run "$CONDA" install -y -p "$PREFIX" -c conda-forge "openjdk=$JDK_VERSION" \
    || die "conda install of openjdk=$JDK_VERSION failed; the env cannot run Viper."
fi

# ---- 4. the verifier itself, at the pin pyproject declares.
PIN="$(sed -n '/^verifier-nagini = \[/,/^\]/{s/^[[:space:]]*"\(nagini==[^"]*\)".*/\1/p;}' \
        "$ROOT/pyproject.toml" 2>/dev/null | head -1 || true)"
if [ -z "$PIN" ]; then
  die "could not read the nagini pin out of $ROOT/pyproject.toml (\`verifier-nagini\` extra)." \
      "Run this from a checkout, or install the pin yourself:" \
      "  $PREFIX/bin/python -m pip install 'nagini==<the version that extra names>'"
fi
WANT="${PIN#nagini==}"
HAVE_NAGINI=""
if [ -x "$PREFIX/bin/python" ]; then
  HAVE_NAGINI="$("$PREFIX/bin/python" -m pip show nagini 2>/dev/null \
                  | sed -n 's/^Version: //p' | head -1 || true)"
fi
if [ "$HAVE_NAGINI" = "$WANT" ]; then
  say "nagini $HAVE_NAGINI already installed at the pin"
else
  [ "$CHECK" = "0" ] || die \
    "$PREFIX has nagini ${HAVE_NAGINI:-not installed}, the pin is $WANT, and --check does not install it." \
    "  $PREFIX/bin/python -m pip install '$PIN'" \
    "A verdict from a different verifier version is not the verdict this benchmark recorded."
  [ -z "$HAVE_NAGINI" ] || say "nagini $HAVE_NAGINI installed, pin is $WANT; replacing"
  # nagini's own metadata pins everything it needs (mypy, typed-ast, toposort,
  # jpype1, astunparse, pytest, z3-solver) to exact versions, so this one
  # pinned requirement fixes the whole verifier toolchain.
  say "installing $PIN (it pins its own mypy, typed-ast, jpype1 and z3-solver)"
  run "$PREFIX/bin/python" -m pip install "$PIN" \
    || die "pip install $PIN failed in $PREFIX." \
           "If it failed building typed-ast, the env's python is too new -- see step 2."
fi

if [ "$DRY_RUN" = "1" ]; then
  say "dry run: stopping before the post-install checks (nothing was installed)"
  exit 0
fi

# ---- 5. check every piece separately, so a gap names itself.
[ -x "$PREFIX/bin/nagini" ] || die \
  "no $PREFIX/bin/nagini even though nagini reports as installed." \
  "Reinstall in that env and read pip's output:" \
  "  $PREFIX/bin/python -m pip install --force-reinstall '$PIN'"
[ -x "$PREFIX/bin/z3" ] || die \
  "no $PREFIX/bin/z3. nagini looks for Z3 beside its own launcher, so a Z3 on PATH is not enough." \
  "Reinstall the verifier, which pins the solver it wants:" \
  "  $PREFIX/bin/python -m pip install --force-reinstall '$PIN'" \
  "or point nagini at an existing binary with Z3_EXE=/path/to/z3."
[ -x "$PREFIX/lib/jvm/bin/java" ] || die \
  "no $PREFIX/lib/jvm/bin/java, which is the JAVA_HOME nagini_verify.sh exports." \
  "Install the JDK INTO the env (a system JDK is not used):" \
  "  ${CONDA:-conda} install -y -p $PREFIX -c conda-forge openjdk=$JDK_VERSION"
BACKENDS="$("$PREFIX/bin/python" -c \
  'import os, nagini_translation.resources as r; print(os.path.join(os.path.dirname(r.__file__), "backends"))' \
  2>/dev/null || true)"
[ -n "$BACKENDS" ] || die \
  "$PREFIX/bin/python cannot import nagini_translation, so the install is broken." \
  "  $PREFIX/bin/python -c 'import nagini_translation'   # read the traceback" \
  "  $PREFIX/bin/python -m pip install --force-reinstall '$PIN'"
[ -f "$BACKENDS/silicon.jar" ] || die \
  "no silicon.jar under $BACKENDS; the nagini wheel that ships Viper's backends is incomplete." \
  "  $PREFIX/bin/python -m pip install --force-reinstall '$PIN'"

say "nagini:  $("$PREFIX/bin/python" -m pip show nagini 2>/dev/null | sed -n 's/^Version: /nagini /p')"
say "z3:      $("$PREFIX/bin/z3" --version 2>&1 | head -1)"
say "java:    $("$PREFIX/lib/jvm/bin/java" -version 2>&1 | head -1)"
say "backends: $(ls "$BACKENDS" | tr '\n' ' ')"

# ---- 6. prove the caller can FIND this env, not just that it exists. The
# wrapper probes a fixed list of conda install dirs, so two things go wrong here
# and both surface downstream as "no verdict" rather than as an env problem: an
# env in a directory it does not search, and -- with two conda installs on the
# host -- a DIFFERENT env of the same name that it searches earlier. Compare the
# prefix it resolves with the one just checked instead of trusting exit 0.
#
# The probe runs with SWEBENCH_NAGINI_VERIFIER_PREFIX unset, because with it set
# the answer is always yes for this shell and says nothing about the shell a
# driver will start in.
resolved_prefix() {
  env -u SWEBENCH_NAGINI_VERIFIER_PREFIX SWEBENCH_NAGINI_VERIFIER_ENV="$ENV_NAME" \
    bash "$ROOT/scripts/nagini_verify.sh" --check-env 2>/dev/null \
    | sed -n 's/^\[sbn\] verifier env: //p' | head -1
}
FOUND="$(resolved_prefix || true)"
if [ -n "$FOUND" ] && [ "$FOUND" -ef "$PREFIX" ]; then
  say "nagini_verify.sh discovers the env by itself"
elif [ -n "$FOUND" ]; then
  die "scripts/nagini_verify.sh resolves a different env: $FOUND" \
      "That one, not $PREFIX, is what every gate run would use." \
      "Pin the one you just checked, everywhere the pipeline runs:" \
      "  export SWEBENCH_NAGINI_VERIFIER_PREFIX=$PREFIX"
elif [ -n "${SWEBENCH_NAGINI_VERIFIER_PREFIX:-}" ]; then
  say "note: the wrapper finds this env only via SWEBENCH_NAGINI_VERIFIER_PREFIX;" \
      "export it in every shell and driver environment that runs a gate"
else
  die "the env is complete but scripts/nagini_verify.sh does not find it." \
      "Export the prefix (add it to your shell profile / the fleet's environment):" \
      "  export SWEBENCH_NAGINI_VERIFIER_PREFIX=$PREFIX"
fi

# ---- 7. end-to-end: a verdict on a real module beats a file listing. Costs one
# JVM + Viper startup.
if [ "$SMOKE" = "1" ]; then
  SMOKE_DIR="$(mktemp -d "${TMPDIR:-/tmp}/sbn-verifier-smoke.XXXXXX")"
  trap 'rm -rf "$SMOKE_DIR"' EXIT
  cat >"$SMOKE_DIR/smoke.py" <<'PY'
from nagini_contracts.contracts import *


def inc(n: int) -> int:
    Requires(n >= 0)
    Ensures(Result() == n + 1)
    return n + 1
PY
  say "smoke test: verifying a one-function module (set SBN_SETUP_SMOKE=0 to skip)"
  if bash "$ROOT/scripts/nagini_verify.sh" "$SMOKE_DIR/smoke.py"; then
    say "smoke test verified"
    trap - EXIT
    rm -rf "$SMOKE_DIR"
  else
    rc=$?
    trap - EXIT               # keep the module, or the command below cannot be run
    die "the env is complete but a trivially-correct module did not verify (exit $rc)." \
        "The module was kept; re-run it for the full output:" \
        "  bash scripts/nagini_verify.sh $SMOKE_DIR/smoke.py"
  fi
fi

if [ "$CHECK" = "1" ]; then
  say "checked: $PREFIX is complete and reachable; nothing was installed"
else
  say "done: $PREFIX is ready; scripts/nagini_verify.sh needs no activation."
fi

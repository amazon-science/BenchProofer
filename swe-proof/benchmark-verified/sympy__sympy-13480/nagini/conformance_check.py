#!/usr/bin/env python3
"""G-CONF differential conformance check for sympy__sympy-13480 (nagini).

SHADOW  — the impl region of model.py copied VERBATIM (the model IS Python;
          no transliteration, and the impl region contains no contract calls
          to strip — Requires/Ensures live outside the impl markers). The
          three @ContractOnly axiom callees (`primary`, `sibling`,
          `directed_infinity`) are, per the contract, bound to the REAL
          patched-repo callees they model (mapping.md: `coth`, `tanh`,
          `S.ComplexInfinity`) through the handle bridge below.

BRIDGE  — mapping.md "Type abstraction": a sympy expression is modelled as an
          opaque int handle, and handle equality against the distinguished
          sentinel handle models the `is`-identity test against the singleton
          `S.ComplexInfinity`. Realized here by interning expressions on
          OBJECT IDENTITY: each distinct live object gets a fresh int handle
          (the intern table keeps every seen object alive, so ids stay
          stable). Because the sentinel is a singleton, handle equality
          against `directed_infinity()`'s handle is exactly the `is` test —
          the only handle comparison the impl performs.

ORACLE  — the REAL patched repo function the model models (mapping.md:
          the periodic-part branch inside `coth.eval`,
          sympy/functions/elementary/hyperbolic.py). PYTHONPATH=/testbed with
          the gold patch applied by the gate before this script runs. For an
          argument `a` that the unchanged peel-off helper `_peeloff_ipi`
          splits into a remainder `x` and a truthy periodic part `m` — i.e.
          exactly the Requires-satisfying inputs: the precondition comments
          say `m` is the present, non-trivial periodic part — the observable
          is `coth(a)` (the full patched evaluation, whose value on this
          domain is produced by the modelled branch), diffed against the
          shadow run on the bridged handles of the SAME peeled parts.
          A version-drift guard (as in axiom_check.py) skips, without
          counting, any peeled `m` whose `coth(m)` is neither the
          directed-infinity sentinel nor zero — outside the branch's design
          domain, the branch is not the producer of `coth(a)`, so a diff
          there would be noise, not signal. At the pinned sympy version every
          truthy peeled `m` is an I*pi/2-multiple, so nothing is skipped.

INPUTS  — boundary cases (the instance's two FAIL_TO_PASS witnesses, a
          symbolic remainder, remainder-zero-adjacent and sign-varied cases,
          a bases x mults grid) plus fuzz over rational remainders and
          rational I*pi multipliers until >= 1e5 Requires-satisfying inputs
          are diffed. Pinned seed: 13480. The oracle/shadow pair is a pure
          deterministic function of the constructed argument, so
          observations are memoized per distinct argument (the 4500-odd
          distinct fuzz keys are each evaluated once against the real repo);
          every generated input is still individually counted and diffed.

Exit 0 iff zero disagreements; on disagreement prints the input and both
outputs and exits 1. stdlib only (plain random) + the repo under test.
"""
import random
import sys

SEED = 13480
N_INPUTS = 100_000
MAX_DRAWS = 8 * N_INPUTS

from sympy import coth, tanh, log, tan, I, pi, S, Symbol, Rational, sympify
from sympy.functions.elementary.hyperbolic import _peeloff_ipi


# ---------------------------------------------------------------------------
# Handle bridge: opaque int handles interned on object identity (mapping.md
# "Type abstraction"). The intern table holds a reference to every expression
# it has seen, so ids cannot be recycled while a handle is live.
# ---------------------------------------------------------------------------

_expr_of = {}     # handle -> expression object
_handle_of = {}   # id(expression object) -> handle


def to_handle(e):
    key = id(e)
    h = _handle_of.get(key)
    if h is None:
        h = len(_expr_of) + 1
        _handle_of[key] = h
        _expr_of[h] = e
    return h


# ---------------------------------------------------------------------------
# The three @ContractOnly axiom callees, bound to the REAL repo callees they
# model (mapping.md "Callee provenance"), lifted through the handle bridge.
# ---------------------------------------------------------------------------

def primary(arg: int) -> int:
    return to_handle(coth(_expr_of[arg]))          # REAL repo coth


def sibling(arg: int) -> int:
    return to_handle(tanh(_expr_of[arg]))          # REAL repo tanh


def directed_infinity() -> int:
    return to_handle(S.ComplexInfinity)            # REAL repo singleton


# ---------------------------------------------------------------------------
# model.py impl region, VERBATIM (no contract calls appear inside the impl
# markers; the signature's int carrier is the handle type above).
# ---------------------------------------------------------------------------

def periodic_part_simplification(x: int, m: int) -> int:
    primary_m = primary(m)
    if primary_m == directed_infinity():
        return primary(x)
    else:
        return sibling(x)


# ---------------------------------------------------------------------------
# Differential check on one constructed argument. Returns True if the input
# was Requires-satisfying (counted), False if out of the modelled domain
# (skipped, not counted). Disagreements are appended to `disagreements`.
# ---------------------------------------------------------------------------

def check_case(arg, disagreements):
    a = sympify(arg)
    if not a.is_Add:
        return False                       # the modelled branch needs an Add
    x, m = _peeloff_ipi(a)                 # unchanged peel-off helper
    if not m:
        return False                       # precondition: m present/non-trivial
    cm = coth(m)
    if not (cm is S.ComplexInfinity or cm == 0):
        return False                       # version-drift guard (see ORACLE)

    shadow_h = periodic_part_simplification(to_handle(x), to_handle(m))
    shadow_e = _expr_of[shadow_h]

    try:
        observed = coth(a)                 # REAL patched repo evaluation
    except Exception as exc:               # the shadow never raises here
        disagreements.append((a, x, m, shadow_e, "raised %r" % (exc,)))
        return True

    if shadow_e != observed:
        disagreements.append((a, x, m, shadow_e, observed))
    return True


def boundary_args():
    y = Symbol('y')
    # The instance's two FAIL_TO_PASS witness arguments (the first becomes an
    # Add via the branch cut of log on a negative real).
    yield log(tan(2))
    yield 1 + I * pi / 2
    # Symbolic remainder, both sentinel and finite periodic evaluations.
    yield y + I * pi
    yield y + I * pi / 2
    yield y + 3 * I * pi / 2
    yield y + 2 * I * pi
    # Sign-varied / small / large multiplier cases over concrete remainders.
    yield 1 + I * pi
    yield -1 + I * pi / 2
    yield 1 - I * pi / 2
    yield -1 - I * pi
    yield Rational(1, 2) + I * pi / 2
    yield Rational(-3, 2) + 5 * I * pi / 2
    yield 2 + 7 * I * pi
    yield log(2) + I * pi / 2
    yield log(2) + I * pi
    # multiplier not itself a half-integer: the peel leaves a residual in x
    yield 1 + Rational(2, 3) * I * pi
    yield 1 + Rational(7, 3) * I * pi
    yield -2 + Rational(-5, 3) * I * pi
    # bases x mults grid (mirrors the domain axiom_check.py validated)
    bases = [S(1), Rational(3, 2), log(2), Rational(5, 2), S(2), y]
    mults = [Rational(1, 2), S(1), Rational(3, 2), S(2), Rational(5, 2), S(3),
             Rational(1, 3), Rational(2, 3), -S(1), Rational(-1, 2)]
    for x0 in bases:
        for k in mults:
            yield x0 + k * I * pi


def main():
    rng = random.Random(SEED)
    disagreements = []
    counted = 0

    for arg in boundary_args():
        if check_case(arg, disagreements):
            counted += 1
        if disagreements:
            break

    # Fuzz: rational remainder + rational I*pi multiplier; memoized per
    # distinct constructed key (the check is deterministic per argument),
    # each drawn input still counted and diffed.
    memo = {}   # key -> (fired, n_disagreements_recorded_for_key)
    draws = 0
    while counted < N_INPUTS and not disagreements and draws < MAX_DRAWS:
        draws += 1
        key = (rng.randint(-6, 6), rng.randint(1, 5),
               rng.randint(-6, 6), rng.randint(1, 4))
        hit = memo.get(key)
        if hit is None:
            x0 = Rational(key[0], key[1])
            k = Rational(key[2], key[3])
            before = len(disagreements)
            fired = check_case(x0 + k * I * pi, disagreements)
            memo[key] = (fired, len(disagreements) - before)
            hit = memo[key]
        if hit[0]:
            counted += 1

    if disagreements:
        print("G-CONF FAIL: %d disagreement(s) after %d counted inputs "
              "(seed=%d):" % (len(disagreements), counted, SEED))
        for a, x, m, sh, orc in disagreements[:10]:
            print("  arg=%r  peeled x=%r m=%r\n    shadow(impl region)=%r\n"
                  "    real patched repo =%r" % (a, x, m, sh, orc))
        return 1

    if counted < N_INPUTS:
        print("G-CONF ERROR: only %d Requires-satisfying inputs reached in "
              "%d draws — the peel-off convention of this sympy version "
              "leaves the modelled domain unexercised (seed=%d)"
              % (counted, draws, SEED))
        return 1

    print("G-CONF OK: model.py impl shadow (real coth/tanh/ComplexInfinity "
          "callees through the handle bridge) agrees with the real patched "
          "repo evaluation on %d Requires-satisfying inputs (%d distinct "
          "fuzz keys, seed=%d), 0 disagreements." %
          (counted, len(memo), SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())

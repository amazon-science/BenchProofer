#!/usr/bin/env python3
"""G-CONF differential conformance check for sympy__sympy-13615 (plan §4.1).

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both sides on the same fuzzed inputs and comparing observable outputs:

  * SHADOW  — the R/I-tagged ops of Solution.lean's impl region transliterated
              to Python: classify each element of the finite operand by the
              ambient set's three-valued membership verdict
              (`contains in [True, False] else None`, the `ternary_sift` of
              mapping.md §2) and partition into
                definite  = elements with verdict False  (definiteOut)
                symbolic  = elements with verdict None    (symbolicUnknown)
              dropping the verdict-True elements.  This is exactly
              `complementFinite` under the mapping.md bijection
              (FiniteSet ↔ List Int; Set.contains verdict ↔ Trit).
  * ORACLE  — `patch.diff`'s behaviour: the patched
              `sympy.sets.sets.Set._complement(ambient, other)` applied at
              base_commit (the real correctness oracle, G-RESOLVE).  Its return
              value — `Union(FiniteSet(*sifted[False]),
              Complement(FiniteSet(*sifted[None]), self, …))` — is decomposed
              back into (definite-member set, symbolic-member set).

They must agree (as sets of elements) on every input.  Exit 0 iff zero
disagreements; any disagreement is a mechanical R/I-fidelity counterexample.

Runs in-container (the prebuilt SWE-Bench instance image, with the gold patch
applied), sympy + stdlib only.  The fuzz seed is pinned (mapping.md §4) for a
deterministic verdict.
"""
import random
import sys

SEED = 13615
N_FUZZ = 100_000

from sympy import (FiniteSet, Interval, Symbol, Integer, Union, Complement,
                   EmptySet, S)
from sympy.sets.sets import Set


# --- the membership trichotomy, mirroring the gold `ternary_sift` exactly -----
def _trit(ambient, el):
    """Return 'inside' | 'outside' | 'unknown' for ambient.contains(el),
    using the gold's `contains if contains in [True, False] else None` key."""
    c = ambient.contains(el)
    if c in [True, False]:           # decided
        return "inside" if c == True else "outside"
    return "unknown"                  # symbolic Contains -> None bucket


# --- SHADOW: complementFinite's definiteOut / symbolicUnknown selections ------
def _shadow(ambient, elems):
    definite, symbolic = [], []
    for el in elems:
        t = _trit(ambient, el)
        if t == "outside":
            definite.append(el)        # definiteOut: verdict False
        elif t == "unknown":
            symbolic.append(el)        # symbolicUnknown: verdict None
        # t == "inside": dropped (in neither field)
    return frozenset(definite), frozenset(symbolic)


# --- ORACLE: the real patched Set._complement, decomposed ---------------------
def _decompose(result):
    """Read (definite members, symbolic members) off the patched return value:
    a FiniteSet contributes definite members; a Complement(FiniteSet, self)
    contributes symbolic members; EmptySet contributes nothing; a Union is the
    join of its terms."""
    definite, symbolic = set(), set()
    terms = list(result.args) if isinstance(result, Union) else [result]
    for t in terms:
        if isinstance(t, Complement):
            inner = t.args[0]
            if isinstance(inner, FiniteSet):
                symbolic |= set(inner.args)
        elif isinstance(t, FiniteSet):
            definite |= set(t.args)
        elif t == S.EmptySet or isinstance(t, EmptySet):
            pass
        else:
            # Unexpected shape — surface it as a disagreement, not a silent pass.
            raise ValueError("unexpected complement term: %r" % (t,))
    return frozenset(definite), frozenset(symbolic)


def _oracle(ambient, other):
    # Call the modeled function directly (unbound) so we test exactly the gold
    # hunk's branch, independent of any caller-side reduce.
    result = Set._complement(ambient, other)
    return _decompose(result)


# --- fuzz input generation ----------------------------------------------------
def _make_case(rng):
    """Build (ambient, other_finiteset, elems) with a mix of numbers (decidable)
    and symbols (undetermined), so all three verdicts occur."""
    kind = rng.choice(["interval", "finite"])
    if kind == "interval":
        lo = rng.randint(-50, 0)
        hi = rng.randint(1, 50)
        ambient = Interval(lo, hi)
    else:
        pts = rng.sample(range(-50, 51), rng.randint(1, 6))
        ambient = FiniteSet(*[Integer(p) for p in pts])

    elems = []
    n = rng.randint(0, 6)
    for _ in range(n):
        c = rng.random()
        if c < 0.45:
            elems.append(Integer(rng.randint(-80, 80)))      # number: decidable
        else:
            elems.append(Symbol("s%d" % rng.randint(0, 20)))  # symbol: unknown
    # FiniteSet drops duplicates; keep `elems` distinct so list↔set is exact.
    seen, distinct = set(), []
    for e in elems:
        if e not in seen:
            seen.add(e); distinct.append(e)
    # The modeled branch is `elif isinstance(other, FiniteSet)`. An empty operand
    # is EmptySet (not a FiniteSet) and never enters it, so it is out of scope —
    # guarantee at least one element so `other` is a genuine FiniteSet.
    if not distinct:
        distinct = [Symbol("s%d" % rng.randint(0, 20))]
    other = FiniteSet(*distinct)
    return ambient, other, list(other.args)


def _boundary_cases():
    x, y, z = Symbol("x"), Symbol("y"), Symbol("z")
    out = []
    # The issue's own example: {x, y, 2} \ [-10, 10].
    out.append((Interval(-10, 10), FiniteSet(x, y, Integer(2))))
    # All symbols (all unknown).
    out.append((Interval(-10, 10), FiniteSet(x, y, z)))
    # All numbers, mix of inside/outside.
    out.append((Interval(-10, 10), FiniteSet(Integer(2), Integer(50), Integer(-99))))
    # Single inside number (all dropped -> empty result).
    out.append((Interval(-10, 10), FiniteSet(Integer(0))))
    # Finite ambient.
    out.append((FiniteSet(Integer(1), Integer(2), Integer(3)),
                FiniteSet(Integer(1), Integer(5), x)))
    return [(amb, other, list(other.args)) for amb, other in out]


def main():
    rng = random.Random(SEED)
    checked = 0
    disagreements = 0

    cases = _boundary_cases()
    cases += [_make_case(rng) for _ in range(N_FUZZ)]

    for ambient, other, elems in cases:
        try:
            o_def, o_sym = _oracle(ambient, other)
        except Exception as exc:  # noqa: BLE001
            print("ORACLE error on ambient=%r other=%r: %r" % (ambient, other, exc))
            disagreements += 1
            continue
        s_def, s_sym = _shadow(ambient, elems)
        checked += 1
        if s_def != o_def or s_sym != o_sym:
            disagreements += 1
            if disagreements <= 10:
                print("DISAGREE ambient=%r other=%r" % (ambient, other))
                print("  shadow definite=%r symbolic=%r" % (set(s_def), set(s_sym)))
                print("  oracle definite=%r symbolic=%r" % (set(o_def), set(o_sym)))

    if disagreements:
        print("G-CONF FAIL: %d/%d disagreements (seed=%d)."
              % (disagreements, checked, SEED))
        return 1
    print("G-CONF OK: R/I shadow of complementFinite agrees with patch.diff "
          "behaviour on %d inputs (seed=%d), 0 disagreements." % (checked, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())

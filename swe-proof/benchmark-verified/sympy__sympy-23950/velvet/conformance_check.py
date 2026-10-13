#!/usr/bin/env python3
"""G-CONF differential conformance check for sympy__sympy-23950 (plan §4.1).

Refutes (does not prove) the single I-tagged refinement leg of refinement.md by
executing both sides on the same fuzzed inputs and comparing observable outputs:

  * SHADOW  — the I-tagged op of Solution.lean's `asSet` impl
              (`out = Except.ok a.container`), transliterated to Python over the
              real repo type via the mapping.md bijection: the modeled
              `MembershipAssertion` carrier ↔ the real membership-assertion
              object, its `container` component ↔ the assertion's second stored
              component (`.args[1]`), `Except.ok v` ↔ the value `v` returned
              normally. So the shadow returns `assertion.args[1]`.
  * ORACLE  — patch.diff's behaviour: the patched `Contains.as_set` applied at
              base_commit (the real correctness oracle, G-RESOLVE). The harness
              applies patch.diff before this runs.

They must agree on every membership-assertion input. Exit 0 iff zero
disagreements; any disagreement is a mechanical I-fidelity counterexample.

Runs in-container (the prebuilt SWE-Bench instance image), stdlib + sympy only.
The fuzz seed is pinned (mapping.md §4) for a deterministic verdict.
"""
import random
import sys

SEED = 23950
N_FUZZ = 100_000


def build_shadow_oracle_gen():
    """Return (shadow_fn, oracle_fn, gen_fn) closed over a sympy environment."""
    from sympy import (
        Symbol, Contains, FiniteSet, Interval, S, Integer, Rational,
    )

    # A pool of symbols to use as the tested element.
    elems = [Symbol(n) for n in ("x", "y", "z", "a", "b")]
    elems += [Integer(0), Integer(1), Integer(-2), Integer(7), Rational(3, 2)]

    # A pool of sets to use as the container (the second component).
    base_syms = [Symbol(n) for n in ("p", "q", "r")]
    sets = [
        S.Reals, S.Integers, S.Naturals, S.Rationals, S.Complexes,
        S.EmptySet, S.UniversalSet,
        FiniteSet(*base_syms),
        FiniteSet(Integer(1), Integer(2), Integer(3)),
        FiniteSet(base_syms[0]),
        Interval(0, 1),
        Interval(-2, 5),
    ]

    def make(rng):
        x = rng.choice(elems)
        s = rng.choice(sets)
        # Contains(x, s) where s is a genuine Set; Contains.eval may collapse to
        # a boolean/Set for decidable cases, so keep only the ones that stay a
        # symbolic Contains (those are exactly where as_set is meaningful and
        # where the F2P tests live).
        c = Contains(x, s)
        return c, s

    def oracle(c):
        """patch.diff's behaviour: the real patched Contains.as_set()."""
        return c.as_set()

    def shadow(c, s):
        """asSet transliterated: return the assertion's container component,
        i.e. its second stored component (`.args[1]`)."""
        return c.args[1]

    return shadow, oracle, make


def main():
    try:
        shadow, oracle, make = build_shadow_oracle_gen()
    except Exception as e:  # pragma: no cover - environment failure
        print("G-CONF ERROR: could not import sympy env: %r" % (e,))
        return 2

    from sympy import Contains

    rng = random.Random(SEED)
    disagreements = []
    count = 0

    for _ in range(N_FUZZ):
        c, s = make(rng)
        # Only assertions that remain a symbolic Contains expose as_set; a
        # collapsed boolean/Set result is a different code path (Contains.eval).
        if not isinstance(c, Contains):
            continue
        count += 1
        try:
            o = oracle(c)
        except Exception as e:
            disagreements.append(("oracle-raised", repr(c), repr(e)))
            if len(disagreements) >= 5:
                break
            continue
        sh = shadow(c, s)
        # Observable equality of the resulting set objects (sympy structural ==).
        if sh != o:
            disagreements.append((repr(c), repr(sh), repr(o)))
            if len(disagreements) >= 5:
                break

    if disagreements:
        print("G-CONF FAIL: %d disagreement(s): %r"
              % (len(disagreements), disagreements))
        return 1
    print("G-CONF OK: I-shadow of asSet (return the assertion's container "
          "component) agrees with the patched as_set() on %d symbolic "
          "membership assertions (seed=%d), 0 disagreements." % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())

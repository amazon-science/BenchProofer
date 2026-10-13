#!/usr/bin/env python
"""G-CONF: differential conformance for sympy__sympy-23950.

Runs INSIDE the instance image with the gold patch applied (apply_gold=True,
PYTHONPATH=/testbed). Builds the Python shadow of the Lean `implementation_asSet`
skeleton (the R op: return the stored set operand) and diffs it against the REAL
patched `Contains.as_set` over a boundary catalogue plus >=1e5 randomized draws.

  observable: `Contains(element, setArg).as_set()` for a fuzzed element symbol
  and a fuzzed set operand drawn from a catalogue of sympy Set values.

Shadow (transliteration of implementation_asSet / problem_spec_asSet):
    Contains(x, s).as_set()  ->  s            # i.e. the stored set operand,
                                              #      args[1], returned verbatim

The bijection is object identity: the Lean impl returns `some c.setArg`, the set
operand the assertion was built with. The shadow therefore expects
`Contains(x, s).as_set()` to equal that same `s` (the canonicalized operand the
object actually stored, read back as `obj.args[1]`).

Exit 0 iff zero disagreements. stdlib-only fuzzing (pinned seed).
"""
import random
import sys

SEED = 23950
N_RANDOM = 120_000  # >= 1e5


def main():
    try:
        from sympy import (Contains, Symbol, FiniteSet, Interval, S, Integer,
                           Rational, Union, Intersection)
    except Exception as e:  # pragma: no cover
        print(f"status=fail could not import callees: {e!r}")
        return 1

    rng = random.Random(SEED)
    disagreements = 0
    checked = 0

    def report(key, real, shadow):
        nonlocal disagreements
        # real / shadow are sympy objects; compare by structural equality.
        ok = (real == shadow) and (real is not None)
        if not ok:
            disagreements += 1
            if disagreements <= 5:
                print(f"MISMATCH {key!r}: real={real!r} shadow={shadow!r}")

    # element symbols (the membership element x)
    elem_names = ["x", "y", "z", "a", "b", "i", "n", "p", "q"]
    elems = [Symbol(nm) for nm in elem_names]

    # a catalogue of set operands (the setArg). Each is a sympy Set.
    def set_catalogue():
        sets = [
            S.Integers, S.Reals, S.Naturals, S.Naturals0, S.Rationals,
            S.Complexes, S.EmptySet, S.UniversalSet,
            FiniteSet(1, 2, 3), FiniteSet(Symbol('y')), FiniteSet(0),
            FiniteSet(Symbol('a'), Symbol('b')),
            Interval(0, 1), Interval(-2, 3), Interval.open(0, 5),
            Interval(Integer(-1), Rational(7, 2)),
            Union(FiniteSet(1), Interval(2, 3)),
            Intersection(S.Integers, Interval(0, 10)),
        ]
        return sets

    sets = set_catalogue()

    def check_one(x, s, key):
        nonlocal checked
        try:
            c = Contains(x, s)
        except Exception:
            return  # construction rejected this pairing; skip
        # Contains may evaluate to a literal True/False (no .as_set worth
        # comparing as a stored-operand identity) — only test genuine
        # Contains objects, mirroring the symbolic-element case the fix targets.
        if getattr(c, "func", None).__name__ != "Contains":
            return
        # The shadow: implementation_asSet returns the stored set operand,
        # i.e. the object's args[1] (the canonicalized set it actually stored).
        shadow = c.args[1]
        real = c.as_set()
        report(key, real, shadow)
        checked += 1
        # also pin: the produced value IS a value (never absent) and equals
        # the stored operand — the discriminating clause vs the prepatch.
        if real is None:
            report((key, "none"), real, shadow)

    # ---- boundary catalogue: the exact F2P assertions + every set kind ----
    y = Symbol('y')
    check_one(Symbol('x'), FiniteSet(y), ("F2P", "FiniteSet"))
    check_one(Symbol('x'), S.Integers, ("F2P", "Integers"))
    check_one(Symbol('x'), S.Reals, ("F2P", "Reals"))
    for s in sets:
        for x in elems[:3]:
            check_one(x, s, ("boundary", repr(s)))

    # ---- randomized fuzz ----
    for _ in range(N_RANDOM):
        x = rng.choice(elems)
        s = rng.choice(sets)
        check_one(x, s, ("fuzz",))

    print(f"checked={checked} disagreements={disagreements}")
    if disagreements == 0:
        print(f"status=pass conformance OK ({checked} checks, 0 disagreements)")
        return 0
    print(f"status=fail {disagreements} disagreement(s)")
    return 1


if __name__ == "__main__":
    sys.exit(main())

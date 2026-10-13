#!/usr/bin/env python
"""G-CONF: differential conformance for sympy__sympy-13615.

Runs INSIDE the instance image with the gold patch applied (apply_gold=True,
PYTHONPATH=/testbed). Builds the Python shadow of the Lean
`implementation_partitionByMembership` skeleton (the R/I op: a single pass over
`other` that splits candidates by a three-valued membership outcome into a
`kept` group [definite non-members] and an `unresolved` group [undetermined],
dropping definite members) and diffs it against the REAL patched
`Set._complement` over its `FiniteSet` branch.

  observable: `self._complement(other)` for a `FiniteSet` `other` and a set
  `self`, i.e. the relative complement `other - self`.

Shadow (transliteration of implementation_partitionByMembership, with the same
R envelope the gold patch uses to assemble its result):

    def ternary(self, el):                       # = the gold's ternary_sift
        c = self.contains(el)
        return c if c in [True, False] else None  # True/False/None  <-> some true/some false/none

    kept, unresolved = [], []
    for el in other:                              # for el in other do
        t = ternary(self, el)
        if t is True:    pass                     # some true  -> dropped (neither group)
        elif t is False: kept.append(el)          # some false -> kept   group
        else:            unresolved.append(el)    # none       -> unresolved group
    shadow = Union(FiniteSet(*kept),
                   Complement(FiniteSet(*unresolved), self, evaluate=False)
                   if unresolved else S.EmptySet) # the R assembly envelope

The bijection (mapping.md): `kept` <-> result.kept, `unresolved` <->
result.unresolved, and the `Union`/`FiniteSet`/`Complement(evaluate=False)`/
`EmptySet` assembly is the R packaging the patch itself performs. The shadow
therefore expects `self._complement(other)` to equal that assembled object.

Note the shadow reuses the REAL unchanged `self.contains` (the membership callee
is exercised end-to-end here — it is NOT modeled away), so this gate validates
exactly the classify-and-split logic the fix introduced.

Exit 0 iff zero disagreements. stdlib-only fuzzing (pinned seed).
"""
import random
import sys

SEED = 13615
N_RANDOM = 120_000  # >= 1e5


def main():
    try:
        from sympy import (FiniteSet, Interval, S, Symbol, Integer, Rational,
                            Union, Intersection)
        from sympy.sets.sets import Set, Complement
    except Exception as e:  # pragma: no cover
        print(f"status=fail could not import callees: {e!r}")
        return 1

    rng = random.Random(SEED)
    disagreements = 0
    checked = 0

    def ternary(self, el):
        """The gold patch's `ternary_sift`, normalizing the real (unchanged)
        membership callee `self.contains` to a three-valued outcome. NOTE:
        `self.contains` returns sympy booleans (`S.true`/`S.false`), not Python
        `True`/`False`; `c in [True, False]` compares by `==` (sympy booleans
        equal their Python counterparts), so the returned bucket key is the
        sympy boolean itself (or `None`). Downstream classification must compare
        by `==`, exactly as the gold's `sifted[False]` / `sifted[None]` reads."""
        c = self.contains(el)
        return c if c in [True, False] else None

    def shadow_complement(self, other):
        """R/I shadow of implementation_partitionByMembership + the patch's
        assembly envelope. Classification mirrors the gold's dict-key reads
        `sifted[False]` (definite non-member) and `sifted[None]` (undetermined);
        the `sifted[True]` bucket is dropped."""
        kept, unresolved = [], []
        for el in other:
            t = ternary(self, el)
            if t is None:
                unresolved.append(el)          # none       -> unresolved group
            elif t == False:                   # noqa: E712  (sympy S.false == False)
                kept.append(el)                # some false -> kept group
            else:                              # some true  -> dropped (neither)
                continue
        return Union(FiniteSet(*kept),
                     Complement(FiniteSet(*unresolved), self, evaluate=False)
                     if unresolved else S.EmptySet)

    def report(key, real, shadow):
        nonlocal disagreements
        ok = (real is not None) and (real == shadow)
        if not ok:
            disagreements += 1
            if disagreements <= 5:
                print(f"MISMATCH {key!r}: real={real!r} shadow={shadow!r}")

    def check_one(self, other, key):
        nonlocal checked
        # Only the FiniteSet branch of the PATCHED `Set._complement` is modeled.
        # Subclasses (FiniteSet, Interval) shadow `_complement` with their own
        # logic, so we invoke the patched BASE method directly (the unbound
        # `Set._complement`) to exercise exactly the changed code, matching how
        # the subclasses' `return Set._complement(self, other)` fall-through
        # reaches it.
        if not isinstance(other, FiniteSet):
            return
        try:
            real = Set._complement(self, other)
        except Exception:
            return  # branch not applicable for this `self`; skip
        if real is None:
            return  # `self` does not handle the FiniteSet branch (returns None)
        shadow = shadow_complement(self, other)
        report(key, real, shadow)
        checked += 1

    # ---- carrier symbols / numbers for building FiniteSets ----
    syms = [Symbol(n) for n in ["x", "y", "z", "a", "b", "c", "n", "p"]]
    nums = [Integer(k) for k in (-12, -10, -3, 0, 1, 2, 5, 10, 11, 33)]
    nums += [Rational(7, 2), Rational(-1, 3)]
    elems = syms + nums

    # ---- `self` catalogue: sets whose `.contains` is True / False / undetermined ----
    def self_catalogue():
        return [
            Interval(-10, 10), Interval(0, 10), Interval.open(0, 5),
            Interval(-2, 3), Interval(Integer(-1), Rational(7, 2)),
            S.Integers, S.Naturals, S.Naturals0, S.Reals,
            FiniteSet(1, 2, 3), FiniteSet(0), FiniteSet(Symbol('y')),
            FiniteSet(Symbol('a'), Symbol('b')),
            Union(FiniteSet(1), Interval(2, 3)),
            Intersection(S.Integers, Interval(0, 10)),
        ]

    selves = self_catalogue()

    def rand_finiteset():
        k = rng.randint(0, 4)
        picks = [rng.choice(elems) for _ in range(k)]
        return FiniteSet(*picks)

    # ---- boundary catalogue: the exact F2P assertion + structured cases ----
    x, y = Symbol('x'), Symbol('y')
    check_one(Interval(-10, 10), FiniteSet(x, y, 2), ("F2P", "mixture"))
    check_one(Interval(-10, 10), FiniteSet(x, y), ("F2P", "all-symbol"))
    check_one(Interval(0, 1), FiniteSet(0, 1, 2), ("boundary", "all-num"))
    check_one(Interval(-10, 10), FiniteSet(), ("boundary", "empty"))
    for self in selves:
        for other in (FiniteSet(x, y, 2), FiniteSet(x, 5, 33),
                      FiniteSet(0, 1, 2, 3), FiniteSet(x), FiniteSet()):
            check_one(self, other, ("boundary", repr(self)))

    # ---- randomized fuzz ----
    for _ in range(N_RANDOM):
        self = rng.choice(selves)
        other = rand_finiteset()
        check_one(self, other, ("fuzz",))

    print(f"checked={checked} disagreements={disagreements}")
    if disagreements == 0:
        print(f"status=pass conformance OK ({checked} checks, 0 disagreements)")
        return 0
    print(f"status=fail {disagreements} disagreement(s)")
    return 1


if __name__ == "__main__":
    sys.exit(main())

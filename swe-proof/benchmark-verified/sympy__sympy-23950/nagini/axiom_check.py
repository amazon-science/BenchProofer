#!/usr/bin/env python3
"""G-AX executable soundness check for sympy__sympy-23950.

This bundle consumes NO `@ContractOnly` axiom: the modeled change is a pure
component selection (`Contains.as_set` returns the set operand `self.args[1]`),
modelled deeply as object-identity reasoning. The single soundness obligation is
the **type-refinement (R) faithfulness** of the field bijection refinement.md
step 1 relies on — that a real `Contains(x, s)` stores its operands as
`self.args == (x, s)`, so the value the gold patch returns (`self.args[1]`) is
the set `s` (modelled as `self.region`), and the element (`self.args[0]`, the
modelled `self.element`) is the distinct object the postcondition discriminates
against.

It executes the REAL repo class `Contains` in-container on the F2P operands plus
adversarial fuzz and asserts the bijection on every observation. When run against
the gold-patched tree it additionally checks the full view round trip
`Contains(x, s).as_set() is s`. Imports only `sympy` (the repo under test).
Exit 0 iff every observation holds.
"""
import sys


def main():
    from sympy import Symbol, FiniteSet, Interval, S
    from sympy.sets.contains import Contains

    x = Symbol('x')
    y = Symbol('y')
    z = Symbol('z')
    i = Symbol('i', integer=True)

    # Operands exercised: the three F2P sets + adversarial variety. Each entry is
    # (element, set) with the set kept symbolic enough that Contains does NOT
    # evaluate to S.true/S.false (so the Contains object — not a reduced bool —
    # is what carries .args). FiniteSet(y), S.Integers, S.Reals are the exact
    # F2P operands.
    cases = [
        (x, FiniteSet(y)),                 # F2P
        (i, S.Integers),                   # F2P-shaped (kept unevaluated below)
        (x, S.Reals),                      # F2P
        (x, S.Integers),
        (x, S.Naturals),
        (x, S.Rationals),
        (x, FiniteSet(y, z)),
        (x, FiniteSet(1, 2, 3)),
        (x, Interval(0, 1)),
        (x, Interval(-S.Infinity, S.Infinity)),
        (x, FiniteSet(FiniteSet(y), z)),   # nested set operand
        (x, FiniteSet(y) | FiniteSet(z)),  # Union operand
    ]

    n = 0
    for elem, region in cases:
        # Build the membership assertion without auto-evaluation so the Contains
        # object (carrying .args) is preserved regardless of the operands.
        c = Contains(elem, region, evaluate=False)
        the_set = c.args[1]      # the STORED set operand (what the gold returns)
        the_elem = c.args[0]     # the STORED element operand

        # R-bijection (model self.region <-> the stored self.args[1]): the stored
        # set operand compares equal to the set the assertion was built over.
        # (Sympy may rebuild the operand into an equal object, so this is `==`,
        # not `is`, against the input — see mapping.md §2.)
        assert the_set == region, (
            "field bijection unsound: Contains(%r, %r).args[1] == %r is False"
            % (elem, region, the_set))
        # The element operand is stored identically and is the distinct object
        # the postcondition Result() is self.region discriminates against.
        assert the_elem is elem, (
            "field bijection unsound: Contains(%r, %r).args[0] is not the "
            "element operand (%r)" % (elem, region, the_elem))
        assert the_elem is not the_set, (
            "element and set operands coincide for %r — discriminator vacuous"
            % (c,))

        # The modeled operation `return self.region` <-> the gold `return
        # self.args[1]`: as_set must return the STORED set operand BY IDENTITY
        # (Result() is self.region). Guarded so the check is also runnable
        # pre-patch (where as_set raises NotImplementedError / is unimplemented).
        try:
            view = c.as_set()
        except NotImplementedError:
            view = None
        if view is not None:
            assert view is the_set, (
                "as_set unsound: Contains(%r, %r).as_set() is not the stored "
                "set operand self.args[1]" % (elem, region))
            assert view == region, (
                "as_set unsound: Contains(%r, %r).as_set() == %r is False (the "
                "F2P equality)" % (elem, region, view))
            n += 1

    print("G-AX OK: Contains(x, s) field bijection sound on %d operand pairs "
          "(args[1] == the set, args[0] is the element, distinct); as_set "
          "returns the stored set operand by identity (== the set) on %d "
          "(gold-patched)" % (len(cases), n))
    return 0


if __name__ == "__main__":
    sys.exit(main())

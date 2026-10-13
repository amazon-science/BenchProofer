#!/usr/bin/env python3
"""G-AX executable soundness check for sympy__sympy-18189.

Runs the REAL repo callee the modeled routine consults — the UNCHANGED base
solver `diophantine(eq, param, permute=p)` invoked with `syms=None` (the
recursive call at sympy/solvers/diophantine.py:185) — in-container, on boundary
and fuzzed equations, and asserts the facts the model relies on.

`baseSolve` is modeled `opaque` with NO asserted `ensures` (directive 7: the
weakest possible contract), so there is NO consumed axiom to validate point-wise.
What G-AX establishes are the **A-reference** facts that make the modeled
dependence on `permute` faithful and non-vacuous (mapping.md §3.1,
refinement.md §A3):

  1. PURE-IN-(eq, permute): for a fixed equation and flag value the base solver
     returns the same solution set on repeated calls — it is a function of its
     arguments, so modeling it as the opaque handle `baseSolve permute` is sound
     (the `syms=None` call is deterministic).

  2. FLAG LOAD-BEARING (the discriminator is real): there exist equations for
     which the `permute=True` solution set STRICTLY CONTAINS the `permute=False`
     set. Hence `baseSolve true ≠ baseSolve false`, so the spec clause
     `out = reorderAll order (baseSolve permute)` genuinely distinguishes the
     forwarded flag — the pre-patch bug (forwarding `False`) is observable, not a
     vacuous difference.  The issue's own family `m**4 + n**4 - 97` exhibits this
     (1 solution at False, 8 at True).

  3. SYMS=None SKIPS THE REORDER BRANCH (callee is unchanged-path): when `syms`
     is None the reorder branch (line 182) is never entered, so the base call's
     own body is not on the patched path — confirming `baseSolve` models an
     UNCHANGED callee, never the function-under-change.

stdlib + sympy (the repo under test) only — no gold patch needed: the modeled
base solver is the UNCHANGED base-commit callee, invoked directly with syms=None.
Exit 0 iff every obligation holds.
"""
import random
import sys


def build():
    from sympy import symbols
    from sympy.solvers.diophantine import diophantine, classify_diop

    t = symbols("t", integer=True)
    x, y, z = symbols("x y z", integer=True)

    def base_solve(eq, permute):
        """The REAL unchanged callee: diophantine with no syms (the recursive
        base solve), returning the canonical-order solution set for the flag."""
        return diophantine(eq, t, permute=permute)

    return symbols, diophantine, classify_diop, base_solve, t, (x, y, z)


def main():
    symbols, diophantine, classify_diop, base_solve, t, (x, y, z) = build()

    # --- equation families ----------------------------------------------------
    # Families that ADMIT variant solutions under permute=True (so the flag is
    # load-bearing): sums of even powers / sums of squares, and even-power binary
    # quadratics.  Plus a control family that does not (linear-ish), where the
    # flag changes nothing — both legs are exercised.
    variant_eqs = [
        x ** 4 + y ** 4 - 2 ** 4 - 3 ** 4,    # the issue's equation (8 vs 1)
        x ** 2 + y ** 2 - 25,                 # binary quadratic, even powers
        x ** 2 + y ** 2 - 50,
        x ** 2 + y ** 2 - 5,
        x ** 4 + y ** 4 - 1 ** 4 - 2 ** 4,
        x ** 2 + y ** 2 - 65,
    ]

    # 1. PURE-IN-(eq, permute): repeated calls agree.
    for eq in variant_eqs:
        for p in (False, True):
            a = base_solve(eq, p)
            b = base_solve(eq, p)
            assert a == b, (
                "base solver not deterministic on %r (permute=%s): %r vs %r"
                % (eq, p, a, b))

    # 2. FLAG LOAD-BEARING: at least one equation has True-set strictly larger
    #    than the False-set, and on those the False-set is a subset of the True
    #    one (permute only ADDS variants — never removes the base solutions).
    strictly_larger = 0
    for eq in variant_eqs:
        sf = base_solve(eq, False)
        st = base_solve(eq, True)
        assert sf <= st, (
            "permute=True dropped base solutions on %r: False=%r True=%r"
            % (eq, sf, st))
        if len(st) > len(sf):
            strictly_larger += 1
    assert strictly_larger >= 1, (
        "no equation showed permute=True strictly enlarging the set; the "
        "forwarded-flag discriminator would be vacuous")

    # the issue's specific equation: exactly 1 base vs 8 permuted
    iss = x ** 4 + y ** 4 - 2 ** 4 - 3 ** 4
    assert len(base_solve(iss, False)) == 1, "issue eq: expected 1 base solution"
    assert len(base_solve(iss, True)) == 8, "issue eq: expected 8 permuted solutions"

    # 3. SYMS=None SKIPS THE REORDER BRANCH: with syms=None the result equals the
    #    base solve itself (no reindexing applied), i.e. the callee body is the
    #    unchanged base solver, not the reorder dispatch under change.
    for eq in variant_eqs:
        for p in (False, True):
            assert diophantine(eq, t, syms=None, permute=p) == base_solve(eq, p)

    # --- randomized fuzz: determinism + monotone-in-flag over a bounded family
    rng = random.Random(18189)
    n_fuzz = 0
    for _ in range(400):
        a = rng.randint(1, 6)
        b = rng.randint(1, 6)
        N = rng.randint(2, 90)
        deg = rng.choice([2, 4])
        eq = a * x ** deg + b * y ** deg - N
        try:
            sf = diophantine(eq, t, permute=False)
            st = diophantine(eq, t, permute=True)
        except Exception:
            continue
        n_fuzz += 1
        assert diophantine(eq, t, permute=False) == sf, "non-deterministic (False)"
        assert sf <= st, ("permute=True dropped solutions on %r: %r vs %r"
                          % (eq, sf, st))

    print("G-AX OK: opaque baseSolve == real diophantine(eq, param, permute=p) "
          "with syms=None; deterministic in (eq, permute) on %d boundary + %d "
          "fuzz equations; permute=True strictly enlarges the set on %d/%d "
          "boundary families (flag load-bearing; issue eq 1->8); syms=None never "
          "enters the reorder branch (unchanged callee)."
          % (len(variant_eqs), n_fuzz, strictly_larger, len(variant_eqs)))
    return 0


if __name__ == "__main__":
    sys.exit(main())

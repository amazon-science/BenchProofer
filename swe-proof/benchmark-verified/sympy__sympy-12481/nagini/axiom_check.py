#!/usr/bin/env python3
"""G-AX executable soundness check for sympy__sympy-12481.

This bundle consumes NO axiom: the cyclic-form composition is modelled DEEPLY
(model.py's `swap_val` + the verified loop in `compose_cycles`). G-AX therefore
validates that DEEP MODEL (an A-reference) against the REAL repository callee —
the cyclic-form constructor `Permutation([[a, b], [c, d]], size=n)` (built from
`Cycle` composition) — on boundary + exhaustive + fuzz inputs, INCLUDING the
non-disjoint cycle inputs (the two cycles share a point with EACH OTHER) that
are the whole point of the change.

For every pair of GENUINE two-element cycles (a b), (c d) over n points the
model claims position i of the array form is

    swap_val(swap_val(i, a, b), c, d)

(apply (a b) then (c d), left to right).  "Genuine two-element cycle" means the
two points named within ONE cycle are distinct: `a != b` and `c != d`.  This is
the model's `Requires` domain and it is exactly the real callee's accepting set:
the within-cycle uniqueness check (untouched by the change) rejects a repeated
point inside one cycle (`[e, e]` raises "All elements must be unique in a
cycle"), while only the CROSS-cycle (non-disjoint) rejection is removed.  We
therefore sweep only `a != b and c != d` — the congruent domain — and assert
the deep model equals the real
`Permutation([[a, b], [c, d]], size=n).array_form` for ALL such (a, b, c, d)
with n <= 6 (exhaustive over the touched points), plus larger randomized sizes,
plus the explicit problem-statement / FAIL_TO_PASS witnesses:

    Permutation([[0, 1], [0, 2]]) == Permutation(0, 1, 2)       (F2P assertion)
    Permutation([[0, 1], [0, 1]]) == identity                  (problem statement)
    Permutation([[1], [1, 2]])    constructs (no longer rejected)

The last witness pairs a SINGLETON cycle `[1]` with a swap `[1, 2]`.  A singleton
cycle is the IDENTITY on its point (it is NOT the swap `(1 1)`, which would
raise the within-cycle uniqueness error); so its image is checked against a
faithful singleton model `single_then_swap` below, not against the two-swap
`model_array`.

Imports the repository package `sympy` (the module the gold patch lives in) — it
is run IN-CONTAINER where sympy is installed, with the gold patch applied,
exactly as the real callee runs.  Exit 0 iff every observation matches the deep
model.
"""
import random
import sys
from itertools import product

from sympy.combinatorics.permutations import Permutation, Cycle


# --- model.py deep-model reference (kept in lock-step with swap_val) ---------

def swap_val(x, a, b):
    if x == a:
        return b
    if x == b:
        return a
    return x


def model_array(n, a, b, c, d):
    """Reference implementation of model.py's compose_cycles: array form of the
    composition of the two GENUINE two-element swaps (a b) then (c d) over n
    points (a != b, c != d)."""
    return [swap_val(swap_val(i, a, b), c, d) for i in range(n)]


def single_then_swap(n, e, c, d):
    """Faithful model of a SINGLETON cycle [e] (the identity on e) composed with
    the swap (c d) over n points.  The singleton contributes nothing, so the
    result is just the swap (c d) applied point-wise (left-to-right: identity
    first, then the swap)."""
    return [swap_val(swap_val(i, e, e), c, d) for i in range(n)]  # swap_val(i,e,e)==i


# --- the real callee ---------------------------------------------------------

def real_array(n, a, b, c, d):
    """The REAL repository construction: build the permutation from the two
    cycles in cyclic form with explicit size n, return its array form."""
    p = Permutation([[a, b], [c, d]], size=n)
    return list(p.array_form)


def check(n, a, b, c, d):
    observed = real_array(n, a, b, c, d)
    expected = model_array(n, a, b, c, d)
    assert observed == expected, (
        "deep model unsound on n=%d cycles (%d %d)(%d %d): "
        "real array_form=%r, model gives=%r"
        % (n, a, b, c, d, observed, expected))
    # The composition is always a genuine rearrangement (the model's
    # in-range postcondition); confirm against the real callee too.
    assert sorted(observed) == list(range(n)), (
        "real array_form is not a permutation of 0..%d: %r" % (n - 1, observed))


def check_domain_congruence(n, a, b, c, d):
    """Boundary check for SPEC_GUIDE directive 7 / verdict P0 hardening: every
    input the model's `Requires` admits (a != b and c != d) must be ACCEPTED by
    the real callee (no raise).  A raise here would be a domain over-claim."""
    try:
        real_array(n, a, b, c, d)
    except Exception as exc:  # noqa: BLE001 — any raise on an in-domain input is a defect
        raise AssertionError(
            "domain over-claim: model Requires admits genuine cycles "
            "(%d %d)(%d %d) over n=%d but the real callee RAISED %s: %s"
            % (a, b, c, d, n, type(exc).__name__, exc))


def main():
    # --- exhaustive over all pairs of GENUINE two-element cycles, n <= 6 ------
    # Guard a != b and c != d: this is the model's `Requires` domain AND the
    # real callee's accepting set (within-cycle uniqueness is untouched by the
    # change; only the cross-cycle non-disjoint rejection is removed).  The
    # two cycles still MAY share a point with each other — every non-disjoint
    # configuration is swept here, which is precisely the behaviour the change
    # enables.
    exhaustive = 0
    for n in range(1, 7):
        for a, b, c, d in product(range(n), repeat=4):
            if a == b or c == d:
                continue
            check_domain_congruence(n, a, b, c, d)
            check(n, a, b, c, d)
            exhaustive += 1

    # --- explicit witnesses from the problem statement / FAIL_TO_PASS --------
    # Permutation([[0,1],[0,2]]) == Permutation(0,1,2)  (the F2P assertion):
    # two genuine swaps sharing point 0 (non-disjoint).
    assert Permutation([[0, 1], [0, 2]]) == Permutation(0, 1, 2), \
        "F2P witness failed: [[0,1],[0,2]] != (0 1 2)"
    assert model_array(3, 0, 1, 0, 2) == [1, 2, 0]
    # Permutation([[0,1],[0,1]]) is the identity (problem statement): two
    # genuine swaps that coincide (fully non-disjoint).
    assert Permutation([[0, 1], [0, 1]]) == Permutation([0, 1]), \
        "problem-statement witness failed: [[0,1],[0,1]] is not the identity"
    assert model_array(2, 0, 1, 0, 1) == [0, 1]
    # Permutation([[1],[1,2]]) now CONSTRUCTS (formerly rejected as non-disjoint:
    # singleton [1] shares point 1 with swap [1,2]).  The singleton [1] is the
    # IDENTITY on point 1 (NOT the swap (1 1), which raises), so its image is
    # checked against the faithful singleton model.
    witness = Permutation([[1], [1, 2]])          # must not raise
    assert list(witness.array_form) == [0, 2, 1], \
        "singleton witness [[1],[1,2]] array_form changed: %r" % (list(witness.array_form),)
    assert single_then_swap(3, 1, 1, 2) == [0, 2, 1]

    # --- randomized fuzz over larger sizes (genuine two-element cycles) -------
    rng = random.Random(12481)
    fuzz = 0
    for _ in range(20000):
        n = rng.randint(2, 40)        # n >= 2 so two distinct points exist
        a = rng.randint(0, n - 1)
        b = rng.randint(0, n - 1)
        while b == a:                 # genuine cycle: a != b
            b = rng.randint(0, n - 1)
        c = rng.randint(0, n - 1)
        d = rng.randint(0, n - 1)
        while d == c:                 # genuine cycle: c != d
            d = rng.randint(0, n - 1)
        check_domain_congruence(n, a, b, c, d)
        check(n, a, b, c, d)
        fuzz += 1

    print("G-AX OK: deep model (swap_val composition) == real "
          "Permutation cyclic-form construction on %d exhaustive (n<=6) + "
          "%d fuzz pairs of genuine two-element cycles (a!=b, c!=d) + 3 "
          "problem/F2P witnesses; all observations match, incl. every "
          "non-disjoint (shared-point) configuration; domain congruence held "
          "(no in-domain input raised)." % (exhaustive, fuzz))
    return 0


if __name__ == "__main__":
    sys.exit(main())

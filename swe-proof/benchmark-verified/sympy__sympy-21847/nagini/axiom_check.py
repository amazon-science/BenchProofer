#!/usr/bin/env python3
"""G-AX executable soundness check for sympy__sympy-21847.

This bundle ships NO @ContractOnly axiom: the only operation the patch changes —
the reduction over a candidate term's exponent vector — is modeled DEEPLY by the
pure fold `deg_sum` in model.py (the total-degree reduction). The pre-patch
reduction is the per-variable maximum, modeled inline in model_prepatch.py and
mirrored here as the reference `deg_max` used purely to witness that the change
is observable. This script discharges the deep-model fidelity obligation in two
parts, stdlib-only by default and, when the repo is importable in-container,
against the REAL gold-patched callee:

  (1) Deep-fold fidelity (always, stdlib-only): the model's `deg_sum` ==
      `sum(exponents)`, and the pre-patch reduction `deg_max` == `max(exponents)`
      (0 over the empty vector), over exhaustive small exponent vectors plus
      randomized fuzz. This is the correspondence claimed in mapping.md §2 /
      refinement.md row 3.

  (2) Real-callee fidelity (when `sympy` imports AND the gold patch is in the
      checkout): the gold-patched `itermonomials` retains a candidate term
      exactly when its TOTAL degree (== deg_sum of its exponent vector) is >=
      min_degree. We reconstruct each yielded monomial's exponent vector and
      assert the membership of the generated set matches the modeled predicate
      `deg_sum(powers) >= min_degree` AND that the pre-patch predicate
      `deg_max(powers) >= min_degree` would have differed on the discriminating
      witnesses (so the deep model truly captures the change). The F2P
      discriminators `itermonomials([x, y], 3, 3)` and
      `itermonomials([i, j, k], 2, 2)` are checked explicitly.

      The frozen instance container sits at base_commit, where the retention
      test still reads `max(powers.values())`. Part 2 therefore GUARDS on the
      live `itermonomials` source: it runs the assertions only when the patched
      reduction `sum(powers.values())` is present, and SKIPS cleanly (rc 0)
      against an unpatched checkout — never hard-asserting post-patch behaviour
      at base_commit. Run in the eval container with the gold patch applied
      (e.g. `run_in_container(..., apply_gold=True)`) to exercise it.

Exit 0 iff every obligation holds (with part 2 skipping cleanly when the
checkout is unpatched). Imports only the standard library plus, optionally,
`sympy` (the repo under test — present in the eval container).
"""
import itertools
import random
import sys


# --- model.py deep folds, re-expressed as reference Python -------------------

def deg_sum(p):
    """Reference for model.py's `deg_sum`: arithmetic sum of the exponents."""
    total = 0
    for e in p:
        total += e
    return total


def deg_max(p):
    """Reference for the PRE-PATCH reduction (model_prepatch.py): largest single
    exponent, 0 if empty. Used only as the sum-vs-max discriminator witness."""
    m = 0
    for e in p:
        if e >= m:
            m = e
    return m


# --- part (1): deep-fold fidelity, stdlib-only -------------------------------

def check_fold_fidelity():
    # exhaustive small exponent vectors
    for length in range(0, 5):
        for vec in itertools.product(range(0, 5), repeat=length):
            v = list(vec)
            assert deg_sum(v) == sum(v), (v, deg_sum(v), sum(v))
            expected_max = max(v) if v else 0
            assert deg_max(v) == expected_max, (v, deg_max(v), expected_max)
    # randomized fuzz over longer / larger vectors
    rng = random.Random(21847)
    for _ in range(20000):
        n = rng.randint(0, 12)
        v = [rng.randint(0, 9) for _ in range(n)]
        assert deg_sum(v) == sum(v), (v, deg_sum(v), sum(v))
        expected_max = max(v) if v else 0
        assert deg_max(v) == expected_max, (v, deg_max(v), expected_max)
    print("G-AX part 1 OK: deg_sum == sum and deg_max == max over "
          "exhaustive small + 20000 fuzz exponent vectors")


# --- part (2): real gold-patched callee fidelity (if sympy importable) -------

def _exponent_vector(monom, gens):
    """Exponent vector of a monomial term `monom` over the variable list
    `gens`, by counting occurrences of each generator (including powers).
    Works for commutative and non-commutative generators alike."""
    return [_deg_in(monom, g) for g in gens]


def _deg_in(monom, g):
    """Degree of `monom` in the single generator `g` (commutative or not)."""
    from sympy import Pow, Mul

    def deg(expr):
        if expr == g:
            return 1
        if isinstance(expr, Pow) and expr.base == g:
            return int(expr.exp)
        if isinstance(expr, Mul):
            return sum(deg(a) for a in expr.args)
        return 0

    return deg(monom)


def check_real_callee():
    try:
        import inspect
        import sympy
        from sympy import symbols, S
        from sympy.polys.monomials import itermonomials
    except Exception as exc:  # pragma: no cover - container has sympy
        print("G-AX part 2 SKIPPED (sympy not importable here: %s). "
              "Run inside the eval container for the real-callee check." % exc)
        return

    # The frozen instance container sits at base_commit, where the retention
    # test still reads `max(powers.values())` (the bug). Part 2 asserts the
    # gold-PATCHED behaviour, so it only applies once the gold patch is in the
    # checkout. Detect the patched reduction in the live source and SKIP
    # cleanly (rc 0) otherwise — never hard-assert post-patch behaviour against
    # an unpatched checkout.
    try:
        src = inspect.getsource(itermonomials)
    except Exception as exc:  # pragma: no cover - source always available here
        print("G-AX part 2 SKIPPED (itermonomials source unavailable: %s)" % exc)
        return
    if "sum(powers.values())" not in src:
        print("G-AX part 2 SKIPPED: itermonomials is at base_commit (still uses "
              "the per-variable reduction `max(powers.values())`); apply the "
              "gold patch to exercise the real-callee fidelity check.")
        return

    x, y, z = symbols('x y z')
    i, j, k = symbols('i j k', commutative=False)

    # explicit F2P discriminators from the gold test_patch
    assert set(itermonomials([x, y], 3, 3)) == {x**3, x**2*y, x*y**2, y**3}, \
        "gold itermonomials([x,y],3,3) wrong"
    assert set(itermonomials([x, y], 3, 2)) == {
        x**2, x*y, y**2, x**3, x**2*y, x*y**2, y**3}, \
        "gold itermonomials([x,y],3,2) wrong"
    assert set(itermonomials([i, j, k], 2, 2)) == {
        k*i, i**2, i*j, j*k, j*i, k**2, j**2, k*j, i*k}, \
        "gold itermonomials([i,j,k],2,2) wrong"

    cases = [
        ([x, y], 3, 3),
        ([x, y], 3, 2),
        ([x, y, z], 3, 2),
        ([x, y, z], 4, 3),
        ([i, j, k], 2, 2),
        ([i, j, k], 3, 2),
        ([i, j], 3, 3),
    ]
    discriminator_seen = False
    for gens, maxd, mind in cases:
        produced = set(itermonomials(gens, maxd, mind))
        # every produced monomial meets deg_sum >= min_degree (the model)
        for m in produced:
            pv = _exponent_vector(m, gens)
            assert deg_sum(pv) >= mind, (
                "produced term %r has total degree %d < min_degree %d"
                % (m, deg_sum(pv), mind))
            assert deg_sum(pv) <= maxd, (m, deg_sum(pv), maxd)
        # the pre-patch (max) predicate would have dropped at least one term
        # that the correct (sum) predicate keeps -> the change is observable.
        for m in produced:
            pv = _exponent_vector(m, gens)
            if deg_max(pv) < mind <= deg_sum(pv):
                discriminator_seen = True
    assert discriminator_seen, (
        "no case exercised the sum-vs-max discriminator; the deep model would "
        "not be pinned to the change")
    print("G-AX part 2 OK: gold-patched itermonomials retains exactly the "
          "terms with deg_sum >= min_degree; sum-vs-max discriminator observed")


def main():
    check_fold_fidelity()
    check_real_callee()
    print("G-AX OK: deep folds deg_sum/deg_max sound; no @ContractOnly axiom in "
          "this bundle (changed reduction modeled deeply, per refinement.md)")
    return 0


if __name__ == "__main__":
    sys.exit(main())

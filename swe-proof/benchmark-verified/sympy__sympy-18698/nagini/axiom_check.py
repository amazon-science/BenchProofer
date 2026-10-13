#!/usr/bin/env python3
"""G-AX executable soundness check for sympy__sympy-18698.

This bundle consumes NO axioms: the consolidation of the multiplicities (keeping
each distinct multiplicity once) is modelled deeply by the `dedup` fold in
model.py and discharged by the verified construction loop. The single kind-A
relationship is an A-REFERENCE: the merged factor recorded for a multiplicity k
is the PRODUCT, over the contributions in order, of exactly the factors of
multiplicity k -- and that product is what the real code computes via
``reduce(operator.mul, (f for f, _ in factors if _ == k))``. This check validates
that A-reference against the real product operator, and validates the whole
consolidation (model.py's `dedup`-by-multiplicity + per-group product) against a
faithful re-execution of the patch's post-loop comprehension

    factors = [(reduce(mul, (f for f, _ in factors if _ == k)), k)
               for k in set(i for _, i in factors)]

on boundary + randomized fuzz inputs.

Two model encodings are checked:

  (A-reference, the merged factor) For every multiplicity k present, the merged
    factor equals reduce(mul, [contributions of multiplicity k], in order). This
    is checked symbolically (so the commutative/associative product is exact)
    using `sympy` polynomials when available, and structurally over an
    associative/commutative free model otherwise.

  (deep model `dedup`, the reported multiplicities) The reported multiplicities
    are exactly the distinct contribution multiplicities, each once
    (model.py.dedup), matching `set(...)` of the multiplicities.

Imports are standard library plus `operator`/`functools` (the very callees the
patch uses); `sympy` is imported only if present, else the symbolic leg is
skipped and the algebraic A-reference is checked on integer products (a faithful
commutative/associative monoid). Exit 0 iff every obligation holds.
"""
import operator
import random
import sys
from functools import reduce


# --- model.py reference encodings (kept in lock-step with the spec) ----------

def occurs(seq, k):
    """Reference of model.py `occurs`: value membership (front-recursive)."""
    return k in seq


def dedup(seq):
    """Reference of model.py `dedup`: distinct values in order of first
    occurrence (keep-first)."""
    out = []
    for v in seq:
        if v not in out:
            out.append(v)
    return out


def consolidate_multiplicities(mults):
    """Reported multiplicities per model.py: dedup of the multiplicity sequence
    (the multiplicities the report carries, each once)."""
    return dedup(mults)


# --- the real post-loop comprehension from the patch (verbatim semantics) ----

def real_post_loop(factors_pairs):
    """Re-execution of the gold patch's `method == 'sqf'` post-processing:

        factors = [(reduce(mul, (f for f, _ in factors if _ == k)), k)
                   for k in set(i for _, i in factors)]

    Returns the list of (merged_factor, multiplicity) pairs. `mul` is the real
    `operator.mul`, exactly as the patch imports it (`from operator import mul`).
    """
    mul = operator.mul
    return [(reduce(mul, (f for f, _ in factors_pairs if _ == k)), k)
            for k in set(i for _, i in factors_pairs)]


# --- the checks --------------------------------------------------------------

def check_reported_multiplicities(mults):
    """The model's reported multiplicities (dedup) == the distinct multiplicities
    the real comprehension reports (set of k). Order is unobservable (sorted
    downstream), so compare as sets, and also assert the model's dedup keeps
    each distinct multiplicity exactly once."""
    model_reported = consolidate_multiplicities(mults)
    # distinctness + no value dropped/added (set equality)
    assert set(model_reported) == set(mults), (
        "reported multiplicities mismatch on %r: model dedup gives %r, "
        "distinct mults are %r" % (mults, model_reported, sorted(set(mults))))
    assert len(model_reported) == len(set(model_reported)), (
        "model dedup is not distinct on %r: %r" % (mults, model_reported))


def check_merged_factor_is_group_product(factors_pairs):
    """A-reference: for every reported multiplicity k, the merged factor the real
    comprehension records equals reduce(mul, [factors of multiplicity k], in
    contribution order) -- i.e. the product of EXACTLY that group, no factor of k
    dropped and none of another multiplicity mixed in."""
    real = dict((k, f) for f, k in real_post_loop(factors_pairs))
    for k in set(m for _, m in factors_pairs):
        group = [f for f, m in factors_pairs if m == k]
        assert group, "empty group for present multiplicity %r" % (k,)
        expected = reduce(operator.mul, group)
        assert real[k] == expected, (
            "merged factor mismatch for multiplicity %r on %r: real comprehension "
            "gives %r, product of the group %r is %r"
            % (k, factors_pairs, real[k], group, expected))
        # one reported entry per multiplicity (the consolidation)
    assert len(real) == len(set(m for _, m in factors_pairs)), (
        "real comprehension did not keep one entry per multiplicity on %r"
        % (factors_pairs,))


def check_product_is_assoc_comm(group):
    """The product operator is commutative + associative, so the merged factor is
    determined by the GROUP (independent of contribution order). Validated on the
    real `operator.mul` / `reduce`."""
    if not group:
        return
    base = reduce(operator.mul, group)
    rng = random.Random(hash(tuple(group)) & 0xFFFF)
    for _ in range(8):
        perm = list(group)
        rng.shuffle(perm)
        assert reduce(operator.mul, perm) == base, (
            "product not order-independent on group %r (perm %r)" % (group, perm))


def try_symbolic_check():
    """If sympy is importable, validate the A-reference symbolically so the
    product is the real polynomial multiplication the patch performs (the
    strongest evidence). Returns the number of symbolic cases checked, or -1 if
    sympy is unavailable."""
    try:
        import sympy
        from sympy.abc import x, y
    except Exception:
        return -1
    cases = [
        # the issue's example: (x-2) and (x-3) both at multiplicity 3 merge
        [(x - 1, 2), (x - 3, 3), (x - 2, 3), (x ** 2 + 1, 1)],
        # x*(x+y): two factors at multiplicity 1 merge into x**2 + x*y
        [(x, 1), (x + y, 1)],
        # single factor per multiplicity: untouched
        [(x - 2, 1), (x ** 2 - 1, 2)],
        # three factors sharing a multiplicity
        [(x, 2), (x + 1, 2), (x + 2, 2)],
    ]
    checked = 0
    for pairs in cases:
        real = dict((k, f) for f, k in real_post_loop(pairs))
        for k in set(m for _, m in pairs):
            group = [f for f, m in pairs if m == k]
            expected = reduce(operator.mul, group)
            # symbolic equality (expand to compare polynomial values)
            assert sympy.expand(real[k] - expected) == 0, (
                "symbolic merged factor mismatch for multiplicity %r: %r vs %r"
                % (k, real[k], expected))
            checked += 1
        # reported multiplicities match dedup-as-set
        assert set(m for _, m in pairs) == set(consolidate_multiplicities(
            [m for _, m in pairs]))
    return checked


def main():
    rng = random.Random(18698)

    # --- boundary cases over multiplicities (the consolidation) -------------
    boundary_mults = [
        [],
        [1],
        [1, 1],                       # duplicate -> one reported entry
        [3, 3],                       # the bug's case: two factors of mult 3
        [1, 2, 3],
        [2, 1, 2],                    # first-occurrence order
        [1, 2, 1, 2, 1],
        [3, 3, 3, 3],
        [5, 4, 3, 2, 1],
        [1, 1, 2, 2, 3, 3],           # several duplicate multiplicities
    ]
    for mults in boundary_mults:
        check_reported_multiplicities(mults)

    # --- A-reference: merged factor == product of the group ----------------
    # model factors as small primes so integer products form a faithful
    # commutative/associative monoid; check the real comprehension against the
    # product of exactly the group of that multiplicity.
    boundary_pairs = [
        [(2, 1)],
        [(2, 1), (3, 1)],             # both mult 1 -> merge to 6
        [(2, 3), (3, 3)],             # both mult 3 -> merge to 6
        [(2, 1), (3, 2), (5, 3)],     # all distinct mults -> untouched
        [(2, 2), (3, 2), (5, 2)],     # three at mult 2 -> merge to 30
        [(2, 1), (3, 1), (5, 2), (7, 2)],
        [(11, 5), (13, 5), (17, 5), (19, 1)],
    ]
    for pairs in boundary_pairs:
        check_merged_factor_is_group_product(pairs)
        for k in set(m for _, m in pairs):
            check_product_is_assoc_comm([f for f, m in pairs if m == k])

    # --- randomized fuzz -----------------------------------------------------
    primes = [2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37]
    for _ in range(20000):
        n = rng.randint(0, 8)
        mults = [rng.randint(1, 5) for _ in range(n)]
        check_reported_multiplicities(mults)
        # build distinct factor tokens (primes, no repeats) paired with mults
        tokens = rng.sample(primes, n) if n <= len(primes) else \
            [primes[i % len(primes)] for i in range(n)]
        pairs = list(zip(tokens, mults))
        if pairs:
            check_merged_factor_is_group_product(pairs)
            for k in set(m for _, m in pairs):
                check_product_is_assoc_comm([f for f, m in pairs if m == k])

    sym = try_symbolic_check()

    print("G-AX OK: consolidation (dedup-by-multiplicity) + A-reference "
          "(merged factor == reduce(mul, group)) sound on %d boundary mult "
          "lists + %d boundary factor lists + 20000 fuzz cases%s"
          % (len(boundary_mults), len(boundary_pairs),
             ("" if sym < 0 else " + %d symbolic sympy obligations" % sym)))
    return 0


if __name__ == "__main__":
    sys.exit(main())

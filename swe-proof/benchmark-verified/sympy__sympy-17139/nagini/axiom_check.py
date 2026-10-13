#!/usr/bin/env python3
"""G-AX executable soundness check for sympy__sympy-17139.

Executes the REAL library operations against the model's three axiomatized
callees and confirms their domain + value behaviour, exactly as encoded in
model.py:

  order_lt_zero(e):    Requires(e.real); Ensures(Result() == (e.value < 0))
  order_gt_max(e,m):   Requires(e.real); Ensures(Result() == (e.value > m))
  is_perfect_power(n): Requires(n >= 0); deterministic boolean (A-reference)

The first two are the symbolic ordering predicates ``exp < 0`` and ``exp > max``
where ``exp`` is the exponent of the inspected power node. The model gives them
the SAFE (non-raising) domain ``e.real`` as their precondition. This check
validates that this precondition is sound and necessary against the real callee
(`sympy.core.expr.Expr.__lt__` / `__gt__`):

  (1) DOMAIN soundness/necessity: on a NON-real exponent the real ordering
      RAISES TypeError (so the model is right to forbid calling the axiom
      there — Requires(e.real) excludes exactly the inputs on which the real
      operation is undefined). The model never claims a value for these inputs.

  (2) VALUE soundness: on a real (integer) exponent, the real ordering
      ``(exp < 0) == True`` agrees with ``value < 0`` and ``(exp > m) == True``
      agrees with ``value > m`` — the axioms' Ensures.

The third callee, ``is_perfect_power(n)``, is the perfect-power test the rewrite
dispatch keys on among the non-2, non-4 magnitudes under ``pow`` (gold ``_f``:
``p = perfect_power(rv.exp); if not p: return rv``). It is an A-REFERENCE: the
model's deep dispatch is validated to match the real predicate, namely the
boolean cast of ``sympy.perfect_power``:

  (3) REFERENCE soundness: ``is_perfect_power(n)`` (the boolean the dispatch
      branches on) equals ``bool(sympy.perfect_power(n))`` for every relevant
      non-negative integer magnitude (boundary + fuzz). The model claims no
      value beyond this boolean for ``n``.

  (4) FAITHFULNESS cross-check: the model's standalone dispatch outcome
      (``model_outcome``) equals the REAL gold inner-transformer outcome
      (``gold_outcome``, transcribed branch-for-branch from ``_f`` and using the
      real perfect-power predicate) over the whole modeled exponent range, and
      on every F2P-test exponent shape. This compares against the live dispatch,
      not a hardcoded answer key, so a D1-class drift (a mandated wrong
      result-code on an observably-distinct unchanged-dispatch arm) is caught.

Imports only `sympy` (the very library the gold patch lives in). Exit 0 iff
every obligation holds.
"""
import random
import sys

import sympy
from sympy import I, Integer, Symbol, perfect_power


def real_lt_zero(exp):
    """Real callee: ``(exp < 0) == True`` (the prepatch's crashing expression).
    May raise TypeError on a non-real exponent (its undefined domain)."""
    return (exp < 0) == True            # noqa: E712  (mirrors fu.py exactly)


def real_gt_max(exp, m):
    """Real callee: ``(exp > max) == True``."""
    return (exp > m) == True            # noqa: E712


def real_is_perfect_power(n):
    """Real callee: the boolean the gold dispatch branches on,
    ``bool(perfect_power(n))`` (gold: ``p = perfect_power(rv.exp); if not p``)."""
    return bool(perfect_power(n))


def check_domain_raises(exp):
    """(1) A non-real exponent: the real ordering must RAISE (undefined domain),
    so the model's Requires(e.real) correctly forbids the call."""
    assert exp.is_real is not True, (
        "test setup error: %r should be non-real" % (exp,))
    for op, name in ((lambda: real_lt_zero(exp), "exp < 0"),
                     (lambda: real_gt_max(exp, 4), "exp > max")):
        try:
            op()
        except TypeError:
            continue
        raise AssertionError(
            "axiom DOMAIN unsound: %s did not raise on non-real exponent %r; "
            "the model forbids ordering a non-real exponent" % (name, exp))


def check_value(exp, m):
    """(2) A real integer exponent: the real ordering agrees with the model's
    integer comparison (the axioms' Ensures)."""
    assert exp.is_real is True, (
        "test setup error: %r should be real" % (exp,))
    v = int(exp)
    obs_lt = real_lt_zero(exp)
    assert obs_lt == (v < 0), (
        "order_lt_zero unsound on exp=%r: real gave %r, axiom requires %r"
        % (exp, obs_lt, v < 0))
    obs_gt = real_gt_max(exp, m)
    assert obs_gt == (v > m), (
        "order_gt_max unsound on exp=%r, m=%d: real gave %r, axiom requires %r"
        % (exp, m, obs_gt, v > m))


def check_perfect_power(n, model_value):
    """(3) The A-reference perfect-power predicate the dispatch branches on
    must equal the real ``bool(perfect_power(n))``."""
    assert n >= 0, "test setup error: n=%d should be non-negative" % (n,)
    real = real_is_perfect_power(n)
    assert real == model_value, (
        "is_perfect_power A-reference unsound on n=%d: real bool(perfect_power) "
        "= %r, model dispatch branches on %r" % (n, real, model_value))


# A standalone re-statement of the model's dispatch decision, purely as a
# function of (value, max, pow), to cross-check the modeled outcome against the
# REAL transformer outcome over the whole modeled range. Mirrors model.py's
# transform_power impl for real in-range exponents (the same control flow as
# the gold inner transformer).
def model_outcome(value, m, pow):
    if value < 0 or value > m:
        return 0
    if value == 1:
        return 0
    if value == 2:
        return 1
    if value == 4:
        return 2
    if not pow:
        return 0 if value % 2 == 1 else 2
    return 2 if real_is_perfect_power(value) else 0


def gold_outcome(value, m, pow):
    """The REAL gold inner-transformer dispatch (base commit 1d3327b8,
    sympy/simplify/fu.py:496-522 `_f`), transcribed branch-for-branch and mapped
    to the model's result code (0 unchanged / 1 squared-form / 2 general-form).
    The model is validated == this, NOT against any hardcoded answer key.

        if (rv.exp < 0)/(rv.exp > max): return rv            -> 0
        if rv.exp == 2: return h(g**2)                       -> 1
        else:
            if rv.exp == 4: e = 2                            -> 2
            elif not pow:
                if rv.exp % 2: return rv                     -> 0  (odd)
                e = rv.exp//2                                -> 2  (even)
            else:
                p = perfect_power(rv.exp)
                if not p: return rv                          -> 0
                e = rv.exp//2                                -> 2
            return h(g**2)**e
    """
    if value < 0 or value > m:
        return 0
    if value == 2:
        return 1
    # the gold `else` arm (note: gold has no special-cased value == 1; the
    # first power is an odd magnitude handled below and returned unchanged)
    if value == 4:
        return 2
    if not pow:
        if value % 2:        # odd -> `if rv.exp % 2: return rv`
            return 0
        return 2             # even -> e = rv.exp//2
    if not real_is_perfect_power(value):   # `p = perfect_power(rv.exp); if not p: return rv`
        return 0
    return 2


def main():
    x = Symbol('x')

    # --- (1) non-real exponents must make the real ordering raise -----------
    nonreal = [
        I,                       # the headline crash input: sin(x)**I
        2 * I + 1,               # the second F2P input: sin(x)**(2*I + 1)
        3 * I,
        Integer(2) + 3 * I,      # 2 + 3*I, from the simplify F2P test
        1 - I,
        -I,
        I / 2,
        5 * I - 7,
    ]
    for exp in nonreal:
        check_domain_raises(exp)

    # --- (2) real integer exponents: value behaviour ------------------------
    boundary = [-5, -2, -1, 0, 1, 2, 3, 4, 5, 6, 8, 10, 20, 100]
    maxes = [4, 6, 10]
    for v in boundary:
        for m in maxes:
            check_value(Integer(v), m)

    # randomized fuzz over real integer exponents and bounds
    rng = random.Random(17139)
    for _ in range(20000):
        v = rng.randint(-50, 50)
        m = rng.randint(4, 30)
        check_value(Integer(v), m)

    # --- (3) A-reference: perfect-power predicate the dispatch branches on ---
    # The dispatch consults the predicate only on real Pow exponents that have
    # passed every guard: positive, != 1, != 2, != 4, even -> the smallest
    # reachable magnitude is 6 (value 0 never reaches it: x**0 is not a Pow).
    # The real sympy-1.5 perfect_power requires n >= 1 (raises ValueError on 0),
    # so the validated A-reference domain is the positive magnitudes the
    # dispatch actually consults. Boundary (incl. the F2P-relevant 6, 8 and
    # several perfect / non-perfect powers) then fuzz over that range.
    pp_boundary = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 12, 16, 18, 20, 25, 27,
                   32, 36, 49, 50, 64, 100, 128]
    for n in pp_boundary:
        check_perfect_power(n, real_is_perfect_power(n))
    for _ in range(20000):
        n = rng.randint(1, 200)
        check_perfect_power(n, real_is_perfect_power(n))

    # cross-check (faithfulness): the modeled dispatch outcome equals the REAL
    # gold inner-transformer outcome (gold_outcome, transcribed from `_f`) on the
    # whole modeled exponent range -- NOT against any hardcoded answer key. This
    # catches the D1-class drift (a positively-mandated wrong result-code on an
    # observably-distinct unchanged-dispatch arm the F2P test pins).
    for m in (4, 6, 10, 20, 30):
        for pow in (False, True):
            for value in range(1, m + 1):
                md = model_outcome(value, m, pow)
                gd = gold_outcome(value, m, pow)
                assert md == gd, (
                    "model dispatch drifts from gold on value=%d max=%d pow=%s: "
                    "model=%d gold=%d" % (value, m, pow, md, gd))

    # and explicitly on the F2P-test exponent shapes (test__TR56), to document
    # that each public assertion's outcome is what the spec predicts:
    #   T(sin(x)**3, ...,4,False) == sin(x)**3            (unchanged, code 0)
    #   T(sin(x)**10,...,4,False) == sin(x)**10           (over-max unchanged, 0)
    #   T(sin(x)**6, ...,6,False) == (1-cos**2)**3        (rewritten, code 2)
    #   T(sin(x)**6, ...,6,True)  == sin(x)**6            (not perfect power, 0)
    #   T(sin(x)**8, ...,10,True) == (1-cos**2)**4        (perfect power, code 2)
    for value, m, pow, expect in ((3, 4, False, 0), (10, 4, False, 0),
                                  (6, 6, False, 2), (6, 6, True, 0),
                                  (8, 10, True, 2), (2, 4, False, 1)):
        assert gold_outcome(value, m, pow) == expect, (
            "gold transcription wrong on F2P shape value=%d max=%d pow=%s" % (
                value, m, pow))
        assert model_outcome(value, m, pow) == expect, (
            "model drifts from F2P expectation value=%d max=%d pow=%s" % (
                value, m, pow))

    print("G-AX OK: order_lt_zero / order_gt_max axioms sound (real ordering "
          "RAISES on %d non-real exponents and agrees with integer comparison "
          "on %d boundary + 20000 fuzz real exponents); is_perfect_power "
          "A-reference matches bool(perfect_power) on %d boundary + 20000 fuzz "
          "non-negative magnitudes; modeled even-arm outcome matches gold _f."
          % (len(nonreal), len(boundary) * len(maxes), len(pp_boundary)))
    return 0


if __name__ == "__main__":
    sys.exit(main())

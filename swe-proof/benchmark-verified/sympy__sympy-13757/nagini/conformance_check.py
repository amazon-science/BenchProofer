#!/usr/bin/env python
"""G-CONF differential conformance check for sympy__sympy-13757 (nagini).

SHADOW: the impl regions of model.py (``product_is_evaluated``,
``polynomial_priority``, ``generic_times_polynomial``), copied VERBATIM below
with only the contract calls (Requires / Ensures / Assert) stripped. The
@Pure helper ``resolved_by_right`` (the deep model of the unchanged dispatch
rule, mapping.md section 3.1) and the axioms-region constant
``default_priority`` copy over as plain functions — they are pure
float/bool predicates, no PSeq shim needed. There are no @ContractOnly
callees (mapping.md section 3: both references are A-references, i.e. deep
models validated against the real repo — which is exactly what the oracle
side below does differentially).

ORACLE: the REAL patched repo, per mapping.md section 1. The gate applies
patch.diff to /testbed and sets PYTHONPATH so ``import sympy`` resolves to
the patched tree. Three oracle surfaces:

  1. ``product_is_evaluated`` <-> the real ``binary_op_wrapper`` produced by
     ``sympy.core.decorators.call_highest_priority``: two probe operand
     classes carry the given ``_op_priority`` floats; the right operand
     exposes the named reverse handler iff ``other_has_handler``; each
     handler returns its operand's ``evaluates`` boolean, so the wrapper's
     return value IS the modeled observable (the winning operand's
     contribution).
  2. ``polynomial_priority`` <-> the real ``Poly._op_priority`` class datum
     (the patched value), and ``default_priority`` <-> the real
     ``Expr._op_priority`` baseline.
  3. ``generic_times_polynomial`` <-> the real end-to-end product
     ``<generic expr> * Poly(x)``: evaluated iff the result is a ``Poly``
     equal to ``Poly(x) * <generic expr>``.

TYPE BRIDGE (mapping.md section 2): the repo priorities are Python floats
and the model carrier is the interpreted float (float-encoding=real), so the
bridge is the identity on floats; the observable is a plain bool on both
sides. Every (float, bool, float, bool, bool) tuple is Requires-satisfying
(the preconditions are empty).

INPUT PLAN (>= 1e5 Requires-satisfying inputs): a boundary grid over
priority values around the two modeled data points (ties, half-ULP and
1e-15 offsets, negatives, zeros, infinities, NaN, large magnitudes) crossed
with all 8 boolean combinations, plus 100000 random fuzz tuples over mixed
float generators (uniform near the baseline, wide-range, tiny offsets,
special values, forced exact ties) and random booleans. Pinned fuzz seed:
13757 (recorded in mapping.md). Exit 0 iff zero disagreements; on
disagreement prints the input and both outputs and exits 1. stdlib only;
py2/py3 compatible (the instance container may run Python 2.7).
"""
from __future__ import print_function

import json
import random
import sys

SEED = 13757
N_FUZZ = 100000


# --- axioms region of model.py, contracts stripped ----------------------------

def default_priority():
    return 10.0


# --- pure region of model.py, contracts stripped ------------------------------

def resolved_by_right(self_priority, other_priority, other_has_handler):
    return other_has_handler and other_priority > self_priority


# --- impl regions of model.py, verbatim, contract calls stripped --------------

def product_is_evaluated(self_priority, self_evaluates,
                         other_priority, other_evaluates,
                         other_has_handler):
    if resolved_by_right(self_priority, other_priority, other_has_handler):
        return other_evaluates
    return self_evaluates


def polynomial_priority():
    return 10.001


def generic_times_polynomial():
    # The generic operand carries the baseline selection attribute, and its own
    # contribution to a product with a polynomial is NOT the computed product
    # (it would leave an unsimplified expression) -> left_evaluates False.
    left_priority = default_priority()
    left_evaluates = False
    # The polynomial operand is able to contribute (the boolean is True), its
    # contribution IS the computed product (right_evaluates True), and it
    # carries the polynomial selection attribute.
    right_priority = polynomial_priority()
    right_evaluates = True
    # (Assert stripped: contract-side cross-check only.)
    # With the polynomial's attribute strictly greater and it being able to
    # contribute, the selection rule picks the polynomial and the product comes
    # out computed.
    return product_is_evaluated(left_priority, left_evaluates,
                                right_priority, right_evaluates, True)


# --- oracle: the real patched repo -------------------------------------------

def make_dispatch_oracle():
    """Probe classes around the REAL call_highest_priority wrapper.

    The wrapper reads ``self._op_priority`` / ``other._op_priority`` and the
    presence of the named reverse handler at call time, so one set of classes
    serves every probe: the per-call priorities and contribution booleans are
    set as instance attributes.
    """
    from sympy.core.decorators import call_highest_priority

    class LeftOperand(object):
        _op_priority = 0.0
        _contribution = False

        @call_highest_priority('__r_probe__')
        def probe(self, other):
            # func(self, other): the left operand contributed the result
            return self._contribution

    class RightWithHandler(object):
        _op_priority = 0.0
        _contribution = False

        def __r_probe__(self, other):
            # the right operand's reverse handler contributed the result
            return self._contribution

    class RightWithoutHandler(object):
        # exposes _op_priority but NOT the reverse handler
        _op_priority = 0.0

    def oracle(self_priority, self_evaluates, other_priority,
               other_evaluates, other_has_handler):
        left = LeftOperand()
        left._op_priority = self_priority
        left._contribution = self_evaluates
        if other_has_handler:
            right = RightWithHandler()
            right._contribution = other_evaluates
        else:
            right = RightWithoutHandler()
        right._op_priority = other_priority
        return left.probe(right)

    return oracle


def real_priorities():
    """The real class data the two modeled constants stand for."""
    from sympy.core.expr import Expr
    from sympy.polys.polytools import Poly
    return Expr._op_priority, Poly._op_priority


def real_generic_times_polynomial(generic_expr):
    """End-to-end observable: is <generic expr> * Poly(x) the computed
    polynomial product (an evaluated Poly equal to Poly(x) * expr)?"""
    from sympy import Symbol, Poly
    x = Symbol('x')
    p = Poly(x, x)
    prod = generic_expr * p
    return isinstance(prod, Poly) and prod == p * generic_expr


# --- input generation ----------------------------------------------------------

def boundary_priorities():
    base = default_priority()          # 10.0
    poly = polynomial_priority()       # 10.001
    ulp = 8.881784197001252e-16        # one ULP of a float at 10.0
    vals = [
        base, poly,
        base + 1e-15, base - 1e-15,
        base + ulp, base - ulp,
        base + ulp / 2.0,              # collapses onto base when added
        base + 1e-3, base - 1e-3,
        poly + 1e-15, poly - 1e-15,
        0.0, -0.0, 1.0, -1.0, -10.0, -10.001,
        1e-300, -1e-300, 1e300, -1e300,
        float('inf'), float('-inf'), float('nan'),
        5e-324,                        # smallest subnormal
        9.999999999999998, 10.000000000000002,
    ]
    return vals


def fuzz_priority(rng):
    k = rng.randint(0, 5)
    if k == 0:
        return rng.uniform(9.9, 10.1)
    if k == 1:
        return 10.0 + rng.uniform(-1e-14, 1e-14)
    if k == 2:
        return rng.uniform(-1e6, 1e6)
    if k == 3:
        return rng.choice([10.0, 10.001, 0.0, -0.0, 1e300, -1e300,
                           float('inf'), float('-inf'), float('nan')])
    if k == 4:
        # wide dynamic range via random exponent
        m = rng.uniform(-1.0, 1.0)
        e = rng.randint(-300, 300)
        return m * (10.0 ** e)
    return float(rng.randint(-20, 20))


def fmt(v):
    return repr(v)


def main():
    dispatch = make_dispatch_oracle()

    checked = 0
    disagreements = [0]

    def check(sp, se, op, oe, oh):
        shadow = product_is_evaluated(sp, se, op, oe, oh)
        real = dispatch(sp, se, op, oe, oh)
        if bool(shadow) != bool(real):
            disagreements[0] += 1
            print("DISAGREEMENT at self_priority=%s self_evaluates=%r "
                  "other_priority=%s other_evaluates=%r other_has_handler=%r:\n"
                  "  shadow (impl region)        = %r\n"
                  "  real (call_highest_priority) = %r"
                  % (fmt(sp), se, fmt(op), oe, oh, shadow, real))
            return False
        return True

    # 1) constants vs the real class data (the patched datum + the baseline)
    real_default, real_poly = real_priorities()
    if default_priority() != real_default:
        print("DISAGREEMENT on the baseline priority constant:\n"
              "  shadow default_priority() = %r\n"
              "  real Expr._op_priority    = %r"
              % (default_priority(), real_default))
        return 1
    if polynomial_priority() != real_poly:
        print("DISAGREEMENT on the polynomial priority constant:\n"
              "  shadow polynomial_priority() = %r\n"
              "  real Poly._op_priority       = %r"
              % (polynomial_priority(), real_poly))
        return 1

    # 2) end-to-end observable vs the real product, several generic operands
    from sympy import Symbol
    x = Symbol('x')
    for expr in (x, x + 1, x ** 2, 2 * x):
        real_e2e = real_generic_times_polynomial(expr)
        shadow_e2e = generic_times_polynomial()
        checked += 1
        if bool(shadow_e2e) != bool(real_e2e):
            print("DISAGREEMENT on the end-to-end product with generic "
                  "operand %s:\n"
                  "  shadow generic_times_polynomial() = %r\n"
                  "  real (expr * Poly evaluated?)     = %r"
                  % (expr, shadow_e2e, real_e2e))
            return 1

    # 3) boundary grid: priority pairs x all 8 boolean combinations
    bvals = boundary_priorities()
    bools = [False, True]
    n_boundary = 0
    for sp in bvals:
        for op in bvals:
            for se in bools:
                for oe in bools:
                    for oh in bools:
                        checked += 1
                        n_boundary += 1
                        if not check(sp, se, op, oe, oh):
                            return 1

    # 4) randomized fuzz, pinned seed; exact ties forced ~1/8 of the time
    rng = random.Random(SEED)
    for _ in range(N_FUZZ):
        sp = fuzz_priority(rng)
        op = sp if rng.randint(0, 7) == 0 else fuzz_priority(rng)
        se = rng.randint(0, 1) == 1
        oe = rng.randint(0, 1) == 1
        oh = rng.randint(0, 1) == 1
        checked += 1
        if not check(sp, se, op, oe, oh):
            return 1

    print("G-CONF OK: shadow impl == real patched repo on %d inputs "
          "(2 priority constants + 4 end-to-end products + %d boundary + "
          "%d fuzz, seed %d); 0 disagreements."
          % (checked, n_boundary, N_FUZZ, SEED))
    print(json.dumps({"checked": checked, "disagreements": 0, "seed": SEED,
                      "shadow": "direct (contract-stripped impl region)"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())

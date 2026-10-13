#!/usr/bin/env python3
"""G-AX executable soundness check for sympy__sympy-13757.

Executes the REAL SymPy callees (the priority-dispatch decorator, the two
operation-priority class data, and the end-to-end product) and asserts every
observation matches the model, as encoded in model.py.

The kind-A checks (all A-reference: the relevant code is UNCHANGED by the patch
and modeled DEEPLY, not behind a consumed axiom):

  (A-reference, mapping.md §3.1) the deep model `resolved_by_right(p_self,
      p_other, has)` == the real `binary_op_wrapper` delegation decision from
      `sympy.core.decorators.call_highest_priority`: a binary special method
      delegates to the right operand's reverse handler iff that operand exposes
      it AND `other._op_priority > self._op_priority` (strict). Patch-independent.

  (A-reference, mapping.md §3.2) the modeled priorities == the real class data:
      `default_priority() == Expr._op_priority == 10.0`, and a polynomial
      advertises `Poly._op_priority` strictly above the default. The latter is
      the patched datum: in the GOLD (post-patch) container this strict order
      holds (and equals the modeled `polynomial_priority() == 10.001`); the
      script also records the pre-patch equality (the bug) when run unpatched.

  (end-to-end) with the real `Symbol('x')` and `Poly(x)`, the product
      `x * Poly(x)` is the EVALUATED polynomial `Poly(x)*x` exactly when the
      strict priority order holds — i.e. `generic_times_polynomial()`'s
      observable. Post-patch it must evaluate.

Imports only `sympy` (the package the patch lives in). Exit 0 iff every
obligation holds in the state it is run (the GOLD-applied container for the
A-reference validation; it also tolerates and reports the pre-patch state).
"""
import random
import sys


# --- model.py reference encodings (kept in lock-step with the deep models) ----

DEFAULT_PRIORITY = 10.0          # default_priority()
POLYNOMIAL_PRIORITY = 10.001     # polynomial_priority()


def resolved_by_right(self_priority, other_priority, other_has_handler):
    """Reference implementation of model.py's deep dispatch model."""
    return other_has_handler and other_priority > self_priority


# --- the real callee: the priority-dispatch decorator -------------------------

def real_delegates(self_priority, other_priority, other_has_handler):
    """Run the REAL `binary_op_wrapper` from
    sympy.core.decorators.call_highest_priority and report whether it delegated
    to the right operand's reverse handler. Patch-independent (decorator code is
    unchanged)."""
    from sympy.core.decorators import call_highest_priority

    delegated = {"v": False}

    class Left(object):
        _op_priority = self_priority

        @call_highest_priority('__rother__')
        def op(self, other):
            return "left"   # func(self, other): the left operand handled it

    class RightWithHandler(object):
        _op_priority = other_priority

        def __rother__(self, other):
            delegated["v"] = True
            return "right"  # the right operand's reverse handler ran

    class RightNoHandler(object):
        _op_priority = other_priority
        # exposes _op_priority but NOT the reverse handler

    right = RightWithHandler() if other_has_handler else RightNoHandler()
    Left().op(right)
    return delegated["v"]


def check_dispatch(self_priority, other_priority, other_has_handler):
    observed = real_delegates(self_priority, other_priority, other_has_handler)
    expected = resolved_by_right(self_priority, other_priority, other_has_handler)
    assert observed == expected, (
        "dispatch deep model unsound on (self=%r, other=%r, has=%r): real "
        "binary_op_wrapper delegated=%r, model resolved_by_right=%r"
        % (self_priority, other_priority, other_has_handler, observed, expected))


def main():
    # --- A-reference §3.1: dispatch deep model == real binary_op_wrapper ------
    grid = [10.0, 10.001, 9.999, 11.0, 0.0, -1.0, 1e9, 10.0000001]
    boundary = []
    for ps in grid:
        for po in grid:
            for has in (True, False):
                boundary.append((ps, po, has))
    # explicit equal-priority tie (the pre-patch bug locus) and the strict cross
    boundary += [
        (10.0, 10.0, True),      # tie: left handles (no delegation) -> the bug
        (10.0, 10.001, True),    # strict cross: right (Poly) handles -> the fix
        (10.0, 10.001, False),   # strict cross but no handler: left handles
    ]
    for ps, po, has in boundary:
        check_dispatch(ps, po, has)

    rng = random.Random(13757)
    for _ in range(20000):
        ps = rng.choice([rng.uniform(-1e3, 1e3), 10.0, 10.001])
        po = rng.choice([rng.uniform(-1e3, 1e3), 10.0, 10.001])
        has = rng.random() < 0.5
        check_dispatch(ps, po, has)

    # --- A-reference §3.2: modeled priorities == real class data --------------
    from sympy.core.expr import Expr
    from sympy import Poly
    assert Expr._op_priority == DEFAULT_PRIORITY, (
        "default priority drifted: model %r, real Expr._op_priority %r"
        % (DEFAULT_PRIORITY, Expr._op_priority))

    poly_prio = Poly._op_priority
    strict_above = poly_prio > Expr._op_priority

    # --- end-to-end: x * Poly(x) evaluates iff the strict order holds ---------
    from sympy.abc import x
    p = Poly(x)
    left_times = p * x          # Poly(x) * x : always evaluated (Poly.__mul__)
    right_times = x * p         # x * Poly(x) : the bugged side
    assert getattr(left_times, "is_Poly", False), (
        "Poly(x)*x should be an evaluated Poly, got %r" % (left_times,))

    if strict_above:
        # GOLD (post-patch) state: this is the world the A-reference validates.
        assert poly_prio == POLYNOMIAL_PRIORITY, (
            "polynomial priority drifted: model %r, real Poly._op_priority %r"
            % (POLYNOMIAL_PRIORITY, poly_prio))
        assert getattr(right_times, "is_Poly", False), (
            "post-patch: x*Poly(x) must be an evaluated Poly, got %r"
            % (right_times,))
        assert right_times == left_times, (
            "post-patch: x*Poly(x) must equal Poly(x)*x, got %r vs %r"
            % (right_times, left_times))
        print("G-AX OK: dispatch deep model == real binary_op_wrapper over %d "
              "boundary + 20000 fuzz; Expr._op_priority==10.0, "
              "Poly._op_priority==%r (> default); x*Poly(x) evaluates and "
              "equals Poly(x)*x." % (len(boundary), poly_prio))
        return 0

    # PRE-PATCH state (Poly inherits the default): record the bug, still sound
    # as a faithful observation of the unpatched callee. The A-reference
    # validation proper is run with the gold patch applied (apply_gold=True).
    assert poly_prio == Expr._op_priority, (
        "pre-patch expected Poly to inherit the default priority, got %r"
        % (poly_prio,))
    assert not getattr(right_times, "is_Poly", False), (
        "pre-patch: x*Poly(x) is expected to stay unevaluated, got %r"
        % (right_times,))
    print("G-AX OK (pre-patch observed): dispatch deep model == real "
          "binary_op_wrapper over %d boundary + 20000 fuzz; Poly inherits the "
          "default priority (the bug: x*Poly(x) does not evaluate). Run with "
          "the gold patch applied to validate the post-patch A-reference."
          % (len(boundary),))
    return 0


if __name__ == "__main__":
    sys.exit(main())

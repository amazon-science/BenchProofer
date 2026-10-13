#!/usr/bin/env python
"""G-AX — deep-model reference validation for sympy__sympy-13757.

The bundle consumes NO `_prop` axiom: the precedence-dispatch decision is modeled
DEEPLY in the impl (the comparison `polyPriority > exprPriority` is spelled out).
But the impl's faithfulness rests on two PATCH-INDEPENDENT facts about the real
repo, tagged A-reference in refinement.md. This check asserts them against the
actual sympy source (run in-container at base_commit):

  1. A plain expression advertises operator precedence `Expr._op_priority == 10.0`
     (the UNCHANGED left-operand priority the impl pins as `exprPriority := 10`).
  2. The binary-operator dispatch (`call_highest_priority`) delegates the
     operation to the OTHER operand iff that operand advertises a STRICTLY
     greater `_op_priority`; otherwise it builds the default product. This is the
     rule the impl encodes as `if polyPriority > exprPriority then ... else
     symbolic`.
  3. The polynomial's own multiplication routines (`Poly.__mul__`/`__rmul__`)
     coerce the plain-expression factor into a polynomial and carry the product
     out (-> a Poly, `evaluated`) when the expression is CONVERTIBLE over the
     polynomial's generators, and fall back to a plain symbolic expression
     (-> non-Poly, `symbolic`) when it is not. This is the rule the impl encodes
     as `if coercible then evaluated else symbolic` on both branches.

All are unchanged by the patch (the patch only sets `Poly._op_priority`, which
G-GOLD/G-RESOLVE validate). We additionally record `Poly._op_priority` so the
post-patch value (10.001) is observable, but the SOUNDNESS-critical assertions
are the unchanged facts above.

stdlib + the in-repo sympy only; exit 0 iff every observation meets the modeled
property.
"""
import os
import sys

# Make the in-container repo importable (cwd is the repo root in the harness).
sys.path.insert(0, os.getcwd())

FAILURES = []


def check(cond, msg):
    if not cond:
        FAILURES.append(msg)


def main() -> int:
    from sympy.core.expr import Expr
    from sympy.core.decorators import call_highest_priority

    # --- Fact 1: the plain-expression operator precedence is 10.0 -------------
    check(Expr._op_priority == 10.0,
          f"Expr._op_priority expected 10.0, got {Expr._op_priority!r}")

    # --- Fact 2: the dispatch rule — delegate iff strictly greater priority ---
    # Two toy operands carrying `_op_priority`; the decorated method delegates to
    # `other.<method_name>` only when other outranks self, else runs the body.
    class Operand(object):
        def __init__(self, priority, tag):
            self._op_priority = priority
            self.tag = tag

        @call_highest_priority('__rmul__')
        def __mul__(self, other):
            return ("body", self.tag, other.tag)   # default product (no delegation)

        def __rmul__(self, other):
            return ("delegated", self.tag, other.tag)

    def outcome(self_pr, other_pr):
        a = Operand(self_pr, "self")
        b = Operand(other_pr, "other")
        res = a.__mul__(b)
        return res[0]   # "delegated" or "body"

    # other strictly greater -> delegated (the "evaluated" analogue)
    check(outcome(10.0, 10.001) == "delegated",
          "dispatch: other(10.001) > self(10.0) must delegate")
    # tie -> NOT delegated (this is exactly the pre-patch bug: stays symbolic)
    check(outcome(10.0, 10.0) == "body",
          "dispatch: equal priorities must NOT delegate (falls to default product)")
    # other lower -> NOT delegated
    check(outcome(10.001, 10.0) == "body",
          "dispatch: other(10.0) < self(10.001) must NOT delegate")
    # a spread of pairs: delegate iff strictly greater
    for sp in (9.5, 10.0, 10.001, 10.5):
        for op in (9.5, 10.0, 10.001, 10.5):
            expect = "delegated" if op > sp else "body"
            check(outcome(sp, op) == expect,
                  f"dispatch rule mismatch at self={sp} other={op}")

    # --- Fact 3: Poly.__mul__/__rmul__ — coerce when convertible, else fall ---
    # back to the plain symbolic product. UNCHANGED by the patch. Exercised
    # directly on the in-repo Poly (no priority dispatch involved on polyLeft;
    # __rmul__ is called explicitly to bypass the dispatch on polyRight).
    try:
        from sympy import symbols, sin, sqrt
        from sympy.polys.polytools import Poly as _Poly
        _x = symbols('x')
        _p = _Poly(_x, _x)
        # coercible operand (a generator): both routines produce a Poly
        r = _p.__mul__(_x)
        check(getattr(r, 'is_Poly', False) is True,
              f"Poly.__mul__(coercible) expected a Poly, got {type(r).__name__}")
        r = _p.__rmul__(_x)
        check(getattr(r, 'is_Poly', False) is True,
              f"Poly.__rmul__(coercible) expected a Poly, got {type(r).__name__}")
        # non-coercible operands (generator used non-polynomially): both
        # routines fall back to a plain (non-Poly) expression
        for bad in (sin(_x), sqrt(_x), 1/_x):
            r = _p.__mul__(bad)
            check(getattr(r, 'is_Poly', False) is not True,
                  f"Poly.__mul__({bad}) expected non-Poly fallback, got {r!r}")
            r = _p.__rmul__(bad)
            check(getattr(r, 'is_Poly', False) is not True,
                  f"Poly.__rmul__({bad}) expected non-Poly fallback, got {r!r}")
    except ImportError as e:  # pragma: no cover
        FAILURES.append(f"could not exercise Poly mul routines ({e})")

    # --- Observe the post-patch Poly priority (informational) -----------------
    try:
        from sympy.polys.polytools import Poly
        poly_pr = Poly._op_priority
        # At base_commit this is the inherited 10.0; post-patch 10.001. Either is
        # a valid observation depending on the checkout; we only require it to be
        # >= the expression priority (never lower).
        check(poly_pr >= 10.0,
              f"Poly._op_priority expected >= 10.0, got {poly_pr!r}")
        print(f"observed Poly._op_priority={poly_pr!r}")
    except Exception as e:  # pragma: no cover
        print(f"note: could not import Poly ({e}); skipping Poly observation")

    if FAILURES:
        for f in FAILURES:
            print("AXIOM VIOLATION:", f)
        print("status=fail")
        return 1
    print("status=pass all A-reference facts hold against the real repo")
    return 0


if __name__ == "__main__":
    sys.exit(main())

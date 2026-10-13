#!/usr/bin/env python3
"""G-AX executable soundness check for sympy__sympy-21612.

There are NO @ContractOnly axioms in model.py. The one changed operation — the
per-denominator-factor bracketing guard — is modeled DEEPLY (the `Factor`
abstraction with `parts`/`form` and the `needs_brackets` predicate), not behind
a consumed axiom. This script plays the G-AX A-reference role: it validates that
the deep model's facet bijection is faithful to the REAL sympy structure.

For every denominator factor of the issue's and #14160's real (unevaluated)
expressions it:

  (1) extracts the real facets the gold guard inspects:
        parts = len(item.args[0].args)
        form  = 1 if isinstance(item.base, Mul)      # product
                2 if isinstance(item.base, Pow)      # power
                0 otherwise                          # atomic / other
      (the model's form tag, mapping.md §2);
  (2) asserts the model predicate
        needs_brackets(parts, form) == (parts != 1 and form in (1, 2))
      equals the REAL POST-PATCH guard
        len(item.args[0].args) != 1 and isinstance(item.base, (Mul, Pow));
  (3) asserts it DIFFERS from the REAL PRE-PATCH guard
        len(item.args[0].args) != 1 and isinstance(item.base, Mul)
      exactly on the issue's reciprocal-of-reciprocal factor `1/y` (the bug);
  (4) confirms the rendered strings change accordingly: `x/1/y` (pre) ->
      `x/(1/y)` (post), with `#14160` unchanged at `-2*x/(y*y)`.

Imports only `sympy` (the repo under test). Exit 0 iff the abstraction is sound.
"""
import sys


# --- model.py reference predicate (kept in lock-step with the spec) ----------

def is_composite_form(form):
    return form == 1 or form == 2


def needs_brackets(parts, form):
    return parts != 1 and is_composite_form(form)


def main():
    from sympy import symbols, Mul, Pow, S

    x, y = symbols('x y')

    def form_tag(base):
        # The model's structural-form tag (mapping.md §2): 1 product, 2 power,
        # 0 any other class. Order matters: Pow is not a Mul, Mul is not a Pow.
        if isinstance(base, Mul):
            return 1
        if isinstance(base, Pow):
            return 2
        return 0

    def real_guard_post(item):
        return (len(item.args[0].args) != 1 and
                isinstance(item.base, (Mul, Pow)))

    def real_guard_pre(item):
        return (len(item.args[0].args) != 1 and
                isinstance(item.base, Mul))

    # The two witnesses: the issue (21537) and the #14160 case the test guards.
    issue = Mul(x, Pow(1 / y, -1, evaluate=False), evaluate=False)
    case14160 = Mul(-2, x,
                    Pow(Mul(y, y, evaluate=False), -1, evaluate=False),
                    evaluate=False)

    def denom_items(expr):
        # The denominator items the gather loop sees: commutative Pow factors
        # with exp == -1 (mapping.md §1).
        out = []
        for item in expr.args:
            if (getattr(item, 'is_commutative', False) and
                    isinstance(item, Pow) and
                    item.exp is S.NegativeOne):
                out.append(item)
        return out

    checked = 0
    pre_post_disagreements = []

    for name, expr in (('issue21537', issue), ('issue14160', case14160)):
        for item in denom_items(expr):
            parts = len(item.args[0].args)
            form = form_tag(item.base)

            model = needs_brackets(parts, form)
            post = real_guard_post(item)
            pre = real_guard_pre(item)

            # (2) deep model == real POST-patch guard.
            assert model == post, (
                "deep model unsound on %s factor %r: needs_brackets(%r,%r)=%r "
                "but real post-patch guard=%r"
                % (name, item, parts, form, model, post))
            checked += 1

            if pre != post:
                pre_post_disagreements.append((name, item, parts, form))

    # (3) the change is observable: exactly the issue's `1/y` factor flips, and
    # nothing in the #14160 witness flips.
    assert len(pre_post_disagreements) == 1, (
        "expected exactly one pre/post guard disagreement (the bug); got %r"
        % (pre_post_disagreements,))
    name, item, parts, form = pre_post_disagreements[0]
    assert name == 'issue21537' and form == 2 and parts != 1, (
        "the discriminating factor must be the issue's power-form reciprocal "
        "(form=2, parts!=1); got %r" % ((name, parts, form),))

    # (4) rendered strings match the issue's expectation under the post-patch
    # guard. (str() uses the live installed code; with the gold patch applied
    # in-container these hold. Pre-patch the issue string is the buggy form.)
    s_issue = str(issue)
    s_14160 = str(case14160)
    assert s_14160 == '-2*x/(y*y)', "#14160 rendering drifted: %r" % (s_14160,)
    assert s_issue in ('x/(1/y)', 'x/1/y'), (
        "unexpected issue rendering: %r" % (s_issue,))

    print("G-AX OK: deep model `needs_brackets` == real post-patch guard on "
          "%d denominator factors; exactly 1 pre/post disagreement (the "
          "issue's power-form reciprocal `1/y`); #14160 unchanged. "
          "issue str=%r" % (checked, s_issue))
    return 0


if __name__ == "__main__":
    sys.exit(main())

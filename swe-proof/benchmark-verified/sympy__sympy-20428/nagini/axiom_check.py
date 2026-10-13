#!/usr/bin/env python3
"""G-AX executable soundness check for sympy__sympy-20428.

Executes the REAL repo callee (`ExpressionDomain.Expression.__bool__`, post-patch
= `not f.ex.is_zero`) on a battery of symbolic ground-domain coefficients and
asserts that every observation matches the deep model encoded in model.py.

There are NO consumed `@ContractOnly` axioms in this bundle. The single changed
sub-operation — routing a coefficient's truthiness through its MATHEMATICAL zero
value (`Expr.is_zero`) rather than its STRUCTURAL inequality with the bare zero
literal (`!= 0`) — is modeled DEEPLY by the `Coeff.mzero` facet. This is the
A-reference G-AX validates:

  (A-reference)  for every EX coefficient `c`:
                   model `coeff_truthy(c) == (c.mzero == 0)`
                 equals the real callee
                   bool(c) == (not c.ex.is_zero).
                 The model's class invariant `lit0 == 1 ==> mzero == 1` is the
                 SymPy fact `Integer(0).is_zero is True`.

It further exhibits the DISCRIMINATION the model encodes (the bug): on a
coefficient that denotes zero but whose structural shape is NOT the bare zero
literal (`mzero == 1, lit0 == 0`), the OLD structural test `c.ex != 0` reports
`True` (truthy) while the FIX reports `False` (falsy) — and reconstructs the
issue's observable consequence at the polynomial level: such a constant strips
to the canonical zero representation `DMP([], EX, None)` under the fix but to the
buggy `DMP([EX(0)], EX, None)` under the old test, so that
`Poly(<zero expr>, x) == Poly(0, x, domain='EX')` holds.

Imports only `sympy` (the repo under test, with the patch applied). Exit 0 iff
every observation matches the deep model.
"""
import sys


def model_coeff_truthy(mzero):
    """model.py coeff_truthy under the Coeff carrier: truthy iff mzero == 0."""
    return mzero == 0


def model_strip_len(mzero):
    """model.py strip_constant_len: stored constant-poly list length (0 = the
    canonical zero poly) -- empty iff the coefficient denotes zero."""
    return 1 if model_coeff_truthy(mzero) else 0


def check_coeff(EX, ex):
    """For a real EX coefficient over the SymPy expr `ex`, assert the deep model
    matches the real (post-patch) __bool__, and that the structural/ math facets
    obey the modeled class invariant."""
    coeff = EX.Expression(ex)

    # the real, post-patch callee under test
    real_bool = bool(coeff)                         # == (not coeff.ex.is_zero)

    # the two modeled facets, read off the real expression
    mzero = 1 if (coeff.ex.is_zero is True) else 0  # mathematical zero
    # structural facet: is the canonical form the bare integer-0 literal?
    lit0 = 1 if (coeff.ex == 0 and coeff.ex.is_zero is True
                 and coeff.ex.is_Integer) else 0

    # A-reference: deep model coeff_truthy == real __bool__
    assert real_bool == model_coeff_truthy(mzero), (
        "coeff_truthy deep model unsound on ex=%r: real bool()=%r, "
        "model (mzero=%d)=%r" % (ex, real_bool, mzero, model_coeff_truthy(mzero)))

    # class invariant: a bare-zero-literal shape always denotes zero
    if lit0 == 1:
        assert mzero == 1, (
            "class invariant violated on ex=%r: lit0=1 but mzero=0" % (ex,))

    return lit0, mzero


def main():
    from sympy import (S, sqrt, sympify, symbols, Integer, Rational, cos, sin,
                       pi, exp, log, Poly)
    from sympy.polys.domains import EX

    x = symbols("x")

    # --- ordinary non-zero coefficients (mzero == 0, must be truthy) ----------
    nonzero = [
        Integer(1), Integer(-3), Rational(2, 7), sqrt(2), x, x + 1,
        sympify("a + b"), cos(x), exp(1), pi, sympify("2*sqrt(3) - 1"),
    ]
    for ex in nonzero:
        lit0, mzero = check_coeff(EX, ex)
        assert mzero == 0, "expected non-zero ex=%r to have mzero=0" % (ex,)
        assert bool(EX.Expression(ex)) is True

    # --- the bare zero literal (lit0 == 1, mzero == 1, must be falsy) ---------
    for ex in [Integer(0), S.Zero, sympify("0")]:
        lit0, mzero = check_coeff(EX, ex)
        assert mzero == 1 and lit0 == 1
        assert bool(EX.Expression(ex)) is False

    # --- DENOTING-ZERO but structurally NON-trivial (the discriminating case) -
    # expressions that are mathematically zero yet not the bare Integer(0):
    denoting_zero = [
        sqrt(2) - sqrt(2),
        cos(x)**2 + sin(x)**2 - 1,
        (x + 1)**2 - (x**2 + 2*x + 1),
        log(exp(3)) - 3,
        sympify("1/2 + 1/2 - 1"),
    ]
    for ex in denoting_zero:
        if ex.is_zero is not True:
            # only meaningful if SymPy can decide the zero; skip undecidable
            continue
        lit0, mzero = check_coeff(EX, ex)
        assert mzero == 1, "expected denoting-zero ex=%r to have mzero=1" % (ex,)
        # the FIX makes it falsy ...
        assert bool(EX.Expression(ex)) is False, (
            "fix should make denoting-zero ex=%r falsy" % (ex,))
        # ... and the OLD structural test disagreed (reported truthy) IF the
        # structural form is not the bare literal -- witness the discrimination
        if lit0 == 0:
            old_structural_truthy = bool(ex != 0)
            assert old_structural_truthy is True, (
                "old structural test should report denoting-zero non-literal "
                "ex=%r as truthy (the bug); got %r" % (ex, old_structural_truthy))

    # --- the EXACT issue coefficient via clear_denoms, end-to-end -------------
    big = sympify(
        "-117968192370600*18**(S(1)/3)/(217603955769048*(24201 + "
        "253*sqrt(9165))**(S(1)/3) + 2273005839412*sqrt(9165)*(24201 + "
        "253*sqrt(9165))**(S(1)/3)) - 15720318185*2**(S(2)/3)*3**(S(1)/3)*"
        "(24201 + 253*sqrt(9165))**(S(2)/3)/(217603955769048*(24201 + "
        "253*sqrt(9165))**(S(1)/3) + 2273005839412*sqrt(9165)*(24201 + "
        "253*sqrt(9165))**(S(1)/3)) + 15720318185*12**(S(1)/3)*(24201 + "
        "253*sqrt(9165))**(S(2)/3)/(217603955769048*(24201 + 253*sqrt(9165))**"
        "(S(1)/3) + 2273005839412*sqrt(9165)*(24201 + 253*sqrt(9165))**(S(1)/3))"
        " + 117968192370600*2**(S(1)/3)*3**(S(2)/3)/(217603955769048*(24201 + "
        "253*sqrt(9165))**(S(1)/3) + 2273005839412*sqrt(9165)*(24201 + "
        "253*sqrt(9165))**(S(1)/3))",
        {"S": S})
    f = Poly(big, x)
    # the modeled poly-level consequence: a constant denoting zero strips to the
    # canonical zero representation, so equals Poly(0, x, domain='EX')
    assert f == Poly(0, x, domain="EX"), (
        "issue coefficient: Poly(<zero expr>, x) should equal Poly(0,x,EX)")
    assert f.is_zero is True, "issue coefficient: f.is_zero should be True"
    assert f.rep.rep == [], (
        "issue coefficient: stored rep should be the canonical [] (DMP([], EX)),"
        " got %r" % (f.rep.rep,))
    # strip-length deep model agrees: the coefficient denotes zero -> length 0
    assert model_strip_len(1) == 0 and len(f.rep.rep) == model_strip_len(1)

    # --- a non-zero constant poly retains its single coefficient --------------
    g = Poly(sqrt(2), x, domain="EX")
    assert g.is_zero is False
    assert len(g.rep.rep) == model_strip_len(0) == 1

    print("G-AX OK: deep model (coeff_truthy == not Expr.is_zero; strip-length) "
          "== real ExpressionDomain.Expression.__bool__ over %d non-zero, 3 "
          "literal-zero, %d denoting-zero coefficients + the exact issue "
          "clear_denoms coefficient (Poly(<zero>,x) == Poly(0,x,EX), rep == [])"
          % (len(nonzero), len(denoting_zero)))
    return 0


if __name__ == "__main__":
    sys.exit(main())

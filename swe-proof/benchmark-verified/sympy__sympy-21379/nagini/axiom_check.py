#!/usr/bin/env python3
"""G-AX executable soundness check for sympy__sympy-21379.

Executes the REAL sympy callee (`sympy.gcd`, the common-factor routine the
modular-reduction code calls) on inputs covering each operand-shape code the
model uses, and asserts that every observation matches the axioms encoded in
model.py.

The model abstracts the dividend/divisor pair by an integer operand-shape code:

  code 0 — a genuine common factor: `gcd` returns NORMALLY a NON-trivial factor
           (`Result() != 1`).            (axiom `common_factor(0) != 1`)
  code 1 — a trivial common factor: `gcd` returns NORMALLY the multiplicative
           identity (`Result() == 1`).   (axiom `common_factor(1) == 1`)
  code 2 — the case-split (Piecewise) shape: `gcd` REFUSES, raising
           `PolynomialError`.            (axiom `common_factor_compute`
                                          `Exsures(FactorUnavailable, code==2)`)

The checks:

  (A-consumed) `common_factor` / `common_factor_compute` — the unchanged
      common-factor routine `sympy.gcd`:
        * code-0 operand pairs (a shared factor): gcd returns != 1, no raise;
        * code-1 operand pairs (coprime): gcd returns == 1, no raise;
        * code-2 operand pairs (a Piecewise / case-split argument): gcd RAISES
          PolynomialError — so the model's refusal branch is sound and the fix's
          try/except is load-bearing.

  (end-to-end, refusal path) with the gold fix applied, the FAIL_TO_PASS
      operations (`Mod` over a Piecewise/z argument, and the `is_zero` query that
      triggers it) COMPLETE without raising — confirming clause (1)/(2): the
      operation always completes and on the unanswerable input keeps the identity
      factor and leaves the operands unchanged.

  (end-to-end, transform path) on an answerable input with a non-identity factor
      (`divide_out` / `gcd_terms`, `build_result` / Mul-Mod construction), the
      `Mod` actually rewrites each operand by dividing the factor out, so the
      operands are transformed before the result is built — confirming clause
      (3a) and the soundness of `divide_out` / `build_result` (the operand
      transform the strengthened spec makes load-bearing). Validated against the
      F2P test's own pre-existing code-0 assertions.

Imports only `sympy` (the patched repo, on PYTHONPATH in-container) — nothing
bundle-specific. Exit 0 iff every obligation holds.
"""
import sys


def main():
    from sympy import symbols, Piecewise, gcd, S, exp
    from sympy.functions.elementary.hyperbolic import sinh, cosh, tanh
    from sympy.polys.polyerrors import PolynomialError

    x, y, z = symbols('x y z', real=True)
    a, b = symbols('a b')

    # --- A-consumed: code 0 (genuine common factor) -> gcd returns != 1 -------
    code0_pairs = [
        (2 * x, 2 * y),
        (S(6), S(9)),
        (4 * a, 6 * a),
        (3 * x * y, 3 * x),
        (x ** 2 - 1, x ** 2 - 3 * x + 2),   # docstring example: gcd == x - 1
        (S(10), S(15)),
        (12 * a * b, 8 * a),
    ]
    for p, q in code0_pairs:
        G = gcd(p, q)                       # must NOT raise
        assert G != 1, (
            "common_factor axiom unsound (code 0): gcd(%r, %r) == %r, "
            "model requires a NON-trivial factor (!= 1)" % (p, q, G))

    # --- A-consumed: code 1 (trivial common factor) -> gcd returns == 1 -------
    code1_pairs = [
        (x, y),
        (S(7), S(13)),
        (a, b),
        (x + 1, x - 1),
        (S(1), S(1)),
        (x, S(5)),
    ]
    for p, q in code1_pairs:
        G = gcd(p, q)                       # must NOT raise
        assert G == 1, (
            "common_factor axiom unsound (code 1): gcd(%r, %r) == %r, "
            "model requires the trivial factor (== 1)" % (p, q, G))

    # --- A-consumed: code 2 (case-split / Piecewise shape) -> gcd REFUSES -----
    pw = Piecewise((x, y > x), (y, True))
    code2_pairs = [
        (pw / z, S.One),
        (pw, x),
        (pw / z, S(2)),
        (pw * z ** -1, y),
        (Piecewise((a, a > 2), (S(2), True)), a),
    ]
    raised = 0
    for p, q in code2_pairs:
        try:
            G = gcd(p, q)
            raise AssertionError(
                "common_factor_compute axiom unsound (code 2): gcd(%r, %r) "
                "returned %r instead of raising PolynomialError" % (p, q, G))
        except PolynomialError:
            raised += 1
    assert raised == len(code2_pairs), (
        "expected every code-2 pair to raise PolynomialError; got %d/%d"
        % (raised, len(code2_pairs)))

    # --- end-to-end (gold fix applied): FAIL_TO_PASS completes, no raise ------
    # On the case-split shape the reduction keeps the trivial factor (G == 1)
    # and leaves the operands unchanged: the Mod simply does not evaluate away.
    for fn in (sinh, cosh, tanh):
        # the is_zero query that, pre-fix, propagated PolynomialError out of Mod
        _ = fn(Piecewise((x, y > x), (y, True)) * z ** -1.0).is_zero
    r1 = (Piecewise((x, y > x), (y, True)) / z) % 1
    from sympy.core.mod import Mod
    assert isinstance(r1, Mod), (
        "expected (Piecewise/z) %% 1 to stay an unevaluated Mod (G == 1, "
        "operands unchanged); got %r" % (r1,))
    expr = exp(sinh(Piecewise((x, y > x), (y, True)) / z))
    expr.subs({1: 1.0})                     # must NOT raise

    # --- end-to-end (transform path): code-0 operands ARE rewritten -----------
    # On an answerable input with a non-identity factor the real Mod divides the
    # factor out of each operand (divide_out / gcd_terms) and builds the result
    # from the rewritten operands (build_result). These are the F2P test's own
    # pre-existing code-0 assertions: dropping the operand transform breaks them,
    # so they witness that divide_out / build_result are load-bearing (the hole
    # the strengthened spec now closes). gcd(12*x+18*y, 3*x) == 3*x is non-trivial.
    transform_cases = [
        ((12 * x + 18 * y) % (3 * x), 3 * Mod(6 * y, x)),
        ((4 * x + 6 * y + 5) % (2 * x), Mod(6 * y + 5, 2 * x)),
    ]
    for got, want in transform_cases:
        assert got == want, (
            "operand-transform (divide_out/build_result) unsound: %r != %r "
            "(the code-0 regroup must rewrite each operand by dividing the "
            "factor out before building the result)" % (got, want))
    # the bare factor on a code-0 pair is non-identity (the divide_out guard).
    assert gcd(12 * x + 18 * y, 3 * x) != 1

    print("G-AX OK: common_factor / common_factor_compute axioms sound on "
          "%d code-0 (!= 1), %d code-1 (== 1), %d code-2 (Piecewise->refuse) "
          "operand pairs; FAIL_TO_PASS Mod/is_zero complete without raising and "
          "%d code-0 operand-transform assertions (divide_out/build_result) hold "
          "post-fix" % (len(code0_pairs), len(code1_pairs), len(code2_pairs),
                        len(transform_cases)))
    return 0


if __name__ == "__main__":
    sys.exit(main())

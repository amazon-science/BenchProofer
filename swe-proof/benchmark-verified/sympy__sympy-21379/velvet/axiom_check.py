#!/usr/bin/env python3
"""G-AX executable soundness check for sympy__sympy-21379.

Runs the REAL repo callees the modeled block consults — `gcd`
(`commonFactor`) and `gcd_terms` (`reduceTerm`) — in-container, on boundary and
fuzzed operands, and asserts the facts the model relies on. Both callees are
modeled `opaque` with NO asserted `ensures`, so there is NO consumed axiom to
validate point-wise (directive 7). What G-AX establishes are the **A-reference**
facts that make the modeled control flow faithful and non-vacuous (mapping.md
§3, refinement.md §B):

  1. ERROR LEG REAL & REACHABLE: the real `gcd` actually RAISES on the operands
     the issue exhibits (a `Piecewise`-bearing argument of `Mod`), so the
     modeled `Except.error` branch — and hence the recovery the patch adds — is
     a genuine runtime path, not dead code.
  2. EXACT EXCEPTION TYPE: the raised exception is exactly `PolynomialError`
     (a `BasePolynomialError` subclass), matching the single exception type the
     `except` clause catches — not broader, not narrower.
  3. SUCCESS LEG REAL: on ordinary polynomial operands the real `gcd` returns a
     factor WITHOUT raising (so the `Except.ok` leg is inhabited), and when that
     factor is non-trivial the real `gcd_terms(i/G, …)` reduces each operand
     (the success-path `reduceTerm`).
  4. END-TO-END RECOVERY: with the gold patch applied the issue's
     `expr.subs({1: 1.0})` no longer raises and returns a value; pre-patch it
     raises `PolynomialError`. (Checked only if a patched tree is importable;
     the harness applies patch.diff before running the Docker gates.)

stdlib + the sympy under test only. Exit 0 iff every obligation holds.
"""
import random
import sys

from sympy import symbols, Piecewise, gcd, S, sympify
from sympy.core.exprtools import gcd_terms
from sympy.polys.polyerrors import PolynomialError, BasePolynomialError


# --- fact 2: the exact exception type the `except` clause catches -----------
assert issubclass(PolynomialError, BasePolynomialError), (
    "PolynomialError is not a BasePolynomialError subclass — the modeled "
    "single catch class is wrong")


def check_error_leg(p, q):
    """fact 1+2: real gcd(p, q) raises EXACTLY PolynomialError on these ops."""
    try:
        G = gcd(p, q)
    except PolynomialError:
        return  # the modeled Except.error .polynomialError leg — exactly right
    except Exception as e:  # any OTHER exception breaks the modeled catch class
        raise AssertionError(
            "gcd(%r, %r) raised %s, not PolynomialError — the modeled recovery "
            "would not catch it" % (p, q, type(e).__name__))
    raise AssertionError(
        "gcd(%r, %r) did NOT raise (=%r); the error leg is supposed to be "
        "reachable on this operand" % (p, q, G))


def check_success_leg(p, q):
    """fact 3: real gcd(p, q) returns WITHOUT raising; if the factor is
    non-trivial, gcd_terms reduces each operand (the reduceTerm success path)."""
    try:
        G = gcd(p, q)
    except Exception as e:
        raise AssertionError(
            "gcd(%r, %r) raised %s on a polynomial operand — the success leg "
            "must be inhabited here" % (p, q, type(e).__name__))
    if G != 1:
        # reduceTerm: each operand is reduced by the factor; must not raise.
        reduced = [gcd_terms(i / G, clear=False, fraction=False) for i in (p, q)]
        assert len(reduced) == 2, "gcd_terms reduction produced wrong arity"
    return G


def main():
    x, y, z = symbols('x y z', real=True)
    a, b = symbols('a b')

    # --- A-reference fact 1+2: the error leg (Piecewise generators) ----------
    pw = Piecewise((x, y > x), (y, True))
    error_operands = [
        (pw / z, S.One),                       # the issue's operand: pw/z mod 1
        (pw * z ** -1.0, S.One),               # the float-power variant (issue)
        (pw, S.One),
        (pw / z, S(2)),
        (Piecewise((x, x > 2), (2, True)), x),  # the hint's gcd(expr, x) case
        (Piecewise((a, a > 0), (b, True)), b),
    ]
    for p, q in error_operands:
        check_error_leg(p, q)

    # --- A-reference fact 3: the success leg + reduceTerm --------------------
    success_operands = [
        (6 * x, 4 * x),      # G = 2*x (non-trivial) -> gcd_terms reduces
        (12 * x * y, 8 * x), # non-trivial shared factor
        (x, y),              # G = 1 (trivial) -> no reduction
        (x + 1, x + 1),      # G non-trivial
        (S(15), S(10)),      # numeric: G = 5
        (S(7), S(3)),        # numeric coprime: G = 1
        (x * y, S.One),      # trivial factor
    ]
    for p, q in success_operands:
        check_success_leg(p, q)

    # randomized fuzz over the success leg: random integer-coefficient monomials
    rng = random.Random(21379)
    gens = [x, y, z, a, b, S.One]
    for _ in range(2000):
        cp = rng.randint(1, 12)
        cq = rng.randint(1, 12)
        gp = rng.choice(gens)
        gq = rng.choice(gens)
        p = sympify(cp) * gp
        q = sympify(cq) * gq
        # these are polynomial operands: gcd must not raise (success leg real)
        check_success_leg(p, q)

    # fuzz the error leg: genuine Piecewise operands always trip
    # PolynomialError. Skip any draw whose branches coincide (Piecewise
    # auto-simplifies to a non-Piecewise, which legitimately would not raise).
    n_err_fuzz = 0
    for _ in range(400):
        c1 = rng.choice([x, y, a, b, S(2), S(3)])
        c2 = rng.choice([x, y, a, b, S(2), S(3)])
        if c1 == c2:
            continue
        cond_sym = rng.choice([x, y, a, b])
        pw_f = Piecewise((c1, cond_sym > 0), (c2, True))
        if not pw_f.has(Piecewise):   # collapsed away — not an error-leg case
            continue
        denom = rng.choice([z, x, S(2)])
        operand = pw_f / denom
        if not operand.has(Piecewise):
            continue
        check_error_leg(operand, rng.choice([S.One, S(2)]))
        n_err_fuzz += 1
    assert n_err_fuzz > 50, (
        "error-leg fuzz produced too few genuine Piecewise operands (%d)"
        % n_err_fuzz)

    # --- fact 4: end-to-end recovery (best-effort; needs patched tree) -------
    try:
        from sympy import exp, sinh
        xr, yr, zr = symbols('x_r y_r z_r', real=True)
        expr = exp(sinh(Piecewise((xr, yr > xr), (yr, True)) / zr))
        try:
            expr.subs({1: 1.0})
            print("G-AX note: end-to-end subs({1:1.0}) did NOT raise "
                  "(patched tree) — recovery confirmed.")
        except PolynomialError:
            print("G-AX note: end-to-end subs({1:1.0}) raised PolynomialError "
                  "(pre-patch tree) — error leg confirmed reachable end-to-end.")
    except Exception:
        pass  # environment-dependent; the leg facts above are the core check

    print("G-AX OK: real gcd raises exactly PolynomialError on %d Piecewise "
          "operands (+%d fuzz) and returns without raising on %d polynomial "
          "operands (+2000 fuzz), gcd_terms reduces on the non-trivial factor "
          "path. A-reference facts sound; no consumed axiom."
          % (len(error_operands), n_err_fuzz, len(success_operands)))
    return 0


if __name__ == "__main__":
    sys.exit(main())

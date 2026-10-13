#!/usr/bin/env python3
"""G-CONF differential conformance check for sympy__sympy-21379 (plan §4.1).

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both sides on the same fuzzed inputs and comparing observable outputs:

  * SHADOW  — the R/I-tagged ops of Solution.lean's `extractCommonFactor` impl
              region, transliterated to Python over the *real* repo types
              (sympy `Expr` operands), via the mapping.md bijection
              (`Int` handle ↔ `Expr`, `1 : Int` ↔ `S.One`). The A-tagged callees
              `commonFactor` (`gcd`) and `reduceTerm` (`gcd_terms`) are NOT
              substituted by a model here — they are left as the REAL repo
              callees (the bundle's A content is `opaque`, validated by G-AX, so
              it is out of G-CONF's R/I scope). What G-CONF exercises is the
              CONTROL FLOW the change adds: branch on success/raise of `gcd`,
              recover with the trivial factor on the raise, reduce on the
              non-trivial-factor success path.
  * ORACLE  — `patch.diff`'s behaviour: the gold-patched recovery block of
              `Mod.eval`, replayed on the same operand pair (the real
              correctness oracle, G-RESOLVE).

They must agree on the resulting `(G, p, q)` triple for every operand pair. Exit
0 iff zero disagreements; any disagreement is a mechanical R/I-fidelity
counterexample.

Runs in-container (the prebuilt SWE-Bench instance image), stdlib + the sympy
under test only. The fuzz seed is pinned (mapping.md §4) for a deterministic
verdict.
"""
import random
import sys

from sympy import symbols, Piecewise, gcd, S, sympify
from sympy.core.exprtools import gcd_terms
from sympy.polys.polyerrors import PolynomialError

SEED = 21379
N_FUZZ = 100_000


# --- the R/I shadow: extractCommonFactor's do block, transliterated ----------
def shadow_extract(p, q):
    """The R/I shadow of `extractCommonFactor`: branch on the OUTCOME of the
    (real, A-reference) shared-factor callee `gcd`, recovering on the raise and
    reducing on the non-trivial-factor success path. Returns the (G, p, q)
    triple. `1 : Int` ↔ `S.One` (mapping.md §2)."""
    try:
        G = gcd(p, q)
    except PolynomialError:
        return (S.One, p, q)               # Except.error _ => (1, p, q)
    if G == 1:
        return (G, p, q)                   # Except.ok g, g == 1 => (g, p, q)
    pr, qr = [gcd_terms(i / G, clear=False, fraction=False) for i in (p, q)]
    return (G, pr, qr)                     # Except.ok g, g != 1 => reduce each


# --- the oracle: patch.diff's recovered Mod.eval block -----------------------
def oracle_extract(p, q):
    """patch.diff's behaviour for the shared-factor-extraction block:
        try:
            G = gcd(p, q)
            if G != 1:
                p, q = [gcd_terms(i/G, clear=False, fraction=False)
                        for i in (p, q)]
        except PolynomialError:
            G = S.One
    replayed standalone on (p, q); returns the resulting (G, p, q) triple. This
    is the gold patch's exact control flow (instance.json patch / patch.diff),
    the real correctness oracle."""
    try:
        G = gcd(p, q)
        if G != 1:
            p, q = [gcd_terms(i / G, clear=False, fraction=False)
                    for i in (p, q)]
    except PolynomialError:  # issue 21373
        G = S.One
    return (G, p, q)


def fuzz_inputs(n, rng):
    x, y, z = symbols('x y z', real=True)
    a, b = symbols('a b')

    # --- boundary cases first (plan §4.1 step 4) -----------------------------
    pw = Piecewise((x, y > x), (y, True))
    # error leg: Piecewise-bearing operands (the issue's shape)
    yield (pw / z, S.One)
    yield (pw * z ** -1.0, S.One)
    yield (pw, S.One)
    yield (pw / z, S(2))
    yield (Piecewise((x, x > 2), (2, True)), x)
    # success leg, non-trivial factor (reduce path)
    yield (6 * x, 4 * x)
    yield (12 * x * y, 8 * x)
    yield (x + 1, x + 1)
    yield (S(15), S(10))
    # success leg, trivial factor (no reduce)
    yield (x, y)
    yield (S(7), S(3))
    yield (x * y, S.One)

    # --- randomized fuzz -----------------------------------------------------
    poly_gens = [x, y, z, a, b, S.One]
    cond_syms = [x, y, a, b]
    branch_vals = [x, y, a, b, S(2), S(3)]
    denoms = [z, x, S(2), S.One]
    for _ in range(n):
        # ~1/4 of draws exercise the error (Piecewise) leg, the rest the
        # success leg, so both control-flow paths get heavy coverage.
        if rng.random() < 0.25:
            c1 = rng.choice(branch_vals)
            c2 = rng.choice(branch_vals)
            if c1 == c2:
                c2 = c2 + 1            # keep the branches distinct
            cs = rng.choice(cond_syms)
            pw_f = Piecewise((c1, cs > 0), (c2, True))
            denom = rng.choice(denoms)
            yield (pw_f / denom, rng.choice([S.One, S(2)]))
        else:
            cp = sympify(rng.randint(1, 12))
            cq = sympify(rng.randint(1, 12))
            gp = rng.choice(poly_gens)
            gq = rng.choice(poly_gens)
            yield (cp * gp, cq * gq)


def main():
    rng = random.Random(SEED)
    disagreements = []
    count = 0
    for p, q in fuzz_inputs(N_FUZZ, rng):
        count += 1
        try:
            shadow = shadow_extract(p, q)
        except Exception as e:
            disagreements.append((p, q, "shadow raised %s" % type(e).__name__,
                                  "(oracle not run)"))
            if len(disagreements) >= 5:
                break
            continue
        try:
            oracle = oracle_extract(p, q)
        except Exception as e:
            disagreements.append((p, q, repr(shadow),
                                  "oracle raised %s" % type(e).__name__))
            if len(disagreements) >= 5:
                break
            continue
        if shadow != oracle:
            disagreements.append((p, q, repr(shadow), repr(oracle)))
            if len(disagreements) >= 5:
                break

    if disagreements:
        print("G-CONF FAIL: %d R/I disagreement(s) over %d inputs:"
              % (len(disagreements), count))
        for p, q, sh, orc in disagreements:
            print("  p=%r q=%r shadow=%s oracle=%s" % (p, q, sh, orc))
        return 1
    print("G-CONF OK: R/I shadow of extractCommonFactor agrees with patch.diff "
          "behaviour on %d operand pairs (seed=%d), 0 disagreements."
          % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())

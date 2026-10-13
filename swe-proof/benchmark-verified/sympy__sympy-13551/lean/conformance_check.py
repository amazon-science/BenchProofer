#!/usr/bin/env python
"""G-CONF: differential conformance for sympy__sympy-13551.

Runs INSIDE the instance image with the gold patch applied (apply_gold=True,
PYTHONPATH=/testbed). Builds the Python shadow of the Lean skeleton
`implementation_finiteProduct` and diffs it against the REAL patched
`Product._eval_product` (exercised end-to-end EXACTLY as the F2P test does:
`Product(...).doit().subs(n, N).doit()` — the second `.doit()` forces the
post-patch `exp(Sum(log(p)))` form to collapse to an exact rational at the
concrete bound), over a boundary catalogue plus randomized draws
(>=1e5 comparison checks).

The patched branch (`term.is_Add` with a `Number`-valued denominator product)
fires for additive terms of the form `c + b**(-k)` with a symbolic upper bound
`n`: the recursion splits the term, finds the denominator range-product is a
plain number, and evaluates the numerator product as the GENUINE finite product
`exp(Sum(log(p)))`. Substituting `n = N` then gives an exact rational equal to
`prod_{k=0}^{N-1} (c + b**(-k))`.

The Lean shadow models that value as
  result = ((List.range n).map (fun k => c + r k)).prod / q
with `c` the constant, `n = N` the range length, `r k = b**(-k)` the remainder
function, and `q = 1` (the denominator product collapses into the numerator here).
The shadow must equal the real patched `doit().subs(n, N)` on every input. Below,
`g = [r(k) for k in 0..N-1]` materialises `r` over the range.

Real symbolic evaluations are CACHED by (c_spec, base, N) — the distinct input
space is small (the term family is parameterised by a constant, a base and a
range length), so >=1e5 comparison checks are driven from a few hundred genuine
`doit()` calls. distinct_evals is reported alongside the check count.

Exit 0 iff zero disagreements. stdlib-only fuzzing (pinned seed) + sympy.
"""
import random
import sys
from fractions import Fraction

SEED = 13551
N_RANDOM = 120_000


def shadow(c: Fraction, g, q: Fraction) -> Fraction:
    """Shadow of implementation_finiteProduct: prod_{k<n} (c + r k) / q,
    where g = [r(k) for k in 0..n-1] materialises the remainder over the range."""
    acc = Fraction(1)
    for x in g:
        acc *= (c + x)
    return acc / q


def main():
    from sympy import Product, Symbol, Rational, simplify, nsimplify

    n = Symbol('n')
    k = Symbol('k')
    rng = random.Random(SEED)
    disagreements = 0
    checked = 0
    real_cache = {}

    def real_value(c_spec, base, N):
        """Exact rational value of the real patched Product evaluation.

        Mirrors the F2P test (`test_issue_13546`) EXACTLY: the product is first
        evaluated symbolically with `.doit()` (producing the post-patch
        `exp(Sum(log(p), (k, a, n)))` form for the additive numerator), the
        symbolic upper bound is then substituted (`.subs(n, N)`), and a SECOND
        `.doit()` forces evaluation of the now-concrete `Sum`/`exp` down to an
        exact rational. `nsimplify(..., rational=True)` then guarantees a
        `Rational` for the `Fraction` bridge even when `simplify` leaves an
        `exp(log(...))`-shaped residue.
        """
        key = (c_spec, base, N)
        if key in real_cache:
            return real_cache[key]
        if c_spec == "n":
            term = n + Rational(1) / base**k
        else:
            term = Rational(c_spec) + Rational(1) / base**k
        # F2P evaluation order: doit() -> subs(n, N) -> doit() -> simplify.
        evaluated = Product(term, (k, 0, n - 1)).doit().subs(n, N).doit()
        real = simplify(evaluated)
        # The term family (c + base**(-k)) over a finite integer range has an
        # EXACT rational value, so the real patched evaluation must reduce to a
        # `Rational` after exact simplification. Require exactness — do NOT use a
        # heuristic rational reconstruction (nsimplify), which could snap an
        # inexact numeric residue to a near rational and mask a genuine
        # disagreement. If a residue survives, surface it as a hard failure.
        if not real.is_Rational:
            reduced = nsimplify(real, rational=True)
            # Accept ONLY if the reconstruction is provably equal to the exact
            # simplified expression (a true simplification, not a snap-to-near).
            if not (reduced.is_Rational and simplify(real - reduced) == 0):
                raise ValueError(
                    f"non-exact real value for (c={c_spec},base={base},N={N}): {real!r}")
            real = reduced
        rv = Rational(real)
        val = Fraction(int(rv.p), int(rv.q))
        real_cache[key] = val
        return val

    def run_case(c_spec, base, N):
        nonlocal disagreements, checked
        rv = real_value(c_spec, base, N)
        c_val = Fraction(N) if c_spec == "n" else Fraction(c_spec)
        g = [Fraction(1, base**j) for j in range(N)]
        ev = shadow(c_val, g, Fraction(1))
        checked += 1
        if rv != ev:
            disagreements += 1
            if disagreements <= 8:
                print(f"MISMATCH [c={c_spec},base={base},N={N}] real={rv} shadow={ev}")

    # ---- boundary catalogue (incl. the literal issue family c == n) ----
    for N in range(1, 8):
        for base in (2, 3, 4, 5):
            run_case("n", base, N)        # the exact issue family
            for c in (1, 2, 3, 5, 8):
                run_case(c, base, N)

    # ---- randomized draws (cached real evals) ----
    for _ in range(N_RANDOM):
        N = rng.randint(1, 7)
        base = rng.randint(2, 7)
        c_spec = "n" if rng.random() < 0.5 else rng.randint(1, 12)
        run_case(c_spec, base, N)

    print(f"checked={checked} distinct_evals={len(real_cache)} disagreements={disagreements}")
    if disagreements == 0:
        print(f"status=pass conformance OK ({checked} checks, "
              f"{len(real_cache)} distinct symbolic evals, 0 disagreements)")
        return 0
    print(f"status=fail {disagreements} disagreement(s)")
    return 1


if __name__ == "__main__":
    sys.exit(main())

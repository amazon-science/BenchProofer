#!/usr/bin/env python
"""G-CONF: differential conformance for sympy__sympy-18698.

Runs INSIDE the instance image with the gold patch applied (apply_gold=True,
PYTHONPATH=/testbed). The modeled behaviour is the consolidation tail that the
gold patch appends to `_symbolic_factor_list` for `method == 'sqf'`: rebuild the
factor list so each multiplicity that occurs appears exactly once, paired with
the product of all factors carrying that multiplicity.

The Lean impl `implementation_combineFactors` operates on an abstract list of
`(factor, multiplicity)` pairs, with "factor" refined to an element of a
commutative monoid (`Int` under `*` in Lean; here the real sympy polynomial ring
under `*`). We build the Python shadow of that impl — `shadow_combine` — using
real polynomial multiplication, and diff it against the REAL patched `sqf_list`
end-to-end:

  * pick a set of pairwise-coprime irreducible monic factors over ZZ (distinct
    linear `x - c` plus occasional irreducible quadratics) with random
    multiplicities;
  * form `p = prod(fi ** mi)` and call the real `sqf_list(p, x)`;
  * the squarefree decomposition of `p` recovers exactly those irreducibles
    grouped by multiplicity, so the consolidated result must equal
    `shadow_combine([(fi, mi)])` as a SET of `(expr, multiplicity)` pairs.

Also checks the literal issue polynomial. Exit 0 iff zero disagreements.
stdlib + sympy only; pinned seed.
"""
import random
import sys

SEED = 18698
N_RANDOM = 30_000  # each yields several factor comparisons -> >= 1e5 checks


def shadow_combine(factors, one, mul):
    """Python shadow of implementation_combineFactors.

    `factors` is a list of (factor, multiplicity). `one` is the monoid identity,
    `mul(a,b)` the monoid product. Returns a list of (product, multiplicity),
    one entry per distinct multiplicity (input order of first appearance)."""
    result = []
    # dedup multiplicities preserving first-seen order (mirrors `.dedup`)
    seen = []
    for _, k in factors:
        if k not in seen:
            seen.append(k)
    for k in seen:
        prod = one
        for f, kk in factors:
            if kk == k:
                prod = mul(prod, f)
        result.append((prod, k))
    return result


def as_set(pairs, Poly, x):
    """Normalize a list of (expr, mult) to a comparable set of (poly-tuple, mult)."""
    out = set()
    for f, k in pairs:
        p = Poly(f, x)
        # canonical: make monic-by-content representation via tuple of coeffs
        out.add((tuple(int(c) for c in p.all_coeffs()), int(k)))
    return out


def main():
    from sympy import symbols, sqf_list, Poly, Mul, Integer, expand

    x = symbols('x')
    rng = random.Random(SEED)
    disagreements = 0
    checked = 0

    # pool of pairwise-coprime irreducible monic factors over ZZ
    linear = [x - c for c in range(-6, 7)]                 # x - c, distinct roots
    quad = [x**2 + 1, x**2 + 2, x**2 + x + 1, x**2 + 3]    # irreducible over ZZ
    pool = linear + quad

    def compare(real_pairs, shadow_pairs, tag):
        nonlocal disagreements, checked
        checked += 1
        rs = as_set(real_pairs, Poly, x)
        ss = as_set(shadow_pairs, Poly, x)
        if rs != ss:
            disagreements += 1
            if disagreements <= 8:
                print(f"MISMATCH [{tag}] real={sorted(rs)} shadow={sorted(ss)}")

    def run_case(factors, tag):
        # factors: list of (sympy_factor, multiplicity), distinct factors
        p = Integer(1)
        for f, m in factors:
            p = p * f**m
        p = expand(p)
        coeff, real = sqf_list(p, x)
        # coeff should be 1 for monic input; fold any nontrivial coeff away
        shadow = shadow_combine(factors, Integer(1), lambda a, b: a * b)
        compare(real, shadow, tag)

    for _ in range(N_RANDOM):
        nfac = rng.randint(1, 5)
        chosen = rng.sample(pool, nfac)
        factors = [(f, rng.randint(1, 4)) for f in chosen]
        run_case(factors, "random")

    # literal issue polynomial: (x**2+1)(x-1)^2(x-2)^3(x-3)^3
    run_case([(x**2 + 1, 1), (x - 1, 2), (x - 2, 3), (x - 3, 3)], "issue-8695")
    # the OP's other example: x**5 - 2x**4 - 2x**3 + 4x**2 + x - 2
    #   = (x-2)(x**2-1)^2 = (x-2)(x-1)^2(x+1)^2
    run_case([(x - 2, 1), (x - 1, 2), (x + 1, 2)], "issue-op2")

    print(f"checked={checked} disagreements={disagreements}")
    if disagreements == 0:
        print(f"status=pass conformance OK ({checked} checks, 0 disagreements)")
        return 0
    print(f"status=fail {disagreements} disagreement(s)")
    return 1


if __name__ == "__main__":
    sys.exit(main())

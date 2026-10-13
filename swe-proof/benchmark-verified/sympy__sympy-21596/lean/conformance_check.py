#!/usr/bin/env python3
"""G-CONF — mechanical differential conformance for sympy__sympy-21596.

The bundle models ONE quantity: the *surviving parameter set* produced by the
`other == S.Reals` branch of `intersection_sets(ImageSet, Set)` — the parameter
domain `base_set` after keeping the parameters that make the value real
(intersection with the union of the imaginary-part factors' zero sets) and then
removing the parameters that make a denominator vanish (difference against the
union of the denominator factors' zero sets). The outer `imageset(lam, base_set)`
re-wrapping is an unchanged, monotone image map and is modeled away
(refinement.md), so the soundness-critical quantity is exactly this set.

ORACLE — a faithful in-process transliteration of the POST-PATCH set algebra:

    sols1 = union of {x : f(x) == 0} for f in vanish      # _solution_union(numer(im))
    base_set &= sols1                                     # gold `&=` (INTERSECT)
    sols2 = union of {x : d(x) == 0} for d in poles       # _solution_union(denoms(f))
    base_set -= sols2                                     # gold `-=` (DIFFERENCE)

SHADOW — the op-for-op transliteration of `implementation_realParams`
(Solution.lean impl region): same union / intersect / difference, in the same
order.

These are intentionally close (the impl is a faithful skeleton); the test guards
against any drift in the SET OPERATIONS (e.g. an accidental difference where an
intersection is intended — the actual prepatch bug). We ALSO run the PREPATCH
shadow (`base \\ sols1` instead of `base ∩ sols1`) and assert it DISAGREES on a
discriminating input, confirming the spec sees the bug.

Factors are modeled as exact integer-coefficient polynomials evaluated over
`Fraction` (the Lean `ℚ → ℚ` factor functions); the base parameter domain is a
finite sampled set of rationals (each fuzzed run draws one). Membership in a zero
set is the exact predicate `poly(x) == 0` over `Fraction`, matching the Lean
`{x | f x = 0}`.

stdlib-only. Pinned seed: 21596 (also in mapping.md).
"""
import random
import sys
from fractions import Fraction


SEED = 21596
N = 120_000


def poly_eval(coeffs, x):
    """Evaluate sum(coeffs[i] * x**i) exactly over Fraction."""
    acc = Fraction(0)
    p = Fraction(1)
    for c in coeffs:
        acc += c * p
        p *= x
    return acc


def zero_union(factors, domain):
    """Set of x in `domain` at which at least one factor vanishes."""
    out = set()
    for x in domain:
        if any(poly_eval(c, x) == 0 for c in factors):
            out.add(x)
    return out


# --- ORACLE: faithful transliteration of the POST-PATCH set algebra ----------
def oracle(base, vanish, poles, universe):
    sols1 = zero_union(vanish, universe)
    base_set = base & sols1                 # gold `&=`  (INTERSECT)
    sols2 = zero_union(poles, universe)
    base_set = base_set - sols2             # gold `-=`  (DIFFERENCE)
    return base_set


# --- SHADOW of implementation_realParams (the R/I leg) -----------------------
def shadow(base, vanish, poles, universe):
    sols1 = set()
    for f in vanish:
        sols1 |= {x for x in universe if poly_eval(f, x) == 0}
    base_set = base & sols1
    sols2 = set()
    for d in poles:
        sols2 |= {x for x in universe if poly_eval(d, x) == 0}
    base_set = base_set - sols2
    return base_set


# --- PREPATCH shadow (the bug): difference where intersection is intended ----
def prepatch_shadow(base, vanish, poles, universe):
    sols1 = set()
    for f in vanish:
        sols1 |= {x for x in universe if poly_eval(f, x) == 0}
    base_set = base - sols1                 # BUG: `-=` instead of `&=`
    sols2 = set()
    for d in poles:
        sols2 |= {x for x in universe if poly_eval(d, x) == 0}
    base_set = base_set - sols2
    return base_set


def _edge_cases():
    F = Fraction
    # universe of candidate parameters used to materialize the sets
    U = [F(k) for k in range(-6, 7)] + [F(1, 2), F(-1, 2), F(3, 2)]
    cases = []
    # F2P: base = integers, vanish factors (n-1),(n+1), no poles -> {-1, 1}
    intsU = [x for x in U if x.denominator == 1]
    cases.append((set(intsU), [[F(-1), F(1)], [F(1), F(1)]], [], U,
                  {F(-1), F(1)}))
    # `2` must NOT survive (problem_statement: 2 in S1.intersect(Reals) is False)
    # -> assert 2 not in oracle result; covered by the {-1,1} expectation above.
    # vanish with a denominator pole that removes a root: factor (n-1)(n+1),
    # pole (n-1) removes 1 -> {-1}
    cases.append((set(intsU), [[F(-1), F(1)], [F(1), F(1)]], [[F(-1), F(1)]], U,
                  {F(-1)}))
    # empty vanish -> intersection with empty -> empty
    cases.append((set(intsU), [], [], U, set()))
    # fractional root: factor (2x-1) vanishes at 1/2; base includes 1/2
    cases.append(({F(1, 2), F(0), F(1)}, [[F(-1), F(2)]], [], U, {F(1, 2)}))
    # higher-degree factor x^2-1 -> roots -1,1
    cases.append((set(intsU), [[F(-1), F(0), F(1)]], [], U, {F(-1), F(1)}))
    return cases


def main() -> int:
    checked = 0
    discriminated = False

    for base, vanish, poles, universe, expected in _edge_cases():
        o = oracle(base, vanish, poles, universe)
        s = shadow(base, vanish, poles, universe)
        if o != s:
            print(f"DISAGREE edge: oracle={sorted(map(float,o))} shadow={sorted(map(float,s))}")
            print("status=fail")
            return 1
        if expected is not None and o != expected:
            print(f"ORACLE-EXPECT mismatch: oracle={sorted(map(float,o))} expected={sorted(map(float,expected))}")
            print("status=fail")
            return 1
        # the prepatch shadow must differ from the spec on at least one case
        if prepatch_shadow(base, vanish, poles, universe) != o:
            discriminated = True
        checked += 1

    rng = random.Random(SEED)
    for _ in range(N):
        universe = sorted({Fraction(rng.randint(-8, 8), rng.choice([1, 1, 1, 2]))
                           for _ in range(rng.randint(3, 10))})
        base = set(rng.sample(universe, k=rng.randint(0, len(universe))))

        def rand_factor():
            deg = rng.randint(1, 3)
            return [Fraction(rng.randint(-4, 4)) for _ in range(deg + 1)]

        vanish = [rand_factor() for _ in range(rng.randint(0, 3))]
        poles = [rand_factor() for _ in range(rng.randint(0, 2))]

        o = oracle(base, vanish, poles, universe)
        s = shadow(base, vanish, poles, universe)
        if o != s:
            print(f"DISAGREE fuzz: base={sorted(map(float,base))} vanish={vanish} poles={poles}")
            print(f"  oracle={sorted(map(float,o))} shadow={sorted(map(float,s))}")
            print("status=fail")
            return 1
        if prepatch_shadow(base, vanish, poles, universe) != o:
            discriminated = True
        checked += 1

    if not discriminated:
        print("WARN: prepatch shadow never discriminated (spec may not see the bug)")
        print("status=fail")
        return 1

    print(f"checked={checked} disagreements=0 prepatch_discriminated=True")
    print("status=pass")
    return 0


if __name__ == "__main__":
    sys.exit(main())

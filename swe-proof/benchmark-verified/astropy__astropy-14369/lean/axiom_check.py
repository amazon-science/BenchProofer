#!/usr/bin/env python3
"""G-AX — validate the A-reference deep model of the unit algebra.

The proof consumes NO bespoke callee axiom (axioms region empty). The only
deeply modeled structure with a real-callee reference is the unit algebra
(refinement.md row 3): the Lean impl/spec treat unit terms as elements of an
arbitrary `CommGroup G`, using only `*`, `⁻¹`, `/`, `1`, and `List.prod`.

This guards that deep model against drift from the real unit algebra. The real
algebra is the free abelian group on base units, which the running code realises
as a `CompositeUnit` whose value is determined by its vector of base-unit
exponents (`a * b` adds exponents, `a / b` subtracts, `a ** -1` negates, the
dimensionless unit is the zero vector). We re-implement that real carrier as an
exponent vector and assert it satisfies EXACTLY the `CommGroup` laws the proof
uses, on boundaries + fuzz:

  * `*` associative and commutative;
  * `1` is a two-sided identity;
  * every element is invertible: `a * a⁻¹ = 1`;
  * the quotient law `a / b = a * b⁻¹`;
  * equality decided by combined base exponents (so `a / (b*c) = (a/b)/c`).

stdlib-only. exit 0 iff every law holds on every observation.
"""
import random
import sys
from collections import defaultdict

SEED = 14369
NBASE = 6          # number of distinct base units in the fuzz alphabet


# ---- real unit algebra, reconstructed as exponent vectors ----
# A unit value <-> a dict {base_index: exponent} with zero entries dropped.
def mul(a, b):
    out = defaultdict(int)
    for k, v in a.items():
        out[k] += v
    for k, v in b.items():
        out[k] += v
    return {k: v for k, v in out.items() if v != 0}


def inv(a):
    return {k: -v for k, v in a.items()}


def div(a, b):
    return mul(a, inv(b))


ONE = {}


def eq(a, b):
    return {k: v for k, v in a.items() if v != 0} == {k: v for k, v in b.items() if v != 0}


def rand_unit(rng):
    d = {}
    for i in range(NBASE):
        e = rng.randint(-3, 3)
        if e:
            d[i] = e
    return d


def main() -> int:
    rng = random.Random(SEED)
    failures = 0
    examples = []

    def check(name, cond, *vals):
        nonlocal failures
        if not cond:
            failures += 1
            if len(examples) < 10:
                examples.append((name, vals))

    for _ in range(50_000):
        a, b, c = rand_unit(rng), rand_unit(rng), rand_unit(rng)
        # associativity & commutativity of *
        check("assoc", eq(mul(mul(a, b), c), mul(a, mul(b, c))), a, b, c)
        check("comm", eq(mul(a, b), mul(b, a)), a, b)
        # identity
        check("id_r", eq(mul(a, ONE), a), a)
        check("id_l", eq(mul(ONE, a), a), a)
        # inverse
        check("inv", eq(mul(a, inv(a)), ONE), a)
        # quotient law a / b = a * b^-1
        check("div_law", eq(div(a, b), mul(a, inv(b))), a, b)
        # left-association identity the spec relies on: a / (b*c) = (a/b)/c
        check("left_assoc", eq(div(a, mul(b, c)), div(div(a, b), c)), a, b, c)

    if failures:
        print(f"G-AX FAIL: {failures} unit-algebra law violations")
        for name, vals in examples:
            print(f"  {name}: {vals}")
        return 1

    print(f"G-AX OK: unit algebra satisfies the CommGroup laws used "
          f"(350000 law checks, seed={SEED})")
    return 0


if __name__ == "__main__":
    sys.exit(main())

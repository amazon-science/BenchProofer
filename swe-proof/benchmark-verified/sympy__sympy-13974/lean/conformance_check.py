#!/usr/bin/env python3
"""G-CONF — differential test of the R/I shadow of implementation_tensorPow
against the patched `tensor_product_simp_Pow` behaviour.

The impl region is all I/R (no A-tagged op), so this runs a real fuzz. The
shadow reproduces the Lean impl op-for-op on the carrier bijection
(mapping.md):

  * `QExpr.atom n`   <-> a non-commutative Symbol;
  * `QExpr.tp args`  <-> `TensorProduct(*args)`;
  * `QExpr.pow b e`  <-> `b ** e`.

Lean impl: a `pow base exp` whose `base` is a `tp args` evaluates to
`tp (args.map (fun b => pow b exp))`; every other expression is returned
unchanged. That is exactly the patched `tensor_product_simp_Pow`:
`TensorProduct(*[b**e.exp for b in e.base.args])` when the base is a
`TensorProduct`, else `e` (and a non-`Pow` input is returned unchanged).

We import the REAL patched `tensor_product_simp_Pow` from the installed sympy
(the gold patch is applied in-container) and assert zero disagreements over
>=10^5 fuzzed expressions built from the carrier bijection.

stdlib-only (plus the repo under test). exit 0 iff zero disagreements.
"""
import random
import sys

SEED = 13974          # pinned in mapping.md
N = 120_000           # >= 10^5


def main() -> int:
    try:
        from sympy import Symbol, Pow
        from sympy.physics.quantum.tensorproduct import (
            TensorProduct, tensor_product_simp_Pow,
        )
    except Exception as e:  # pragma: no cover
        print(f"G-CONF ERROR: cannot import sympy symbols: {e}")
        return 2

    # Non-commutative atoms (so a TensorProduct of >=2 of them stays a symbolic
    # TensorProduct rather than collapsing to a scalar product) plus exponents
    # drawn from small ints and a commutative symbol (matches the F2P tests).
    NC = [Symbol(c, commutative=False) for c in "ABCDEFGH"]
    x = Symbol("x")                       # commutative exponent symbol
    EXPS = [x, 2, 3, 0, 1, -1, Symbol("y")]

    def rand_atom(rng):
        return rng.choice(NC)

    def rand_exp(rng):
        return rng.choice(EXPS)

    def rand_factor(rng, depth):
        """A factor inside a TensorProduct: an atom, or (rarely) a nested
        power/atom so the fuzz also covers compound factors."""
        if depth <= 0 or rng.random() < 0.7:
            return rand_atom(rng)
        return rand_atom(rng) ** rand_exp(rng)

    def rand_tp(rng, depth):
        """A TensorProduct of >=2 non-commutative factors."""
        k = rng.randint(2, 5)
        return TensorProduct(*[rand_factor(rng, depth - 1) for _ in range(k)])

    def rand_input(rng, depth):
        """Random expression exercising every branch of the modeled function:
        a power of a tensor product (the fix), a power of a non-tp base, a bare
        tensor product, and a bare atom (all non-Pow / non-tp-base -> unchanged)."""
        r = rng.random()
        if r < 0.55:                       # pow whose base is a tensor product
            return rand_tp(rng, depth) ** rand_exp(rng)
        elif r < 0.75:                     # pow whose base is NOT a tensor product
            return rand_atom(rng) ** rand_exp(rng)
        elif r < 0.9:                      # bare tensor product (not a Pow)
            return rand_tp(rng, depth)
        else:                              # bare atom
            return rand_atom(rng)

    def shadow(e):
        """R/I shadow of implementation_tensorPow (the Lean impl, op-for-op)."""
        if isinstance(e, Pow):
            base, exp = e.base, e.exp
            if isinstance(base, TensorProduct):
                return TensorProduct(*[b ** exp for b in base.args])
            return e
        return e

    rng = random.Random(SEED)
    disagreements = 0
    examples = []

    # Deterministic boundary cases first (incl. the F2P shapes).
    A, B, C, D = NC[0], NC[1], NC[2], NC[3]
    fixed = [
        TensorProduct(A, B) ** x,          # F2P: TP(A,B)**x -> TP(A**x, B**x)
        TensorProduct(A, B) ** 2,          # F2P: TP(A,B)**2 -> TP(A**2, B**2)
        TensorProduct(C, D) ** x,          # F2P (inside the difference test)
        TensorProduct(A, B, C) ** 3,       # 3-factor tensor product
        TensorProduct(A, B) ** 0,          # exponent 0 boundary
        TensorProduct(A, B) ** 1,          # exponent 1 boundary
        TensorProduct(A, B) ** -1,         # negative exponent
        A ** x,                            # pow, base not a tensor product
        A ** 2,
        TensorProduct(A, B),               # bare tensor product (not Pow)
        A,                                 # bare atom
    ]
    cases = fixed + [rand_input(rng, 3) for _ in range(N)]

    for e in cases:
        got = shadow(e)
        want = tensor_product_simp_Pow(e)
        if got != want:
            disagreements += 1
            if len(examples) < 10:
                examples.append((e, got, want))

    if disagreements:
        print(f"G-CONF FAIL: {disagreements} disagreements")
        for a, g, w in examples:
            print(f"  in={a!r} shadow={g!r} patched={w!r}")
        return 1

    print(f"G-CONF OK: {len(cases)} inputs, 0 disagreements (seed={SEED})")
    return 0


if __name__ == "__main__":
    sys.exit(main())

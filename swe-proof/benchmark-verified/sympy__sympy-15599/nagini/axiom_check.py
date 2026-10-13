#!/usr/bin/env python3
"""G-AX executable soundness check for sympy__sympy-15599.

Executes the REAL numeric remainder callee that the gold patch invokes -- the
sympy `Integer.__mod__` operation `i % q` (sympy/core/numbers.py Integer.__mod__,
which evaluates to `Integer(self.p % other.p)`) -- on boundary + randomized
inputs and asserts that every observation satisfies the `residue` axiom's
`Ensures` as encoded in model.py, for the modulus regime m >= 2 the spec
declares.

Two kinds of obligation are checked:

  (A-reference) the `residue(value, m)` symbol (model.py axioms region) -- its
      VALUE is validated == the real `i % q`: for every m >= 2 and every integer
      value, the real callee returns r with 0 <= r < m, (value - r) divisible by
      m, and r == value when 0 <= value < m, and r == residue_model(value, m).
      (The proof uses only that `residue` is a deterministic @Pure, not these
      Ensures -- hence A-reference, not A-consumed; see refinement.md / mapping.md.)

  (A-reference) the deep per-factor reduction `reduced_factor` (model.py pure
      region) reproduces, factor by factor, the integer-coefficient rewrite the
      gold patch performs on a product's non-modular factors:
        integer factor i with (i % q) != 0  ->  i % q
        opaque (symbolic) factor             ->  unchanged
        integer factor with (i % q) == 0      ->  unchanged
      validated by running the rewrite on the REAL sympy objects and comparing
      against the modelled list transform.

Imports only sympy (the very package the gold patch lives in) and the standard
library. Exit 0 iff every obligation holds.
"""
import random
import sys

from sympy import Integer, S, Symbol, Mul


# --- model.py reference encodings (kept in lock-step with the spec) ----------

def residue_model(value, m):
    """Reference for model.py's `residue` axiom: least non-negative residue."""
    r = value % m            # Python floored mod; matches Integer.__mod__
    return r


def reduced_factor_model(is_int, value, m):
    """Reference for model.py's `reduced_factor` pure function."""
    if is_int == 1 and residue_model(value, m) != 0:
        return residue_model(value, m)
    return value


# --- (A-reference) residue value vs the REAL sympy Integer % -----------------

def check_residue_axiom(value, m):
    observed = int(Integer(value) % Integer(m))      # REAL callee i % q
    # axiom Ensures #1: range
    assert 0 <= observed < m, (
        "residue axiom unsound: %d %% %d -> %d not in [0,%d)"
        % (value, m, observed, m))
    # axiom Ensures #2: congruence
    assert (value - observed) % m == 0, (
        "residue axiom unsound: %d - (%d %% %d)=%d not divisible by %d"
        % (value, value, m, value - observed, m))
    # axiom Ensures #3: idempotence on in-range values
    if 0 <= value < m:
        assert observed == value, (
            "residue axiom unsound: %d %% %d -> %d but value already in range"
            % (value, m, observed))
    # the model encoding must agree with the real callee
    assert observed == residue_model(value, m), (
        "residue model disagrees with sympy: %d %% %d -> real %d / model %d"
        % (value, m, observed, residue_model(value, m)))


# --- (A-reference) per-factor reduction vs the REAL sympy rewrite ------------

def real_reduce_factor(factor, q):
    """The exact factor rewrite the gold patch applies to one factor of a
    product (sympy/core/mod.py, the integer-coefficient block):
        if factor.is_Integer and (factor % q is not S.Zero): factor % q
        else: factor
    Returns the resulting sympy factor."""
    if factor.is_Integer and (factor % q is not S.Zero):
        return factor % q
    return factor


def check_reduction_reference(factors, q_int):
    """`factors` is a list of (is_int, value, sympy_obj) triples; q_int >= 2."""
    q = Integer(q_int)
    for is_int, value, obj in factors:
        # real rewrite on the actual sympy object
        real = real_reduce_factor(obj, q)
        # model rewrite on the abstract (is_int, value) encoding
        model_val = reduced_factor_model(is_int, value, q_int)
        if is_int == 1:
            real_val = int(real)
            assert real_val == model_val, (
                "reduced_factor unsound on integer %d mod %d: real %d / model %d"
                % (value, q_int, real_val, model_val))
        else:
            # opaque factor: must be left identically unchanged
            assert real == obj, (
                "reduced_factor unsound: opaque factor %r changed to %r"
                % (obj, real))
            assert model_val == value, (
                "reduced_factor model altered opaque factor value %d -> %d"
                % (value, model_val))


def main():
    rng = random.Random(15599)

    # --- (A-reference) residue value: boundary moduli + values -------------
    boundary_m = [2, 3, 4, 5, 6, 7, 8, 12, 100]
    boundary_v = [-100, -8, -5, -3, -2, -1, 0, 1, 2, 3, 4, 7, 8, 9, 99, 100,
                  1000, -1000]
    for m in boundary_m:
        for v in boundary_v:
            check_residue_axiom(v, m)
    # randomized fuzz
    for _ in range(50000):
        m = rng.randint(2, 50)
        v = rng.randint(-10000, 10000)
        check_residue_axiom(v, m)

    # --- (A-reference) per-factor reduction on real sympy factors ----------
    i = Symbol('i', integer=True, positive=True)
    x = Symbol('x')
    # opaque symbolic factors that must be preserved
    opaque = [(0, 0, i), (0, 0, x), (0, 0, Symbol('y')), (0, 0, i * x)]
    for q_int in [2, 3, 4, 5, 8, 12]:
        # integer-constant factors across the residue boundary
        int_factors = []
        for v in [-10, -4, -3, -2, -1, 0, 1, 2, 3, 4, 5, 8, 9, 16, 99]:
            int_factors.append((1, v, Integer(v)))
        check_reduction_reference(int_factors, q_int)
        check_reduction_reference(opaque, q_int)

    # randomized fuzz on integer factors
    for _ in range(20000):
        q_int = rng.randint(2, 30)
        v = rng.randint(-5000, 5000)
        check_reduction_reference([(1, v, Integer(v))], q_int)

    print("G-AX OK: residue axiom (== sympy Integer %%) sound on %d boundary "
          "+ 50000 fuzz pairs; reduced_factor deep model == sympy factor "
          "rewrite on boundary + 20000 fuzz factors."
          % (len(boundary_m) * len(boundary_v)))
    return 0


if __name__ == "__main__":
    sys.exit(main())

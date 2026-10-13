#!/usr/bin/env python3
"""G-AX executable soundness check for sympy__sympy-14711.

Runs the REAL repo callees the modeled add operator routes through — both
UNCHANGED by the gold patch — in-container, on boundary + fuzzed operands, and
asserts the A-reference facts the model relies on (mapping.md §3, refinement.md
steps 4-5). There is NO consumed axiom to validate point-wise (directive 7);
what G-AX establishes is that the two A-reference callees behave as modeled and
that the discriminator is real:

  1. asVector ⇔ `_check_vector` (vector.py:723-726), UNCHANGED:
       - returns the SAME object on a genuine `Vector` (the `Except.ok` leg);
       - RAISES `TypeError` on the additive identity `0` — this is exactly the
         pre-fix failure path the gold guard sidesteps (so the bug is real and
         the discriminator `other == 0` is genuine), AND on any other foreign
         non-vector value (the `Except.error .notAVector` leg).
  2. combine ⇔ `Vector(self.args + other.args)` (vector.py:60), UNCHANGED:
       - returns a `Vector` WITHOUT raising on two genuine vectors (so the
         `Except.ok (combine self v)` leg is inhabited and faithful).
  3. DISJOINTNESS: every genuine `Vector` in the modeled pool tests `!= 0`
       (so the `vec` and `zero` operand classes are disjoint — an empty vector,
       which would alias both, is excluded from the pool, mapping.md §3.1).

stdlib + the sympy under test only (no gold patch needed — both callees are the
UNCHANGED base-commit callees). Exit 0 iff every obligation holds.
"""
import random
import sys

SEED = 14711
N_FUZZ = 2000


def build_pool():
    from sympy.physics.vector import ReferenceFrame
    from sympy import symbols
    N = ReferenceFrame('N')
    A = N.orientnew('A', 'Axis', [symbols('q1'), N.x])
    x, y, z = symbols('x y z')
    # Genuine, non-zero vectors over real reference frames.
    pool = [
        N.x, N.y, N.z,
        A.x, A.y, A.z,
        x * N.x,
        x * N.x + y * N.y,
        x * N.x + y * N.y + z * N.z,
        x ** 2 * N.x + y ** 2 * N.y,
        2 * N.x + 3 * N.y,
        x * A.x + y * A.z,
    ]
    return pool


def foreign_samples():
    from sympy import symbols, Integer, Rational
    x = symbols('x')
    # Non-vector, non-zero values. (`0` is the ZERO class, handled separately.)
    return [1, 2, -5, 3.5, "x", x, Integer(7), Rational(3, 2), (1, 2), [1], {1: 2}]


def main():
    try:
        from sympy.physics.vector import Vector
        from sympy.physics.vector.vector import _check_vector
    except Exception as e:  # pragma: no cover
        print("G-AX FAIL: cannot import sympy.physics.vector:", type(e).__name__, e)
        return 1

    rng = random.Random(SEED)
    pool = build_pool()
    errors = []

    # --- Obligation 3: genuine vectors are disjoint from the zero class. -----
    for v in pool:
        try:
            if v == 0:
                errors.append(("pool-vec-is-zero", repr(v)))
        except Exception as e:
            errors.append(("pool-vec-eq0-raised", repr(v), type(e).__name__))

    # --- Obligation 1a: _check_vector returns the SAME genuine vector. -------
    for v in pool:
        try:
            out = _check_vector(v)
            if out is not v:
                errors.append(("check_vector-not-identity", repr(v), repr(out)))
        except Exception as e:
            errors.append(("check_vector-vec-raised", repr(v), type(e).__name__))

    # --- Obligation 1b: _check_vector RAISES TypeError on the identity 0
    #     (the pre-fix failure path) and on every foreign value. -------------
    boundary_foreign = [0] + foreign_samples()
    for f in boundary_foreign:
        try:
            _check_vector(f)
            errors.append(("check_vector-no-raise-on-foreign", repr(f)))
        except TypeError:
            pass  # expected
        except Exception as e:
            errors.append(("check_vector-wrong-exc", repr(f), type(e).__name__))

    # --- Obligation 2: combine (Vector(self.args + other.args)) returns a
    #     Vector without raising on two genuine vectors. --------------------
    for a in pool:
        for b in pool:
            try:
                # The exact UNCHANGED construction from __add__ line 60.
                res = Vector(a.args + b.args)
                if not isinstance(res, Vector):
                    errors.append(("combine-not-vector", repr(a), repr(b)))
            except Exception as e:
                errors.append(("combine-raised", repr(a), repr(b), type(e).__name__))

    # --- Fuzz: random genuine-vector pairs through combine; random foreign
    #     values through _check_vector. ---------------------------------------
    n_fuzz_combine = 0
    n_fuzz_foreign = 0
    for _ in range(N_FUZZ):
        a = rng.choice(pool)
        b = rng.choice(pool)
        try:
            res = Vector(a.args + b.args)
            if not isinstance(res, Vector):
                errors.append(("fuzz-combine-not-vector", repr(a), repr(b)))
            n_fuzz_combine += 1
        except Exception as e:
            errors.append(("fuzz-combine-raised", type(e).__name__))
        f = rng.choice(boundary_foreign)
        try:
            _check_vector(f)
            errors.append(("fuzz-foreign-no-raise", repr(f)))
        except TypeError:
            n_fuzz_foreign += 1
        except Exception as e:
            errors.append(("fuzz-foreign-wrong-exc", type(e).__name__))

    if errors:
        print("G-AX FAIL:", len(errors), "violation(s). First few:")
        for e in errors[:10]:
            print("   ", e)
        return 1

    print(
        "G-AX OK: _check_vector returns the same object on %d genuine vectors and "
        "raises TypeError on the identity 0 + %d foreign values (+%d fuzz); the "
        "unchanged Vector(args+args) construction returns a Vector on all %d "
        "genuine pairs (+%d fuzz); every pool vector tests != 0 (vec/zero "
        "disjoint). A-reference facts sound; no consumed axiom."
        % (len(pool), len(boundary_foreign) - 1, n_fuzz_foreign,
           len(pool) * len(pool), n_fuzz_combine)
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())

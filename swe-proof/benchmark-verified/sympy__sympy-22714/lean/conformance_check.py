#!/usr/bin/env python
"""G-CONF: differential conformance for sympy__sympy-22714.

Runs INSIDE the instance image with the gold patch applied (apply_gold=True,
PYTHONPATH=/testbed). Builds the Python R/I shadow of the Lean
`implementation_imaginaryCheck` skeleton and diffs it against the REAL patched
imaginary-coordinate guard in `sympy/geometry/point.py`:

    any(a.is_number and im(a).is_zero is False for a in coords)

Modeled decision: for a tuple of sympified coordinates, return the boolean the
guard's `any(...)` computes (True ⇒ the constructor raises
ValueError('Imaginary coordinates are not permitted.')).

Bridge (mapping.md): each coordinate `a` is projected to a `Coord` record
    isNumber        = bool(a.is_number)
    imagPartTruthy  = bool(im(a))            # pre-patch form-level reading
    imagPartDetZero = im(a).is_zero          # three-valued -> some/none
and the Lean impl's per-element predicate is
    isNumber and (imagPartDetZero is False)
existentially short-circuited over the tuple. The shadow consumes exactly those
observations, so it is the faithful R/I leg; the "real" leg evaluates the
genuine guard expression on the actual SymPy objects.

The reported bug manifests under `evaluate(False)`, where `im(a)` of a real
coordinate stays an unevaluated truthy object while `im(a).is_zero` is still
True. We fuzz BOTH evaluate settings so that divergence is exercised.

Exit 0 iff zero disagreements. stdlib + sympy only; pinned seed.
"""
import random
import sys

SEED = 20240627
N_RANDOM = 120_000  # >= 1e5


# ---- Python shadow of implementation_imaginaryCheck (post-patch R/I leg) -----

def shadow_imaginary_check(coords_obs):
    """Transliteration of problem_spec_imaginaryCheck / implementation_imaginaryCheck.
    `coords_obs` is a list of (isNumber, imagPartTruthy, imagPartDetZero) where
    imagPartDetZero is True / False / None (the three-valued is_zero)."""
    for isNumber, _imagPartTruthy, imagPartDetZero in coords_obs:
        if isNumber and (imagPartDetZero is False):
            return True
    return False


# ---- real guard observation -------------------------------------------------

def observe(a):
    """Project a SymPy coordinate to (isNumber, imagPartTruthy, imagPartDetZero)."""
    from sympy.functions.elementary.complexes import im
    return (bool(a.is_number), bool(im(a)), im(a).is_zero)


def real_imaginary_check(coords):
    """Evaluate the genuine post-patch guard on the actual SymPy coordinates."""
    from sympy.functions.elementary.complexes import im
    return bool(any(a.is_number and im(a).is_zero is False for a in coords))


def main():
    from sympy import (Integer, Rational, Float, Symbol, I, pi, sqrt, sympify,
                       Add, Mul)
    from sympy.core.parameters import evaluate as evaluate_ctx

    rng = random.Random(SEED)

    x, y = Symbol('x'), Symbol('y')

    # building blocks spanning: real numbers, imaginary/complex numbers,
    # symbols, and non-trivially-written-but-real expressions.
    atoms = [
        Integer(0), Integer(1), Integer(2), Integer(-3),
        Rational(1, 2), Rational(-5, 7),
        Float(0.5), Float(0.0), Float(-2.25),
        I, 2 * I, 1 + I, 3 - 2 * I, I / 2,
        pi, sqrt(2), sqrt(-1), 2 + sqrt(2),
        x, y, x + 1, x * I, 2 * x,
        # non-trivially written but real / zero:
        sqrt(2) ** 2, (I * I) + 1,
    ]

    def build_pool(do_eval):
        with evaluate_ctx(do_eval):
            pool = []
            for a in atoms:
                # re-sympify the string form so the (un)evaluated state is the
                # one a parser would produce under this evaluate setting.
                try:
                    pool.append(sympify(a, evaluate=do_eval))
                except Exception:
                    pool.append(a)
            return pool

    disagreements = 0
    checked = 0

    for do_eval in (True, False):
        pool = build_pool(do_eval)
        # discrete catalogue: all 1- and 2-element coordinate tuples from pool.
        cases = []
        for a in pool:
            cases.append([a])
        for a in pool:
            for b in pool:
                cases.append([a, b])

        # randomized tuples of length 1..4
        for _ in range(N_RANDOM // 2):
            n = rng.randint(1, 4)
            cases.append([rng.choice(pool) for _ in range(n)])

        for coords in cases:
            with evaluate_ctx(do_eval):
                obs = [observe(a) for a in coords]
                got = real_imaginary_check(coords)
            exp = shadow_imaginary_check(obs)
            checked += 1
            if got != exp:
                disagreements += 1
                if disagreements <= 5:
                    print(f"MISMATCH eval={do_eval} coords={coords!r} "
                          f"obs={obs!r}: real={got} shadow={exp}")

    print(f"checked={checked} disagreements={disagreements}")
    if disagreements == 0:
        print(f"status=pass conformance OK ({checked} checks, 0 disagreements)")
        return 0
    print(f"status=fail {disagreements} disagreement(s)")
    return 1


if __name__ == "__main__":
    sys.exit(main())

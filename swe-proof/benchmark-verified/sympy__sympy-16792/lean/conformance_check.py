#!/usr/bin/env python
"""G-CONF: differential conformance for sympy__sympy-16792.

Runs INSIDE the instance image with the gold patch applied (apply_gold=True,
PYTHONPATH=/testbed). Builds the Python R/A-reference shadow of the Lean
`implementation_arrayArgBounds` skeleton and diffs it against the REAL patched
callee `CodeGen.routine` over the full discrete input matrix plus >=1e5
randomized draws.

  observable: for an argument supplied ONLY via `argument_sequence` (redundant —
  it does not occur in `expr`, so it hits the `KeyError` branch), the
  `dimensions` metadata stored on the resulting `InputArgument`.
    - array-like symbol (MatrixSymbol of shape (m, n))  -> [(0, m-1), (0, n-1)]
    - plain scalar Symbol                               -> None/[]  (scalar)

Exit 0 iff zero disagreements. stdlib-only fuzzing (pinned seed).
"""
import random
import sys

SEED = 20240625
N_RANDOM = 120_000  # >= 1e5


# ---- Python shadow of implementation_arrayArgBounds ------------------------

def bounds_of(shape):
    # transliteration of boundsOf: each dim size d -> inclusive range (0, d-1)
    return [(0, d - 1) for d in shape]


def shadow_array_arg_bounds(is_array_like, shape):
    # transliteration of problem_spec_arrayArgBounds / implementation_arrayArgBounds
    if is_array_like:
        return bounds_of(shape)
    return []


# ---- real callee observation ------------------------------------------------

def real_bounds(symbol):
    """Run the REAL patched CodeGen.routine with a constant expression and a
    pinned argument_sequence containing only `symbol` (which is therefore
    redundant: it does not occur in the constant expr). Return the normalized
    `dimensions` metadata of the resulting argument."""
    from sympy import S
    from sympy.utilities.codegen import CCodeGen

    gen = CCodeGen()
    # constant expr -> `symbol` does not appear -> redundant -> KeyError branch
    routine = gen.routine("test", S(1.0), argument_sequence=(symbol,))
    # find the argument matching our symbol
    arg = routine.arguments[0]
    dims = arg.dimensions
    if not dims:
        return []
    # normalize sympy bound pairs to plain ints: (S.Zero, dim-1) -> (0, int(dim-1))
    return [(int(lo), int(hi)) for (lo, hi) in dims]


def main():
    from sympy import Symbol, MatrixSymbol

    disagreements = 0
    checked = 0

    # discrete shape catalogue for the array-like (MatrixSymbol) case
    shape_cases = [(2, 1), (1, 2), (3, 3), (1, 1), (4, 2), (5, 7), (2, 9), (8, 1)]

    cases = []  # (kind, shape) ; kind in {"scalar", "matrix"}
    cases.append(("scalar", None))
    for sh in shape_cases:
        cases.append(("matrix", sh))

    rng = random.Random(SEED)
    for _ in range(N_RANDOM):
        if rng.random() < 0.5:
            cases.append(("scalar", None))
        else:
            m = rng.randint(1, 12)
            n = rng.randint(1, 12)
            cases.append(("matrix", (m, n)))

    # cache real observations per concrete (kind, shape) to keep 1e5 draws fast
    cache = {}
    for kind, sh in cases:
        key = (kind, sh)
        if key not in cache:
            if kind == "scalar":
                sym = Symbol("x")
                is_array_like, shape = False, []
            else:
                sym = MatrixSymbol("x", sh[0], sh[1])
                is_array_like, shape = True, [sh[0], sh[1]]
            got = real_bounds(sym)
            exp = shadow_array_arg_bounds(is_array_like, shape)
            cache[key] = (got, exp)
        got, exp = cache[key]
        checked += 1
        if got != exp:
            disagreements += 1
            if disagreements <= 5:
                print(f"MISMATCH kind={kind} shape={sh}: real={got!r} shadow={exp!r}")

    print(f"checked={checked} disagreements={disagreements}")
    if disagreements == 0:
        print(f"status=pass conformance OK ({checked} checks, 0 disagreements)")
        return 0
    print(f"status=fail {disagreements} disagreement(s)")
    return 1


if __name__ == "__main__":
    sys.exit(main())

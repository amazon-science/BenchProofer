#!/usr/bin/env python
"""G-CONF: differential conformance for sympy__sympy-15017.

Runs INSIDE the instance image with the gold patch applied (apply_gold=True,
PYTHONPATH=/testbed). Builds the Python shadow of the Lean
`implementation_arraySize` skeleton and diffs it against the REAL patched
behavior: the element count `len(arr)` of a dense N-dimensional array, which the
patched `_new` derives from the array's shape.

  observable: len(ImmutableDenseNDimArray(...)) for a given shape.
    shadow:  product of the dimension sizes with seed 1 (empty product = 1).
    real:    len(ImmutableDenseNDimArray(<prod elements>, shape=<shape>))

The Lean model is parameterized over the shape (a list of non-negative
dimension sizes); we drive the real constructor with the same shape and read
back `len`, isolating the element-count computation the patch changed.

Exit 0 iff zero disagreements. stdlib-only fuzzing (pinned seed).
"""
import random
import sys

SEED = 20240627
N_RANDOM = 120_000  # >= 1e5


# ---- Python shadow of implementation_arraySize ----------------------------

def shadow_array_size(shape):
    # transliteration of problem_spec_arraySize / implementation_arraySize:
    #   result = shape.prod   (for-loop multiply accumulator seeded at 1)
    acc = 1
    for d in shape:
        acc = acc * d
    return acc


def build_real(shape):
    """Construct the real array for `shape` and return its len()."""
    from sympy import ImmutableDenseNDimArray, Integer
    if len(shape) == 0:
        # rank-0 scalar
        arr = ImmutableDenseNDimArray(Integer(7))
    else:
        prod = 1
        for d in shape:
            prod *= d
        arr = ImmutableDenseNDimArray([0] * prod, shape=tuple(shape))
    return len(arr)


def main():
    disagreements = 0
    checked = 0
    rng = random.Random(SEED)

    def run_case(shape):
        nonlocal disagreements, checked
        real = build_real(shape)
        shadow = shadow_array_size(shape)
        checked += 1
        if real != shadow:
            disagreements += 1
            if disagreements <= 5:
                print(f"MISMATCH shape={shape}: real={real!r} shadow={shadow!r}")

    # discrete catalogue: the F2P cases + a spread of ranks
    discrete = [
        [],          # F2P: scalar rank-0 -> 1
        [0],         # F2P: shape (0,) -> 0
        [1],         # one element
        [2, 3],      # 6
        [3, 4, 5, 6, 3],
        [1, 1, 1],
        [0, 5],      # contains a zero dimension -> 0
        [7],
    ]
    for shape in discrete:
        run_case(shape)

    for _ in range(N_RANDOM):
        rank = rng.randint(0, 4)
        # keep total element count modest so construction is cheap; allow zeros
        shape = [rng.randint(0, 6) for _ in range(rank)]
        run_case(shape)

    print(f"checked={checked} disagreements={disagreements}")
    if disagreements == 0:
        print(f"status=pass conformance OK ({checked} checks, 0 disagreements)")
        return 0
    print(f"status=fail {disagreements} disagreement(s)")
    return 1


if __name__ == "__main__":
    sys.exit(main())

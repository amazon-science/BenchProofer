#!/usr/bin/env python3
"""G-CONF differential conformance check for sympy__sympy-15017 (plan §4.1).

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both sides on the same fuzzed inputs and comparing observable outputs:

  * SHADOW  — the R/I-tagged ops of Solution.lean's impl region transliterated
              to Python over the *real* repo type (a shape tuple), via the
              mapping.md bijection (`List Nat` ↔ shape `Tuple`, `Nat` ↔ each
              dimension size). This is `prodSeq dims` = the product of the
              dimension sizes with the empty product = 1, i.e. the patched
              `functools.reduce(lambda x,y: x*y, shape, 1)`. There is NO
              A-tagged callee (mapping.md §3), so the shadow is pure R/I.
  * ORACLE  — `patch.diff`'s behaviour: the element count the patched
              `DenseNDimArray` exposes through `len(array)` at base_commit (the
              real correctness oracle, G-RESOLVE). The harness applies
              patch.diff before this runs.

They must agree on every input. Exit 0 iff zero disagreements; any disagreement
is a mechanical R/I-fidelity counterexample.

Runs in-container (the prebuilt SWE-Bench instance image), stdlib + sympy only.
The fuzz seed is pinned (mapping.md §4) for a deterministic verdict.
"""
import random
import sys
from functools import reduce


SEED = 15017
N_FUZZ = 100_000


# --- the R/I shadow: Solution.lean prodSeq, transliterated ------------------
def shadow_len(shape):
    """`prodSeq dims` transliterated to a Python shape tuple: the product of
    the dimension sizes, empty product = 1. This is the R/I shadow of the
    arrayLength impl (the patched reduce with initializer 1)."""
    return reduce(lambda x, y: x * y, shape, 1)


# --- the oracle: patch.diff's behaviour -------------------------------------
def _make_array(cls, shape):
    """Build a real NDimArray of the given shape with arbitrary contents (the
    contents do not affect _loop_size / __len__; only the shape does)."""
    import sympy
    shape = tuple(shape)
    if len(shape) == 0:
        # rank-0 scalar (shape == ()), the issue's case
        return cls(sympy.Integer(0))
    n = reduce(lambda x, y: x * y, shape, 1)
    return cls(list(range(n)), shape=shape)


def oracle_len(cls, shape):
    """patch.diff's behaviour: len() of the real patched DenseNDimArray. The
    harness applies patch.diff before this runs."""
    return len(_make_array(cls, shape))


def fuzz_shapes(n, rng):
    # boundary cases first (plan §4.1 step 4)
    yield ()                  # rank-0 scalar — the issue's discriminating case
    yield (0,)                # genuine zero-element 1-D array
    yield (1,)
    yield (5,)
    yield (0, 0)
    yield (0, 3)
    yield (3, 0)
    yield (1, 1, 1)
    yield (2, 3)
    yield (2, 3, 4)
    yield (10,)
    yield (1, 1, 1, 1, 1)
    for _ in range(n):
        rank = rng.randint(0, 5)
        # mix in 0/1 dims (which exercise the empty-product / unit edges) and
        # larger dims; keep total size bounded so construction stays cheap
        dims = []
        total = 1
        for _ in range(rank):
            d = rng.choice([0, 1, 1, 2, 3, 4, 5])
            if total * max(d, 1) > 4096:
                d = rng.choice([0, 1])
            dims.append(d)
            total *= max(d, 1) if d else 0 or 1
        yield tuple(dims)


def main():
    import sympy
    from sympy.tensor.array import ImmutableDenseNDimArray
    # The gold patch fixes ONLY ImmutableDenseNDimArray._new
    # (dense_ndim_array.py:152); the Mutable subclass's _new (:177) is left
    # unchanged by the gold patch and is NOT exercised by the issue or the
    # FAIL_TO_PASS test. The modeled element-count computation therefore binds
    # to the Immutable path (mapping.md §1), so the oracle uses it alone.
    cls = ImmutableDenseNDimArray

    rng = random.Random(SEED)
    disagreements = []
    count = 0
    for shape in fuzz_shapes(N_FUZZ, rng):
        count += 1
        shadow = shadow_len(shape)
        oracle = oracle_len(cls, shape)
        if shadow != oracle:
            disagreements.append((cls.__name__, shape, shadow, oracle))
            if len(disagreements) >= 5:
                break
    if disagreements:
        print("G-CONF FAIL: %d R/I disagreement(s) over %d inputs:"
              % (len(disagreements), count))
        for cn, shape, sh, orc in disagreements:
            print("  cls=%s shape=%r shadow=%r oracle=%r" % (cn, shape, sh, orc))
        return 1
    print("G-CONF OK: R/I shadow of arrayLength (prodSeq) agrees with "
          "patch.diff behaviour (len of patched DenseNDimArray) on %d inputs "
          "(seed=%d), 0 disagreements." % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())

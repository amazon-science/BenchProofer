#!/usr/bin/env python3
"""G-CONF — mechanical differential conformance for pydata__xarray-6721.

The bundle models ONE routine: `get_chunksizes(variables)` (xarray/core/common.py,
mapping.md). Its observable outcome is either a raised `ValueError` (inconsistent
chunks) or a normal return of `Frozen(chunks)` — the dim→block-lengths mapping.

Standing up the real xarray `Variable`/backend machinery to drive the method is
heavy and, for the modeled value, unnecessary: the POST-PATCH method's RESULT is
a pure function of, per variable, whether it is chunked (`hasattr(v._data,
"chunks")`) and its `v.chunksizes` mapping. Crucially the post-patch guard reads
`_data` and so NEVER materializes the variable — the result does not depend on
`isDuckArray`/`materializeRaises` at all.

So the ORACLE below is a faithful in-process replica of the POST-PATCH
`get_chunksizes` over the modeled observables, and the SHADOW is the op-for-op
transliteration of `implementation_getChunksizes` (Solution.lean impl region),
per refinement.md. We fuzz variable collections — including chunked, unchunked,
duck/non-duck, raising/non-raising, consistent and inconsistent chunk layouts —
and assert the two agree on every input (raise-vs-return AND the returned map,
compared order-sensitively since first-seen insertion order is part of the spec).

stdlib-only. Pinned seed: 6721 (also in mapping.md / meta.json).
"""
import random
import sys

SEED = 6721
N = 120_000

DIMS = ["x", "y", "z", "time", "lat", "lon"]


# --- ORACLE: faithful replica of the POST-PATCH get_chunksizes ----------------
# Post-patch reads v._data, so chunked-ness is metadata-only and never raises on
# materialization. Result = walk vars, skip unchunked, merge chunksizes, raise on
# an inconsistent dimension.
def oracle(variables):
    chunks = {}
    for v in variables:
        if v["hasChunks"]:
            for dim, c in v["chunksizes"]:
                if dim in chunks and chunks[dim] != c:
                    return ("error", None)
                chunks[dim] = c
    return ("ok", list(chunks.items()))


# --- SHADOW: op-for-op transliteration of implementation_getChunksizes --------
def shadow(variables):
    chunks = []  # list of (dim, blocks) — models List (String × List Nat)

    def lookup(key):
        for (k, val) in chunks:
            if k == key:
                return val
        return None

    for v in variables:
        if v["hasChunks"]:
            for (dim, c) in v["chunksizes"]:
                found = lookup(dim)
                if found is not None:
                    if found != c:
                        return ("error", None)
                    # agreeing value: no-op
                else:
                    chunks.append((dim, c))
    return ("ok", list(chunks))


def rand_blocks(rng):
    return tuple(rng.randint(1, 9) for _ in range(rng.randint(1, 3)))


def rand_var(rng):
    has = rng.random() < 0.6
    cs = []
    if has:
        for dim in rng.sample(DIMS, rng.randint(0, 3)):
            cs.append((dim, rand_blocks(rng)))
    return {
        "hasChunks": has,
        "chunksizes": cs,
        # observables the post-patch result is independent of — fuzzed anyway so
        # the differential test confirms that independence holds in the shadow:
        "isDuckArray": rng.random() < 0.5,
        "materializeRaises": rng.random() < 0.5,
    }


def main():
    rng = random.Random(SEED)
    disagreements = 0
    # boundary cases
    cases = [
        [],
        [{"hasChunks": False, "chunksizes": [], "isDuckArray": False,
          "materializeRaises": True}],
        [{"hasChunks": True, "chunksizes": [("x", (1, 2))], "isDuckArray": True,
          "materializeRaises": False},
         {"hasChunks": True, "chunksizes": [("x", (1, 2))], "isDuckArray": True,
          "materializeRaises": False}],  # agreeing duplicate
        [{"hasChunks": True, "chunksizes": [("x", (1,))], "isDuckArray": True,
          "materializeRaises": False},
         {"hasChunks": True, "chunksizes": [("x", (9,))], "isDuckArray": True,
          "materializeRaises": False}],  # inconsistent -> raise
    ]
    for variables in cases:
        if oracle(variables) != shadow(variables):
            disagreements += 1

    for _ in range(N):
        variables = [rand_var(rng) for _ in range(rng.randint(0, 6))]
        if oracle(variables) != shadow(variables):
            disagreements += 1
            if disagreements <= 5:
                print(f"DISAGREE: {variables}", file=sys.stderr)

    if disagreements:
        print(f"G-CONF FAIL: {disagreements} disagreement(s)", file=sys.stderr)
        sys.exit(1)
    print(f"G-CONF pass: 0 disagreements over {N}+{len(cases)} inputs (seed {SEED})")
    sys.exit(0)


if __name__ == "__main__":
    main()

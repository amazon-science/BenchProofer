#!/usr/bin/env python3
"""G-CONF for astropy__astropy-12907.

Differential test: the R/I Python shadow of `implementation_direct_sum`
(Solution.lean) vs. the REAL patched combinator `_cstack` (the array/array
branch) in `astropy/modeling/separable.py`. The orchestrator applies the gold
patch before running this, so the imported `_cstack` is the fixed version.

`_cstack` is the `&`-operator handler in `_separable`; on nested compound
models it is always invoked with two already-computed correlation arrays
(never `Model` objects), so we exercise it exactly on ndarray/ndarray inputs.

Type bridge (mapping.md): a correlation matrix `List (List Nat)` ↔ a 2-D
ndarray; entry 0 ↔ independent, nonzero ↔ dependent. `_cstack` returns a
float {0,1} array; we compare the 0/nonzero boolean pattern, which is all the
downstream `separability_matrix` (`!= 0`) consumes.

Exit 0 iff zero disagreements over >=1e5 fuzzed cases. stdlib + numpy only.
"""
import random
import sys

import numpy as np

SEED = 12907
N_CASES = 100_000


def shadow(left, right, lin, rin):
    """R/I transliteration of implementation_direct_sum (Solution.lean).

    left, right: lists of rows (each a list of {0,1}); lin/rin their widths.
    Returns the combined matrix as a list of rows.
    """
    lout = len(left)
    rout = len(right)
    noutp = lout + rout
    result = []
    for i in range(noutp):
        cleft_row = left[i] if i < lout else [0] * lin
        cright_row = right[i - lout] if lout <= i else [0] * rin
        result.append(list(cleft_row) + list(cright_row))
    return result


def to_array(rows, width):
    """List-of-rows -> 2-D ndarray (handles the empty-rows / zero-width cases)."""
    if len(rows) == 0:
        return np.zeros((0, width))
    return np.array(rows, dtype=float)


def main():
    from astropy.modeling.separable import _cstack

    rng = random.Random(SEED)
    mismatches = 0
    checked = 0
    for _ in range(N_CASES):
        lout = rng.randint(0, 6)
        rout = rng.randint(0, 6)
        lin = rng.randint(0, 6)
        rin = rng.randint(0, 6)
        # _cstack's array branch needs left.shape[1]/right.shape[1]; a
        # 0-output block still carries a defined width, which numpy keeps only
        # for non-empty arrays. Skip degenerate all-empty pairs that can't form
        # a 2-D array on the numpy side (no observable behavior there).
        if (lout == 0 and rout == 0):
            continue
        left = [[rng.randint(0, 1) for _ in range(lin)] for _ in range(lout)]
        right = [[rng.randint(0, 1) for _ in range(rin)] for _ in range(rout)]

        # numpy oracle requires real 2-D blocks; build them, skip cases numpy
        # itself cannot represent (a 0-row block has shape (0,) under np.array,
        # so feed an explicit zeros block of the right width).
        cleft = to_array(left, lin)
        cright = to_array(right, rin)
        if cleft.ndim != 2 or cright.ndim != 2:
            continue
        if cleft.shape[1] == 0 and cright.shape[1] == 0:
            continue
        try:
            oracle = _cstack(cleft, cright)
        except Exception:
            # shape edge the real code rejects -> nothing to compare
            continue

        got = shadow(left, right, lin, rin)
        got_arr = to_array(got, lin + rin)

        ob = (oracle != 0)
        gb = (got_arr != 0)
        if ob.shape != gb.shape or not np.array_equal(ob, gb):
            mismatches += 1
            if mismatches <= 5:
                print(f"MISMATCH lout={lout} rout={rout} lin={lin} rin={rin}")
                print(" oracle:", ob.astype(int).tolist())
                print(" shadow:", gb.astype(int).tolist())
        checked += 1

    if mismatches == 0:
        print(f"status=pass checked={checked} mismatches=0")
        sys.exit(0)
    print(f"status=fail checked={checked} mismatches={mismatches}")
    sys.exit(1)


if __name__ == "__main__":
    main()

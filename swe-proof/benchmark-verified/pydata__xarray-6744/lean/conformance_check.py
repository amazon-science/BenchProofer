#!/usr/bin/env python
"""G-CONF for pydata__xarray-6744.

Differential test of the R/I legs of `implementation_rollingWindows` against the
PATCHED xarray rolling iterator (the gate git-applies the gold patch before
running this, so `xarray` here is the fixed code).

Modeled (R) behavior: when manually iterating a 1-D rolling object, each
position's window covers the contiguous slice `[start, stop)` of the input
sequence dictated by the window length and the alignment flag — forward shift
`(w+1)//2` when centered, else `1`, with the leading positions clamped to start
0.

Shadow (this file): replicate that start/stop arithmetic in pure Python and
extract each slice from the input list. Compare against the slice each window
actually covers when iterating the patched `DataArrayRolling` (the pre-mask
`isel` slice values).

stdlib + xarray/numpy only. Exit 0 iff zero disagreements over >=1e5 inputs.
"""
import random
import sys

import numpy as np
import xarray as xr

SEED = 6744
N = 100_000


def shadow_windows(xs, window, center):
    """List (per position) of the contiguous slice the window covers — the
    modeled R/I logic."""
    n = len(xs)
    offset = (window + 1) // 2 if center else 1
    out = []
    for i in range(n):
        stop = offset + i
        start = 0 if i + offset < window else stop - window
        out.append(list(xs[start:stop]))
    return out


def oracle_windows(xs, window, center):
    """The slice each yielded window covers, from the patched iterator. We read
    the window's own coordinate index positions (not the masked values) so the
    comparison is against the slice arithmetic the fix changes, independent of
    the downstream min_periods masking."""
    da = xr.DataArray(np.asarray(xs), dims="x", coords={"x": np.arange(len(xs))})
    roll = da.rolling(x=window, center=center)
    out = []
    for _label, w in roll:
        # `w` is the isel slice (before where-masking is the count>=min_periods
        # step; min_periods defaults to the window size). Recover the covered
        # index range from the window's own `x` coordinate.
        idx = [int(v) for v in np.asarray(w["x"].values).ravel()]
        out.append([int(xs[k]) for k in idx])
    return out


def gen_case(rng):
    n = rng.randint(0, 40)
    window = rng.randint(1, max(1, min(12, n if n else 1)))
    center = rng.random() < 0.5
    xs = [rng.randint(-1000, 1000) for _ in range(n)]
    return xs, window, center


def main():
    rng = random.Random(SEED)
    # boundary cases first
    boundary = [
        ([], 1, False), ([], 1, True),
        ([5], 1, True), ([5], 1, False),
        ([1, 2, 3, 4, 5, 6, 7, 8, 9], 3, True),
        ([1, 2, 3, 4, 5, 6, 7, 8, 9], 3, False),
        ([1, 2, 3, 4, 5, 6, 7], 7, True),
        ([1, 2, 3, 4, 5], 2, True),
        ([1, 2, 3, 4, 5], 2, False),
    ]
    checked = 0
    for xs, window, center in boundary:
        s = shadow_windows(xs, window, center)
        o = oracle_windows(xs, window, center)
        if s != o:
            print(f"DISAGREE (boundary) xs={xs} w={window} center={center}: "
                  f"shadow={s} oracle={o}")
            sys.exit(1)
        checked += 1
    for _ in range(N):
        xs, window, center = gen_case(rng)
        s = shadow_windows(xs, window, center)
        o = oracle_windows(xs, window, center)
        if s != o:
            print(f"DISAGREE xs={xs} w={window} center={center}: "
                  f"shadow={s} oracle={o}")
            sys.exit(1)
        checked += 1
    print(f"G-CONF ok: {checked} cases, zero disagreements")
    sys.exit(0)


if __name__ == "__main__":
    main()

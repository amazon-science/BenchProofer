#!/usr/bin/env python3
"""G-AX executable soundness check for pydata__xarray-4687.

The bundle has NO consumed axioms. Its single kind-A row (refinement.md op 1) is
an **A-reference**: the deep model `whereSelect` (Solution.lean `pure` region)
models the UNCHANGED elementwise value-selection primitive the routine delegates
to. `xarray`'s `where` computes its cell values via
`apply_ufunc(duck_array_ops.where, cond, x, y, …)`, and `duck_array_ops.where`
dispatches to `numpy.where` for in-memory arrays. G-AX validates the deep model
against that REAL primitive:

    whereSelect(cond, x, y)[i] == np.where(cond, x, y)[i]
        = x[i] if cond[i] else y[i]

over boundary cases and randomized fuzz of equal-length integer arrays (the
modeled, aligned 1-D shape — mapping.md §2). The attrs-propagation decision
(the CHANGED behaviour) is a closed boolean function modeled directly in
Solution.lean and is exercised by conformance_check.py (G-CONF), not here.

Imports `numpy` and `xarray.core.duck_array_ops` — the same primitive the gold
patch's value path runs through. Exit 0 iff every obligation holds.
"""
import random
import sys

import numpy as np

try:
    from xarray.core import duck_array_ops
    _REAL_WHERE = duck_array_ops.where           # the real callee xarray uses
except Exception:                                # pragma: no cover
    _REAL_WHERE = None


def real_where(cond, x, y):
    """The REAL unchanged value-selection primitive, returned as a Python list of
    ints. Prefer xarray's duck_array_ops.where (what `where` actually calls);
    fall back to numpy.where (its in-memory backend) if xarray is absent."""
    if _REAL_WHERE is not None:
        out = _REAL_WHERE(np.asarray(cond, dtype=bool),
                          np.asarray(x, dtype=np.int64),
                          np.asarray(y, dtype=np.int64))
    else:
        out = np.where(np.asarray(cond, dtype=bool),
                       np.asarray(x, dtype=np.int64),
                       np.asarray(y, dtype=np.int64))
    return [int(v) for v in np.asarray(out).tolist()]


def where_select(cond, x, y):
    """Reference of Solution.lean's deep model `whereSelect` (front-recursive
    elementwise select over aligned cell lists)."""
    n = min(len(cond), len(x), len(y))
    return [int(x[i]) if cond[i] else int(y[i]) for i in range(n)]


def check_reference(cond, x, y):
    observed = real_where(cond, x, y)            # real primitive
    expected = where_select(cond, x, y)          # deep model
    assert observed == expected, (
        "whereSelect deep model unsound on cond=%r x=%r y=%r: "
        "real np.where gave %r, deep model gives %r"
        % (cond, x, y, observed, expected))


def main():
    # --- boundary cases -----------------------------------------------------
    boundary = [
        ([], [], []),                               # empty
        ([True], [7], [-3]),                        # single true
        ([False], [7], [-3]),                       # single false
        ([True, False], [1, 1], [0, 0]),            # the F2P shape/values
        ([False, True], [1, 1], [0, 0]),
        ([True, True, True], [5, 6, 7], [0, 0, 0]),
        ([False, False, False], [5, 6, 7], [9, 9, 9]),
        ([True, False, True, False],
         [-2147483648, 0, 2147483647, 42],
         [11, -11, 0, -42]),                        # large/zero/neg sentinels
    ]
    for cond, x, y in boundary:
        check_reference(cond, x, y)

    # --- randomized fuzz ----------------------------------------------------
    rng = random.Random(4687)
    for _ in range(20000):
        n = rng.randint(0, 24)
        cond = [rng.choice([True, False]) for _ in range(n)]
        x = [rng.randint(-1000, 1000) for _ in range(n)]
        y = [rng.randint(-1000, 1000) for _ in range(n)]
        check_reference(cond, x, y)

    print("G-AX OK: whereSelect deep model (== duck_array_ops.where / np.where) "
          "sound on %d boundary + 20000 fuzz equal-length int arrays; "
          "no consumed axioms to check." % len(boundary))
    return 0


if __name__ == "__main__":
    sys.exit(main())

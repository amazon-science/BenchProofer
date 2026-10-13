#!/usr/bin/env python3
"""G-AX executable soundness check for pydata__xarray-4356.

The one modeled callee is the element-count product introduced by the fix:
`np.take(mask.shape, axis).prod()` — the number of elements collapsed into each
output cell of a reduction over a collection of dimensions. It is modeled
DEEPLY by `prodList` (Solution.lean pure region), not behind a consumed axiom,
so this is an **A-reference** check: the deep model `prodList` must equal the
real array reduction `np.take(shape, axis).prod()`.

  (A-reference) prodList(sizes) == int(np.take(shape, axis).prod())
      where shape/axis are constructed so np.take(shape, axis) == sizes.
      In particular the empty product is 1 (np.prod([]) == 1.0), and a single
      reduced axis reproduces the pre-patch `mask.shape[axis]` while two or more
      give the genuine product — the behavioural content of the fix.

Imports only `numpy` — the same array library the gold patch's `.prod()` runs
on. Exit 0 iff every obligation holds.
"""
import random
import sys

import numpy as np


def prod_list(sizes):
    """Reference implementation of Solution.lean's deep model `prodList`:
    prodList [] = 1; prodList (x :: xs) = x * prodList xs."""
    total = 1
    for s in sizes:
        total = s * total
    return total


def check_prod_reference(shape, axis):
    """Assert the deep model prodList(sizes) == the REAL np.take(shape,axis).prod()
    where sizes are the gathered reduced-axis extents."""
    gathered = np.take(np.array(shape), axis)          # real gather over axes
    real = int(np.asarray(gathered).prod())            # real reduction (callee)
    model = prod_list([int(x) for x in np.atleast_1d(gathered)])  # deep model
    assert real == model, (
        "prodList deep model unsound for shape=%r axis=%r: "
        "np.take(shape,axis).prod()=%r, prodList=%r"
        % (shape, axis, real, model))


def main():
    # --- boundary cases ----------------------------------------------------
    # empty product (reduction over no axis) -> 1
    assert prod_list([]) == 1
    assert int(np.asarray(np.take(np.array([3, 4, 5]), [])).prod()) == 1

    boundary = [
        ((3, 4, 5), 0),            # single axis (pre-patch's correct case)
        ((3, 4, 5), 1),
        ((3, 4, 5), 2),
        ((3, 4, 5), [0, 1]),       # two axes -> genuine product (the fix)
        ((3, 4, 5), [0, 1, 2]),    # all axes (the F2P all-dims reduction)
        ((3, 4, 5), (1, 2)),
        ((2, 3), [0, 1]),
        ((1, 1, 1), [0, 1, 2]),    # unit dims
        ((1, 7), [0, 1]),
        ((0, 5), [0, 1]),          # a zero-length dim -> product 0
        ((10, 1), 0),
        ((6,), 0),                 # 1-D
        ((6,), [0]),
        ((100, 200), [0, 1]),      # large
    ]
    for shape, axis in boundary:
        check_prod_reference(shape, axis)

    # --- randomized fuzz ---------------------------------------------------
    rng = random.Random(4356)
    for _ in range(20000):
        ndim = rng.randint(1, 5)
        shape = tuple(rng.randint(0, 12) for _ in range(ndim))
        k = rng.randint(0, ndim)                       # how many axes reduced
        axis = sorted(rng.sample(range(ndim), k))
        if k == 1:
            axis = axis[0]                             # int axis form
        elif k == 0:
            axis = []                                  # empty -> product 1
        check_prod_reference(shape, axis)

    print("G-AX OK: prodList deep model (== np.take(shape,axis).prod()) sound "
          "on %d boundary + 20000 fuzz reduced-axis configurations "
          "(empty product = 1)." % len(boundary))
    return 0


if __name__ == "__main__":
    sys.exit(main())

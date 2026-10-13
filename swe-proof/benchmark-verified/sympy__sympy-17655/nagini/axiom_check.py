#!/usr/bin/env python3
"""G-AX executable soundness check for sympy__sympy-17655.

This bundle consumes NO `@ContractOnly` axioms.  The single changed operation
-- scaling a point's coordinates by a factor, accessible from both the left and
the right -- is modelled DEEPLY as the per-coordinate integer multiplication
`scaled` in model.py's pure region:

    scaled(s, factor)[i] == s[i] * factor      (dimension preserved)

G-AX validates that DEEP MODEL against the REAL sympy callees `Point.__mul__`
(right multiplication, the unchanged operation) and `Point.__rmul__` (left
multiplication, the post-patch operation) on the coordinate carrier, over
boundary cases and randomized fuzzing.  Two obligations:

  (A-reference, right)  the deep model `scaled(coords, factor)` equals the
      coordinates of the REAL `Point(*coords) * factor`.

  (A-reference, left)   the deep model `scaled(coords, factor)` equals the
      coordinates of the REAL `factor * Point(*coords)` -- i.e. left scaling
      reproduces the per-coordinate scaling, exactly the commutativity property
      the spec pins (and the property the gold patch establishes).

Imports nothing repo-internal beyond the public `sympy.geometry.Point`, the
very class the gold patch edits.  Exit 0 iff every observation matches.
"""
import random
import sys

from sympy.geometry import Point


def scaled(coords, factor):
    """Reference implementation of model.py's deep model `scaled`: each
    coordinate multiplied by the factor, in order, dimension preserved."""
    return [c * factor for c in coords]


def real_right_coords(coords, factor):
    """Coordinates of the REAL right multiplication  Point(*coords) * factor."""
    p = Point(*coords)
    res = p * factor
    return [int(x) for x in res.args]


def real_left_coords(coords, factor):
    """Coordinates of the REAL left multiplication  factor * Point(*coords)
    (uses Point.__rmul__, the post-patch operation)."""
    p = Point(*coords)
    res = factor * p
    return [int(x) for x in res.args]


def check(coords, factor):
    expected = scaled(coords, factor)               # deep model
    right = real_right_coords(coords, factor)        # real Point.__mul__
    left = real_left_coords(coords, factor)          # real Point.__rmul__
    assert right == expected, (
        "deep model unsound vs real right-multiplication on coords=%r "
        "factor=%r: real %r, model %r" % (coords, factor, right, expected))
    assert left == expected, (
        "deep model unsound vs real left-multiplication on coords=%r "
        "factor=%r: real %r, model %r" % (coords, factor, left, expected))
    # commutativity witness (the property the gold patch establishes)
    assert left == right, (
        "left != right scaling on coords=%r factor=%r: %r vs %r"
        % (coords, factor, left, right))


def main():
    # --- boundary cases ------------------------------------------------------
    boundary = [
        ([1, 1], 5),           # the 2D F2P case: 5 * Point(1, 1) == Point(5, 5)
        ([1, 1, 1], 5),        # the 3D F2P case: 5 * Point(1, 1, 1)
        ([0, 0], 5),
        ([1, 1], 0),
        ([1, 1], 1),
        ([2, 3], 5),
        ([1, 2, 3], 4),
        ([0, 1], 7),
        ([3, 0, 4], 2),
        ([1, 1], -3),          # negative factor
        ([-2, 5], 6),          # negative coordinate
        ([10, 20, 30, 40], 3), # higher dimension
    ]
    for coords, factor in boundary:
        check(coords, factor)

    # --- randomized fuzz -----------------------------------------------------
    rng = random.Random(17655)
    for _ in range(2000):
        dim = rng.randint(2, 5)             # Point requires >= 2 coordinates
        coords = [rng.randint(-50, 50) for _ in range(dim)]
        factor = rng.randint(-50, 50)
        check(coords, factor)

    print("G-AX OK: deep model `scaled` == real Point.__mul__ and "
          "Point.__rmul__ (commutative) on %d boundary + 2000 fuzz inputs"
          % len(boundary))
    return 0


if __name__ == "__main__":
    sys.exit(main())

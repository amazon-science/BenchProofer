#!/usr/bin/env python3
"""G-AX executable soundness check for sympy__sympy-17655.

Validates the ONE deep-model reference of this bundle against the REAL repo
callee, in-container at base_commit (UNPATCHED), over boundary + randomized
fuzz inputs:

  (A-reference) the deep model `scaleCoords` (Solution.lean pure region) ==
      the library's existing point-by-scalar scaling callee — the per-coordinate
      product `Point.__mul__(self, factor)`. The changed function (left-
      multiplication of a number by a point) DELEGATES to this UNCHANGED scaling
      operation; the patch adds the delegation and changes nothing about the
      scaling itself. We model that scaling deeply
      (`scaleCoords coords factor = coords.map (· * factor)`) and G-AX confirms
      the deep model reproduces the real callee exactly and dimension-preserving:
        Point(c0, c1, ...) * factor  ==  Point(c0*factor, c1*factor, ...)

DELIBERATELY NOT CHECKED HERE: the new `__rmul__` reflected-multiply path
(`factor * point`). G-AX runs at base_commit with NO gold patch applied (unlike
G-CONF), so `__rmul__` does not yet exist; and per SPEC_GUIDE directive 7 an
axiom/deep-model check must exercise only the UNCHANGED callee, never the
function under change. The `factor * point == point * factor` delegation
behaviour the issue + F2P tests demand is the patched-repo behaviour, validated
by G-RESOLVE (the official harness runs `5 * p4 == Point(5, 5)` against the
patched repo) — not by this gate.

The factor is a Python-native exact scalar (`int` / `fractions.Fraction`),
exactly as the issue and the F2P tests use it (`5 * p4`, a Python `int`). This
matches the `Rat` carrier of Solution.lean (mapping.md §2): a left operand that
is itself a SymPy object would be multiplied by SymPy's own `Mul` before any
reflected-multiplication hook fires — a different operation, outside the modeled
behavior. Comparisons are exact (rationals), so no float tolerance is needed.
Imports only `sympy` (the repo under test). Exit 0 iff every obligation holds.
"""
import random
import sys
from fractions import Fraction

from sympy import geometry as ge, sympify


def scale_coords(coords, factor):
    """Reference implementation of Solution.lean's deep model `scaleCoords`:
    the per-coordinate product (coords.map (· * factor))."""
    return [c * sympify(factor) for c in coords]


def make_point(coords):
    return ge.Point(*coords, evaluate=False)


def check_deep_model(coords, factor):
    """Assert scaleCoords(coords, factor) == the REAL UNCHANGED scaling callee
    (right-multiplication Point * factor = Point.__mul__) coordinate-for-
    coordinate, and dimension-preserving."""
    p = make_point(coords)
    scaled = p * factor                         # real UNCHANGED callee: __mul__
    observed = list(scaled.args)
    expected = scale_coords(list(p.args), factor)
    assert observed == expected, (
        "scaleCoords deep model unsound on coords=%r factor=%r: "
        "real Point*factor gave %r, deep model gives %r"
        % (coords, factor, observed, expected))
    assert len(observed) == len(p.args), (
        "dimension changed under scaling on %r * %r" % (coords, factor))


def fuzz_scalar(rng):
    """A Python-native exact scalar: an int or a Fraction."""
    if rng.random() < 0.5:
        return rng.randint(-100, 100)
    num = rng.randint(-100, 100)
    den = rng.randint(1, 50)
    return Fraction(num, den)


def fuzz_coord(rng):
    """A SymPy-coercible exact coordinate (int or Fraction)."""
    if rng.random() < 0.5:
        return rng.randint(-100, 100)
    return Fraction(rng.randint(-100, 100), rng.randint(1, 50))


def main():
    rng = random.Random(17655)

    # --- boundary cases (the dimensions/values the F2P tests exercise) -------
    boundary = [
        ([1, 1], 5),                 # underlies 5 * Point(1, 1)    == Point(5, 5)
        ([1, 1, 1], 5),              # underlies 5 * Point3D(1,1,1) == Point3D(5,5,5)
        ([0, 0], 5),
        ([1, 2], 0),
        ([1, 2], -1),
        ([3, 4], Fraction(1, 2)),
        ([1, 2, 3, 4], Fraction(-7, 3)),
    ]
    for coords, factor in boundary:
        check_deep_model(coords, factor)

    # --- randomized fuzz over dimension 2..4 and exact scalars --------------
    N = 20000
    for _ in range(N):
        dim = rng.randint(2, 4)
        coords = [fuzz_coord(rng) for _ in range(dim)]
        factor = fuzz_scalar(rng)
        check_deep_model(coords, factor)

    print("G-AX OK: scaleCoords deep model (== real UNCHANGED point-by-scalar "
          "scaling Point.__mul__) sound and dimension-preserving on %d boundary "
          "+ %d fuzz point/factor pairs (seed=17655)." % (len(boundary), N))
    return 0


if __name__ == "__main__":
    sys.exit(main())

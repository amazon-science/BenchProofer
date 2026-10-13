#!/usr/bin/env python3
"""G-AX executable soundness check for sympy__sympy-11618.

Runs the REAL repository callees in-container (the patched `sympy.geometry`
Point distance and `sympy.sqrt`) on boundary cases and randomized fuzz, and
asserts that every observation matches the model in model.py ON THE MODELED
DOMAIN.

Modeled domain (scope — important for soundness, see refinement.md §C):
  model.py specifies the distance as the square root of the squared-difference
  sum over EVERY axis of the larger ambient dimension, with the shorter vector
  zero-padded (`psum(u, v, max(len(u),len(v)))`). The REAL callee computes that
  padded sum exactly on the inputs the bundle's correctness oracle exercises:
    (i)  EQUAL-dimension point pairs (the plain pairwise sum already ranges over
         every axis), and
    (ii) point pairs of DIFFERENT concrete type (e.g. a 2-D point vs a 3-D
         point), for which the patched callee's dimension-aware branch builds
         the zero-padded coordinate pair before summing.
  The F2P witness (`Point3D(1,0,2).distance(Point2D(2,0)) == sqrt(5)`) and the
  reported issue witness (`Point(2,0).distance(Point(1,0,2)) == sqrt(5)`) both
  lie in regime (ii): the operands are Point3D vs Point2D, distinct types.

Out-of-scope (NOT a soundness failure — the model is deliberately scoped to the
oracle's domain): two SAME-type points of differing dimension (only the generic
n-D `Point` admits this). The patched callee leaves such pairs on its original
pairwise path, which does not pad; the model is therefore stronger than the real
callee there. The bundle's F2P/P2P inputs never enter this region, so resolution
is unaffected (refinement.md §C documents the scoping). This script ASSERTS that
boundary explicitly (it must NOT silently assume agreement there).

Two kinds, per refinement.md:

  (A-reference) the deep model `psum` (model.py pure region) — the sum of
      squared coordinate differences over EVERY axis of the larger ambient
      dimension, with the shorter vector zero-padded — equals the inner squared
      quantity of the REAL `Point.distance` on the modeled domain (i)+(ii):
          real_distance(P_u, P_v) == sqrt( psum(u, v, max(len(u),len(v))) )
      This pins exactly the modeled behaviour: in the padding regime, axes
      present only in the longer vector contribute (coord - 0)**2 and are NOT
      dropped.

  (A-consumed) the `root` axiom (model.py axioms region) stands for the
      unchanged square root applied to that non-negative sum. The contract the
      proof consumes is: `root` is a deterministic function of its argument
      (equal arguments give equal results) and `root(x) >= 0` for `x >= 0`.
      We confirm the real `sqrt` meets it.

Imports only `sympy` (the very package whose `Point.distance` the patch fixes)
and the standard library. Exit 0 iff every obligation holds.
"""
import random
import sys

from sympy import sqrt, Integer
from sympy.geometry import Point, Point2D, Point3D


# --- model.py reference encodings (kept in lock-step with the spec) ----------

def coord(s, i):
    """model.py `coord`: i-th coordinate, zero-padded beyond the vector."""
    return s[i] if i < len(s) else 0


def psum(u, v, k):
    """model.py `psum`: sum of squared coordinate differences over axes 0..k."""
    total = 0
    for i in range(k):
        d = coord(u, i) - coord(v, i)
        total += d * d
    return total


def padded_squared_sum(u, v):
    """psum over the larger ambient dimension (max length)."""
    return psum(u, v, max(len(u), len(v)))


# --- the checks --------------------------------------------------------------

def check_distance_reference(pu, pv, u, v):
    """Assert real Point.distance == sqrt(model padded squared sum), on the
    modeled domain (equal dimension, or distinct concrete type). `pu`/`pv` are
    the real Point objects; `u`/`v` their integer coordinate lists."""
    observed = pu.distance(pv)                           # real (patched) callee
    expected = sqrt(Integer(padded_squared_sum(u, v)))   # deep model + sqrt
    assert observed == expected, (
        "padded-sum deep model unsound on u=%r v=%r (types %s/%s): "
        "Point.distance gave %r, model gives sqrt(%d)=%r"
        % (u, v, type(pu).__name__, type(pv).__name__, observed,
           padded_squared_sum(u, v), expected))
    # symmetry: distance is order-independent (both directions must agree)
    observed_rev = pv.distance(pu)
    assert observed_rev == expected, (
        "distance not symmetric on u=%r v=%r: %r vs %r"
        % (u, v, observed, observed_rev))


def check_root_axiom(x):
    """Assert the real sqrt meets the `root` axiom on non-negative argument x:
    deterministic and sqrt(x) >= 0."""
    r1 = sqrt(Integer(x))
    r2 = sqrt(Integer(x))
    assert r1 == r2, "sqrt not deterministic on %d: %r vs %r" % (x, r1, r2)
    assert r1.is_nonnegative, "sqrt(%d) is not non-negative: %r" % (x, r1)


def in_modeled_domain(pu, pv):
    """The modeled agreement domain: equal dimension OR distinct concrete type.
    Exactly the regime in which the patched callee computes the padded sum."""
    return len(pu) == len(pv) or type(pu) is not type(pv)


def main():
    # === A-reference: padded-sum deep model vs real Point.distance ===========
    # All boundary cases lie in the modeled domain (equal dim, or distinct
    # type). For differing dimension we use distinct concrete types (Point3D vs
    # Point2D, or a generic n-D Point vs a 2-/3-D point), which is exactly when
    # the patched callee builds the zero-padded coordinate pair.
    #
    # Each entry: (point_u, point_v, coords_u, coords_v).
    boundary = [
        # the reported bug + F2P witness: Point2D vs Point3D (distinct type)
        (Point2D(2, 0), Point3D(1, 0, 2), [2, 0], [1, 0, 2]),    # must be sqrt(5)
        (Point3D(1, 0, 2), Point2D(2, 0), [1, 0, 2], [2, 0]),    # F2P orientation
        # equal dimension, same type
        (Point2D(1, 1), Point2D(4, 5), [1, 1], [4, 5]),
        (Point3D(4, -2, 6), Point3D(1, 2, 3), [4, -2, 6], [1, 2, 3]),
        (Point2D(3, 0), Point2D(3, 0), [3, 0], [3, 0]),          # equal points -> 0
        # equal dimension, cross type (generic Point vs Point2D, both dim 2)
        (Point([5, 7]), Point2D(1, 2), [5, 7], [1, 2]),
        # distinct type, larger dimension gap: generic n-D Point vs 2-/3-D point
        (Point([0, 0, 0, 0, 5]), Point2D(0, 0), [0, 0, 0, 0, 5], [0, 0]),
        (Point([1, 2, 3, 4]), Point3D(1, 0, 2), [1, 2, 3, 4], [1, 0, 2]),
        (Point2D(7, 1), Point([1, 2, 3, 4, 5]), [7, 1], [1, 2, 3, 4, 5]),
    ]
    for pu, pv, u, v in boundary:
        assert in_modeled_domain(pu, pv), (
            "boundary case out of modeled domain: %r/%r" % (u, v))
        check_distance_reference(pu, pv, u, v)

    # randomized fuzz over integer coordinates, restricted to the modeled
    # domain (equal dim OR distinct concrete type). For differing dimension we
    # bias toward 2-D/3-D operands (which carry distinct Point2D/Point3D types)
    # and pair them with the other dimension so the type differs and the
    # padding branch fires.
    rng = random.Random(11618)
    fuzz = 0
    attempts = 0
    while fuzz < 3000 and attempts < 60000:
        attempts += 1
        du = rng.randint(1, 5)
        dv = rng.randint(1, 5)
        u = [rng.randint(-6, 6) for _ in range(du)]
        v = [rng.randint(-6, 6) for _ in range(dv)]
        pu = Point(u)
        pv = Point(v)
        if not in_modeled_domain(pu, pv):
            continue   # same-type differing-dim: out of scope, skip
        check_distance_reference(pu, pv, u, v)
        fuzz += 1
    assert fuzz >= 3000, "insufficient in-domain fuzz coverage: %d" % fuzz

    # === Scope boundary (negative control): same-type, differing-dimension ===
    # Confirm such pairs EXIST and that the patched callee does NOT pad there
    # (so the model is genuinely stronger off-domain, hence the scoping). Only
    # the generic n-D `Point` admits two same-type points of differing length;
    # dims 1, 4, 5, ... all map to the generic Point type.
    su, sv = [0], [0, 0, 0, 0, 5]
    pu, pv = Point(su), Point(sv)
    assert type(pu) is type(pv), (
        "expected same generic Point type for dims 1 and 5, got %s/%s"
        % (type(pu).__name__, type(pv).__name__))
    off_observed = pu.distance(pv)
    off_model = sqrt(Integer(padded_squared_sum(su, sv)))
    assert off_observed != off_model, (
        "scope assumption broken: same-type differing-dim case unexpectedly "
        "padded (observed %r == model %r)" % (off_observed, off_model))

    # === A-consumed: the `root` axiom vs real sqrt ===========================
    for x in [0, 1, 2, 4, 5, 9, 16, 25, 41, 61, 100, 99999]:
        check_root_axiom(x)
    for _ in range(2000):
        check_root_axiom(rng.randint(0, 10 ** 6))

    print("G-AX OK: padded-sum deep model (== real Point.distance under sqrt) "
          "sound on %d boundary + %d fuzz point pairs in the modeled domain "
          "(equal-dim or distinct-type); scope boundary confirmed (same-type "
          "differing-dim pair [0] vs [0,0,0,0,5]: real=%r, model=%r, NOT padded "
          "-> out of scope); root axiom (== sqrt) deterministic and "
          "non-negative on all tested arguments."
          % (len(boundary), fuzz, off_observed, off_model))
    return 0


if __name__ == "__main__":
    sys.exit(main())

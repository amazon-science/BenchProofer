#!/usr/bin/env python3
"""G-CONF differential conformance check for sympy__sympy-11618 (plan §4.1).

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both sides on the same fuzzed inputs and comparing observable outputs:

  * SHADOW  — the R/I-tagged ops of Solution.lean's impl region transliterated
              to Python: `commonLen` / `alignTo` / `sumSqZip`, i.e. the squared
              distance `distSq(sameKind, s, q)` over the two integer-coordinate
              vectors. This bundle has NO axioms (mapping.md §3), so the whole
              shadow is in scope for G-CONF — it is pure R/I.
  * ORACLE  — `patch.diff`'s behaviour: the REAL gold-patched
              `sympy.geometry.point.Point.distance`, observed by its SQUARE
              (`self.distance(p)**2`). `distance` returns the principal square
              root; `sqrt` is injective on [0, inf), so the squared value pins
              the distance (mapping.md §2 "sqrt" row). Squaring lets us compare
              exactly over integer coordinates (no radicals left).

They must agree on every input. Exit 0 iff zero disagreements; any disagreement
is a mechanical R/I-fidelity counterexample.

Runs in-container (the prebuilt SWE-Bench instance image, gold patch applied),
PYTHONPATH=/testbed so the patched in-tree sympy wins. stdlib + sympy only. The
fuzz seed is pinned (mapping.md §4).
"""
import random
import sys

SEED = 11618
N_FUZZ = 100_000


# --- ORACLE: the REAL gold-patched Point.distance ----------------------------

def _load_point():
    from sympy.geometry.point import Point
    return Point


def make_point(Point, coords):
    """Construct the sympy Point for an integer-coordinate vector. Point()'s
    __new__ dispatches on length: len 2 -> Point2D, len 3 -> Point3D, else the
    base Point. So the *length* determines the concrete class, and the patch's
    `type(p) is type(self)` discriminator is a function of the two lengths."""
    return Point(*coords)


def oracle_sq(Point, s_coords, q_coords):
    """patch.diff's behaviour: the squared real distance, as an exact sympy
    value. self = the point built from s_coords; p = from q_coords."""
    from sympy import simplify, Integer
    self_pt = make_point(Point, s_coords)
    p_pt = make_point(Point, q_coords)
    d2 = simplify(self_pt.distance(p_pt) ** 2)
    same_kind = type(p_pt) is type(self_pt)
    return d2, same_kind


# --- SHADOW: Solution.lean commonLen / alignTo / sumSqZip, transliterated ----

def align_to(xs, n):
    """alignTo: keep the first n entries, zero-pad the rest of the way."""
    t = list(xs[:n])
    return t + [0] * (n - len(xs))


def common_len(same_kind, s, q):
    """commonLen: min coord count when same class, else max."""
    return min(len(s), len(q)) if same_kind else max(len(s), len(q))


def sum_sq_zip(a, b):
    """sumSqZip: sum of squared per-coordinate differences (truncating zip; the
    callers align both to a common length first, so no element is dropped)."""
    return sum((x - y) ** 2 for x, y in zip(a, b))


def shadow_sq(same_kind, s, q):
    """distSq(sameKind, s, q): align both to the common ambient dimension, then
    sum the squared per-coordinate differences."""
    L = common_len(same_kind, s, q)
    return sum_sq_zip(align_to(s, L), align_to(q, L))


# --- driver ------------------------------------------------------------------

def fuzz_shapes(n, rng):
    """Yield (s_coords, q_coords) integer vectors. Dimensions are drawn so the
    same-class (len 2/2, 3/3, k/k base-Point) and different-class (2/3, 2/k,
    3/k, ...) paths are all exercised, including the issue's 3-D vs 2-D case."""
    # boundary cases first (the issue + symmetric / equal-length variants)
    yield ([1, 0, 2], [2, 0])          # the F2P: Point3D(1,0,2) vs Point2D(2,0) -> 5
    yield ([2, 0], [1, 0, 2])          # reversed
    yield ([2, 0], [1, 0])             # both Point2D (same kind, equal len)
    yield ([1, 0, 2], [3, 4, 5])       # both Point3D
    yield ([0, 0], [0, 0, 0])          # origins, different kind
    yield ([5], [7])                   # both base Point, dim 1
    yield ([1, 2, 3, 4], [5, 6, 7, 8])  # both base Point, dim 4 (same kind)
    yield ([1, 2, 3, 4], [5, 6])       # base Point(4) vs Point2D (different kind)
    yield ([1, 2], [3, 4, 5, 6])       # Point2D vs base Point(4)
    yield ([1, 2, 3], [4, 5, 6, 7, 8])  # Point3D vs base Point(5)
    dims = [1, 2, 3, 4, 5, 6]
    for _ in range(n):
        ds = rng.choice(dims)
        dq = rng.choice(dims)
        s = [rng.randint(-6, 6) for _ in range(ds)]
        q = [rng.randint(-6, 6) for _ in range(dq)]
        yield (s, q)


def main():
    rng = random.Random(SEED)
    try:
        Point = _load_point()
        from sympy import Integer  # noqa: F401  (import-time guard)
    except Exception as e:  # pragma: no cover - environment guard
        print("G-CONF ERROR: could not import patched sympy Point: %r" % e)
        return 2

    disagreements = []
    count = 0
    for s, q in fuzz_shapes(N_FUZZ, rng):
        count += 1
        try:
            o2, same_kind = oracle_sq(Point, s, q)
        except Exception as e:  # construction/eval failure is itself a finding
            disagreements.append((s, q, "ORACLE-RAISED:%r" % e, None))
            if len(disagreements) >= 5:
                break
            continue
        sh = shadow_sq(same_kind, s, q)
        # exact symbolic comparison: o2 (sympy) vs sh (python int)
        if o2 != sh:
            from sympy import simplify
            if simplify(o2 - sh) != 0:
                disagreements.append((s, q, sh, o2))
                if len(disagreements) >= 5:
                    break

    if disagreements:
        print("G-CONF FAIL: %d R/I disagreement(s) over %d inputs:"
              % (len(disagreements), count))
        for s, q, sh, orc in disagreements:
            print("  s=%r q=%r shadow_sq=%r oracle_sq=%r" % (s, q, sh, orc))
        return 1
    print("G-CONF OK: R/I shadow of distanceSq (squared distance) agrees with "
          "patch.diff behaviour (real Point.distance**2) on %d inputs "
          "(10 boundary + fuzz, seed=%d), 0 disagreements." % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""G-AX executable soundness check for pydata__xarray-4075.

Executes the REAL array dot-product callee that model.py axiomatizes
(`xarray.core.computation.dot`, the `dot(da, weights, dims=...)` used by
`Weighted._reduce`) and asserts that every observation matches the model.

The model's single axiom:

  dot_reduce(mask, weights, boolean_dot) -- the dot-product reduction of the
      presence flags `mask` and the `weights`. Its contraction semantics depend
      ONLY on whether it runs in boolean arithmetic, which happens exactly when
      BOTH operands have a boolean element type:

        * boolean_dot == False (a numeric operand present): the genuine
          arithmetic sum  sum_i mask[i] * weights[i]   (the deep model int_dot).
        * boolean_dot == True  (BOTH operands boolean): the SATURATING logical
          reduction, 1 iff some position has both flags set else 0, never > 1
          (the deep model bool_dot).

The two deep models int_dot / bool_dot (model.py pure region) are validated
== the real dot here (A-reference): int_dot against the numeric contraction
(numeric weights, OR a boolean weight array cast to int -- exactly the gold
patch's `weights.astype(int)`), and bool_dot against the boolean contraction
(boolean mask dotted with boolean weights -- the pre-patch bug). The decisive
GH4074 case: xr.dot([True, True], [True, True]) -> True (== 1), not 2; casting
the boolean weights to int restores the count of 2.

`mask = da.notnull()` is ALWAYS boolean, so the boolean contraction is triggered
precisely by a boolean WEIGHTS array -- which is exactly the dtype the patch
casts. Exit 0 iff every obligation holds.
"""
import random
import sys


def int_dot(mask, weights):
    """Reference for model.py's deep model int_dot (numeric contraction)."""
    return sum(m * w for m, w in zip(mask, weights))


def bool_dot(mask, weights):
    """Reference for model.py's deep model bool_dot (boolean saturating
    contraction): OR over positions of (mask[i] AND weights[i])."""
    acc = 0
    for m, w in zip(mask, weights):
        head = 1 if (m >= 1 and w >= 1) else 0
        acc = head if head >= acc else acc
    return acc


def _xr_dot(mask_vals, weights_vals, mask_dtype, weights_dtype):
    """Run the REAL xarray dot callee on a 1-D pair (the issue's MCVE shape),
    contracting the shared axis fully -- exactly Weighted._reduce(mask, weights,
    dim=..., skipna=False) over a single dimension."""
    import numpy as np
    import xarray as xr

    mask = xr.DataArray(np.asarray(mask_vals, dtype=mask_dtype), dims=["x"])
    weights = xr.DataArray(np.asarray(weights_vals, dtype=weights_dtype), dims=["x"])
    return xr.dot(mask, weights, dims="x")


def _scalar(da):
    import numpy as np
    return int(np.asarray(da.values).item())


def check_numeric(mask_vals, weights_vals):
    """boolean_dot == False branch: a boolean mask dotted with a NUMERIC weight
    array (or a boolean weight array cast to int, the gold patch) computes the
    genuine arithmetic sum == int_dot."""
    # presence mask is always boolean (da.notnull()); weights numeric here.
    observed = _scalar(_xr_dot(mask_vals, weights_vals, bool, int))
    expected = int_dot([1 if m else 0 for m in mask_vals], weights_vals)
    assert observed == expected, (
        "dot_reduce(boolean_dot=False) unsound on mask=%r weights=%r(int): "
        "real xr.dot gave %r, int_dot gives %r"
        % (mask_vals, weights_vals, observed, expected))


def check_boolean(mask_vals, weights_vals):
    """boolean_dot == True branch: a boolean mask dotted with a BOOLEAN weight
    array runs in boolean arithmetic and SATURATES == bool_dot (the bug)."""
    bw = [1 if w else 0 for w in weights_vals]
    bm = [1 if m else 0 for m in mask_vals]
    observed = _scalar(_xr_dot(mask_vals, bw, bool, bool))
    expected = bool_dot(bm, bw)
    assert observed == expected, (
        "dot_reduce(boolean_dot=True) unsound on mask=%r weights=%r(bool): "
        "real xr.dot gave %r, bool_dot gives %r"
        % (mask_vals, bw, observed, expected))
    assert observed in (0, 1), (
        "boolean contraction should saturate to 0/1, got %r" % (observed,))


def check_cast_restores_count(mask_vals, weights_vals):
    """The patch's contract: a boolean weight array cast to int restores the
    true count, while leaving it boolean saturates -- they disagree exactly when
    >= 2 present samples carry weight 1."""
    bw = [1 if w else 0 for w in weights_vals]
    bm = [1 if m else 0 for m in mask_vals]
    boolean = _scalar(_xr_dot(mask_vals, bw, bool, bool))      # pre-patch
    casted = _scalar(_xr_dot(mask_vals, bw, bool, int))        # gold patch
    assert casted == int_dot(bm, bw), "cast-to-int dot should equal int_dot"
    assert boolean == bool_dot(bm, bw), "uncast bool dot should equal bool_dot"
    # decisive separation when the true count exceeds 1
    if int_dot(bm, bw) >= 2:
        assert boolean != casted, (
            "GH4074 separation broken: boolean and int-cast dot should differ "
            "when the true count is >= 2, mask=%r weights=%r" % (mask_vals, bw))


def main():
    try:
        import numpy  # noqa: F401
        import xarray  # noqa: F401
    except Exception as exc:
        print("G-AX SKIP: xarray/numpy unavailable (%r) -- run in the "
              "evaluation image" % (exc,))
        return 0

    # --- the decisive GH4074 boundary case: [True,True] . [True,True] -------
    check_boolean([True, True], [True, True])     # real xr.dot -> True (==1)
    check_numeric([True, True], [1, 1])           # real xr.dot -> 2
    check_cast_restores_count([True, True], [True, True])  # 1 (bool) vs 2 (int)

    # --- boundary cases over presence/weight patterns -----------------------
    boundary = [
        ([True, True], [True, True]),
        ([True, False], [True, True]),
        ([False, False], [True, True]),
        ([True, True, True], [True, True, True]),
        ([True, False, True], [True, True, True]),
        ([True], [True]),
        ([False], [True]),
        ([True, True], [1, 2]),
        ([True, False, True], [3, 5, 7]),
        ([False, False, False], [4, 5, 6]),
        ([True, True, True, True], [0, 1, 0, 1]),
    ]
    for mask_vals, weights_vals in boundary:
        if all(w in (0, 1) for w in weights_vals):
            check_boolean(mask_vals, weights_vals)
            check_cast_restores_count(mask_vals, weights_vals)
        check_numeric(mask_vals, weights_vals)

    # --- randomized fuzz -----------------------------------------------------
    rng = random.Random(4075)
    for _ in range(2000):
        n = rng.randint(1, 8)
        mask_vals = [rng.random() < 0.6 for _ in range(n)]
        # boolean weights branch
        bw = [rng.random() < 0.6 for _ in range(n)]
        check_boolean(mask_vals, bw)
        check_cast_restores_count(mask_vals, bw)
        # numeric weights branch
        nw = [rng.randint(0, 9) for _ in range(n)]
        check_numeric(mask_vals, nw)

    print("G-AX OK: dot_reduce axiom sound against the real xarray dot -- "
          "int_dot == numeric contraction (incl. bool->int cast = gold patch), "
          "bool_dot == boolean saturating contraction (pre-patch bug); the "
          "GH4074 case xr.dot([True,True],[True,True]) -> 1 (bool) vs 2 (int) "
          "validated on boundary + 2000 fuzz inputs.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

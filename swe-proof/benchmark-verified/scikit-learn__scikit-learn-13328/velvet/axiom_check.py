#!/usr/bin/env python3
"""G-AX executable soundness check for scikit-learn__scikit-learn-13328.

Validates the single kind-A leg of refinement.md: the **A-reference** deep model
`resolveElemType` (Solution.lean `pure` region) against the REAL unchanged callee
`sklearn.utils.check_array`, invoked with the element-type request the gold patch
adds — `dtype=[np.float64, np.float32]`.

`resolveElemType` (the deep model):

    resolveElemType(orig) = orig            if orig in {float64, float32}
                          = float64          otherwise

Soundness claim (A-reference): for every input element type `orig`, the element
type of the array returned by

    check_array(X, dtype=[np.float64, np.float32], ...)         # X.dtype == orig

equals `resolveElemType(orig)` under the mapping.md §2 bijection, and is always a
floating type (the property the fix guarantees and `resolveElemType_isFloating`
encodes).

We exercise every `DType` category modeled in Solution.lean (boundary) plus
randomized fuzz matrices, on both the 2-D `ensure_2d=True` path the real
`HuberRegressor.fit` uses and the flat 1-D path (`ensure_2d=False`) to confirm
the resolution is shape-independent.

Imports only `numpy` and the unchanged repo callee `sklearn.utils.check_array`
(the same routine the gold patch's `check_X_y` forwards `dtype` to). Runs
in-container against the prebuilt instance image. Exit 0 iff every obligation
holds.
"""
import random
import sys

import numpy as np

from sklearn.utils import check_array


# --- Solution.lean `pure` region, transliterated (kept in lock-step) ---------
# DType bijection (mapping.md §2): the np.dtype categories the resolution
# distinguishes, each mapped to a representative concrete numpy dtype.
DTYPE_CATEGORIES = {
    "f64": np.float64,
    "f32": np.float32,
    "f16": np.float16,
    "boolean": np.bool_,
    "integer": np.int64,
    "object": np.object_,
}

ACCEPTED = {"f64", "f32"}          # DType.isAccepted
FLOATING = {"f64", "f32", "f16"}   # DType.isFloating


def resolve_elem_type(cat):
    """Reference of Solution.lean `resolveElemType` over DType categories."""
    return cat if cat in ACCEPTED else "f64"


def category_of(np_dtype):
    """The mapping.md §2 bijection: a resolved np.dtype -> DType category."""
    kind = np_dtype.kind
    if kind == "f":
        if np_dtype == np.dtype(np.float64):
            return "f64"
        if np_dtype == np.dtype(np.float32):
            return "f32"
        if np_dtype == np.dtype(np.float16):
            return "f16"
        return "other-float"
    if kind == "b":
        return "boolean"
    if kind in "iu":
        return "integer"
    if kind == "O":
        return "object"
    return "other:%s" % kind


def make_matrix(cat, n_rows, n_cols, rng):
    """A small matrix whose element type is the given DType category."""
    np_dtype = DTYPE_CATEGORIES[cat]
    if cat == "object":
        # object array of python floats (numeric-coercible, as the real X is)
        a = np.empty((n_rows, n_cols), dtype=object)
        for i in range(n_rows):
            for j in range(n_cols):
                a[i, j] = float(rng.uniform(-3, 3))
        return a
    if cat == "boolean":
        return (rng.integers(0, 2, size=(n_rows, n_cols)) > 0).astype(np_dtype)
    if cat == "integer":
        return rng.integers(-5, 5, size=(n_rows, n_cols)).astype(np_dtype)
    return rng.uniform(-3, 3, size=(n_rows, n_cols)).astype(np_dtype)


REQUEST = [np.float64, np.float32]      # the dtype argument the gold patch adds


def check_one(cat, X, ensure_2d):
    """Assert real check_array's resolved element type == resolveElemType(cat),
    and that it is floating."""
    out = check_array(X, dtype=REQUEST, ensure_2d=ensure_2d,
                      accept_sparse=["csr"], copy=False)
    observed = category_of(out.dtype)
    expected = resolve_elem_type(cat)
    assert observed == expected, (
        "resolveElemType A-reference unsound on input dtype %r (cat=%s, "
        "ensure_2d=%s): real check_array resolved to %r (cat=%s), deep model "
        "requires %s" % (np.dtype(DTYPE_CATEGORIES[cat]), cat, ensure_2d,
                         out.dtype, observed, expected))
    assert observed in FLOATING, (
        "fix-guarantee violated: resolved element type %s on input cat=%s is "
        "not floating" % (observed, cat))


def main():
    rng = np.random.default_rng(13328)
    pyrng = random.Random(13328)

    cats = list(DTYPE_CATEGORIES.keys())

    # --- boundary: every DType category, several shapes -----------------------
    n_boundary = 0
    for cat in cats:
        for (r, c) in [(1, 1), (1, 3), (5, 2), (10, 4), (200, 2)]:
            X = make_matrix(cat, r, c, rng)
            check_one(cat, X, ensure_2d=True)
            n_boundary += 1
        # 1-D path (shape independence)
        X1 = make_matrix(cat, 1, 8, rng).reshape(-1)
        check_one(cat, X1, ensure_2d=False)
        n_boundary += 1

    # --- randomized fuzz ------------------------------------------------------
    n_fuzz = 4000
    for _ in range(n_fuzz):
        cat = pyrng.choice(cats)
        r = pyrng.randint(1, 30)
        c = pyrng.randint(1, 6)
        X = make_matrix(cat, r, c, rng)
        check_one(cat, X, ensure_2d=True)

    print("G-AX OK: resolveElemType deep model (== real check_array under "
          "dtype=[float64,float32]) sound and floating-guaranteed on %d "
          "boundary + %d fuzz matrices across %d DType categories"
          % (n_boundary, n_fuzz, len(cats)))
    return 0


if __name__ == "__main__":
    sys.exit(main())

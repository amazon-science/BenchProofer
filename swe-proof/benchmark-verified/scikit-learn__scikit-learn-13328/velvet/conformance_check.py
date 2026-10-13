#!/usr/bin/env python3
"""G-CONF differential conformance check for scikit-learn__scikit-learn-13328.

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both sides on the same fuzzed inputs and comparing observable outputs:

  * SHADOW  — the R/I-tagged ops of Solution.lean's impl region transliterated
              to Python over the real repo type (a numpy matrix), via the
              mapping.md §2 bijection (np.dtype <-> DType). The impl computes
                  accepted = orig in {float64, float32}
                  out      = orig if accepted else float64
              i.e. the concrete `if orig.isAccepted then orig else f64` ladder.
  * ORACLE  — patch.diff's behaviour: the patched `HuberRegressor.fit` input
              validation, i.e. exactly the call the gold patch produces:
                  check_X_y(X, y, copy=False, accept_sparse=['csr'],
                            y_numeric=True, dtype=[np.float64, np.float32])
              We observe the element type of the returned X.

They must agree on every input element type. Exit 0 iff zero disagreements; any
disagreement is a mechanical R/I-fidelity counterexample.

Runs in-container (the prebuilt SWE-Bench instance image), against the repo at
base_commit with patch.diff applied (the harness applies it before this runs).
numpy + sklearn only. The fuzz seed is pinned (mapping.md §4) for a
deterministic verdict.
"""
import random
import sys

import numpy as np

from sklearn.utils import check_X_y

SEED = 13328
N_FUZZ = 100_000

DTYPE_CATEGORIES = {
    "f64": np.float64,
    "f32": np.float32,
    "f16": np.float16,
    "boolean": np.bool_,
    "integer": np.int64,
    "object": np.object_,
}
ACCEPTED = {"f64", "f32"}

REQUEST = [np.float64, np.float32]


def shadow_resolve(cat):
    """The R/I shadow: Solution.lean's `if orig.isAccepted then orig else f64`
    over DType categories. Returns the resolved DType category."""
    return cat if cat in ACCEPTED else "f64"


def category_of(np_dtype):
    """mapping.md §2 bijection: a resolved np.dtype -> DType category."""
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
    np_dtype = DTYPE_CATEGORIES[cat]
    if cat == "object":
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


def oracle_resolve(X):
    """patch.diff's behaviour: the patched fit's input-validation call.
    Returns the resolved DType category of the validated X."""
    y = np.arange(X.shape[0], dtype=np.float64)
    Xo, _ = check_X_y(X, y, copy=False, accept_sparse=["csr"],
                      y_numeric=True, dtype=REQUEST)
    return category_of(Xo.dtype)


def fuzz_inputs(n, rng, pyrng):
    cats = list(DTYPE_CATEGORIES.keys())
    # boundary first: every category, a few shapes
    for cat in cats:
        for (r, c) in [(1, 1), (2, 1), (3, 2), (5, 4)]:
            yield cat, r, c
    for _ in range(n):
        yield pyrng.choice(cats), pyrng.randint(1, 20), pyrng.randint(1, 5)


def main():
    rng = np.random.default_rng(SEED)
    pyrng = random.Random(SEED)
    disagreements = []
    count = 0
    for cat, r, c in fuzz_inputs(N_FUZZ, rng, pyrng):
        count += 1
        X = make_matrix(cat, r, c, rng)
        shadow = shadow_resolve(cat)
        oracle = oracle_resolve(X)
        if shadow != oracle:
            disagreements.append((cat, r, c, shadow, oracle))
            if len(disagreements) >= 5:
                break
    if disagreements:
        print("G-CONF FAIL: %d R/I disagreement(s) over %d inputs:"
              % (len(disagreements), count))
        for cat, r, c, sh, orc in disagreements:
            print("  input_cat=%s shape=(%d,%d) shadow=%s oracle=%s"
                  % (cat, r, c, sh, orc))
        return 1
    print("G-CONF OK: R/I shadow of validatedElementType agrees with patch.diff "
          "behaviour on %d inputs (seed=%d), 0 disagreements." % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())

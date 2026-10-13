#!/usr/bin/env python3
"""G-AX executable soundness check for scikit-learn__scikit-learn-25102.

Executes the REAL column-projection callee `sklearn.utils._safe_indexing(X,
mask, axis=1)` (the post-patch projector used by `SelectorMixin._transform`) on
pandas DataFrames carrying heterogeneous per-column dtypes, under boolean masks
(boundary masks over the dtype space + randomized fuzz), and asserts that every
observation matches the deep model `selectMasked` / `keptCol` of Solution.lean.

The single kind-A check (A-reference):

  (A-reference) the deep model `selectMasked` (Solution.lean pure region) ==
      the real `_safe_indexing(X, mask, axis=1)` per-column dtypes, IN ORDER.
      The changed projection is modeled DEEPLY, not behind a consumed axiom;
      G-AX validates that deep model against the real callee:
        kept column (mask bit True)  -> contributes its OWN dtype, unchanged
        dropped column (mask bit False) -> contributes nothing
        no column kept -> empty 0-column frame  (the DataFrame `iloc[:, :0]` path)

Contrast clause (non-vacuity): the PRE-patch path `np.asarray(X)[:, mask]`
collapses every kept column to one homogeneous dtype, so the modeled change
(per-column dtype preservation) is real, not vacuous.

Imports pandas / numpy and the real `sklearn.utils._safe_indexing` — the same
callee the gold patch invokes. Exit 0 iff every obligation holds.
"""
import random
import sys

import numpy as np
import pandas as pd

from sklearn.utils import _safe_indexing


# --- the dtype universe: distinct dtypes <-> distinct integer codes ----------
# (mapping.md §2: equality of codes <-> equality of dtypes, the only relation
# the F2P tests observe). Each builder makes a length-n column of that dtype.
def _cat_col(n, rng):
    cats = ["a", "b", "j", "x", "z"]
    return pd.Series([rng.choice(cats) for _ in range(n)], dtype="category")

_DTYPE_SPECS = [
    ("float16", lambda n, rng: pd.Series(np.arange(n), dtype=np.float16)),
    ("float32", lambda n, rng: pd.Series(np.arange(n), dtype=np.float32)),
    ("float64", lambda n, rng: pd.Series(np.arange(n), dtype=np.float64)),
    ("int64",   lambda n, rng: pd.Series(np.arange(n), dtype=np.int64)),
    ("int32",   lambda n, rng: pd.Series(np.arange(n), dtype=np.int32)),
    ("bool",    lambda n, rng: pd.Series([(i % 2 == 0) for i in range(n)], dtype=bool)),
    ("category", _cat_col),
]
# A stable code per dtype *string* (its identity). category gets its own code.
_CODE = {name: i for i, (name, _) in enumerate(_DTYPE_SPECS)}


def _dtype_code(dtype):
    """Map a realized pandas dtype back to its integer identity code."""
    name = str(dtype)
    if name == "category" or isinstance(dtype, pd.CategoricalDtype):
        return _CODE["category"]
    return _CODE[name]


# --- the deep model (Solution.lean pure region), transliterated --------------
def kept_col(p):
    """keptCol (p : Int x Bool) : List Int."""
    code, keep = p
    return [code] if keep else []


def select_masked(cols):
    """selectMasked : List (Int x Bool) -> List Int (front-recursive concat)."""
    out = []
    for p in cols:
        out.extend(kept_col(p))
    return out


# --- real callee observation -------------------------------------------------
def real_projection_codes(df, mask):
    """The post-patch projector's per-column dtype codes, in order.

    `_safe_indexing(X, mask, axis=1)` is what `_transform` calls. For the
    no-column-kept case the patch uses `X.iloc[:, :0]`; `_safe_indexing` with an
    all-False boolean mask returns exactly that 0-column frame, so it models
    both arms of the patched `_transform`."""
    out = _safe_indexing(df, np.asarray(mask, dtype=bool), axis=1)
    return [_dtype_code(out.dtypes.iloc[j]) for j in range(out.shape[1])]


def prepatch_homogeneous_codes(df, mask):
    """The PRE-patch ndarray path np.asarray(X)[:, mask]: every kept column is
    emitted with one homogeneous dtype. Used only to confirm the modeled change
    is non-vacuous (the bug really collapses dtypes)."""
    arr = np.asarray(df)                       # homogenizes to one dtype
    sel = arr[:, np.asarray(mask, dtype=bool)]
    homo = _dtype_code(pd.Series(sel.ravel()).dtype) if sel.shape[1] else None
    return [homo] * sel.shape[1]


def build_frame(dtype_names, n, rng):
    data = {}
    for j, name in enumerate(dtype_names):
        builder = dict(_DTYPE_SPECS)[name]
        data["col%d" % j] = builder(n, rng)
    return pd.DataFrame(data)


def check(df, mask, dtype_names):
    cols = [(_CODE[name], bool(b)) for name, b in zip(dtype_names, mask)]
    expected = select_masked(cols)                 # deep model
    observed = real_projection_codes(df, mask)     # real callee
    assert observed == expected, (
        "selectMasked deep model unsound: dtypes=%r mask=%r -> real %r, "
        "model %r" % (dtype_names, mask, observed, expected))


def main():
    rng = random.Random(25102)
    names = [n for n, _ in _DTYPE_SPECS]

    # --- boundary masks over a frame holding one column of every dtype -------
    n = 5
    all_names = names[:]                            # one of each dtype
    df = build_frame(all_names, n, rng)
    k = len(all_names)
    boundary_masks = []
    boundary_masks.append([True] * k)               # keep all
    boundary_masks.append([False] * k)              # keep none (empty path)
    for j in range(k):                              # exactly one kept
        m = [False] * k; m[j] = True; boundary_masks.append(m)
    for j in range(k):                              # exactly one dropped
        m = [True] * k; m[j] = False; boundary_masks.append(m)
    boundary_masks.append([j % 2 == 0 for j in range(k)])   # alternating
    boundary_masks.append([j % 2 == 1 for j in range(k)])
    for m in boundary_masks:
        check(df, m, all_names)

    # non-vacuity: with >=2 distinct kept dtypes the pre-patch path collapses
    # them while the real projector preserves them. The contrast is exhibited on
    # a *numeric-only* heterogeneous frame (the issue's own float16/float64 ->
    # float64 collapse): `np.asarray` of a frame carrying a non-numeric column
    # (e.g. a string `category`) yields an `object` ndarray, which is not a
    # dtype the F2P assertions range over and has no homogeneous numeric code —
    # so the pre-patch ndarray contrast is only meaningful over numeric dtypes.
    # (The deep-model soundness loop above and below still ranges over the full
    # dtype universe incl. category/bool via the real `_safe_indexing` callee,
    # which projects columns without any numeric coercion.)
    numeric_names = ["float16", "float32", "float64", "int64", "int32"]
    cdf = build_frame(numeric_names, n, rng)
    ck = len(numeric_names)
    hetero_mask = [True] * ck
    preserved = real_projection_codes(cdf, hetero_mask)
    collapsed = prepatch_homogeneous_codes(cdf, hetero_mask)
    assert len(set(preserved)) >= 2, "expected heterogeneous preserved dtypes"
    assert len(set(collapsed)) == 1, (
        "expected pre-patch path to collapse to one dtype, got %r" % (collapsed,))
    assert preserved != collapsed, (
        "modeled change is vacuous: preserve == collapse (%r)" % (preserved,))

    # --- randomized fuzz: random frame widths, dtypes, masks -----------------
    for _ in range(20000):
        width = rng.randint(1, 8)
        dtype_names = [rng.choice(names) for _ in range(width)]
        nrows = rng.randint(1, 6)
        frame = build_frame(dtype_names, nrows, rng)
        mask = [rng.random() < 0.5 for _ in range(width)]
        check(frame, mask, dtype_names)

    print("G-AX OK: selectMasked deep model (== real _safe_indexing(X, mask, "
          "axis=1) per-column dtypes) sound on %d boundary + 20000 fuzz frames; "
          "pre-patch ndarray path confirmed to collapse heterogeneous dtypes "
          "(modeled change non-vacuous)." % (len(boundary_masks),))
    return 0


if __name__ == "__main__":
    sys.exit(main())

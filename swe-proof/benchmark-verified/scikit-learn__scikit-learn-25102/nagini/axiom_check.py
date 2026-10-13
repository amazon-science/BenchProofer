#!/usr/bin/env python3
"""G-AX executable soundness check for scikit-learn__scikit-learn-25102.

This bundle consumes NO `@ContractOnly` axiom: the changed operation is a pure
per-column selection over a tabular container's row labels (index) and per-
column descriptors (dtypes), modelled DEEPLY by `select_columns` in model.py
(`kept_descs` is the column-compress; the row labels are carried over). G-AX
therefore validates the *behavioural facts the deep model rests on* against the
REAL runtime semantics the patched code uses — the post-patch `_transform`
column-selection in sklearn/feature_selection/_base.py.

The real POST-patch `_transform`, on the branches the model covers, is:

    mask = self.get_support()
    if not mask.any():
        ...warn...
        if hasattr(X, "iloc"):
            return X.iloc[:, :0]           # dataframe: keep index, 0 columns
        return np.empty(0, dtype=X.dtype).reshape((X.shape[0], 0))
    return _safe_indexing(X, mask, axis=1) # dataframe: keep per-column dtype + index

The PRE-patch `_transform` instead did, for the non-empty case:

    return X[:, safe_mask(X, mask)]        # numpy: homogenises ALL column dtypes

and, for the empty case, `np.empty(0, dtype=X.dtype)` — which on a DataFrame
references the non-existent `.dtype` attribute (DataFrames expose `.dtypes`),
losing the dataframe nature / index entirely.

G-AX runs the REAL `_safe_indexing` over real pandas DataFrames with mixed
per-column dtypes and asserts, over a boundary battery + randomized fuzz:

  (1) DEEP-MODEL FIDELITY. The deep model `select_columns` (re-expressed here in
      plain Python, identical control/data flow — `kept_descs` is the compress
      of the per-column dtype codes by the boolean mask, the index is carried
      over) yields the same resulting (index labels, per-column dtypes) as the
      real post-patch column selection, for non-empty AND empty masks, on
      DataFrames with heterogeneous dtypes and non-trivial indices.

  (2) DISCRIMINATING DIVERGENCE. The pre-patch numpy selection
      `X.values[:, mask]` homogenises the retained columns to a single common
      dtype, diverging from the deep model / post-patch on EXACTLY the
      heterogeneous-dtype case the F2P tests exercise and `model_prepatch.py`
      fails on (clause: output descriptors == compress of the input descriptors,
      each carried over). The empty-mask pre-patch path additionally fails to
      keep the dataframe's own index.

Imports only `pandas` / `numpy` and the standard library (present in the
instance's eval image — the very stack the patched code builds on) plus the
repo's own `_safe_indexing`, the unchanged callee the patch newly invokes.
Exit 0 iff every obligation holds.
"""
import random
import sys

import numpy as np
import pandas as pd

from sklearn.utils import _safe_indexing


# --- the deep model `select_columns`, re-expressed in plain Python -----------
# Mirrors model.py: a column is kept exactly when its mask flag is set, in input
# order, carrying over its OWN per-column descriptor (here: the dtype). The row
# labels (index) are carried over unchanged regardless of how many columns
# survive (including none). Returns (index_labels, kept_dtypes).

def kept_descs(dtypes, mask):
    """model.py's `kept_descs`: compress the per-column descriptors by the
    boolean mask, in input order (each kept descriptor is the column's own)."""
    return [d for d, m in zip(dtypes, mask) if m]


def model_select(df_index, df_dtypes, mask):
    out_index = list(df_index)                       # row labels preserved
    out_dtypes = kept_descs(df_dtypes, mask)         # per-column descriptors kept
    return out_index, out_dtypes


# --- the REAL post-patch column selection (the branches the model covers) ----

def real_postpatch(X, mask):
    if not mask.any():
        if hasattr(X, "iloc"):
            return X.iloc[:, :0]
        return np.empty(0, dtype=X.dtype).reshape((X.shape[0], 0))
    return _safe_indexing(X, mask, axis=1)


# --- the PRE-patch (buggy) column selection ----------------------------------

def real_prepatch(X, mask):
    # The empty branch references X.dtype (absent on a DataFrame) -> the bug.
    if not mask.any():
        return np.empty(0, dtype=X.dtype).reshape((X.shape[0], 0))
    # numpy boolean column indexing over .values: homogenises ALL dtypes.
    return X.values[:, mask]


# --- observation helpers ------------------------------------------------------

def labels(seq):
    return [str(x) for x in list(seq)]


def make_df(index, col_dtypes):
    """Build a DataFrame with the given index and per-column dtypes (a list of
    numpy/pandas dtype objects), one column per dtype."""
    n = len(index)
    data = {}
    for j, dt in enumerate(col_dtypes):
        name = "c%d" % j
        if str(dt) == "category":
            data[name] = pd.Series(
                [("a" if (k % 2 == 0) else "b") for k in range(n)],
                index=list(index), dtype="category")
        else:
            data[name] = pd.Series(
                np.arange(n).astype(dt), index=list(index))
    return pd.DataFrame(data, index=list(index))


# --- checks -------------------------------------------------------------------

def check_select_case(index, col_dtypes, mask):
    """Non-empty mask: deep model == real post-patch _safe_indexing."""
    df = make_df(index, col_dtypes)
    df_dtypes = list(df.dtypes)

    real = real_postpatch(df, np.asarray(mask, dtype=bool))
    assert hasattr(real, "iloc"), (
        "post-patch must keep the dataframe nature on a non-empty mask; got %r"
        % (type(real),))
    real_idx = labels(real.index)
    real_dtypes = list(real.dtypes)

    m_idx, m_dtypes = model_select(list(index), df_dtypes,
                                   [bool(b) for b in mask])
    m_idx = labels(m_idx)

    # (1a) row labels preserved
    assert m_idx == real_idx == labels(index), (
        "index disagreement (non-empty): index=%r mask=%r model=%r real=%r"
        % (index, mask, m_idx, real_idx))
    # (1b) per-column descriptors (dtypes) carried over, in input order
    assert [str(d) for d in m_dtypes] == [str(d) for d in real_dtypes], (
        "per-column dtype disagreement (non-empty): col_dtypes=%r mask=%r "
        "model=%r real=%r" % (col_dtypes, mask, m_dtypes, real_dtypes))


def check_empty_case(index, col_dtypes):
    """Empty mask: deep model == real post-patch (X.iloc[:, :0])."""
    df = make_df(index, col_dtypes)
    mask = np.zeros(len(col_dtypes), dtype=bool)

    real = real_postpatch(df, mask)
    assert hasattr(real, "iloc"), (
        "post-patch must keep the dataframe nature on an empty mask; got %r"
        % (type(real),))
    real_idx = labels(real.index)
    real_dtypes = list(real.dtypes)

    m_idx, m_dtypes = model_select(list(index), list(df.dtypes),
                                   [False] * len(col_dtypes))
    # row labels preserved; zero columns
    assert labels(m_idx) == real_idx == labels(index), (
        "index disagreement (empty): index=%r model=%r real=%r"
        % (index, labels(m_idx), real_idx))
    assert m_dtypes == [] and len(real_dtypes) == 0, (
        "empty mask must yield zero columns: model=%r real=%r"
        % (m_dtypes, real_dtypes))
    assert real.shape == (len(index), 0), (
        "empty mask must yield shape (n, 0); got %r" % (real.shape,))


def check_discriminating_divergence():
    """The pre-patch numpy selection homogenises the retained columns to one
    common dtype; the post-patch / deep model keep each column's own dtype. This
    is the heterogeneous-dtype case the F2P tests exercise and model_prepatch.py
    fails on. Also: the pre-patch empty branch loses the dataframe nature."""
    # heterogeneous dtypes: float32, category, float64
    index = [0, 1, 2]
    col_dtypes = [np.float32, "category", np.float64]
    df = make_df(index, col_dtypes)
    mask = np.array([True, True, True])

    post = real_postpatch(df, mask)
    post_dtypes = [str(d) for d in post.dtypes]
    assert post_dtypes == ["float32", "category", "float64"], (
        "post-patch must preserve each column's own dtype; got %r" % (post_dtypes,))

    pre = real_prepatch(df, mask)
    # numpy view: a single homogeneous dtype across all columns
    assert not hasattr(pre, "dtypes"), (
        "pre-patch numpy selection must NOT be a dataframe (homogenised)")
    common = str(pre.dtype)
    assert len({common}) == 1 and common != "category", (
        "pre-patch must homogenise to a single non-category dtype; got %r"
        % (common,))
    # divergence is observable: the deep model keeps 3 distinct descriptors,
    # the pre-patch collapses them to one.
    assert len(set(post_dtypes)) >= 2, (
        "the F2P heterogeneous case must have >=2 distinct dtypes to discriminate")

    # empty-mask pre-patch path on a DataFrame references the absent .dtype:
    empty_mask = np.zeros(3, dtype=bool)
    raised = False
    try:
        real_prepatch(df, empty_mask)
    except AttributeError:
        raised = True
    assert raised, (
        "pre-patch empty branch must reference the absent DataFrame.dtype "
        "attribute (losing the dataframe nature)")


def main():
    # ---- boundary battery: non-empty masks over heterogeneous dtypes ---------
    dtype_palettes = [
        [np.float32, np.float64],
        [np.float32, "category", np.float64],
        [np.int32, np.int64, np.float32, "category"],
        ["category", "category"],
        [np.float64],
    ]
    index_choices = [[0, 1, 2], [0, 1, 2, 3, 4], [10, 11, 12]]
    for palette in dtype_palettes:
        ncols = len(palette)
        for index in index_choices:
            # enumerate several non-trivial masks (not all-False)
            masks = []
            masks.append([True] * ncols)
            masks.append([k % 2 == 0 for k in range(ncols)])
            masks.append([k == ncols - 1 for k in range(ncols)])
            masks.append([k == 0 for k in range(ncols)])
            for mask in masks:
                if any(mask):
                    check_select_case(index, palette, mask)
        # empty mask for this palette
        check_empty_case([0, 1, 2], palette)

    # ---- the discriminating clause -------------------------------------------
    check_discriminating_divergence()

    # ---- randomized fuzz -----------------------------------------------------
    rng = random.Random(25102)
    base_dtypes = [np.float16, np.float32, np.float64, np.int32, np.int64,
                   "category"]
    fuzz = 0
    for _ in range(1500):
        ncols = rng.randint(1, 6)
        palette = [rng.choice(base_dtypes) for _ in range(ncols)]
        nrows = rng.randint(2, 6)
        index = list(range(nrows)) if rng.random() < 0.5 else \
            [100 + k for k in range(nrows)]
        mask = [rng.random() < 0.5 for _ in range(ncols)]
        if any(mask):
            check_select_case(index, palette, mask)
        else:
            check_empty_case(index, palette)
        fuzz += 1

    print("G-AX OK: deep model `select_columns` (kept_descs compress + index "
          "carry-over) matches the real post-patch _transform column selection "
          "(_safe_indexing axis=1 / X.iloc[:, :0]) over the boundary battery + "
          "%d fuzz configurations; each retained column keeps its OWN dtype and "
          "the dataframe's own index is preserved (incl. the empty-mask case). "
          "The pre-patch numpy selection homogenises ALL column dtypes (and its "
          "empty branch references the absent DataFrame.dtype) — diverging on "
          "EXACTLY the heterogeneous-dtype case model_prepatch.py fails on."
          % fuzz)
    return 0


if __name__ == "__main__":
    sys.exit(main())

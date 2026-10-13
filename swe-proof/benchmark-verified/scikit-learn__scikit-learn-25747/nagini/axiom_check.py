#!/usr/bin/env python3
"""G-AX executable soundness check for scikit-learn__scikit-learn-25747.

This bundle consumes NO `@ContractOnly` axiom: the changed operation is a pure
label-routing rule over a tabular container's row labels (index) and column
labels, modelled DEEPLY by `wrap_in_container` in model.py. G-AX therefore
validates the *behavioural facts the deep model rests on* against the REAL
runtime semantics the patched code uses — the post-patch
`_wrap_in_pandas_container` container-labelling logic.

The real post-patch helper (sklearn/utils/_set_output.py) is, on the branches
the model covers:

    if isinstance(data_to_wrap, pd.DataFrame):
        if columns is not None:
            data_to_wrap.columns = columns
        # (the supplied index is NO LONGER applied here)
        return data_to_wrap
    return pd.DataFrame(data_to_wrap, index=index, columns=columns)

The PRE-patch helper additionally executed, in the DataFrame branch:

        if index is not None:
            data_to_wrap.index = index          # the bug

G-AX reconstructs both helpers over real pandas objects (no sklearn import
needed — the logic is two `pd.DataFrame` attribute writes / a constructor) and
asserts, over a boundary battery + randomized fuzz:

  (1) DEEP-MODEL FIDELITY. The deep model `wrap_in_container` (re-expressed in
      plain Python here, identical control/data flow) yields the same resulting
      (index labels, column labels) as the real POST-patch helper, on:
        - already-a-DataFrame inputs (with/without a supplied index, with/without
          a supplied set of columns; supplied index of EQUAL or DIFFERENT length
          than the frame's own index — the aggregation case), and
        - not-a-DataFrame (ndarray) inputs (with/without index/columns).
  (2) DISCRIMINATING DIVERGENCE. The pre-patch helper diverges from the deep
      model / post-patch helper on EXACTLY the case the F2P test exercises and
      `model_prepatch.py` fails on: an already-a-DataFrame input plus a supplied
      index. There the post-patch result keeps the frame's OWN index while the
      pre-patch result overwrites it with the supplied index (and, when the
      lengths differ, the pre-patch write is the actual reported ValueError).

Imports only `pandas` / `numpy` (present in the instance's eval image — the
very stack the patched helper builds on) and the standard library. Exit 0 iff
every obligation holds.
"""
import random
import sys

import numpy as np
import pandas as pd


# --- the REAL post-patch DataFrame-labelling logic (verbatim branches) -------

def real_postpatch(data_to_wrap, columns, index):
    if isinstance(data_to_wrap, pd.DataFrame):
        if columns is not None:
            data_to_wrap.columns = columns
        # post-patch: the supplied index is intentionally NOT applied
        return data_to_wrap
    return pd.DataFrame(data_to_wrap, index=index, columns=columns)


# --- the PRE-patch (buggy) logic: also overwrites the frame's index ----------

def real_prepatch(data_to_wrap, columns, index):
    if isinstance(data_to_wrap, pd.DataFrame):
        if columns is not None:
            data_to_wrap.columns = columns
        if index is not None:
            data_to_wrap.index = index          # the bug
        return data_to_wrap
    return pd.DataFrame(data_to_wrap, index=index, columns=columns)


# --- the deep model `wrap_in_container`, re-expressed in plain Python --------
# Mirrors model.py: returns the resulting (index_labels, column_labels) pair.
# `nrows`/`ncols` are the data payload's row/column counts; in the not-a-frame
# branch an axis with NO supplied label set gets the default positional
# labelling range(nrows) / range(ncols) (matching model.py's `is_range`
# postconditions and pandas's default RangeIndex / column index).

def model_wrap(data_is_frame, df_index, df_columns, columns, index,
               nrows=0, ncols=0):
    if data_is_frame:
        out_columns = list(df_columns)
        if columns is not None:
            out_columns = list(columns)          # refresh column labels
        # the supplied index is NOT applied: keep the frame's own index
        out_index = list(df_index)
        return out_index, out_columns
    out_index = list(index) if index is not None else list(range(nrows))
    out_columns = list(columns) if columns is not None else list(range(ncols))
    return out_index, out_columns


# --- observation helpers ------------------------------------------------------

def labels(seq):
    return [str(x) for x in list(seq)]


def observe_frame(result):
    return labels(result.index), labels(result.columns)


def make_df(index, n_cols=3):
    n = len(index)
    data = np.arange(n * n_cols).reshape(n, n_cols)
    return pd.DataFrame(data, index=list(index), columns=["c%d" % j for j in range(n_cols)])


# --- checks -------------------------------------------------------------------

def check_frame_case(df_index, columns, supplied_index):
    """Already-a-DataFrame input: deep model == post-patch real helper."""
    df = make_df(df_index)
    df_columns_before = labels(df.columns)

    real = real_postpatch(df, columns, supplied_index)
    real_idx, real_cols = observe_frame(real)

    m_idx, m_cols = model_wrap(
        True, list(df_index),
        # model uses code-style label lists; compare via str()
        df_columns_before, columns, supplied_index)
    m_idx = labels(m_idx)
    m_cols = labels(m_cols)

    assert m_idx == real_idx, (
        "deep model index disagrees with real post-patch (frame branch):\n"
        "  df_index=%r columns=%r supplied_index=%r\n  model=%r real=%r"
        % (df_index, columns, supplied_index, m_idx, real_idx))
    assert m_cols == real_cols, (
        "deep model columns disagrees with real post-patch (frame branch):\n"
        "  df_index=%r columns=%r supplied_index=%r\n  model=%r real=%r"
        % (df_index, columns, supplied_index, m_cols, real_cols))

    # the headline guarantee: the frame's OWN index is preserved
    assert real_idx == labels(df_index), (
        "post-patch must preserve the frame's own index; got %r for own %r"
        % (real_idx, labels(df_index)))


def check_array_case(supplied_index, columns, ncols=3):
    """Not-a-DataFrame input: deep model == post-patch real helper, on BOTH the
    supplied corner AND the unsupplied (None) corner. When an axis has no
    supplied label set, the real post-patch helper builds a default positional
    RangeIndex (range(nrows) / range(ncols)); the deep model must reproduce it
    exactly (this is the corner that was previously unconstrained, letting a
    wrong impl stamp arbitrary labels — see model.py's `is_range` clauses)."""
    nrows = len(supplied_index) if supplied_index is not None else 2
    arr = np.arange(nrows * ncols).reshape(nrows, ncols)
    real = real_postpatch(arr, columns, supplied_index)
    real_idx, real_cols = observe_frame(real)

    m_idx, m_cols = model_wrap(False, None, None, columns, supplied_index,
                               nrows=nrows, ncols=ncols)
    m_idx = labels(m_idx)
    m_cols = labels(m_cols)

    # full index axis (supplied OR the default positional RangeIndex)
    assert m_idx == real_idx, (
        "deep model index disagrees with real post-patch (array branch): "
        "supplied_index=%r columns=%r model=%r real=%r"
        % (supplied_index, columns, m_idx, real_idx))
    # full column axis (supplied OR the default positional RangeIndex)
    assert m_cols == real_cols, (
        "deep model columns disagrees with real post-patch (array branch): "
        "supplied_index=%r columns=%r model=%r real=%r"
        % (supplied_index, columns, m_cols, real_cols))

    # the headline of the previously-blind corner: when NOT supplied, the axis
    # is the default positional RangeIndex [0, 1, ..., k-1], NOT arbitrary.
    if supplied_index is None:
        assert real_idx == labels(range(nrows)), (
            "post-patch must assign a default RangeIndex when no index is "
            "supplied; got %r for range(%d)" % (real_idx, nrows))
    if columns is None:
        assert real_cols == labels(range(ncols)), (
            "post-patch must assign default RangeIndex columns when none are "
            "supplied; got %r for range(%d)" % (real_cols, ncols))


def check_discriminating_divergence():
    """The pre-patch helper overwrites the frame's index with the supplied one;
    the post-patch helper / deep model keep the frame's own index. This is the
    clause model_prepatch.py fails on and the F2P test exercises (an aggregating
    transformer: supplied index LONGER than the frame's own index)."""
    own = [0, 1]
    supplied = ["s0", "s1"]          # same length, different labels

    post = real_postpatch(make_df(own), None, supplied)
    post_idx, _ = observe_frame(post)
    assert post_idx == labels(own), (
        "post-patch must keep the frame's own index; got %r" % (post_idx,))

    pre = real_prepatch(make_df(own), None, supplied)
    pre_idx, _ = observe_frame(pre)
    assert pre_idx == labels(supplied), (
        "pre-patch must (buggily) overwrite with the supplied index; got %r"
        % (pre_idx,))
    assert pre_idx != post_idx, "the bug must be observable when an index is supplied"

    # the F2P scenario proper: an aggregating transformer returns FEWER rows
    # than the original input, so the supplied (original) index is LONGER. The
    # pre-patch write then raises ValueError (length mismatch); the post-patch
    # helper succeeds and keeps the aggregated frame's own short index.
    aggregated = make_df(["d0", "d1"])     # 2 rows after aggregation
    original_index = [10, 11, 12, 13]      # 4 original rows
    post2 = real_postpatch(aggregated.copy(), None, original_index)
    assert labels(post2.index) == ["d0", "d1"], (
        "post-patch must keep the aggregated frame's own index")
    raised = False
    try:
        real_prepatch(make_df(["d0", "d1"]), None, original_index)
    except ValueError:
        raised = True
    assert raised, (
        "pre-patch must raise the reported length-mismatch ValueError when the "
        "supplied index is longer than the aggregated frame's own index")


def main():
    # ---- boundary battery: frame branch --------------------------------------
    own_indices = [[0, 1], [0, 1, 2, 3], ["a", "b"]]
    supplied_choices = [None, [0, 1], [10, 11], ["s0", "s1"]]
    columns_choices = [None, ["f0", "f1", "f2"], ["x", "y", "z"]]
    for own in own_indices:
        for supplied in supplied_choices:
            # only use supplied indices whose length matches when assigning would
            # otherwise raise in the (unused) pre-patch path; the post-patch path
            # never assigns the index, so any supplied index is safe here.
            for cols in columns_choices:
                check_frame_case(own, cols, supplied)

    # ---- boundary battery: array branch --------------------------------------
    # Cover BOTH corners of each axis, including index=None and columns=None
    # (the default-positional-RangeIndex corner that was previously blind), at
    # several column counts so range(ncols) is actually exercised.
    for supplied in [None, [0, 1], [10, 11, 12], ["r0", "r1"]]:
        for cols in [None, ["f0", "f1"], ["f0", "f1", "f2"], ["x", "y", "z"]]:
            ncols = len(cols) if cols is not None else 3
            check_array_case(supplied, cols, ncols=ncols)

    # ---- the discriminating clause -------------------------------------------
    check_discriminating_divergence()

    # ---- randomized fuzz: frame branch ---------------------------------------
    rng = random.Random(25747)
    fuzz = 0
    for _ in range(2000):
        n_own = rng.randint(1, 6)
        own = list(range(n_own))
        # supplied index of the SAME length (post-patch ignores it anyway, but
        # this keeps the model/real comparison on identical inputs)
        sup_choice = rng.randint(0, 2)
        if sup_choice == 0:
            supplied = None
        elif sup_choice == 1:
            supplied = [1000 + k for k in range(n_own)]
        else:
            supplied = ["s%d" % k for k in range(n_own)]
        cols = None if rng.random() < 0.4 else ["g%d" % j for j in range(3)]
        check_frame_case(own, cols, supplied)
        fuzz += 1

    print("G-AX OK: deep model `wrap_in_container` matches the real post-patch "
          "_wrap_in_pandas_container labelling over the boundary battery + %d "
          "fuzz configurations (frame branch: supplied index present/absent x "
          "columns present/absent; array branch: index/columns present/absent); "
          "the frame's own index is preserved; the pre-patch logic diverges on "
          "EXACTLY a supplied index in the DataFrame branch (model_prepatch.py's "
          "failing clause), raising the reported length-mismatch ValueError in "
          "the aggregation scenario." % fuzz)
    return 0


if __name__ == "__main__":
    sys.exit(main())

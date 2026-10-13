#!/usr/bin/env python3
"""G-CONF — mechanical differential conformance for scikit-learn__scikit-learn-25102.

The bundle models ONE function: the feature-selection `transform`
(`SelectorMixin.transform` composed with `SelectorMixin._transform`). Its Lean
implementation (`implementation_transform`) reduces a tabular input to the
columns picked by a boolean support mask, while deciding whether to keep each
column's original element type:

    keep_native = is_dataframe and output_pandas
    block       = cols if keep_native else cast_all(cols, common_dtype)
    selected    = [c for (c, m) in zip(block, mask) if m]
    result      = TransformResult(cols=selected, n_rows=n_rows)

where `cast_all(cols, dt)` collapses every column's dtype to the single common
dtype `dt` (the homogenisation `check_array` performs when casting a DataFrame to
an ndarray).

This script transliterates that R/I impl into Python (`shadow`) and differential-
tests it against the ORACLE: a faithful in-process replica of the POST-PATCH
behavior of `transform`/`_transform` (`sklearn/feature_selection/_base.py`):

    preserve_X = hasattr(X, "iloc") and output_config_dense == "pandas"
    X = _validate_data(..., cast_to_ndarray=not preserve_X)   # cast -> common dtype
    mask = get_support()
    if not mask.any():
        return X.iloc[:, :0] (dataframe) / empty (n_rows, 0)
    return _safe_indexing(X, mask, axis=1)

We do NOT stand up an estimator / fit loop (heavy, and the modeled value is the
pure column-and-dtype bookkeeping the step performs). Instead we reproduce the
patched behavior with the SAME observables the real code exposes (mapping.md):
`hasattr(X, "iloc")` -> `is_dataframe`, `output_config_dense == "pandas"` ->
`output_pandas`, the input columns + per-column dtypes -> `cols`, the homogenised
numpy dtype -> `common_dtype`, `get_support()` -> `mask`, `X.shape[0]` -> `n_rows`.

The oracle homogenises (collapses every column's dtype to `common_dtype`) unless
the container is preserved, then selects the masked columns — exactly the patch.
The shadow reaches the same result via the Lean `castAll`/`selectByMask`. They
must agree for every input — in particular when a selected column's original
dtype differs from `common_dtype` under the preserve gate, which is the
dtype-preservation the patch adds and the pre-patch code omitted.

stdlib-only; deterministic built-in fuzzer. Pinned seed: 25102 (also in mapping.md).
"""
import sys

SEED = 25102
N = 120_000


# --- helpers mirroring Solution.lean -----------------------------------------
def cast_all(cols, dt):
    # castAll: collapse every column's dtype to the common dtype
    return [(name, dt) for (name, _dtype) in cols]


def select_by_mask(cols, mask):
    # selectByMask: keep flagged columns, input order (zip truncates to min length)
    return [c for (c, m) in zip(cols, mask) if m]


# --- ORACLE: the post-patch behavior, faithful in-process replica -------------
# Returns (selected_cols, n_rows): the output columns (name, dtype) in order and
# the row count.
def oracle(is_dataframe, output_pandas, cols, n_rows, common_dtype, mask):
    preserve_X = is_dataframe and output_pandas
    if preserve_X:
        block = list(cols)                       # cast_to_ndarray=False: keep dtypes
    else:
        block = cast_all(cols, common_dtype)     # check_array homogenisation
    if not any(mask):
        return ([], n_rows)                      # X.iloc[:, :0] / empty (n_rows, 0)
    return (select_by_mask(block, mask), n_rows)


# --- shadow of implementation_transform (the R/I leg) -------------------------
# Mirrors Solution.lean exactly.
def shadow(is_dataframe, output_pandas, cols, n_rows, common_dtype, mask):
    keep_native = is_dataframe and output_pandas
    block = list(cols)
    if not keep_native:
        block = cast_all(cols, common_dtype)
    selected = select_by_mask(block, mask)
    if not any(mask):
        return ([], n_rows)
    return (selected, n_rows)


def disagree(args):
    got = oracle(*args)
    want = shadow(*args)
    if got != want:
        return (args, got, want)
    return None


# --- input corpus -------------------------------------------------------------
def _lcg(seed):
    x = seed & 0xFFFFFFFF
    while True:
        x = (1103515245 * x + 12345) & 0x7FFFFFFF
        yield x


def _enumerate_edge():
    cases = []
    col_sets = [
        [],                                   # no columns
        [(0, 5)],                             # single column, dtype != common
        [(0, 0), (1, 0)],                     # all dtypes already == common (0)
        [(0, 1), (1, 2), (2, 3)],             # mixed dtypes (the bug case)
        [(0, 9), (1, 9), (2, 9), (3, 9)],     # all same non-common dtype
    ]
    mask_sets = [
        [],                  # empty mask
        [True],
        [False],
        [True, False, True],
        [False, False, False],
        [True, True, True, True],
    ]
    common_dtypes = [0, 7]
    for is_df in (True, False):
        for out_pd in (True, False):
            for cols in col_sets:
                for cd in common_dtypes:
                    for mask in mask_sets:
                        cases.append((is_df, out_pd, cols, 4, cd, mask))
    return cases


def main() -> int:
    checked = 0

    for args in _enumerate_edge():
        d = disagree(args)
        if d:
            print(f"DISAGREE edge {d[0]!r}: oracle={d[1]} shadow={d[2]}")
            print("status=fail")
            return 1
        checked += 1

    rnd = _lcg(SEED)
    for _ in range(N):
        is_df = (next(rnd) & 1) == 1
        out_pd = (next(rnd) & 1) == 1
        n_cols = next(rnd) % 8                     # 0..7 columns
        cols = [(i, next(rnd) % 5) for i in range(n_cols)]   # dtype in 0..4
        common_dtype = next(rnd) % 5
        n_rows = next(rnd) % 100
        # mask length sometimes != n_cols to exercise zip truncation robustness
        len_mask = next(rnd) % 8
        mask = [(next(rnd) & 1) == 1 for _ in range(len_mask)]
        d = disagree((is_df, out_pd, cols, n_rows, common_dtype, mask))
        if d:
            print(f"DISAGREE fuzz {d[0]!r}: oracle={d[1]} shadow={d[2]}")
            print("status=fail")
            return 1
        checked += 1

    print(f"checked={checked} disagreements=0")
    print("status=pass")
    return 0


if __name__ == "__main__":
    sys.exit(main())

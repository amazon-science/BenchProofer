#!/usr/bin/env python3
"""G-CONF differential conformance check for scikit-learn__scikit-learn-25747
(nagini).

SHADOW: the impl region of model.py, copied verbatim below with the contract
calls (Requires/Ensures/Invariant/Assert) stripped. The model IS Python: the
`Frame` carrier class (plain field assignments), the modeled function
`wrap_in_container`, and its two impl helpers `_copy_labels` / `_range_labels`
run directly. The @Pure spec helpers (`opt_seq`, `is_range`) copy over as
plain functions; `PSeq`/`ToSeq` become a thin tuple shim.

ORACLE: the REAL patched repo helper the model models per mapping.md —
`sklearn.utils._set_output._wrap_in_pandas_container`. The gate applies the
gold patch to /testbed before this script runs and sets PYTHONPATH so the
patched package is what imports here; this script does NOT apply any patch.

Type bridge (mapping.md section 2):
  * a labelled tabular container <-> `Frame(index, columns)`: only the two
    label axes are observed; the payload content is irrelevant to the modeled
    behaviour, so the oracle side uses a zero payload of the matching shape;
  * a label axis (an Index of labels) <-> `List[int]` of label codes: labels
    are arbitrary hashables compared by equality/order, which a 1:1 integer
    code encoding preserves; the fuzz therefore uses integer labels on BOTH
    sides and observes the oracle's axes as `[int(x) for x in axis]`;
  * `isinstance(data, DataFrame)` <-> the bool `data_is_frame`: the shadow is
    driven with the branch value the oracle input actually has;
  * the keyword args `columns` / `index` <-> `Optional[List[int]]`
    (None <-> absent);
  * the payload's shape <-> `nrows`/`ncols` (derived from the raw input on
    the shadow side, never read back from the oracle's output).

Input domain: the model's precondition admits any optional label lists and
nrows >= 0, ncols >= 0. Generation is confined to the oracle's SUCCESS domain
(the modeling boundary per refinement.md): on the fresh-container branch a
supplied axis label set has the matching length (len(index) == nrows,
len(columns) == ncols) since the container constructor raises otherwise; on
the already-a-container branch a supplied replacement column set matches the
container's column count, while the supplied ROW label set may have ANY
length (equal, shorter, or longer than the container's own row count) — that
axis is the behaviour under test and length-mismatched sets are included
deliberately (the aggregation scenario).

>= 1e5 Requires-satisfying inputs: a boundary battery (empty axes, 0-row /
0-column payloads, supplied/absent sets in all combinations, mismatched-length
row label sets) + 105000 fuzz cases split over both branches. Pinned fuzz
seed: 25747.

Exit 0 iff zero disagreements; on disagreement prints the input and both
sides' observations and exits 1. stdlib + numpy only.
"""
import json
import random
import sys

import numpy as np

SEED = 25747
N_FRAME_FUZZ = 60_000
N_ARRAY_FUZZ = 45_000

from typing import List, Optional


# --- PSeq / ToSeq shim (pure sequence values become tuples) -------------------

class PSeq(tuple):
    def __new__(cls, *elems):
        return super().__new__(cls, elems)

    def take(self, n):
        return PSeq(*self[:n])

    def drop(self, n):
        return PSeq(*self[n:])


def ToSeq(xs):
    return tuple(xs)


# --- the impl region of model.py, verbatim, contract calls stripped -----------

class Frame:
    def __init__(self, index: List[int], columns: List[int],
                 si, sc) -> None:
        # `si`/`sc` are ghost witnesses of the intended label sequences (spec
        # plumbing only; values are ignored at runtime).
        self.index = index
        self.columns = columns


# @Pure spec helpers, copied as plain functions

def opt_seq(x: Optional[List[int]]):
    """The sequence value of an optional label set: its element sequence when a
    set is supplied, the empty sequence when none is."""
    if x is None:
        return PSeq(0).take(0)
    return ToSeq(x)


def is_range(s, n: int) -> bool:
    """``s`` is the default positional labelling ``[0, 1, ..., n-1]``."""
    return len(s) == n and all(s[k] == k for k in range(n))


def wrap_in_container(data_is_frame: bool,
                      df: Frame,
                      columns: Optional[List[int]],
                      index: Optional[List[int]],
                      nrows: int,
                      ncols: int) -> Frame:
    # impl-start (contracts and ghost Asserts stripped)
    if data_is_frame:
        if columns is not None:
            refreshed = _copy_labels(columns)  # type: List[int]
            df.columns = refreshed
        # The supplied row labels are intentionally NOT applied here: the
        # container keeps its own row labels.
        return df
    new_index = []  # type: List[int]
    if index is not None:
        new_index = _copy_labels(index)
    else:
        new_index = _range_labels(nrows)
    new_columns = []  # type: List[int]
    if columns is not None:
        new_columns = _copy_labels(columns)
    else:
        new_columns = _range_labels(ncols)
    gi = ToSeq(new_index)
    gc = ToSeq(new_columns)
    result = Frame(new_index, new_columns, gi, gc)  # type: Frame
    return result
    # impl-end


def _copy_labels(src: List[int]) -> List[int]:
    out = []  # type: List[int]
    i = 0
    while i < len(src):
        out.append(src[i])
        i = i + 1
    return out


def _range_labels(n: int) -> List[int]:
    out = []  # type: List[int]
    i = 0
    while i < n:
        out.append(i)
        i = i + 1
    return out


# --- bridge / observation helpers ---------------------------------------------

def axis_codes(axis):
    """A real label axis observed as its list of integer label codes."""
    return [int(x) for x in list(axis)]


def make_real_df(pd, idx, cols):
    """A real container with the given integer label axes and a zero payload
    of the matching shape (the payload is not touched by the behaviour under
    test)."""
    return pd.DataFrame(np.zeros((len(idx), len(cols))),
                        index=list(idx), columns=list(cols))


def check_frame_case(real_fn, pd, df_index, df_columns, columns, index):
    """Already-a-container input: shadow vs oracle on both label axes."""
    real_df = make_real_df(pd, df_index, df_columns)
    real_out = real_fn(real_df, columns=columns, index=index)

    shadow_df = Frame(list(df_index), list(df_columns),
                      ToSeq(df_index), ToSeq(df_columns))
    shadow_out = wrap_in_container(True, shadow_df, columns, index,
                                   len(df_index), len(df_columns))

    real_obs = (axis_codes(real_out.index), axis_codes(real_out.columns))
    shadow_obs = (list(shadow_out.index), list(shadow_out.columns))
    same_object = real_out is real_df

    if shadow_obs != real_obs or shadow_out is not shadow_df or not same_object:
        return ("DISAGREEMENT (container branch)\n"
                "  df_index=%r df_columns=%r columns=%r index=%r\n"
                "  shadow (index, columns)=%r same_object=%r\n"
                "  real   (index, columns)=%r same_object=%r"
                % (df_index, df_columns, columns, index,
                   shadow_obs, shadow_out is shadow_df,
                   real_obs, same_object))
    return None


def check_array_case(real_fn, nrows, ncols, columns, index):
    """Not-a-container input: shadow vs oracle on both label axes of the
    freshly built container."""
    arr = np.zeros((nrows, ncols))
    real_out = real_fn(arr, columns=columns, index=index)

    dummy = Frame([], [], ToSeq([]), ToSeq([]))
    shadow_out = wrap_in_container(False, dummy, columns, index, nrows, ncols)

    real_obs = (axis_codes(real_out.index), axis_codes(real_out.columns))
    shadow_obs = (list(shadow_out.index), list(shadow_out.columns))

    if shadow_obs != real_obs:
        return ("DISAGREEMENT (fresh-container branch)\n"
                "  nrows=%d ncols=%d columns=%r index=%r\n"
                "  shadow (index, columns)=%r\n"
                "  real   (index, columns)=%r"
                % (nrows, ncols, columns, index, shadow_obs, real_obs))
    return None


# --- input generation ----------------------------------------------------------

def rand_labels(rng, n):
    """n integer label codes: mostly distinct, occasionally with duplicates or
    negatives (labels are arbitrary; codes need not be a range)."""
    style = rng.randint(0, 3)
    if style == 0:
        return list(range(n))                       # the default-looking set
    if style == 1:
        base = rng.randint(-50, 1000)
        return [base + k for k in range(n)]         # shifted distinct codes
    if style == 2:
        return [rng.randint(-20, 20) for _ in range(n)]  # duplicates possible
    return rng.sample(range(-1000, 1000), n)        # scattered distinct codes


def boundary_frame_cases():
    cases = []
    own_axes = [([], []), ([0], [0]), ([5, 6], [1, 2, 3]),
                ([], [7, 8]), ([3, 4], [])]
    for own_idx, own_cols in own_axes:
        col_choices = [None, list(range(100, 100 + len(own_cols)))]
        idx_choices = [None, list(own_idx),                # identical set
                       list(range(200, 200 + len(own_idx))),  # same length
                       list(range(200, 203 + len(own_idx))),  # LONGER set
                       list(range(200, 200 + max(len(own_idx) - 1, 0)))]  # shorter
        for cols in col_choices:
            for idx in idx_choices:
                cases.append((own_idx, own_cols, cols, idx))
    return cases


def boundary_array_cases():
    cases = []
    for nrows, ncols in [(0, 0), (0, 3), (2, 0), (1, 1), (3, 2)]:
        for idx in [None, list(range(50, 50 + nrows))]:
            for cols in [None, list(range(90, 90 + ncols))]:
                cases.append((nrows, ncols, cols, idx))
    return cases


def main():
    # the REAL patched repo helper (PYTHONPATH=/testbed, gold patch applied
    # by the gate before this script runs)
    from sklearn.utils._set_output import _wrap_in_pandas_container
    import pandas as pd

    rng = random.Random(SEED)
    checked = 0

    # --- boundary battery ------------------------------------------------------
    for own_idx, own_cols, cols, idx in boundary_frame_cases():
        err = check_frame_case(_wrap_in_pandas_container, pd,
                               own_idx, own_cols, cols, idx)
        if err:
            print(err)
            return 1
        checked += 1

    for nrows, ncols, cols, idx in boundary_array_cases():
        err = check_array_case(_wrap_in_pandas_container, nrows, ncols,
                               cols, idx)
        if err:
            print(err)
            return 1
        checked += 1

    n_boundary = checked

    # --- fuzz: already-a-container branch --------------------------------------
    for _ in range(N_FRAME_FUZZ):
        n_own = rng.randint(0, 5)
        m_own = rng.randint(0, 4)
        own_idx = rand_labels(rng, n_own)
        own_cols = rand_labels(rng, m_own)
        # replacement column set (when supplied) matches the container's
        # column count (the oracle's success domain)
        cols = None if rng.random() < 0.4 else rand_labels(rng, m_own)
        # supplied row label set: any length, INCLUDING mismatched lengths
        # (the discriminating aggregation scenario)
        r = rng.random()
        if r < 0.3:
            idx = None
        elif r < 0.6:
            idx = rand_labels(rng, n_own)             # matching length
        else:
            idx = rand_labels(rng, rng.randint(0, 8))  # arbitrary length
        err = check_frame_case(_wrap_in_pandas_container, pd,
                               own_idx, own_cols, cols, idx)
        if err:
            print(err)
            return 1
        checked += 1

    # --- fuzz: fresh-container branch -------------------------------------------
    for _ in range(N_ARRAY_FUZZ):
        nrows = rng.randint(0, 6)
        ncols = rng.randint(0, 5)
        idx = None if rng.random() < 0.5 else rand_labels(rng, nrows)
        cols = None if rng.random() < 0.5 else rand_labels(rng, ncols)
        err = check_array_case(_wrap_in_pandas_container, nrows, ncols,
                               cols, idx)
        if err:
            print(err)
            return 1
        checked += 1

    print("G-CONF OK: shadow impl == real patched helper on %d inputs "
          "(%d boundary + %d container-branch fuzz + %d fresh-container fuzz, "
          "seed %d)." % (checked, n_boundary, N_FRAME_FUZZ, N_ARRAY_FUZZ, SEED))
    print(json.dumps({"checked": checked, "disagreements": 0, "seed": SEED,
                      "shadow": "direct (contract-stripped impl region)"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())

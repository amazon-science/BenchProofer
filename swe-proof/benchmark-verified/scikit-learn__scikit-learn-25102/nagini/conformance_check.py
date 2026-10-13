#!/usr/bin/env python3
"""G-CONF differential conformance check for scikit-learn__scikit-learn-25102
(nagini).

SHADOW: the impl region of model.py's `select_columns`, copied VERBATIM below
with the contract calls (Requires/Ensures/Invariant/Assert) stripped, together
with the helpers it uses: the `Frame` container (constructor stripped to its
two field writes), the plain helper `_copy_labels` (contracts stripped), and
the `@Pure` compress `kept_descs` copied over as a plain function on a minimal
PSeq shim (a tuple with take/drop/concat). The model IS Python: the shadow is
the model's own executable code, no transliteration. The bundle consumes NO
`@ContractOnly` axiom, so no real-callee shim is needed inside the shadow.

ORACLE: the REAL patched repo function the model models per mapping.md §1 —
`SelectorMixin._transform(self, X)` in sklearn/feature_selection/_base.py,
invoked through a minimal concrete selector whose support mask is preset, on
real pandas DataFrames. The gate applies the gold patch to /testbed before
this script runs and sets PYTHONPATH so the patched package is what imports
here; this script does NOT apply any patch itself.

Type bridge (mapping.md §2):
  * `Frame.index` (row label codes, List[int])  <->  `X.index` (integer row
    labels; the DataFrames are built with integer indices, compared as ints);
  * `Frame.descs` (per-column descriptor codes) <->  `X.dtypes` per column,
    through an injective str(dtype) -> int code table built on the fly (the
    modelled observation compares descriptors for equality only, so any
    injective coding is a faithful bridge);
  * `mask: List[int]` of 0/1 flags               <->  the boolean support mask
    the selector reports (length == number of columns, the Requires
    `len(df.descs) == len(mask)`).

Observation compared per case: (row labels of the output, per-column
descriptor codes of the output). The shadow's `kept_descs` value is also
cross-checked against the shadow loop's output as an internal consistency
assertion of the copied pure region.

Input domain (all Requires-satisfying): any integer row labels (including
none, and including duplicates), any per-column dtype assignment from a mixed
palette (floats of several widths, ints, bool, object, category), any 0/1
mask of matching length — including the all-zero mask (zero retained columns)
and the zero-column container.

>= 1e5 Requires-satisfying inputs: exhaustive mask enumeration over a
boundary battery (every mask for up to 4 columns x several palettes x several
indices, plus zero-column / zero-row / duplicate-label cases) + 100000
randomized fuzz cases. Pinned seed: 25102. DataFrames are cached per
(palette, index) shape — the observation depends only on dtypes and index, so
reuse across masks is sound.

Exit 0 iff zero disagreements; on disagreement prints the input and both
sides' observations and exits 1. Imports: stdlib + numpy + pandas (the
container the labelled tabular inputs live in) + the patched repo itself.
"""
import itertools
import json
import random
import sys
import warnings

import numpy as np
import pandas as pd

SEED = 25102
N_FUZZ = 100_000


# --- PSeq shim (pure-theory carrier -> plain tuple) ---------------------------

class PSeq(tuple):
    def __new__(cls, *items):
        return super(PSeq, cls).__new__(cls, items)

    @staticmethod
    def _of(iterable):
        return PSeq(*iterable)

    def take(self, n):
        return PSeq._of(tuple(self)[:n])

    def drop(self, n):
        return PSeq._of(tuple(self)[n:])

    def __add__(self, other):
        return PSeq._of(tuple(self) + tuple(other))


def ToSeq(xs):
    return PSeq._of(xs)


# --- the model's pure region, copied as a plain function ----------------------

def kept_descs(descs, mask):
    # verbatim from model.py's @Pure region
    if len(descs) == 0 or len(mask) == 0:
        return PSeq(0).take(0)
    if mask[0] != 0:
        return PSeq(descs[0]) + kept_descs(descs.drop(1), mask.drop(1))
    return kept_descs(descs.drop(1), mask.drop(1))


# --- the impl region of model.py, verbatim, contract calls stripped ----------

class Frame:
    def __init__(self, index, descs, si, sd):
        self.index = index
        self.descs = descs


def _copy_labels(src):
    out = []
    i = 0
    while i < len(src):
        out.append(src[i])
        i = i + 1
    return out


def select_columns(df, mask):
    # impl-start (contracts stripped)
    new_index = _copy_labels(df.index)
    new_descs = []
    i = len(df.descs)
    while i > 0:
        d = df.descs[i - 1]
        m = mask[i - 1]
        if m != 0:
            new_descs = [d] + new_descs
        i = i - 1
    gi = ToSeq(new_index)
    gd = ToSeq(new_descs)
    result = Frame(new_index, new_descs, gi, gd)
    return result
    # impl-end


# --- descriptor coding bridge --------------------------------------------------

_CODES = {}


def code_of(dtype_obj):
    """Injective str(dtype) -> int code (mapping.md §2: descriptors are
    compared for equality only, so any injective coding bridges faithfully)."""
    key = str(dtype_obj)
    if key not in _CODES:
        _CODES[key] = len(_CODES)
    return _CODES[key]


# --- oracle plumbing ------------------------------------------------------------

def make_selector_class():
    """A minimal concrete selector: its support mask is preset, so calling the
    REAL `_transform` exercises exactly the modelled column selection."""
    from sklearn.base import BaseEstimator
    from sklearn.feature_selection._base import SelectorMixin

    class _MaskSelector(SelectorMixin, BaseEstimator):
        def __init__(self, mask):
            self._mask = np.asarray(mask, dtype=bool)

        def fit(self, X, y=None):
            return self

        def _get_support_mask(self):
            return self._mask

    return _MaskSelector


def make_df(index, col_dtypes):
    """Build a DataFrame with the given integer index and per-column dtypes,
    one column per palette entry."""
    n = len(index)
    data = {}
    for j, dt in enumerate(col_dtypes):
        name = "c%d" % j
        if str(dt) == "category":
            data[name] = pd.Series(
                [("a" if (k % 2 == 0) else "b") for k in range(n)],
                index=list(index), dtype="category")
        elif str(dt) == "object":
            data[name] = pd.Series(
                ["v%d" % k for k in range(n)], index=list(index),
                dtype=object)
        else:
            data[name] = pd.Series(
                np.arange(n).astype(dt), index=list(index))
    return pd.DataFrame(data, index=list(index))


# --- one differential case -------------------------------------------------------

def run_case(selector_cls, df, index, mask, label):
    """Diff shadow vs real on one (frame, mask) input. Returns an error string
    on disagreement, else None."""
    descs = [code_of(dt) for dt in df.dtypes]

    # shadow (the model's own impl code)
    frame = Frame(list(index), list(descs), ToSeq(index), ToSeq(descs))
    out = select_columns(frame, list(mask))
    shadow_index = list(out.index)
    shadow_descs = list(out.descs)

    # internal consistency of the copied pure region
    assert tuple(shadow_descs) == tuple(kept_descs(ToSeq(descs), ToSeq(mask))), (
        "shadow impl loop and copied pure compress disagree: descs=%r mask=%r"
        % (descs, mask))

    # real patched repo function on the real labelled container
    sel = selector_cls(mask)
    real = sel._transform(df)
    real_index = [int(x) for x in real.index]
    real_descs = [code_of(dt) for dt in real.dtypes]

    if shadow_index != real_index or shadow_descs != real_descs:
        return ("DISAGREEMENT (%s)\n  index=%r dtypes=%r mask=%r\n"
                "  shadow=(index=%r, descs=%r)\n  real=(index=%r, descs=%r)"
                % (label, index, [str(d) for d in df.dtypes], list(mask),
                   shadow_index, shadow_descs, real_index, real_descs))
    return None


# --- input generation --------------------------------------------------------------

PALETTES = [
    [np.float64],
    [np.float32, np.float64],
    [np.float32, "category", np.float64],
    [np.int32, np.int64, np.float32, "category"],
    ["category", "category"],
    [np.float16, np.int64, "object", np.bool_],
]

INDEX_CHOICES = [
    [0, 1, 2],
    [0, 1, 2, 3, 4],
    [10, 11, 12],
    [7, 7, 9],          # duplicate row labels
    [],                 # zero rows
]

FUZZ_DTYPES = [np.float16, np.float32, np.float64, np.int32, np.int64,
               np.bool_, "object", "category"]


def main():
    warnings.simplefilter("ignore")
    selector_cls = make_selector_class()

    checked = 0

    # ---- boundary battery: EVERY mask over each palette/index pair ----------
    frame_cache = {}

    def cached_df(palette, index):
        key = (tuple(str(d) for d in palette), tuple(index))
        if key not in frame_cache:
            frame_cache[key] = make_df(index, palette)
        return frame_cache[key]

    for palette in PALETTES:
        ncols = len(palette)
        for index in INDEX_CHOICES:
            df = cached_df(palette, index)
            for bits in itertools.product([0, 1], repeat=ncols):
                err = run_case(selector_cls, df, index, list(bits), "boundary")
                if err:
                    print(err)
                    return 1
                checked += 1

    # zero-column container (empty descs, empty mask)
    for index in INDEX_CHOICES:
        df = pd.DataFrame(index=list(index))
        err = run_case(selector_cls, df, index, [], "boundary, zero columns")
        if err:
            print(err)
            return 1
        checked += 1

    # ---- randomized fuzz ------------------------------------------------------
    rng = random.Random(SEED)
    fuzz_frames = []
    for _ in range(400):
        ncols = rng.randint(0, 6)
        palette = [rng.choice(FUZZ_DTYPES) for _ in range(ncols)]
        nrows = rng.randint(0, 6)
        base = rng.randint(-50, 950)
        index = [base + rng.randint(0, 3) for _ in range(nrows)]  # dups possible
        if ncols == 0:
            fuzz_frames.append((pd.DataFrame(index=list(index)), index, 0))
        else:
            fuzz_frames.append((make_df(index, palette), index, ncols))

    for _ in range(N_FUZZ):
        df, index, ncols = fuzz_frames[rng.randrange(len(fuzz_frames))]
        mask = [1 if rng.random() < 0.5 else 0 for _ in range(ncols)]
        err = run_case(selector_cls, df, index, mask, "fuzz")
        if err:
            print(err)
            return 1
        checked += 1

    print("G-CONF OK: shadow impl (contract-stripped select_columns) == real "
          "patched SelectorMixin._transform on %d inputs (exhaustive-mask "
          "boundary battery + %d fuzz cases, seed %d); observation = "
          "(row labels, per-column descriptor codes)."
          % (checked, N_FUZZ, SEED))
    print(json.dumps({"checked": checked, "disagreements": 0, "seed": SEED,
                      "shadow": "direct (contract-stripped impl region; "
                                "no @ContractOnly callees)"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())

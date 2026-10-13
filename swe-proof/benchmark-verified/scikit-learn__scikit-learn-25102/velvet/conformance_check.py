#!/usr/bin/env python3
"""G-CONF differential conformance check for scikit-learn__scikit-learn-25102.

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both sides on the same fuzzed inputs and comparing observable outputs:

  * SHADOW  — the R/I-tagged ops of Solution.lean's impl region transliterated
              to Python over the *real* container type (a pandas DataFrame), via
              the mapping.md bijection (`List (Int x Bool)` <-> a DataFrame with
              one column per list element; `p.1` <-> the column's dtype,
              `p.2` <-> its selection-mask bit). The projection is modeled
              deeply (all R/I); there is NO A-tagged callee left symbolic in the
              impl region, so `conf_skip=false`.
  * ORACLE  — `patch.diff`'s behaviour: a real `SelectorMixin` selector with
              `set_output(transform="pandas")`, fit then `transform`-ed at
              base_commit with the gold patch applied (the real correctness
              oracle, G-RESOLVE). We read the per-column output dtypes/columns.

They must agree on every input: the projected output's per-column dtypes, in
order, must equal the shadow's. Exit 0 iff zero disagreements; any disagreement
is a mechanical R/I-fidelity counterexample.

Runs in-container (the prebuilt SWE-Bench instance image), with the gold patch
applied. The fuzz seed is pinned (mapping.md §4) for a deterministic verdict.
"""
import random
import sys

import numpy as np
import pandas as pd

from sklearn.base import BaseEstimator
from sklearn.feature_selection._base import SelectorMixin

SEED = 25102
N_FUZZ = 100_000

# --- the dtype universe (mapping.md §2): distinct dtype <-> distinct identity -
# Domain restriction (the modeled function's precondition): `_transform` only
# ever runs on an `X` that `transform` first passed through `_validate_data`
# (`fit` does the same). A pandas frame mixing a string `category` column with a
# `bool` column is *rejected* by that numeric validation
# (`ValueError: Cannot cast object dtype to float64`), so such frames never reach
# `_transform` and are outside the modeled behavior. The dtypes below all
# co-validate in any combination (verified in-container), matching the F2P
# scenario (mixed float precisions + string `category`). Dropping `bool` is a
# precondition restriction, not a weakening of the projection contract.
def _cat_col(n, rng):
    cats = ["a", "b", "j", "x", "z"]
    return pd.Series([rng.choice(cats) for _ in range(n)], dtype="category")

_DTYPE_BUILDERS = {
    "float16": lambda n, rng: pd.Series(np.arange(n), dtype=np.float16),
    "float32": lambda n, rng: pd.Series(np.arange(n), dtype=np.float32),
    "float64": lambda n, rng: pd.Series(np.arange(n), dtype=np.float64),
    "int64":   lambda n, rng: pd.Series(np.arange(n), dtype=np.int64),
    "int32":   lambda n, rng: pd.Series(np.arange(n), dtype=np.int32),
    "category": _cat_col,
}
_NAMES = list(_DTYPE_BUILDERS)


class _MaskSelector(SelectorMixin, BaseEstimator):
    """A SelectorMixin whose support mask is a fixed boolean array — the minimal
    concrete selector exercising the patched transform/_transform path."""

    def __init__(self, mask):
        self._mask = np.asarray(mask, dtype=bool)

    def fit(self, X, y=None):
        self._validate_data(X, accept_sparse="csc")
        return self

    def _get_support_mask(self):
        return self._mask


def build_frame(dtype_names, n, rng):
    data = {}
    for j, name in enumerate(dtype_names):
        data["col%d" % j] = _DTYPE_BUILDERS[name](n, rng)
    return pd.DataFrame(data)


# --- the R/I shadow: keptCol / selectMasked transliterated -------------------
def shadow_dtypes(dtype_names, mask):
    """selectMasked over the dtype-coded columns: the ordered dtype identities
    of the kept columns, each preserved (keptCol p = [p.1] if p.2 else [])."""
    return [name for name, keep in zip(dtype_names, mask) if keep]


# --- the oracle: patch.diff's real patched selector behaviour ----------------
def oracle_dtypes(df, mask):
    """patch.diff behaviour: fit a pandas-output selector and read the output's
    per-column dtype identities, in order."""
    sel = _MaskSelector(mask).set_output(transform="pandas")
    sel.fit(df)
    out = sel.transform(df)
    return [_dtype_name(out.dtypes.iloc[j]) for j in range(out.shape[1])]


def _dtype_name(dtype):
    if isinstance(dtype, pd.CategoricalDtype) or str(dtype) == "category":
        return "category"
    return str(dtype)


def fuzz_inputs(n, rng):
    # boundary cases first (plan §4.1 step 4)
    one_each = _NAMES[:]
    k = len(one_each)
    yield (one_each, [True] * k)            # keep all heterogeneous
    yield (one_each, [False] * k)           # keep none -> empty frame
    for j in range(k):
        m = [False] * k; m[j] = True; yield (one_each, m)
        m = [True] * k; m[j] = False; yield (one_each, m)
    yield (one_each, [j % 2 == 0 for j in range(k)])
    yield (["float16", "category", "category", "float64"], [True, False, True, False])
    yield (["float32", "float64"], [True, True])
    for _ in range(n):
        width = rng.randint(1, 8)
        dtype_names = [rng.choice(_NAMES) for _ in range(width)]
        mask = [rng.random() < 0.5 for _ in range(width)]
        yield (dtype_names, mask)


def main():
    rng = random.Random(SEED)
    disagreements = []
    count = 0
    for dtype_names, mask in fuzz_inputs(N_FUZZ, rng):
        count += 1
        nrows = rng.randint(1, 6)
        df = build_frame(dtype_names, nrows, rng)
        shadow = shadow_dtypes(dtype_names, mask)
        oracle = oracle_dtypes(df, mask)
        if shadow != oracle:
            disagreements.append((dtype_names, mask, shadow, oracle))
            if len(disagreements) >= 5:
                break
    if disagreements:
        print("G-CONF FAIL: %d R/I disagreement(s) over %d inputs:"
              % (len(disagreements), count))
        for dn, m, sh, orc in disagreements:
            print("  dtypes=%r mask=%r shadow=%r oracle=%r" % (dn, m, sh, orc))
        return 1
    print("G-CONF OK: R/I shadow of projectColumns agrees with patch.diff "
          "behaviour on %d inputs (seed=%d), 0 disagreements." % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())

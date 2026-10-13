#!/usr/bin/env python3
"""G-CONF differential conformance check for scikit-learn__scikit-learn-13135
(nagini).

SHADOW: the impl region of model.py's `make_bin_edges`, copied verbatim below
with the contract calls (Requires/Ensures/Assert) stripped. The model IS
Python: the ordered-centre midpoints and the bracketed boundary list run
directly. The one @ContractOnly callee, `order4`, is the unchanged numeric
ordering operation `numpy.ndarray.sort` (mapping.md section 3.1); per the
contract for @ContractOnly callees, the shim below calls that REAL callee.
The PSeq result becomes a plain tuple.

ORACLE: the REAL patched repo computation the model models per mapping.md —
the bin-boundary construction of `KBinsDiscretizer.fit` for one feature under
the kmeans strategy (`sklearn/preprocessing/_discretization.py`). The gate
applies the gold patch to /testbed before this script runs and sets
PYTHONPATH so the patched package is what imports here; this script does NOT
apply any patch itself.

Type bridge (mapping.md section 2):
  * the 1-D centre array (four entries — the model's fixed representative
    arity, mapping.md section 2.1) maps to the four float arguments a,b,c,d;
  * `col_min, col_max = column.min(), column.max()` map identically to the
    float arguments col_min, col_max;
  * the fitted `bin_edges_[feature]` array (five float64 boundaries) maps to
    the returned 5-element list, compared elementwise with exact equality
    (both sides halve with an exact power-of-two scaling, so no rounding
    slack is needed).

The modeled computation takes the centres as INPUTS (the centre-producing
clustering call is outside the modeling boundary), so the check runs two
complementary oracle lanes:

  Lane A (input-domain fuzz, the >=1e5 lane): drive the REAL patched `fit`
  while the in-module clustering symbol is temporarily replaced by an
  injector that returns four chosen centres — this steers the genuine
  patched repo code over exactly the model's Requires-satisfying input
  domain (four centres each in [col_min, col_max]). The boundary-building
  lines that execute are the real repo's, unmodified.

  Lane B (end-to-end, nothing replaced): fit the REAL estimator on random
  columns with the REAL clustering; the bridge recomputes the centres for
  the shadow's inputs with the same unchanged deterministic prefix
  (uniform-spaced init, single-init 1-D k-means) applied to the raw column,
  so the shadow's inputs derive from the raw input, never from the oracle's
  output.

Input domain: the model's Requires admit col_min <= col_max with every
centre in [col_min, col_max]. The real kmeans branch is only reached when
col_min != col_max (a constant column short-circuits to a sentinel edge
pair before the modeled computation), so generation uses col_min < col_max —
the reachable oracle domain; the degenerate equal-bounds point admitted by
the (weaker) model precondition has no oracle-side counterpart.

>= 1e5 Requires-satisfying inputs: 100000 injected-centre fuzz cases +
boundary cases (equal centres, bound-pinned centres, ordered / reversed /
permuted centres, tiny and huge ranges, negative ranges) + 300 end-to-end
fitted columns. Pinned seed: 13135.

Exit 0 iff zero disagreements; on disagreement prints the input and both
sides' boundary lists and exits 1. stdlib + numpy only.
"""
import json
import random
import sys

import numpy as np

SEED = 13135
N_INJECT_FUZZ = 100_000
N_FIT_FUZZ = 300


# --- the impl region of model.py, verbatim, contract calls stripped ----------

def order4(a, b, c, d, lo, hi):
    """@ContractOnly callee shim: the REAL unchanged ordering callee
    (numpy.ndarray.sort, in-place ascending) on the four centres; the PSeq
    result becomes a plain tuple."""
    arr = np.array([a, b, c, d], dtype=np.float64)
    arr.sort()                                   # the REAL callee
    return (float(arr[0]), float(arr[1]), float(arr[2]), float(arr[3]))


def make_bin_edges(a, b, c, d, col_min, col_max):
    # impl-start (contracts stripped)
    s = order4(a, b, c, d, col_min, col_max)
    m0 = (s[0] + s[1]) / 2
    m1 = (s[1] + s[2]) / 2
    m2 = (s[2] + s[3]) / 2
    result = [col_min, m0, m1, m2, col_max]
    return result
    # impl-end


# --- oracle plumbing ----------------------------------------------------------

class _CentreInjector(object):
    """Stands in for the centre-producing clustering call inside the REAL
    patched `fit`, returning four preset centres. Only the centre production
    is replaced; every boundary-building line that follows is the genuine
    patched repo code."""
    centres = None      # set per case: list of four floats

    def __init__(self, n_clusters=None, init=None, n_init=None, **kw):
        assert n_clusters == 4, "expected the four-centre configuration"

    def fit(self, X):
        self.cluster_centers_ = np.array(
            [[v] for v in _CentreInjector.centres], dtype=np.float64)
        return self


def real_edges_injected(KBinsDiscretizer, cluster_mod, a, b, c, d,
                        col_min, col_max):
    """Run the REAL patched fit on a column whose min/max are the given
    bounds, with the clustering call injecting the given four centres.
    Returns the fitted five-boundary array for the single feature."""
    _CentreInjector.centres = [a, b, c, d]
    saved = cluster_mod.KMeans
    cluster_mod.KMeans = _CentreInjector
    try:
        est = KBinsDiscretizer(n_bins=4, strategy='kmeans', encode='ordinal')
        est.fit(np.array([[col_min], [col_max]], dtype=np.float64))
    finally:
        cluster_mod.KMeans = saved
    return est.bin_edges_[0]


def bridge_centres(column):
    """The shadow's inputs for an end-to-end case: the four centres computed
    from the raw column by the same unchanged deterministic prefix the repo
    uses (uniform-spaced init, single-init 1-D k-means), in the order the
    clustering emits them."""
    from sklearn.cluster import KMeans
    col_min, col_max = column.min(), column.max()
    uniform_edges = np.linspace(col_min, col_max, 5)
    init = (uniform_edges[1:] + uniform_edges[:-1])[:, None] * 0.5
    km = KMeans(n_clusters=4, init=init, n_init=1)
    centres = km.fit(column[:, None]).cluster_centers_[:, 0]
    return [float(v) for v in centres], float(col_min), float(col_max)


def diff_case(shadow_list, real_arr, label, inputs):
    shadow_t = tuple(float(v) for v in shadow_list)
    real_t = tuple(float(v) for v in real_arr)
    if shadow_t != real_t:
        return ("DISAGREEMENT (%s)\n  inputs=%r\n  shadow=%r\n  real=%r"
                % (label, inputs, shadow_t, real_t))
    return None


# --- input generation -----------------------------------------------------------

def boundary_cases():
    """Hand-picked Requires-satisfying centre/bound configurations."""
    return [
        # (a, b, c, d, col_min, col_max)
        (5.0, 5.0, 5.0, 5.0, 0.0, 10.0),          # all centres equal
        (0.0, 0.0, 0.0, 0.0, 0.0, 10.0),          # all at the lower bound
        (10.0, 10.0, 10.0, 10.0, 0.0, 10.0),      # all at the upper bound
        (0.0, 10.0, 0.0, 10.0, 0.0, 10.0),        # bounds, duplicated
        (1.0, 2.0, 3.0, 4.0, 0.0, 10.0),          # already ordered
        (4.0, 3.0, 2.0, 1.0, 0.0, 10.0),          # reverse ordered
        (2.0, 1.0, 4.0, 3.0, 0.0, 10.0),          # arbitrary permutation
        (1.0, 9.0, 2.0, 8.0, 0.0, 10.0),          # out-of-order interleave
        (0.0, 5.0, 5.0, 10.0, 0.0, 10.0),         # ties in the middle
        (-3.0, -1.0, -2.0, -4.0, -5.0, 0.0),      # negative range
        (1e-9, 3e-9, 2e-9, 4e-9, 0.0, 5e-9),      # tiny width
        (-1e12, 1e12, 0.0, 5e11, -1e12, 1e12),    # huge magnitudes
        (0.25, 9.5, 2.5, 6.0, 0.0, 10.0),         # values shaped like the
        (9.5, 0.25, 6.0, 2.5, 0.0, 10.0),         #   shipped-test column
    ]


def fuzz_case(rng):
    lo = rng.uniform(-1e6, 1e6)
    hi = lo + rng.uniform(1e-6, 1e6)              # strict lo < hi
    vals = []
    for _ in range(4):
        r = rng.random()
        if r < 0.05:
            vals.append(lo)                        # pin to a bound sometimes
        elif r < 0.10:
            vals.append(hi)
        else:
            vals.append(rng.uniform(lo, hi))
    return vals[0], vals[1], vals[2], vals[3], lo, hi


def fuzz_column(nprng):
    """A random column with at least two distinct values (so the kmeans
    branch is reached) and enough samples for four clusters."""
    n = int(nprng.randint(6, 16))
    col = nprng.uniform(-100.0, 100.0, size=n)
    col[0] = col[1:].min() - abs(nprng.uniform(0.5, 2.0))  # force distinct
    return np.asarray(col, dtype=np.float64)


def main():
    # REAL patched repo symbols (PYTHONPATH=/testbed, gold patch applied by
    # the gate before this script runs)
    from sklearn.preprocessing import KBinsDiscretizer
    import sklearn.cluster as cluster_mod

    checked = 0
    rng = random.Random(SEED)
    nprng = np.random.RandomState(SEED)

    # --- lane A: injected-centre boundary + fuzz over the model's domain ----
    for a, b, c, d, lo, hi in boundary_cases():
        shadow = make_bin_edges(a, b, c, d, lo, hi)
        real = real_edges_injected(KBinsDiscretizer, cluster_mod,
                                   a, b, c, d, lo, hi)
        err = diff_case(shadow, real, "boundary, injected centres",
                        (a, b, c, d, lo, hi))
        if err:
            print(err)
            return 1
        checked += 1

    for _ in range(N_INJECT_FUZZ):
        a, b, c, d, lo, hi = fuzz_case(rng)
        shadow = make_bin_edges(a, b, c, d, lo, hi)
        real = real_edges_injected(KBinsDiscretizer, cluster_mod,
                                   a, b, c, d, lo, hi)
        err = diff_case(shadow, real, "fuzz, injected centres",
                        (a, b, c, d, lo, hi))
        if err:
            print(err)
            return 1
        checked += 1

    # --- lane B: end-to-end fitted columns, nothing replaced ----------------
    n_fit = 0
    fit_columns = [np.array([0.0, 0.5, 2.0, 3.0, 9.0, 10.0])]  # the shipped-
    for _ in range(N_FIT_FUZZ - 1):                            # test column
        fit_columns.append(fuzz_column(nprng))
    for column in fit_columns:
        centres, col_min, col_max = bridge_centres(column)
        a, b, c, d = centres
        shadow = make_bin_edges(a, b, c, d, col_min, col_max)

        est = KBinsDiscretizer(n_bins=4, strategy='kmeans', encode='ordinal')
        est.fit(column[:, None])
        real = est.bin_edges_[0]
        err = diff_case(shadow, real, "end-to-end fit",
                        {"column": column.tolist(),
                         "bridged_centres": (a, b, c, d),
                         "col_min": col_min, "col_max": col_max})
        if err:
            print(err)
            return 1
        checked += 1
        n_fit += 1

    print("G-CONF OK: shadow impl == real patched bin-edge construction on "
          "%d inputs (%d injected-centre + %d end-to-end fit cases, seed %d)."
          % (checked, checked - n_fit, n_fit, SEED))
    print(json.dumps({"checked": checked, "disagreements": 0, "seed": SEED,
                      "fit_cases": n_fit,
                      "shadow": "direct (contract-stripped impl region; "
                                "@ContractOnly order4 -> real ndarray.sort)"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())

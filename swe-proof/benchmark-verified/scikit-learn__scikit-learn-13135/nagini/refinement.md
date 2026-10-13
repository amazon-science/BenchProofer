# refinement.md — scikit-learn__scikit-learn-13135

The operation-by-operation correspondence between `model.py`'s implementation
(the `make_bin_edges` impl region and the `order4` axiom) and `patch.diff` (the
gold patch). Each step is tagged **R** (type refinement), **A** (axiomatized
callee — **A-consumed**, the proof uses the axiom's `Ensures`; or **A-reference**,
a deep model validated == the real callee by G-AX), or **I** (identical concrete
operation). The claim: *any implementation that verifies against this frozen
spec, refined per the map below, is behaviourally equal to the gold patch on the
tested inputs, so it resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## A. The kmeans bin-edge construction — `KBinsDiscretizer.fit`, kmeans branch

Gold hunk (`sklearn/preprocessing/_discretization.py`):
```
  centers = km.fit(column[:, None]).cluster_centers_[:, 0]
+ # Must sort, centers may be unsorted even with sorted init
+ centers.sort()
  bin_edges[jj] = (centers[1:] + centers[:-1]) * 0.5
  bin_edges[jj] = np.r_[col_min, bin_edges[jj], col_max]
```

| # | model.py impl op (`make_bin_edges`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameters `a, b, c, d: float` (four representative centres) | `centers = …cluster_centers_[:, 0]` — the 1-D centre array | R | `float64` array of centres ↔ `float` arguments at a fixed representative arity (mapping.md §2, §2.1); arity-uniform so it generalises. |
| A2 | parameters `col_min, col_max: float` | `col_min, col_max = column.min(), column.max()` (`_discretization.py:149`) | R | identity on reals; the precondition `col_min <= each centre <= col_max` mirrors "each cluster centre is a mean of column values, so it lies in `[min, max]`". |
| A3 | `s = order4(a, b, c, d, col_min, col_max)` | `centers.sort()` | A-consumed | the unchanged in-place ascending sort; the proof consumes its `Ensures` (length 4, each element in `[lo, hi]`, non-decreasing). G-AX validates the axiom against the REAL `numpy.ndarray.sort` (mapping.md §3.1). This step **is** the fix. |
| A4 | `m0,m1,m2 = (s[k]+s[k+1])/2` for the consecutive sorted centres | `bin_edges[jj] = (centers[1:] + centers[:-1]) * 0.5` | R + I | numpy vectorised pairwise midpoint of the (now sorted) array ↔ the per-pair real midpoint `(s[k]+s[k+1])/2`; the arithmetic is identical, the carrier is the refined real (R), the operation is the same real midpoint (I). |
| A5 | `result = [col_min, m0, m1, m2, col_max]` | `bin_edges[jj] = np.r_[col_min, bin_edges[jj], col_max]` | R | array concatenation (prepend `col_min`, append `col_max`) ↔ list construction; `Result()[0]==col_min`, `Result()[last]==col_max`. |

The discriminating content of the change — **ordering the centres before forming
the midpoints** — lives in step A3 (`order4`, the modeled `centers.sort()`).
Without it (the pre-patch state), the midpoints `(centers[k]+centers[k+1])/2` are
formed from arbitrarily-ordered centres and need not be non-decreasing, so the
boundary list is out of order and the downstream `np.digitize`
(`_discretization.py:255`) raises `ValueError: bins must be monotonically
increasing or decreasing`. `model_prepatch.py` reproduces exactly that
(midpoints from the raw `a,b,c,d` in given order, **no** `order4` call) and
**fails** the postcondition `non_decreasing(ToSeq(Result()))`, which is precisely
the spec sensing the change (G-DIFF).

## B. The downstream monotonicity requirement — `transform`

The boundary list `make_bin_edges` returns is later consumed by
`np.digitize(Xt[:, jj] + eps, bin_edges[jj][1:])` (`_discretization.py:255`),
which is defined only for monotonic bins. The postcondition
`non_decreasing(ToSeq(Result()))` is the contract that the produced boundary
list satisfies this requirement; it is the property the F2P test
(`test_nonuniform_strategies[kmeans-…-expected_5bins1]`) exercises by computing
`fit_transform` on `X = [0, 0.5, 2, 3, 9, 10]` with `n_bins=5` — the case that
raised before the fix and now yields the documented bin assignment
`[0, 0, 1, 2, 3, 4]`.

| # | model.py construct | patch.diff op / repo obligation | tag | justification |
|---|---|---|---|---|
| B1 | `Ensures(non_decreasing(ToSeq(Result())))` | the implicit `np.digitize` monotonicity requirement the fix restores | I | the postcondition is the exact correctness obligation the kmeans bin-edge construction must meet for `transform` to succeed; it is dischargeable only by an impl that orders the centres (A3) before forming midpoints (A4). |

## C. No kind-3 (unexpressible-changed-op) steps

Every step above is R, A-consumed, or I. The one operation that genuinely
*changed* — inserting the sort of the centres — is the **unchanged numeric
callee** `numpy.ndarray.sort` the new code invokes, modeled by the
**A-consumed** axiom `order4` (mapping.md §3.1) and validated against the real
callee by G-AX. There is **no** axiom about the function under change
(`KBinsDiscretizer.fit`): the midpoint/bracket arithmetic (A4, A5) is spelled out
concretely, and the only axiom covers the callee the patch *adds a call to*. No
deep-model A-reference is needed (the changed operation is itself a library
callee, not an inexpressible numeric internal).

## D. verify(model) ⇒ resolved

`make_bin_edges` verifies only if its output is non-decreasing (B1), and — given
the midpoints are formed by the pairwise-midpoint arithmetic of A4/A5 — that
holds only when the centres are arranged in non-decreasing order first (A3). By
R (centre-array ↔ reals, vectorised midpoint ↔ per-pair real midpoint, `np.r_`
bracket ↔ list construction) the verified computation equals
`np.r_[col_min, (centers[1:]+centers[:-1])*0.5, col_max]` over the sorted
`centers`; by G-AX the `order4` axiom soundly over-approximates the real
`numpy.ndarray.sort`. Therefore a model satisfying this spec, refined by the map
above, is the gold patch up to type refinement and the one audited callee — and
the gold patch resolves (G-RESOLVE). The trust points are exactly the two of
PLAN §1.1: axiom soundness (G-AX) and refinement fidelity (this document, G-EQ).

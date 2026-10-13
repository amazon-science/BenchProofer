# refinement.md — scikit-learn__scikit-learn-13135

Operation correspondence between `implementation_binEdges` (Solution.lean) and
`patch.diff`. Tags: **R** type-refinement, **A-consumed** axiom property used by
proof, **A-reference** deep-modeled callee validated == real (G-AX), **I**
identical concrete op.

| # | Lean op (impl region) | patch.diff / repo counterpart | tag |
|---|---|---|---|
| 1 | `let mut cs := centers` | `centers = km.fit(...).cluster_centers_[:, 0]` (centers as input) | R — `np.ndarray` ↔ `List Rat` |
| 2 | `cs := cs.mergeSort (· ≤ ·)` | `centers.sort()` (the inserted fix line) | R — in-place ascending sort ↔ `List.mergeSort (· ≤ ·)` |
| 3 | `midpoints cs` | `(centers[1:] + centers[:-1]) * 0.5` | R — elementwise consecutive average ↔ `midpoints` fold |
| 4 | `colMin :: (… ++ [colMax])` | `np.r_[col_min, …, col_max]` | R — numpy concat ↔ list cons/append |

- Every op is **R** or **I**; no op is inexpressible. No callee is consumed as an
  axiom: `centers` is an input produced by the unchanged `KMeans` routine, so
  there is no A-consumed / A-reference row. `meta.json` records `conf_skip:false`
  (the impl is all-R, mechanically differential-testable by G-CONF).

## How the spec sees the bug (G-DIFF)

The pre-patch impl omits op #2 (`centers.sort()`): it builds
`colMin :: (midpoints centers ++ [colMax])` from the *raw* centers. The spec
requires the result to equal `colMin :: (midpoints cs ++ [colMax])` for some
sorted permutation `cs` of `centers`. When `centers` is unsorted, the raw
midpoints are NOT the midpoints of any sorted permutation (a sorted permutation
yields monotonically non-decreasing midpoints; an unsorted input does not), so no
witness `cs` exists and `correct_binEdges` is unprovable on the discriminating
input — exactly the non-monotonic `bin_edges` that breaks `np.digitize`.

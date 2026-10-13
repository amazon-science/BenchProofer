# mapping.md — scikit-learn__scikit-learn-13135

## Symbol binding (@ base_commit a061ada48efccf0845acae17009553e01764452b)

- Modeled behavior: the cluster-centers → bin-edges computation in the `kmeans`
  branch of `KBinsDiscretizer.fit`.
  - File: `sklearn/preprocessing/_discretization.py`
  - Function: `KBinsDiscretizer.fit`, lines 165–176 (the `elif self.strategy ==
    'kmeans':` block).
  - The patched lines (172–176 region): after `centers` is obtained from the
    clustering routine, the boundaries are
    `bin_edges[jj] = (centers[1:] + centers[:-1]) * 0.5` then
    `bin_edges[jj] = np.r_[col_min, bin_edges[jj], col_max]`.
  - The fix inserts `centers.sort()` immediately before the midpoint
    computation (patch.diff line: `+ centers.sort()`).

## Lean ↔ Python type bijection (used by G-CONF / G-AX)

| Python | Lean | bijection |
|---|---|---|
| `centers` — `np.ndarray` shape `(n_clusters,)` of float64 | `centers : List Rat` | array ↔ list, in order; float64 ↔ exact `Rat` (only order + averaging matter here — DECISIONS.md float rule) |
| `col_min` (`column.min()`) | `colMin : Rat` | scalar ↔ `Rat` |
| `col_max` (`column.max()`) | `colMax : Rat` | scalar ↔ `Rat` |
| `np.r_[col_min, (c[1:]+c[:-1])*0.5, col_max]` | `colMin :: (midpoints cs ++ [colMax])` | numpy concat ↔ list cons/append |
| `centers.sort()` (ascending, in place) | `cs.mergeSort (· ≤ ·)` | in-place ascending sort ↔ `List.mergeSort` with `≤` |
| `(centers[1:] + centers[:-1]) * 0.5` | `midpoints cs` | elementwise average of tail+init ↔ consecutive-pair midpoints |

`centers[1:] + centers[:-1]` is the elementwise sum of the array shifted by one;
`* 0.5` halves it, giving the `n-1` consecutive midpoints. `midpoints` reproduces
this exactly: `midpoints [c₀..cₙ] = [(cₖ+cₖ₊₁)/2]`.

## Callee provenance

- The cluster centers `centers = km.fit(...).cluster_centers_[:, 0]` are produced
  by `KMeans` — an UNCHANGED upstream callee. It is **not** modeled or
  axiomatized: its output `centers` is an *input* to the modeled bin-edge
  computation. The patch does not touch clustering; it only post-processes the
  centers. Hence no `opaque`/`axiom` callee is consumed (G-AX = skip).

## Flag dependency

- The modeled behavior is reached only under `strategy == 'kmeans'` and a
  non-degenerate column (`col_min != col_max`). The constant-column branch
  (lines 151–156) returns `[-inf, inf]` and is out of scope.

## G-CONF fuzz seed

- pinned seed: `13135`

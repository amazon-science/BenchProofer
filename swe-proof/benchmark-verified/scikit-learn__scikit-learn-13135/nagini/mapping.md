# mapping.md — scikit-learn__scikit-learn-13135

Binds every `model.py` symbol to its repository counterpart at
`base_commit = a061ada48efccf0845acae17009553e01764452b`, states the type
abstraction, and gives the provenance of the axiomatized callee.

Repo file under change: `sklearn/preprocessing/_discretization.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `make_bin_edges(a, b, c, d, col_min, col_max)` | the `kmeans` branch of `KBinsDiscretizer.fit` — `sklearn/preprocessing/_discretization.py:165-176` (the bin-edge construction at lines 174-176) | the modeled changed computation: build the bin-boundary list for one feature from its k-means cluster centres |
| `order4(a, b, c, d, lo, hi)` *(axiom — A-consumed)* | `numpy.ndarray.sort()` — the in-place ascending sort the patch adds at `_discretization.py:175` (`centers.sort()`) | unchanged numeric callee the fix invokes; arranges the centres into non-decreasing order |
| `non_decreasing(s)` | the monotonicity precondition of `numpy.digitize(..., bin_edges[jj][1:])` in `KBinsDiscretizer.transform` — `_discretization.py:255` | pure spec: the boundary-ordering property the downstream digitisation step requires (it raises `ValueError: bins must be monotonically increasing or decreasing` otherwise) |

The pre-patch repo state the change fixes (for the refinement audit, not
referenced from the consumer spec view): line 174 reads
`bin_edges[jj] = (centers[1:] + centers[:-1]) * 0.5` operating on `centers`
exactly as returned by `km.fit(...).cluster_centers_[:, 0]` (line 173) — i.e.
in the order the k-means algorithm emits them, with no sort. The gold patch
inserts `centers.sort()` between lines 173 and 174.

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| the 1-D `centers` array `km.fit(column[:, None]).cluster_centers_[:, 0]` (`float64`, `n_bins[jj]` entries, arbitrary order) | the `float` arguments `a, b, c, d` (a representative arity of four centres) | `centers[k]` ↔ the k-th argument; `len(centers)` ↔ the fixed arity 4 |
| `col_min, col_max = column.min(), column.max()` (`_discretization.py:149`) | the `float` arguments `col_min, col_max` | identity; `col_min <= every centre <= col_max` because each cluster centre is a mean of column values, hence inside `[min, max]` |
| `centers.sort()` (in-place ascending sort, the gold addition) | `order4(a, b, c, d, lo, hi)` (returns the four centres in non-decreasing order, within `[lo, hi]`) | the sorted array `centers` ↔ the returned `PSeq[float]`; `centers[k]` after sort ↔ `order4(...)[k]` |
| `(centers[1:] + centers[:-1]) * 0.5` — element-wise interior midpoints (`_discretization.py:174`) | `m_k = (s[k] + s[k+1]) / 2` for the consecutive sorted centres `s = order4(...)` | the k-th element of the midpoint array ↔ `m_k`; numpy vectorised `+`/`* 0.5` ↔ the per-pair real midpoint |
| `np.r_[col_min, bin_edges[jj], col_max]` — prepend `col_min`, append `col_max` (`_discretization.py:176`) | `result = [col_min, m0, m1, m2, col_max]` | array concatenation ↔ list construction; first element `col_min`, last element `col_max` |

`float` is modelled with interpreted reals (`--float-encoding=real`) because the
behaviour at stake is the real-valued ordering relation among the midpoints; no
bit-level precision is involved (the F2P test compares integer bin assignments
that the ordering determines, and the original failure is a hard `ValueError`,
not a rounding effect).

### 2.1 Fixed representative arity

`fit` builds `n_bins[jj]` centres (≥ 2; the F2P test uses 5). The model fixes the
arity at **four centres → three interior midpoints → five boundaries**. This is
the smallest configuration in which an out-of-order boundary list can occur: it
needs at least two adjacent interior midpoints to compare (two centres give a
single interior midpoint, trivially "ordered"; three give two midpoints, the
first non-trivial case; four exercises three midpoints and two interior
comparisons). The boundary computation is uniform in the number of centres — the
k-th boundary depends only on the k-th and (k+1)-th sorted centres — so the
non-decreasing property proven at arity four holds at every arity ≥ 2. The
discriminating behaviour (sort-before-midpoint) and the failing property
(monotonicity) are identical at every arity; the F2P n_bins=5 case is one
instance of the same uniform computation.

## 3. Callee provenance (kind-A — checked by G-AX / axiom_check.py)

### 3.1 `order4` ↔ `numpy.ndarray.sort` (A-consumed)
**Callee:** `numpy.ndarray.sort()` — sorts an array in place into ascending
order. The gold patch adds `centers.sort()` (`_discretization.py:175`); `centers`
is a 1-D `float64` array, so the default kind (quicksort) yields a
non-decreasing arrangement of the same values. Docs:
https://numpy.org/doc/stable/reference/generated/numpy.ndarray.sort.html .

The axiom encodes only what the proof consumes: the result is a
**rearrangement** (same number of elements, each still within the original
`[lo, hi]` bound) that is **non-decreasing** (`Result()[k] <= Result()[k+1]`).
It does NOT claim the result is a permutation by value of the specific inputs
(the proof never needs which value lands where), nor any exact value — the
weakest contract sufficient for the midpoint-monotonicity argument:

  * `len(Result()) == 4` (length-preservation),
  * `lo <= Result()[k] <= hi` for each k (bound-preservation: sorting cannot move
    a value outside the min/max of the inputs, and every input is in `[lo, hi]`),
  * `Result()[k] <= Result()[k+1]` (the non-decreasing order).

These three together are exactly enough to prove each midpoint lies between its
ordered neighbours, the midpoints are non-decreasing, and they are bracketed by
`[col_min, col_max]`, so the whole boundary list is non-decreasing.

**Why the centres can be unsorted (the A-reference fact behind the bug).**
`centers = km.fit(column[:, None]).cluster_centers_[:, 0]` returns the k-means
cluster centres in the order the algorithm assigns cluster labels. Lloyd's
algorithm relabels clusters across iterations, so the final `cluster_centers_`
need not preserve the order of the (sorted) `init` — exactly as the issue
states: "centers may be unsorted even with sorted init"
(`sklearn/cluster/k_means_.py`, `cluster_centers_` set at line 961 from the
solver output, with no post-hoc ordering). Hence the pre-patch midpoints can be
out of order, which makes the downstream `np.digitize` raise. This is the
behaviour the gold patch's `centers.sort()` repairs.

**Soundness check (G-AX):** `axiom_check.py` runs the REAL `numpy.ndarray.sort`
on boundary inputs (already-sorted, reverse-sorted, all-equal, the failing-test
centres, the min/max bounds) plus randomized fuzz over `[lo, hi]`, and asserts
the three `order4` Ensures clauses (length 4, each element in `[lo, hi]`,
non-decreasing). It also reproduces the discriminator: on unsorted centres the
pre-patch midpoint list is NOT monotone while the sorted one is. Imports only
the standard scientific stack `numpy` (the very module the patch calls) and
`random`. Exit 0 iff sound.

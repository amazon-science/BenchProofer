# mapping.md — scikit-learn__scikit-learn-13135

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = a061ada48efccf0845acae17009553e01764452b`, states the type
abstraction (the bijection G-CONF and G-AX use to bridge Lean↔Python), and
gives the provenance of the one deep-model reference.

Repo file under change: `sklearn/preprocessing/_discretization.py`
(`KBinsDiscretizer.fit`, the `strategy == 'kmeans'` branch).

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `computeBoundaries (centers : List Rat) (lo hi : Rat)` | the bin-edge construction in the kmeans branch of `KBinsDiscretizer.fit` — `sklearn/preprocessing/_discretization.py:174-176` | the modeled changed computation: representatives + column endpoints → bin-edge sequence |
| `centers : List Rat` (free input) | `centers = km.fit(column[:, None]).cluster_centers_[:, 0]` — `_discretization.py:173` | the 1-D cluster representatives; produced by the **unchanged** upstream KMeans call, taken as an opaque input here |
| `lo : Rat` / `hi : Rat` | `col_min, col_max = column.min(), column.max()` — `_discretization.py:148` | the column endpoints that bracket the edges |
| `asc (xs : List Rat)` *(deep model — A-reference)* | `ndarray.sort()` — NumPy in-place ascending sort (`centers.sort()`, the line the patch adds, `_discretization.py:175` post-patch) | pure spec: ascending reorder of the representatives; deep model of the unchanged library routine, validated `asc == numpy .sort` by axiom_check.py (G-AX), NOT consumed as an axiom |
| `mids (xs : List Rat)` | `(centers[1:] + centers[:-1]) * 0.5` — `_discretization.py:176` | pure spec: adjacent-pair midpoints |
| `boundaries centers lo hi` | `np.r_[col_min, (centers[1:]+centers[:-1])*0.5, col_max]` — `_discretization.py:177` | pure spec: the full bracketed bin-edge sequence |

The pre-patch behavior the change repairs (refinement audit only, not in the
consumer spec view): the kmeans branch computed `(centers[1:]+centers[:-1])*0.5`
on the representatives **in their original order**; when those representatives
are not ascending the resulting edges are non-monotone and the downstream
`np.digitize` rejects them. The fix inserts the ascending reorder first.

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4.1) and G-AX use to translate values between the
Lean value domain and the Python repo types. A wrong entry surfaces as spurious
G-CONF disagreements.

| repo reality | Lean carrier | bijection |
|---|---|---|
| `centers` — a 1-D `numpy.ndarray` of `float64` cluster representatives | `List Rat` | `a` (ndarray) ↔ `a.tolist()`-shaped `List Rat`; `len(a)` ↔ `l.length`; `a[k]` ↔ `l[k]`; slice `a[1:]`/`a[:-1]` ↔ `List.tail`/init pairing in `mids`. Order is the only observed property; `Rat` is the exact, order-faithful carrier (no IEEE rounding confound — this is an **order-only** fix). |
| `col_min` / `col_max` — `float64` scalars | `Rat` | scalar ↔ `Rat`; bracketing endpoints, never compared for rounding. |
| in-place `centers.sort()` (`_discretization.py:175` post-patch) | `asc` = `mergeSort (· ≤ ·)` | both are total ascending reorderings; on finite (non-NaN) reals NumPy's sort and Python's `sorted` realize the same total order. Validated by G-AX. |
| midpoint `(x + y) * 0.5` | `(x + y) / 2` over `Rat` | exact halving; `* 0.5` ↔ `/ 2` is exact for the order/value relations the bin-edge sequence is observed by. G-CONF bridges by computing `*0.5` on the float side and `/2`-equivalent on the model side over identical inputs. |
| `np.r_[lo, edges, hi]` concatenation | `[lo] ++ mids (asc centers) ++ [hi]` | array concatenation ↔ `List` `++`. |

NaN/inf are out of scope: KMeans cluster centers over finite column data are
finite; the constant-feature column (`col_min == col_max`) takes the earlier
`continue` branch and never reaches this computation (so `centers` here comes
from a genuine ≥2-point spread). G-AX fuzzes finite floats accordingly.

## 3. Callee provenance (kind-A — checked by G-AX / axiom_check.py)

### 3.1 `asc` deep model ↔ `ndarray.sort` (A-reference)
**Callee:** NumPy `numpy.ndarray.sort()` (in-place, default `kind='quicksort'`,
ascending). The changed reordering operation is modeled **deeply** by `asc`
(`xs.mergeSort (· ≤ ·)`) in the pure region; there is **no consumed sort
axiom**. The patch line is `centers.sort()` (`_discretization.py:175`
post-patch), operating on the 1-D `float64` representative array. For finite
reals an ascending sort is uniquely determined up to the ordering of equal
elements, and both NumPy's sort and the `mergeSort (· ≤ ·)` model produce the
same non-decreasing sequence with the same multiset — so the deep model equals
the real callee on the observed property (the resulting order/values).

**Soundness check (G-AX):** `axiom_check.py` runs the real `numpy.ndarray.sort`
on 11 boundary arrays (empty, singleton, reversed, all-equal, ties, the issue
reproducer shape, mixed-magnitude) plus 20 000 randomized finite-float fuzz
arrays, asserting (a) `list(real_sort(c)) == sorted(list(c))` (the `asc` model)
and (b) every result is non-decreasing. Imports only `numpy` (the repo's
mandatory dependency = the real callee) and stdlib `random`. Exit 0 iff sound.

There are **no consumed axioms** in this bundle (the `axioms` region is empty);
`asc` is the sole kind-A obligation and it is an A-reference, not A-consumed.

## 4. G-CONF fuzz seed (pinned for deterministic eval — plan §4.1, §11.3)

`conformance_check.py` seeds its `random.Random` with **`13135`** so the
consumer-side verdict (§11.3) is reproducible. The R/I shadow transliterates
`mids`/`boundaries` (R/I-tagged ops) to NumPy and runs the A-reference `asc` as
the real callee (`ndarray.sort`), per the §4.1 convention (A legs use the real
callee; their model soundness is G-AX's job).

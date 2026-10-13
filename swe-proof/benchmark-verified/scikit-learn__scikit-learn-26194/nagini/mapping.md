# mapping.md — scikit-learn__scikit-learn-26194

Binds every `model.py` symbol to its repository counterpart at
`base_commit = e886ce4e1444c61b865e7839c9cff5464ee20ace`, states the type
abstraction, and gives the provenance of each axiom (callee source + the exact
behaviour the axiom encodes).

Repo file under change: `sklearn/metrics/_ranking.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `anchor_thresholds(thresholds)` | the threshold-anchoring tail of `roc_curve(...)` — `sklearn/metrics/_ranking.py:973` (changed body line 1086) | the modeled changed behaviour: prepend the extra leading threshold so the ROC curve starts at the origin |
| `pos_inf()` *(axiom — A-consumed)* | `numpy.inf` (used at `sklearn/metrics/_ranking.py:1086` post-patch: `np.r_[np.inf, thresholds]`) | unchanged NumPy primitive: the positive-infinity sentinel prepended as the anchoring threshold |
| `is_pos_inf(x)` *(axiom — A-consumed)* | `numpy.isinf` (the test the F2P regression `test_roc_curve_with_probablity_estimates` performs: `np.isinf(thresholds[0])`) | unchanged NumPy primitive: the is-infinite test |

The pre-patch repo expression the change replaces (for the refinement audit,
not referenced from the consumer spec view): `thresholds[0] + 1`
(`sklearn/metrics/_ranking.py:1086` pre-patch), the largest score nudged upward
by one — a finite value.

The modeled function abstracts only the threshold-anchoring step. The earlier
parts of `roc_curve` (`_binary_clf_curve`, the optional `drop_intermediate`
pruning, and the parallel `tps = np.r_[0, tps]` / `fps = np.r_[0, fps]`
prepends) are unchanged by the patch and lie outside the modeled behaviour; the
`thresholds` argument of `anchor_thresholds` is the descending sequence of
distinct finite scores those steps have already produced (always non-empty,
hence `len(thresholds) >= 1`).

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| `thresholds : ndarray of shape (n_thresholds,)`, dtype float, the distinct scores in descending order | `List[float]` of interpreted real numbers | `thresholds[k]` ↔ `thresholds[k]`; `len(thresholds)` ↔ `len(thresholds)`; the descending order is not relied on by the modeled step and is left unconstrained |
| `np.r_[np.inf, thresholds]` (concatenate a leading scalar onto the 1-D array) | `[pos_inf()] + (the original elements)` built by a forward copy loop | the result array's element `0` ↔ `Result()[0]`; element `k+1` ↔ `Result()[k+1] == thresholds[k]`, i.e. `ToSeq(Result()).drop(1) == ToSeq(thresholds)` |
| `numpy` float64 real number | interpreted `float` (`--float-encoding=real`) | the distinguishing behaviour is the real-number identity (infinite vs finite) of the anchoring entry, so the float is interpreted, not int-scaled |

`numpy` array indexing/iteration and `np.r_` concatenation are modelled by a
`List[float]` and a forward append loop; the specification is phrased over
`PSeq[float]` via `ToSeq` for the tail-preservation clause.

## 3. Callee provenance (kind-A — checked by G-AX / axiom_check.py)

### 3.1 `pos_inf` ↔ `numpy.inf` (A-consumed)
**Callee:** `numpy.inf` — IEEE-754 positive infinity (a module-level float
constant; `np.inf == float("inf")`, version-independent). The patch prepends it
as the anchoring threshold (`thresholds = np.r_[np.inf, thresholds]`,
`_ranking.py:1086` post-patch). The axiom's only obligation is
`is_pos_inf(pos_inf())` — the sentinel it returns is infinite. This is the
weakest contract the proof needs (the post-condition `is_pos_inf(Result()[0])`
is discharged by it).

### 3.2 `is_pos_inf` ↔ `numpy.isinf` (A-consumed)
**Callee:** `numpy.isinf` — tests whether a value is positive or negative
infinity (`numpy/_core/umath`; the F2P test calls `np.isinf(thresholds[0])`).
The axiom is an opaque predicate; its only consumed fact is the one `pos_inf`
guarantees (`is_pos_inf(pos_inf())`). It is deliberately under-constrained on
ordinary finite reals so that the pre-patch finite anchoring value
(`thresholds[0] + 1`) cannot satisfy `is_pos_inf` — which is exactly why
`model_prepatch.py` fails the anchoring post-condition (G-DIFF).

**Soundness check (G-AX):** `axiom_check.py` runs the REAL `numpy` primitives
(`np.isinf(np.inf)` is True, `np.inf > 0`, and `finite + 1.0` is never infinite)
and the REAL `roc_curve` on probability-estimate, confidence, tie, extreme and
large-magnitude inputs (9 boundary cases + the exact F2P seed-42 fixture +
5000 randomized fuzz inputs), asserting that the leading threshold is positive
infinity (`np.isinf(thresholds[0]) and thresholds[0] > 0`) and every remaining
threshold is finite. Imports only `numpy` and `sklearn.metrics.roc_curve` — the
very modules/symbols the patched code uses. Exit 0 iff sound. (G-AX runs
in-container against the post-patch `/testbed` sklearn, the real callee under
specification.)

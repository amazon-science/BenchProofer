# refinement.md — scikit-learn__scikit-learn-26194

The operation-by-operation correspondence between `model.py`'s implementation
(the `anchor_thresholds` impl region) and `patch.diff` (the gold patch). Each
step is tagged **R** (type refinement), **A** (axiomatized callee — split into
**A-consumed**, where the proof uses the axiom's `Ensures`, and **A-reference**,
where a deep model is validated == the real callee by axiom_check.py / G-AX),
or **I** (identical concrete operation). The claim: *any implementation that
verifies against this frozen spec, refined per the map below, is behaviourally
equal to the gold patch on the tested inputs, so it resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## A. The threshold-anchoring site — `roc_curve` (`sklearn/metrics/_ranking.py:1086`)

The gold patch's load-bearing hunk (the rest of the diff is docstring/example
prose):

```
- thresholds = np.r_[thresholds[0] + 1, thresholds]
+ # get dtype of `y_score` even if it is an array-like
+ thresholds = np.r_[np.inf, thresholds]
```

The parallel `tps = np.r_[0, tps]` / `fps = np.r_[0, fps]` prepends on the two
preceding lines are UNCHANGED by the patch and lie outside the modeled
behaviour; only the threshold-anchoring expression changed.

| # | model.py impl op (`anchor_thresholds`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `thresholds: List[float]` | `thresholds` (the post-`drop_intermediate` ndarray of distinct finite scores) | R | ndarray of float ↔ `List[float]`; `thresholds[k]` ↔ `thresholds[k]`, `len` ↔ `len` (mapping.md §2). The descending order is not relied on by the anchoring step. |
| A2 | `lead = pos_inf()` | `np.inf` | A-consumed | `pos_inf` is the weakest contract on the unchanged NumPy constant `np.inf` the proof needs: it returns the positive-infinity sentinel (`Ensures(is_pos_inf(Result()))`). The proof consumes this `Ensures` to discharge the anchoring post-condition. G-AX confirms it against the real `np.inf` (`np.isinf(np.inf)`). (mapping.md §3.1) |
| A3 | `result = [lead]` then append every `thresholds[i]` in order (forward copy loop) | `np.r_[np.inf, thresholds]` — concatenate the leading scalar onto the array | R + I | `np.r_[x, arr]` ↔ `[x] + list(arr)`: the result's element 0 is `lead` and elements `1..n` are the original `thresholds` unchanged and in order. Stated structurally as `len(Result())==len(thresholds)+1` and `ToSeq(Result()).drop(1)==ToSeq(thresholds)`. |
| A4 | post-condition `is_pos_inf(Result()[0])` | the property `np.isinf(thresholds[0])` the regression demands | A-consumed | `is_pos_inf` ↔ the unchanged NumPy primitive `np.isinf`; this clause is the discriminator the F2P test `test_roc_curve_with_probablity_estimates` (`assert np.isinf(thresholds[0])`) checks, and the value the F2P `test_roc_curve_drop_intermediate` expects at index 0 (`[np.inf, ...]`). (mapping.md §3.2) |

The discriminating content of the change — the anchoring threshold is the
positive-infinity sentinel rather than the finite `thresholds[0] + 1` — lives in
step A2 (`lead = pos_inf()`, satisfying `is_pos_inf`) consumed by post-condition
A4. The pre-patch expression `thresholds[0] + 1` is a FINITE value;
`model_prepatch.py` reproduces it (`lead = thresholds[0] + 1.0`) and **fails**
the post-condition `is_pos_inf(Result()[0])`, which is exactly the spec sensing
the change (G-DIFF). The tail-preservation clause (A3) and the length clause
ensure no other freedom: any verifying impl produces `[<the infinite sentinel>]`
followed by the unchanged `thresholds`, i.e. the gold transformation.

## B. No kind-3 (unexpressible-changed-op) steps

Every step above is R, A-consumed, or I. The one operation that genuinely
*changed* — which scalar is prepended as the anchoring threshold — is modeled
**directly** in the impl (`lead = pos_inf()`), not hidden behind an axiom about
the function under change (`roc_curve` / the anchoring step is NOT axiomatized).
The two consumed axioms `pos_inf` / `is_pos_inf` cover **unchanged** NumPy
primitives (`np.inf` / `np.isinf`) the new code invokes; their soundness is
audited by G-AX against the real callees and the real `roc_curve`.

## C. verify(model) ⇒ resolved

`anchor_thresholds` verifies only if its leading element satisfies `is_pos_inf`
(A4, dischargeable only via `pos_inf()`, step A2) and only if the remaining
elements are exactly the input thresholds in order (A3) with the length bumped
by one. By R (ndarray ↔ `List[float]`, `np.r_` ↔ prepend) the verified function
equals `np.r_[np.inf, thresholds]` on the post-`drop_intermediate` thresholds;
by G-AX the axioms `pos_inf`/`is_pos_inf` over-approximate the real
`np.inf`/`np.isinf` and the real `roc_curve` yields an infinite leading
threshold with finite tail. Therefore a model satisfying this spec, refined by
the map above, is the gold patch up to type refinement and audited callees — and
the gold patch resolves (G-RESOLVE). The trust points are exactly the two of
PLAN §1.1: axiom soundness (G-AX) and refinement fidelity (this document, G-EQ).

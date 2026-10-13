# mapping.md — scikit-learn__scikit-learn-26194

## Symbol binding (file:line @ base_commit e886ce4e1444c61b865e7839c9cff5464ee20ace)

| Lean symbol | Python symbol | location |
|---|---|---|
| `implementation_rocCurveThresholds` / `problem_spec_rocCurveThresholds` | the threshold-vector construction inside `roc_curve` (the prepend of the leading position) | `sklearn/metrics/_ranking.py:973-1106` (touched line 1086) |
| `Thr` (pure helper) | the dtype of a returned threshold entry: a finite score value, or the non-finite leading sentinel | `_ranking.py:1086` |
| input `ts : List ℚ` | `thresholds` as bound just before the prepend — the decreasing finite score thresholds from `_binary_clf_curve` (optionally thinned by `drop_intermediate`) | `_ranking.py:1080-1086` |
| `result : List Thr` | the `thresholds` array `roc_curve` returns | `_ranking.py:1106` |

The modeled behavior is the **threshold-vector construction** at the end of
`roc_curve`. It is the only behavior the patch changes and the only behavior the
FAIL_TO_PASS tests observe.

### What the function does (base_commit)

```python
fps, tps, thresholds = _binary_clf_curve(y_true, y_score, ...)   # thresholds: decreasing distinct scores
if drop_intermediate and len(fps) > 2:
    optimal_idxs = ...                                           # thin fps/tps/thresholds (orthogonal to fix)
    fps = fps[optimal_idxs]; tps = tps[optimal_idxs]; thresholds = thresholds[optimal_idxs]
# Add an extra threshold position so the curve starts at (0, 0)
tps = np.r_[0, tps]
fps = np.r_[0, fps]
thresholds = np.r_[thresholds[0] + 1, thresholds]   # <-- the changed line (1086)
...
return fpr, tpr, thresholds
```

`thresholds` coming out of `_binary_clf_curve` is the decreasing vector of
distinct score values (`y_score[threshold_idxs]`), so `thresholds[0]` is the
largest score. The leading position prepended to the threshold vector represents
the operating point "no instance predicted positive" — any finite score is
strictly below it.

- **Pre-patch**: `np.r_[thresholds[0] + 1, thresholds]` sets the leading entry to
  `max(y_score) + 1`. For probability-estimate scores in `[0, 1]` this is a finite
  value that can exceed 1, which is the reported defect.
- **Post-patch**: `np.r_[np.inf, thresholds]` sets the leading entry to `+∞`, the
  natural "predict nothing positive" sentinel, regardless of the score scale.

The tail entries (the actual score thresholds) are identical pre- and post-patch.

### Lean modeling

- A returned threshold entry is modeled by `Thr`: `Thr.finite q` for a finite
  score value (`ℚ`, the exact refinement of the float — only order/equality is
  observed here, never transcendental float arithmetic), and `Thr.posInf` for the
  `np.inf` sentinel. The pre-patch `max+1` is a finite value, hence a
  `Thr.finite`, never `Thr.posInf` — this is exactly the discriminator the F2P
  test `np.isinf(thresholds[0])` checks.
- The decreasing finite score thresholds (`_binary_clf_curve` output, optionally
  thinned by `drop_intermediate`) are UNCHANGED by the patch and orthogonal to
  the fix, so they enter as the grounded input `ts : List ℚ`. The post-patch
  construction is `Thr.posInf :: ts.map Thr.finite`; the impl is the `Id.run do`
  skeleton building `out := ts.map Thr.finite` then `out := Thr.posInf :: out`,
  mirroring the `np.r_[np.inf, thresholds]` prepend.
- Domain: the spec and `correct_*` are TOTAL over `ts : List ℚ` (no `ts ≠ []`
  precondition). In the real repo `_binary_clf_curve` always returns at least
  one threshold (it concatenates `y_true.size - 1` as a final index), so the
  non-empty case is the reachable one; but the post-patch construction
  `np.r_[np.inf, thresholds]` is itself total — on an empty vector it yields
  `[inf]`, exactly `Thr.posInf :: [].map Thr.finite`. Making the theorem total
  removes the partial-domain slack a precondition would leave (a wrong impl free
  to return anything on `[]` would otherwise still verify), without demanding
  any behavior the real post-patch prepend does not have.

## Lean ↔ Python type bijection (used by G-CONF / G-AX)

| Python | Lean | bijection |
|---|---|---|
| a finite float threshold value | `Thr.finite (q : ℚ)` | exact-rational refinement; equality/order preserved |
| `np.inf` (the leading sentinel) | `Thr.posInf` | the single non-finite value used | 
| `thresholds` (decreasing scores, before prepend) | `ts : List ℚ` | element-wise, order-preserving |
| returned `thresholds` array | `result : List Thr` | element-wise, order-preserving |

## Callee provenance + flag dependencies

- **No consumed callee axiom.** The behavior the patch changes — the value at the
  leading threshold position — is modeled DEEPLY (a distinct `Thr.posInf`
  constructor vs. the arithmetic `Thr.finite (max+1)`); SPEC_GUIDE §3 forbids
  axiomatizing a deeply-modeled changed op. The `axioms` region is empty and
  **G-AX skips**.
- `_binary_clf_curve` runs upstream of the touched line and is UNCHANGED by the
  patch; its decreasing-threshold output is carried as the grounded input `ts`.
  Not separately modeled; it constrains no output component the spec leaves free
  (the spec pins the full returned vector).
- `drop_intermediate` flag: when true and `len(fps) > 2`, the thresholds are
  thinned before the prepend. This thinning is orthogonal to the fix (it changes
  *which* finite thresholds appear, never the leading sentinel), and its effect is
  already inside the grounded `ts`. The F2P `test_roc_curve_drop_intermediate`
  exercises `drop_intermediate=True`; the leading entry is `np.inf` regardless,
  which the spec pins via `result.head = Thr.posInf`.

## G-CONF fuzz seed

Pinned LCG seed: **26194** (see `conformance_check.py` `SEED`). Corpus: the empty
list (the construction is total), plus randomized
non-empty `ts` lists of decreasing rationals over a range that includes
probability-estimate scales (`[0, 1]`) and wider score scales, plus hand-picked
edge cases (singleton list; list whose head > 1; list whose head ≤ 1; the
docstring example `[0.8, 0.4, 0.35, 0.1]` and the F2P
`[1.0, 0.7, 0.0]` / `[1.0, 0.9, 0.7, 0.6, 0.0]` threshold tails). The R/I shadow
of `implementation_rocCurveThresholds` is diffed against an in-process replica of
the POST-PATCH construction `[+inf] + ts` over ≥1e5 fuzzed inputs.

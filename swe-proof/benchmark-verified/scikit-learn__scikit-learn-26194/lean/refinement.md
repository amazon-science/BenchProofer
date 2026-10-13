# refinement.md — scikit-learn__scikit-learn-26194

Operation-by-operation correspondence between `implementation_rocCurveThresholds`
(Solution.lean impl region) and `patch.diff` (the POST-PATCH threshold-vector
construction in `roc_curve`). Tags: **R** type refinement, **A-consumed** proof
uses an axiom, **A-reference** deep model validated == real callee, **I**
identical concrete op.

| # | Lean impl op | patch.diff / post-patch Python op | tag |
|---|---|---|---|
| 1 | `let mut out := ts.map Thr.finite` | the decreasing finite score-threshold vector returned by `_binary_clf_curve` (optionally thinned by `drop_intermediate`) — bound to `thresholds` just before the prepend | R |
| 2 | `out := Thr.posInf :: out` | `thresholds = np.r_[np.inf, thresholds]` | R |
| 3 | `return out` | `return fpr, tpr, thresholds` (threshold component) | I |

Notes:

- **Every step is R or I — no A.** The modeled behavior is purely the
  construction of the returned threshold vector from the upstream decreasing
  finite thresholds. The fix changes ONLY the value prepended at the leading
  position (op 2): pre-patch `np.r_[thresholds[0] + 1, thresholds]` (the largest
  score plus one), post-patch `np.r_[np.inf, thresholds]` (the positive-infinity
  sentinel). The changed op is modeled DEEPLY (the sentinel is a distinct
  constructor `Thr.posInf`, not the arithmetic `max+1`), so per SPEC_GUIDE §3 it
  is NOT axiomatized; the `axioms` region is empty and **G-AX skips**.
- **R on op 1**: the upstream `_binary_clf_curve` (+ the optional
  `drop_intermediate` thinning) is UNCHANGED by the patch and orthogonal to the
  fix. Its result — the decreasing finite score thresholds — is carried as the
  grounded input `ts : List ℚ` (float thresholds refined to exact rationals;
  order-only / value-carrying, the patch never changes these entries). The
  bijection (float ↔ `Thr.finite ℚ`, `+∞` ↔ `Thr.posInf`) is in mapping.md. This
  leaves no output component free: `result` is fully pinned to
  `Thr.posInf :: ts.map Thr.finite` — both the sentinel head AND every tail entry
  (= the unchanged input threshold) are pinned (directive 5 frame).
- **The fix itself is op 2**: the leading entry. The post-patch impl prepends
  `Thr.posInf`; the pre-patch impl (`Solution_prepatch.lean`) prepends
  `Thr.finite (ts.headD 0 + 1)` — the exact transliteration of
  `thresholds[0] + 1` (largest score, since `ts` is decreasing, plus one). The
  spec's discriminating clause is `result.head = Thr.posInf`: the pre-patch value
  is a `Thr.finite`, never equal to `Thr.posInf`, so the prepatch is unprovable on
  the discriminating clause. This is exactly the bug the issue reports (a finite
  threshold that can exceed 1 for probability estimates) and exactly what the F2P
  tests observe (`np.isinf(thresholds[0])`).
- **G-CONF** mechanically refutes the R/I legs (no A legs): the Python shadow of
  the impl is diffed against an in-process replica of the POST-PATCH threshold
  construction over ≥1e5 fuzzed inputs.

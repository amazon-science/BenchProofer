# refinement.md — scikit-learn__scikit-learn-25232

Operation correspondence between `implementation_initial_fill` (Solution.lean)
and the gold `patch.diff`, under the type bijection in `mapping.md`.
Tags: **R** type refinement · **A-consumed** proof uses axiom · **A-reference**
deep model validated `== real callee` by G-AX · **I** identical concrete op.

| # | Lean impl op | patch.diff / repo counterpart | tag | note |
|---|---|---|---|---|
| 1 | `let fill := fillValue.getD 0` | gold: `fill_value=self.fill_value` forwarded into the inner `SimpleImputer`, whose `fit` maps `None→0` for numerical data (`_base.py:394-400`) | R | `Option Rat` ↔ Python `fill_value` (None ↔ `none`); the `getD 0` encodes the numerical default. THE CHANGED OP — modeled directly, not axiomatized. |
| 2 | `Array.replicate (nFeatures X) fill` | `SimpleImputer._dense_fit` constant branch `np.full(X.shape[1], fill_value)` → `statistics_` (`_base.py:530-533`) | A-reference | deep model of the unchanged constant-fit callee; validated `==` real `SimpleImputer.statistics_` by conformance. |
| 3 | `for row in X / for j in [0:row.size]` + `if v = missingValues then push fill else push v` | `SimpleImputer.transform`: replace each `_get_mask`-flagged (==missing_values) entry with the per-column statistic, else keep (`_base.py:535-`) | A-reference | deep model of the unchanged transform callee; under `strategy="constant"` every column statistic is `fill`, so the replacement value is `fill`. Validated by conformance. |
| 4 | `nFeatures X` (cols of row 0) | `X.shape[1]` | R | array-of-rows ↔ ndarray shape. |
| 5 | return `{statistics, xFilled}` | `_initial_imputation` returns `(Xt, X_filled, …)`; we model `statistics_` (what the F2P test asserts) + `X_filled` | R | structure ↔ tuple; only the two touched, observable components modeled (mapping.md scope). |

No **A-consumed** rows: nothing is left opaque/assumed; the proof discharges the
deep model directly, so `axiom_check.py` is a skip stub.

No changed op is inexpressible: the single changed op (#1, forwarding the
constant) is modeled deeply as `fillValue.getD 0`. The prepatch hard-codes
`0`, dropping `fillValue` — exactly the bug; its `correct_initial_fill` is then
unprovable on the discriminating clause `statistics[j]! = effFill fillValue`
whenever `fillValue = some c, c ≠ 0`.

## G-CONF (R/I legs)
The R/I shadow built in `conformance_check.py` reimplements ops #1,#4,#5 (the R
refinements) and treats #2,#3 (A-reference) by calling the REAL
`SimpleImputer(strategy="constant", fill_value=…)`; it diffs the bridged
`statistics_` / `X_filled` against the patched-behavior reference over fuzzed
numerical matrices. conf_skip = false (impl has R content).

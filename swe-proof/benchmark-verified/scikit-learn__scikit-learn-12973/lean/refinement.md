# refinement.md — scikit-learn__scikit-learn-12973

Maps every operation in `implementation_deliveredCopy` to its `patch.diff`
counterpart in `LassoLarsIC.fit` (`sklearn/linear_model/least_angle.py`).
Tags: **R** type-refinement, **A-consumed** proof uses a callee axiom,
**A-reference** deep-modeled changed op validated == real callee, **I** identical
concrete op.

## The modeled decision
`LassoLarsIC.fit` resolves a per-call duplicate-input boolean against the
estimator's configured value, then delivers the resolved boolean to the data-
preparation step (`_preprocess_data`). The modeled value is exactly that delivered
boolean:

```python
# post-patch LassoLarsIC.fit body (least_angle.py:1503-1504)
if copy_X is None:
    copy_X = self.copy_X
...
X, y, Xmean, ymean, Xstd = LinearModel._preprocess_data(
    X, y, self.fit_intercept, self.normalize, copy_X)   # <-- resolved value delivered
```

We project away the fitted matrices / coefficients (they are functions of the
solver run, not of the resolution edit) and model the boolean delivered to the
data-preparation step.

## Operation correspondence
| # | Lean op (`implementation_deliveredCopy`) | patch.diff op | tag | note |
|---|---|---|---|---|
| 1 | `configured : Bool` | `self.copy_X` (`__init__` field, `least_angle.py:1477`) | R | the estimator reduced to its one participating field; Python `bool` ↔ Lean `Bool` (mapping.md). |
| 2 | `call : CallChoice` (`Option Bool`) | the `fit` argument `copy_X` (default `None` post-patch, `least_angle.py:1482`) | R | the optional per-call choice; `{None,True,False}` ↔ `{none,some true,some false}` (mapping.md). |
| 3 | `let mut copyX := call; if copyX = none then copyX := some configured` | `if copy_X is None: copy_X = self.copy_X` (`least_angle.py:1503`) | I | identical control flow: when no per-call value is supplied, fall back to the configured value. `none ↔ None`; the assignment overwrites the local with the field. |
| 4 | `return copyX.getD configured` | `LinearModel._preprocess_data(..., copy_X)` — deliver the resolved boolean to the data-preparation step (`least_angle.py:1504`) | R | the modeled observable is the boolean delivered to the data-prep step. After op #3 `copyX` is `some _`, so `.getD configured` returns the resolved value; this equals `call.getD configured`. G-CONF drives the real `fit` and captures the delivered boolean. |

Every op is R or I; **no A row** (no axiom consumed, no deep-model reference of an
unchanged callee — `_preprocess_data`/`lars_path` are not modeled, only the boolean
threaded into the data-prep step). Therefore `meta.json axioms = []`,
`deep_model_references = []`, and `axiom_check.py` is a skip stub.

## Prepatch (G-DIFF)
`Solution_prepatch.lean` replaces ops #3–#4 with the pre-patch behavior: the
per-call choice is discarded and the configured field is delivered to the data-
preparation step directly (`return configured`, mirroring `_preprocess_data(...,
self.copy_X)`). The carried gold proof then leaves the unsolvable goal
`configured = call.getD configured`, so the prepatch fails G-VERIFY exactly when
`call = some b` with `b ≠ configured` — the discriminating clause the F2P test
exercises (`fit(copy_X=False)` on a `copy_X=True` default → delivered must be
`False`, not `True`).

## conf_skip
The impl region is all-R/I (op #4 is the delivery refinement, validated against the
real `fit`). `conf_skip = false`; `conformance_check.py` drives the real patched
`fit` and diffs the boolean delivered to `_preprocess_data` against the shadow.

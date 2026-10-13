# mapping.md — scikit-learn__scikit-learn-12973

## Instance
- repo: `scikit-learn/scikit-learn`
- base_commit: `a7b8b9e9e16d4e15fabda5ae615086c2e1c47d8a`
- modeled file: `sklearn/linear_model/least_angle.py`
- modeled function: `LassoLarsIC.fit`
- F2P test: `sklearn/linear_model/tests/test_least_angle.py::test_lasso_lars_fit_copyX_behaviour[False]`

## What the fix does (issue + gold patch)
`LassoLarsIC` carries a `copy_X` boolean configured at construction
(`self.copy_X`). Its `fit` method ALSO accepts a `copy_X` argument of the same
meaning. Pre-patch the two values were used inconsistently:

```python
# pre-patch LassoLarsIC.fit (least_angle.py:1482, 1503-1504)
def fit(self, X, y, copy_X=True):
    X, y = check_X_y(X, y, y_numeric=True)
    X, y, Xmean, ymean, Xstd = LinearModel._preprocess_data(
        X, y, self.fit_intercept, self.normalize, self.copy_X)   # <-- uses the FIELD
    ...
    alphas_, active_, coef_path_, self.n_iter_ = lars_path(
        X, y, ..., copy_X=copy_X, ...)                            # <-- uses the ARG
```

The data-preparation step `_preprocess_data` is the operation that actually
duplicates (or overwrites in place) the feature matrix `X`; it was handed the
instance field `self.copy_X`, while the `fit`-time argument `copy_X` was only
forwarded to `lars_path`. So a user who set `LassoLarsIC(copy_X=False)` and called
`fit(X, y)` had their choice silently overridden at the duplication site (the field
default `True` was used), and a user passing `fit(X, y, copy_X=False)` had no effect
on the duplication site at all.

The patch makes `fit(self, X, y, copy_X=None)`: a per-call `None` means "fall back
to the configured value", an explicit boolean overrides it, and the resolved value
is the one delivered to `_preprocess_data`:

```python
# post-patch
def fit(self, X, y, copy_X=None):
    if copy_X is None:
        copy_X = self.copy_X
    X, y = check_X_y(X, y, y_numeric=True)
    X, y, Xmean, ymean, Xstd = LinearModel._preprocess_data(
        X, y, self.fit_intercept, self.normalize, copy_X)        # <-- uses the RESOLVED value
    ...
```

The single observable behavior the fix changes is the boolean delivered to the
data-preparation step (`_preprocess_data`'s `copy` argument), as a function of the
configured field and the optional per-call argument.

## Symbol binding (file:line @ base_commit)
| Lean symbol | Python symbol | location @ base_commit | role |
|---|---|---|---|
| `configured : Bool` | `self.copy_X` | set in `LassoLarsIC.__init__`, `least_angle.py:1477`; read at `least_angle.py:1504` | the construction-time configured duplicate-input boolean |
| `call : CallChoice` (`Option Bool`) | the `fit` argument `copy_X` (default `None` post-patch) | `fit` signature, `least_angle.py:1482` (post-patch `copy_X=None`) | the optional per-call duplicate-input boolean |
| `resolveCopy` / `implementation_deliveredCopy` | the resolution `if copy_X is None: copy_X = self.copy_X` then `_preprocess_data(..., copy_X)` | `least_angle.py:1503-1504` (post-patch) | resolves the per-call/optional choice and delivers it to the data-prep step |
| modeled result (`Bool`) | the `copy` argument value `_preprocess_data` is called with | `LinearModel._preprocess_data` call, `least_angle.py:1504` | the boolean delivered to the data-preparation step |

## Lean ↔ Python type bijection (used by G-CONF / G-AX)
| Python | Lean | note |
|---|---|---|
| `bool` `self.copy_X` | `Bool` (`configured`) | the configured duplicate-input flag |
| `fit` arg `copy_X` ∈ {`None`, `True`, `False`} | `Option Bool` (`CallChoice`): `None`↔`none`, `True`↔`some true`, `False`↔`some false` | the optional per-call choice |
| the `copy` value handed to `_preprocess_data` | `Bool` (modeled result) | the boolean delivered to the data-preparation step |
| `if copy_X is None: copy_X = self.copy_X` | `Option.getD call configured` (`resolveCopy configured call`) | `None` falls back to the field; explicit value wins |

## Callee provenance / flag deps
- The modeled value is the boolean threaded into the data-preparation step. The
  data-preparation step `_preprocess_data` and the path solver `lars_path` are
  **not** modeled — only the boolean that `_preprocess_data` is built with is. No
  unchanged callee contract is consumed (no axiom, no A-reference): the resolution
  is pure data flow (R/I), validated by G-CONF against the REAL `fit`.
- No flag dependency on the algorithm: `_preprocess_data` always receives the
  resolved boolean regardless of `precompute`/`criterion`. The F2P test uses
  `precompute=False`.

## G-CONF
- Oracle: drives the REAL patched `LassoLarsIC.fit` in-container; a monkeypatch on
  `LinearModel._preprocess_data` captures the `copy` boolean it is called with
  (then short-circuits the rest of `fit` via a sentinel exception so the expensive
  path solve is skipped). This exercises the genuine
  `__init__ → fit(copy_X=...) → resolve → _preprocess_data(copy=...)` path.
- Shadow: transliteration of `implementation_deliveredCopy`
  (`resolveCopy(configured, call) = call.getD configured`).
- Diff: assert captured `_preprocess_data` `copy` boolean == shadow for every
  fuzzed `(self.copy_X, fit copy_X ∈ {None, True, False})` over ≥10⁵ inputs.
- Pinned fuzz seed: **12973** (also in conformance_check.py).

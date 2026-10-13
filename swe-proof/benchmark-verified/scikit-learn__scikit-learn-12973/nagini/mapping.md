# mapping.md — scikit-learn__scikit-learn-12973

Binds every `model.py` symbol to its repository counterpart at
`base_commit = a7b8b9e9e16d4e15fabda5ae615086c2e1c47d8a`, states the type
abstraction, and documents callee provenance.

Repo file under change: `sklearn/linear_model/least_angle.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `fit(config, data, copy_X)` | `LassoLarsIC.fit(self, X, y, copy_X=True)` — `sklearn/linear_model/least_angle.py:1482` | the modeled changed method (the fitting routine) |
| `Estimator.default_copy` | `self.copy_X` set in `LassoLarsIC.__init__` (`least_angle.py:1477`, from the `copy_X=True` ctor parameter at line 1470) | the construction-time default copy preference |
| `InputArray.intact` | the observable "is the training array `X` still equal to its original content" — what the F2P test reads via `np.array_equal(X, X_copy)` (`tests/test_least_angle.py`, added `test_lasso_lars_fit_copyX_behaviour`) | the input array's post-fit preservation status |
| `InputArray.native_format` | whether the caller's `X` already satisfies `check_array`'s accepted float dtypes (`dtype=FLOAT_DTYPES` inside `LinearModel._preprocess_data` → `check_array`, `sklearn/utils/validation.py`) so validation does NOT have to allocate a converted array. `True` ↔ e.g. a `float64` ndarray (in-place mutation of the caller's buffer is possible); `False` ↔ e.g. an integer-dtype ndarray (validation converts to float, allocating a NEW array regardless of the copy flag, so the caller's array is shielded) | whether preprocessing can even reach the caller's buffer |
| `copy_X` (param, `Optional[bool]`) | `copy_X` parameter of `fit` (`least_angle.py:1482`) | the per-call copy preference; `None` = caller did not supply one |
| `selected_preference(default_copy, per_call)` *(pure spec)* | the resolution `copy_X = copy_X if copy_X is not None else self.copy_X` (post-patch `if copy_X is None: copy_X = self.copy_X`, gold hunk at `least_angle.py:1503-1504`) | the effective preference that governs preprocessing |

The pre-patch repo reality the change fixes (for the refinement audit, not
referenced from the consumer spec view): `fit`'s parameter defaulted to
`copy_X=True` and the preprocessing call used `self.copy_X` directly
(`_preprocess_data(X, y, self.fit_intercept, self.normalize, self.copy_X)`,
`least_angle.py:1503-1504`), while the per-call `copy_X` reached only the
`lars_path` call (`least_angle.py:1509-1510`). Thus a per-call `copy_X` was
silently discarded by preprocessing.

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| `self.copy_X` (a Python `bool` attribute of the estimator) | `Estimator.default_copy : bool` | identity on the boolean value; only this one touched field is modeled |
| `fit`'s `copy_X` argument (`bool` or "argument absent"/`None`) | `copy_X : Optional[bool]` | `True`/`False` ↔ the bool; the gold default `None` ("caller supplied nothing") ↔ Python `None` |
| training array `X : np.ndarray` and the per-call observation `np.array_equal(X, X_copy)` | `InputArray.intact : bool` | `intact == True` ↔ `X` is byte-for-byte its original content (it was copied — or shielded by a dtype-conversion allocation — never overwritten); `intact == False` ↔ `X` was mutated in place during preprocessing. The F2P test reads exactly this one boolean. |
| `X.dtype` being an accepted float working dtype (`FLOAT_DTYPES` in `check_array`) vs anything else (e.g. integer) | `InputArray.native_format : bool` | `native_format == True` ↔ `X.dtype` already satisfies `check_array(dtype=FLOAT_DTYPES)`, so with `copy=False` the caller's own buffer flows into preprocessing and can be mutated in place; `native_format == False` ↔ validation must allocate a converted float array (`check_array` conversion), so the caller's `X` stays intact REGARDLESS of the copy flag. Beyond this dtype-nativeness bit, the contents/shape of `X` are irrelevant to the tested behaviour and omitted. |
| return value `self` (the fitted estimator) | `bool` = the effective copy preference that governed preprocessing | The model returns the governing preference rather than the estimator; this is the value that determines `intact` and that the gold patch routes to BOTH `_preprocess_data` and `lars_path`. The estimator-return is not observed by the F2P tests for this behaviour. |

## 3. Callee provenance

No `@ContractOnly` axiom is consumed by this proof, and there is no deep-model
A-reference either. The changed behaviour is entirely a **boolean dataflow** —
the selection of the governing copy preference and the consequent in-place vs.
copied fate of the input array — which is fully expressible in Nagini and is
modeled directly.

The unchanged callees the real `fit` invokes are recorded here for completeness
(none needs axiomatization because the model does not call them — their only
relevance to the tested behaviour is the boolean property below, which the
model encodes directly as `InputArray.intact == (effective or not
native_format)`):

- `LinearModel._preprocess_data(X, y, fit_intercept, normalize, copy)`
  (`sklearn/linear_model/base.py:93`). Relevant property: it validates via
  `check_array(X, copy=copy, dtype=FLOAT_DTYPES, ...)` (`base.py:117`). When
  `X` is already an accepted float dtype: `copy=True` copies `X` so the
  caller's `X` is left intact, `copy=False` lets preprocessing mutate `X` in
  place (`X -= X_offset`, `base.py:150`). When `X` is NOT an accepted float
  dtype (e.g. integer), `check_array` must allocate a NEW converted float
  array regardless of `copy`, so the caller's `X` is left intact under EITHER
  flag — this is the `not native_format` disjunct in the model's intact
  postcondition. The gold patch's behavioural change is to pass the *resolved
  per-call* `copy_X` here instead of `self.copy_X` (`least_angle.py:1503-1504`).
  Doc/source evidence: `check_array`'s `copy`/`dtype` arguments
  (`sklearn/utils/validation.py`), and `_preprocess_data`'s body.
- `lars_path(..., copy_X=copy_X, ...)` (`least_angle.py:1509-1510`) — already
  received the per-call `copy_X` even pre-patch; unchanged by the fix.

Because nothing is axiomatized, `axiom_check.py` performs the corresponding
sanity role for this instance: it executes the **real** `LassoLarsIC.fit` in
the scikit-learn install (in-container) under both code paths and asserts the
modeled boolean property — that `np.array_equal(X, X_copy)` after `fit` equals
`selected_preference(default_copy, per_call) or not native_format` — holds
across the boundary + fuzzed combinations of `(__init__ copy_X, fit copy_X,
X dtype nativeness)`. This validates that the deep boolean model agrees with
the real estimator's observable behaviour, including on non-float input dtypes
(the domain where the pre-repair model was unfaithful).

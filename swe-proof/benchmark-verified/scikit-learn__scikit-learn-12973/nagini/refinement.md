# refinement.md — scikit-learn__scikit-learn-12973

The operation-by-operation correspondence between `model.py`'s implementation
(the `fit` impl region + the deep `selected_preference` model) and `patch.diff`
(the gold patch). Each step is tagged **R** (type refinement), **A-consumed**
(the proof uses an axiom's `Ensures`), **A-reference** (a deep model validated
== the real callee by axiom_check.py / G-AX), or **I** (identical concrete
operation). The claim: *any implementation that verifies against this frozen
spec, refined per the map below, is behaviourally equal to the gold patch on the
tested inputs, so it resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## The fix — `LassoLarsIC.fit` (`sklearn/linear_model/least_angle.py`)

Gold hunks:
```
- def fit(self, X, y, copy_X=True):
+ def fit(self, X, y, copy_X=None):
  ...
+ if copy_X is None:
+     copy_X = self.copy_X
  X, y = check_X_y(X, y, y_numeric=True)
  X, y, Xmean, ymean, Xstd = LinearModel._preprocess_data(
-     X, y, self.fit_intercept, self.normalize, self.copy_X)
+     X, y, self.fit_intercept, self.normalize, copy_X)
```

| # | model.py impl op (`fit`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| 1 | parameter `copy_X : Optional[bool]` | `def fit(self, X, y, copy_X=None)` | R | the gold default `None` ("caller supplied no per-call preference") ↔ Python `None`; `True`/`False` ↔ the bool (mapping.md §2). |
| 2 | parameter `config : Estimator` with `config.default_copy` | `self` carrying `self.copy_X` (set in `__init__` from the ctor `copy_X`, `least_angle.py:1470,1477`) | R | only the one touched field `self.copy_X` is modeled as `Estimator.default_copy : bool` (mapping.md §1,§2); read-only ⇒ fractional permission `Acc(config.default_copy, 1/2)`. |
| 3 | `if copy_X is None: copy_X = config.default_copy` | `if copy_X is None: copy_X = self.copy_X` | I | identical concrete control flow and assignment on the modeled bool/Optional carrier — the new resolution line, verbatim under the R type-rename. |
| 4 | `effective = copy_X` (the resolved preference, now a `bool`) | the post-resolution local `copy_X` value | I | identity binding; `effective` is the value the gold passes as `copy=` to `_preprocess_data` AND as `copy_X=` to `lars_path`. |
| 5 | `if data.native_format: data.intact = effective else: data.intact = True` | `_preprocess_data(X, y, ..., copy_X)` — validation (`check_array(X, copy=copy_X, dtype=FLOAT_DTYPES)`) copies `X` when `copy_X` is True; when `copy_X` is False it lets preprocessing overwrite the caller's buffer in place ONLY if `X` is already an accepted float dtype — a non-float `X` forces a dtype-conversion allocation that shields the caller's array either way | A-reference | the changed dataflow's *consequence* is modeled **deeply**: `InputArray.intact == (effective or not native_format)` IS the property "the input array is intact iff the governing preference is True or validation had to materialize a converted working copy". There is **no consumed `_preprocess_data` axiom**; instead the deep boolean model is validated **== the real callee** out-of-band by G-AX: axiom_check.py runs the real `LassoLarsIC.fit` (float64 AND integer-dtype inputs) and asserts `np.array_equal(X, X_copy) == (selected_preference(default_copy, per_call) or not native_format)` (mapping.md §3). The real `_preprocess_data` has exactly this behaviour via `check_array(X, copy=copy_X, dtype=FLOAT_DTYPES)` (`base.py:117`). |
| 6 | `return effective` | `return self` | R | the model returns the governing preference (the value that determines the array's fate and that the gold routes to both downstream calls) instead of the estimator object; the estimator-return is not observed by the F2P behaviour (mapping.md §2). The fitting routine's *tested* output is the array-mutation effect, captured by step 5. |

`selected_preference(default_copy, per_call)` (pure region) is the spelled-out
resolution `per_call if per_call is not None else default_copy` — the I-step-3
control flow lifted into a `@Pure` spec helper so the postcondition can name the
governing preference. It is part of the deep model, not an axiom.

## The discriminating behaviour (G-DIFF)

The single behavioural change is: the preference that governs preprocessing must
be the **per-call** `copy_X` when the caller supplies one, instead of always
`self.copy_X`. `model_prepatch.py` reproduces the pre-patch dataflow
(`effective = config.default_copy`, ignoring the per-call argument; the
format-conversion shield `data.intact = True` on non-native input is identical
in both twins, since validation behaviour did not change) under the
byte-identical spec, and **fails** the postcondition
`Result() == selected_preference(Old(config.default_copy), copy_X)` — exactly
when `copy_X == False` and `config.default_copy == True` (the F2P case
`test_lasso_lars_fit_copyX_behaviour[False]`: a default-constructed `LassoLarsIC`
whose `fit(X, y, copy_X=False)` must overwrite `X`, i.e. selected preference
False, but the pre-patch routes `self.copy_X == True` to preprocessing and so
leaves `X` intact). That is the spec sensing the change.

## No kind-3 (unexpressible-changed-op) steps

Every step above is R, A-reference, or I. The operation that genuinely *changed*
— the selection of which copy preference governs preprocessing, and its
consequence for the input array — is modeled **directly** (steps 3-5: a boolean
resolution plus the `intact == effective` deep property), not hidden behind an
axiom about a function under change. There is **no consumed `@ContractOnly`
axiom** (`axioms` region empty); the only callee-relevant property (copy iff
flag) is an **A-reference** validated against the real `LassoLarsIC.fit` /
`_preprocess_data` by axiom_check.py (G-AX).

## verify(model) ⇒ resolved

`fit` verifies only if (a) it returns the per-call preference when supplied and
the construction default otherwise (step 3-4 ⇒ postcondition 1) and (b) it
leaves the input array intact iff that selected preference is True or the array
was not in the native working format (step 5 ⇒ postcondition 2). By R
(bool/Optional carrier, the touched fields, the array's intact-boolean and
dtype-nativeness bit) the verified `fit` equals the gold `fit` on the tested
inputs; by G-AX the deep boolean model `intact == (effective or not
native_format)` equals the real `_preprocess_data`'s behaviour (copy-iff-flag
on native-dtype input, conversion-shielded otherwise) (A-reference). Therefore a model
satisfying this spec, refined by the map above, is the gold patch up to type
refinement and the audited boolean property — and the gold patch resolves
(G-RESOLVE). The trust point reduces to the single A-reference (G-AX); there is
no axiom-soundness trust point because no axiom is consumed.

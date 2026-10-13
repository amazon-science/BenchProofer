# refinement.md — scikit-learn__scikit-learn-10297

Maps every operation in `implementation_initClassifierCV` to its `patch.diff`
counterpart in `RidgeClassifierCV.__init__` (`sklearn/linear_model/ridge.py`).
Tags: **R** type-refinement, **A-consumed** proof uses a callee axiom,
**A-reference** deep-modeled changed op validated == real callee, **I** identical
concrete op.

## Patch (behavioral hunk — the constructor)
```python
def __init__(self, alphas=(0.1, 1.0, 10.0), fit_intercept=True,
             normalize=False, scoring=None, cv=None, class_weight=None,
             store_cv_values=False):                       # <- flag added
    super(RidgeClassifierCV, self).__init__(
        alphas=alphas, fit_intercept=fit_intercept, normalize=normalize,
        scoring=scoring, cv=cv, store_cv_values=store_cv_values)   # <- forwarded
    self.class_weight = class_weight
```
At base the signature has no `store_cv_values` and the `super().__init__(...)`
call omits it; the parent `_BaseRidgeCV.__init__` already accepts and stores it
(`self.store_cv_values = store_cv_values`). The other three hunks of the gold
patch are docstring-only (re-flow + duplicating the parameter doc onto the
classifier) and have NO behavioral effect.

The modeled value is the estimator's STORED CONFIGURATION after construction (the
touched `self.*` attributes), as a function of the constructor's options.

## Operation correspondence
| # | Lean op (`implementation_initClassifierCV`) | patch.diff op | tag | note |
|---|---|---|---|---|
| 1 | `let mut cfg := { alphas, fitIntercept, normalize, scoring, cv, storeCvValues, classWeight := none }` | `super(...).__init__(alphas=…, fit_intercept=…, normalize=…, scoring=…, cv=…, store_cv_values=store_cv_values)` — the parent init assigns each kwarg to the like-named `self.*` (`_BaseRidgeCV.__init__`, `ridge.py:1092-1098`) | R/I | the delegation that records the forwarded options. Type bijections (`List Rat`, `Bool`, `Option Nat`) in mapping.md; the forwarded `store_cv_values` ↔ `storeCvValues` is the bit the fix restores. `class_weight` is set after the super call, so it is initialized to `none` here and overwritten next. |
| 2 | `cfg := { cfg with classWeight := classWeight }` | `self.class_weight = class_weight` | R/I | record the per-class weighting selection on top of the base configuration. `class_weight : None\|dict` (identity) ↔ `classWeight : Option Nat`. |
| 3 | `return cfg` | the constructed estimator's stored configuration consumed by a later `fit` | I | return the stored configuration. |

Every op is R or I; **no A row** (no axiom consumed, no deep-model reference of an
unchanged callee — the parent initializer's per-kwarg storage is modeled
directly). Therefore `meta.json axioms = []`, `deep_model_references = []`, and
`axiom_check.py` is a skip stub.

## R/I legs ⇒ G-CONF
The whole impl is R/I, so `conformance_check.py` mechanically differential-tests
the impl shadow against the REAL patched constructor's stored attributes over
≥10^5 fuzzed option tuples (reading back `alphas`, `fit_intercept`, `normalize`,
`scoring`, `cv`, `class_weight`, `store_cv_values`). `conf_skip = false`.

## Prepatch = the real bug
Pre-patch, `RidgeClassifierCV.__init__` has no `store_cv_values` parameter and
does not forward it; the parent init therefore leaves `self.store_cv_values` at
its default `False`. Passing `store_cv_values=True` to the constructor at base in
fact raises `TypeError: __init__() got an unexpected keyword argument
'store_cv_values'` — observably, the retention selection cannot reach the stored
configuration. The prepatch impl models this as the forwarded value being fixed
to `false` (`storeCvValues := false`), independent of the supplied
`storeCvValues`. It therefore cannot satisfy `problem_spec_initClassifierCV` on
the discriminating clause `result.storeCvValues = storeCvValues` whenever
`storeCvValues = true` — precisely the case the FAIL_TO_PASS test
`test_ridge_classifier_cv_store_cv_values` exercises (it constructs
`RidgeClassifierCV(alphas=…, store_cv_values=True)` and reads `cv_values_` after
`fit`). The carried gold proof body (a 7-fold `rfl`) fails to typecheck against
the buggy impl on the `storeCvValues` conjunct (G-DIFF, confirmed: exit 1 at the
`storeCvValues` `rfl`).

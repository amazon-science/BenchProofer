# refinement.md — scikit-learn__scikit-learn-11310

Maps every operation in `implementation_refitTiming` to its `patch.diff`
counterpart. Tags: **R** (type refinement), **A-consumed** (proof uses an axiom's
property), **A-reference** (deep model validated == real callee by G-AX), **I**
(identical concrete op). Every step is R, A, or I.

## Modeled function: `refitTiming` (`BaseSearchCV.fit`, the refit block)

Post-patch repo code (`patch.diff`, `sklearn/model_selection/_search.py`):
```python
        if self.refit:
            self.best_estimator_ = clone(base_estimator).set_params(
                **self.best_params_)
            refit_start_time = time.time()
            if y is not None:
                self.best_estimator_.fit(X, y, **fit_params)
            else:
                self.best_estimator_.fit(X, **fit_params)
            refit_end_time = time.time()
            self.refit_time_ = refit_end_time - refit_start_time
```

Lean impl (`implementation_refitTiming`):
```lean
def implementation_refitTiming
    (refitEnabled : Bool) (startClock endClock : ℚ) : Option ℚ := Id.run do
  let mut refitDuration : Option ℚ := none
  if refitEnabled then
    let s := startClock
    let e := endClock
    refitDuration := some (e - s)
  return refitDuration
```

| # | Lean op | patch.diff op | tag | note |
|---|---|---|---|---|
| 1 | `let mut refitDuration : Option ℚ := none` | the `refit_time_` attribute starts unset (absent when `self.refit` is falsy) | R | `Option ℚ`: `none` ↔ attribute absent, `some d` ↔ `self.refit_time_ == d`. The pre-patch code never assigns it → it is absent. |
| 2 | `if refitEnabled then …` | `if self.refit:` | R | `refitEnabled : Bool` ↔ truthiness of `self.refit`. The whole timing observable is gated by this branch (identical control flow). |
| 3 | `let s := startClock` | `refit_start_time = time.time()` | R | the wall-clock reading taken immediately before the refit; `time.time()` (a `float` second count) ↔ `startClock : ℚ`. |
| 4 | *(refit happens between the two readings — abstracted)* | `clone(...).set_params(...)`; `self.best_estimator_.fit(X, y, ...)` | I | unchanged by the patch; its only modeled effect is that it occurs between the two readings. Not part of the modeled observable (and the spec imposes no side condition on the readings — the recording is the unconditional subtraction). |
| 5 | `let e := endClock` | `refit_end_time = time.time()` | R | the wall-clock reading taken immediately after the refit; ↔ `endClock : ℚ`. |
| 6 | `refitDuration := some (e - s)` | `self.refit_time_ = refit_end_time - refit_start_time` | R | the elapsed duration is recorded as the observable; subtraction of the two readings is the identical arithmetic, `some` marks the attribute as present. |
| 7 | `return refitDuration` | (the attribute's final value) | I | the observable the modeled block produces. |

No op in the impl is changed-yet-inexpressible: the whole patch is an additive
recording of an elapsed wall-clock duration, modeled exactly as the difference of
two rational clock readings under the refit gate.

## Refinement summary
- **R** rows: 1, 2, 3, 5, 6 (the `Bool`/`ℚ`/`Option ℚ` type bijection for the
  refit flag, the two clock readings, and the recorded-vs-absent attribute).
- **I** rows: 4 (the unchanged clone+fit, abstracted to "time elapses"), 7.
- **A-consumed**: none.
- **A-reference**: none (no callee is deeply modeled; the only modeled operation
  is the arithmetic on the two reading inputs).

The R/I legs are differential-tested by G-CONF (`conformance_check.py`). There is
no A leg, so G-AX is a skip stub.

# mapping.md — scikit-learn__scikit-learn-11310

## Symbol binding (file:line @ base_commit 553b5fb8f84ba05c8397f26dd079deece2b05029)

| Lean symbol | Python symbol | location |
|---|---|---|
| `implementation_refitTiming` / `problem_spec_refitTiming` | the refit block of `BaseSearchCV.fit` | `sklearn/model_selection/_search.py:766-772` (base) / the post-patch block lines `766-775` |
| `result : Option ℚ` | `self.refit_time_` attribute (present iff set) | `_search.py:774` (post-patch added line `self.refit_time_ = ...`) |

The modeled function is the refit block inside `BaseSearchCV.fit`. It is the only
behavior the patch changes (the other hunks add documentation only — see below).
The F2P test `test_search_cv_timing` exercises exactly this: after fitting a
search estimator with `refit` enabled, the estimator must have a `refit_time_`
attribute that is a `float` and `>= 0`.

### What the function does (base_commit, pre-patch)

```python
        if self.refit:
            self.best_estimator_ = clone(base_estimator).set_params(
                **self.best_params_)
            if y is not None:
                self.best_estimator_.fit(X, y, **fit_params)
            else:
                self.best_estimator_.fit(X, **fit_params)
```

When `self.refit` is truthy the best model is refit on the whole dataset. The
pre-patch code records nothing about how long that refit took: there is no
`refit_time_` attribute, so `hasattr(search, "refit_time_")` is `False` and the
F2P test fails.

### What the patch changes

```python
+            refit_start_time = time.time()
             if y is not None:
                 self.best_estimator_.fit(X, y, **fit_params)
             else:
                 self.best_estimator_.fit(X, **fit_params)
+            refit_end_time = time.time()
+            self.refit_time_ = refit_end_time - refit_start_time
```

A wall-clock reading is taken immediately before the refit and immediately after
it, and their difference (the elapsed refit duration in seconds) is stored as
`self.refit_time_`. The whole recording is inside the `if self.refit:` branch, so
the attribute is present exactly when a refit is performed. `time.time()` is
monotonic across the refit on the wall clock, so `refit_end_time >=
refit_start_time` and the recorded duration is `>= 0` (what the test asserts via
`assert_greater_equal(search.refit_time_, 0)`).

The remaining patch hunks (`import time`, and the `refit_time_ : float` entries
in the `GridSearchCV` / `RandomizedSearchCV` class docstrings) are a new import
and documentation only; they add no behavior beyond enabling the block above.

### Lean ↔ Python type bijection (used by G-CONF + G-AX)

| Python | Lean | bijection |
|---|---|---|
| `self.refit` (truthiness) | `refitEnabled : Bool` | whether the final refit is performed. Truthy `self.refit` (an estimator/score-name/`True`) ↔ `true`; `False` ↔ `false`. Modeled as an input boolean (a read-only configuration flag at this call site). |
| `time.time()` taken before the refit (`refit_start_time`) | `startClock : ℚ` | a wall-clock instant, a `float` second count. Modeled as an exact rational (only its order and its difference with `endClock` matter — kernel `Float` order is opaque to tactics, DECISIONS.md, so use `ℚ`). |
| `time.time()` taken after the refit (`refit_end_time`) | `endClock : ℚ` | the wall-clock instant after the refit. (On a real, monotonically advancing wall clock `endClock >= startClock`; the recording itself does not depend on that.) |
| `refit_end_time - refit_start_time` | `endClock - startClock` | identical subtraction; the elapsed refit duration in seconds. |
| `self.refit_time_` (present iff the refit branch ran) | `result : Option ℚ` | `some d` ↔ the attribute exists and equals `d`; `none` ↔ the attribute is absent (`hasattr(...) == False`). |

### Precondition

None. The recording is the unconditional subtraction of the two readings —
`float.__sub__` is total, exactly like `ℚ` subtraction — so the spec demands
`result = some (endClock - startClock)` for EVERY pair of readings, with no
side condition relating them. The theorem therefore carries no
`startClock ≤ endClock` binder: an earlier revision did, and that binder was
pure slack — the adversarial audit exhibited a same-spec wrong impl that
diverges only on `startClock > endClock` inputs yet still closed the
precondition-guarded theorem (G-PANEL-1 WEAK). Dropping the binder is faithful
(the real code performs the identical subtraction on whatever the two readings
are) and leaves zero slack: any impl whose `correct_refitTiming` closes must
agree with the patched behavior pointwise on all inputs. On a real, monotonic
wall clock `startClock ≤ endClock` holds anyway, which is why the recorded
duration is `>= 0` in the F2P test's `assert_greater_equal(search.refit_time_, 0)`.

### Abstracted (unchanged, not in the modeled observable)

`clone(base_estimator).set_params(**self.best_params_)` and
`self.best_estimator_.fit(...)` are unchanged by the patch. Their only modeled
effect is that they occur between the two clock readings (so the elapsed time is
the duration of the refit). They are not part of the modeled observable (modeling
the fitted estimator would require an ungrounded oracle, SPEC_GUIDE §0.8). The
modeled observable is precisely the recorded duration the patch adds.

## Callee provenance + flag deps

- `self.refit` — a constructor argument of `BaseSearchCV` (default `True`); a
  read-only flag. Modeled as the input boolean `refitEnabled`. No callee axiom.
- `time.time()` — `time` stdlib; returns the wall-clock time in seconds as a
  `float`. The two readings are environment-provided values, modeled directly as
  the rational inputs `startClock` / `endClock` (not a called function whose
  internal behavior is axiomatized — they are data the environment supplies).
  The spec is unconditional in the two readings (no monotonicity side
  condition; see "Precondition" above).
- `clone`, `set_params`, `estimator.fit` — unchanged by the patch; abstracted
  (see above). No callee axiom consumed.
- No `opaque`/`axiom` callee contract is consumed: the only modeled operation is
  the gated arithmetic difference of the two reading inputs. `axiom_check.py` is a
  skip stub; G-AX skips.

## G-CONF fuzz seed

Pinned seed: **11310** (also in `conformance_check.py`). The R/I shadow of
`implementation_refitTiming` is differential-tested against an in-process replica
of the patched timing computation (record `end - start` under the `if self.refit`
gate, else leave the attribute absent) over ≥10⁵ fuzzed
`(refitEnabled, startClock, endClock)` inputs covering both `startClock ≤
endClock` and `startClock > endClock` (the spec is unconditional in the two
readings), plus hand-picked edge cases (equal readings → zero duration; reversed
readings → negative duration; refit disabled → absent).

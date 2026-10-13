# refinement.md — scikit-learn__scikit-learn-11310

The operation-by-operation correspondence between `model.py`'s implementation
(the `recorded_refit_duration` impl region, with the axiomatized callee
`elapsed_between` consumed by the proof and `clock_after` referenced for the
ordering precondition) and `patch.diff` (the gold patch). Each step is tagged
**R** (type refinement), **A** (axiomatized callee — split into **A-consumed**,
where the proof uses the axiom's `Ensures`, and **A-reference**, where the real
callee is validated against the axiom by axiom_check.py / G-AX but the proof does
not consume its `Ensures`), or **I** (identical concrete operation). The claim:
*any implementation that verifies against this frozen spec, refined per the map
below, is behaviourally equal to the gold patch on the tested inputs, so it
resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## A. The refit-timing site — `BaseSearchCV.fit` (`sklearn/model_selection/_search.py:766-771`)

Gold hunk (the behavioural change):
```
  if self.refit:
      self.best_estimator_ = clone(base_estimator).set_params(
          **self.best_params_)
+     refit_start_time = time.time()
      if y is not None:
          self.best_estimator_.fit(X, y, **fit_params)
      else:
          self.best_estimator_.fit(X, **fit_params)
+     refit_end_time = time.time()
+     self.refit_time_ = refit_end_time - refit_start_time
```
(plus `+import time` at the top, and two docstring Attributes entries — see §D.)

### Carrier abstraction of the two readings (the signature reshape)
The gold reads the clock twice *inside* the branch (`refit_start_time`,
`refit_end_time`). The model abstracts those two `time.time()` readings as the
two `float` parameters `start` and `end` of `recorded_refit_duration`, with the
precondition `end >= start`. This is a type/carrier refinement (R): the two
internal readings become the two ordered inputs. The ordering `end >= start` is
the timer's monotonicity — the second reading (taken after the fit) is never
earlier than the first (taken before it) — which the `clock_after` axiom models
and axiom_check.py validates against the REAL `time.time()` (A-reference). This
reshape is what lets postcondition (2) pin the result to the genuine real-valued
difference of the two readings (see §E); without exposing the readings the
postcondition could only constrain the result's *value*, not pin it to the real
subtraction, leaving an int/non-real result admissible.

| # | model.py impl op (`recorded_refit_duration`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A0 | the parameters `start`, `end` with `Requires(end >= start)` | the two `time.time()` readings `refit_start_time`, `refit_end_time`, ordered because the second is taken after the first | R + A-reference | the two internal readings ↔ two ordered `float` inputs (carrier R); the ordering `end >= start` is the timer monotonicity modelled by `clock_after` and validated against real `time.time()` by axiom_check.py (A-reference; mapping.md §3.1). |
| A1 | `if do_final_fit:` guards the recording | `if self.refit:` guards the refit branch | R | `self.refit` truthiness ↔ `do_final_fit: bool` (mapping.md §2). The recording happens inside, exactly when the refit branch runs. |
| A2 | the opaque work between the two readings (the comment `... the final fit ... happens here ...` is between A0's two readings) | `self.best_estimator_.fit(X[, y], **fit_params)` | I | the refit itself is unchanged by the patch and irrelevant to the modeled property (the duration); both sides perform it between the two readings. No node beyond ordering. |
| A3 | `result = elapsed_between(start, end)` | `self.refit_time_ = refit_end_time - refit_start_time` | A-consumed | real subtraction of the later minus the earlier reading; `elapsed_between`'s `Requires(later >= earlier)` is discharged by A0's `end >= start`, and its `Ensures(Result() >= 0.0)` plus the postcondition pin `Result() == elapsed_between(start, end)` give the genuine non-negative real-valued duration the F2P test demands (mapping.md §3.2). Assigning to `result` ↔ setting `self.refit_time_`. |
| A4 | falling out of the `if` with `result` still `None` when `not do_final_fit` | the attribute `self.refit_time_` is never set when `self.refit` is falsy | R | "attribute absent" ↔ `Result() is None` (mapping.md §2). The `test_no_refit` P2P relies on the attribute NOT being set when there is no refit; the spec clause `do_final_fit == (Result() is not None)` pins both directions. |

The discriminating content of the change — that a non-negative refit duration,
*equal to the elapsed interval of the two bracketing readings*, is recorded
exactly when the refit runs — lives in the two postconditions:
`do_final_fit == (Result() is not None)` (present iff refit) and
`Implies(Result() is not None, Result() == elapsed_between(start, end))` (pinned to
the real-valued elapsed interval, hence a non-negative float). The pre-patch code
records nothing; `model_prepatch.py` reproduces that (the `if` body is a bare
`pass`, `result` stays `None`) and **fails** the first postcondition when
`do_final_fit` is true — exactly the spec sensing the change (G-DIFF).

## B. No separate prepatch for the docstring/import hunks

The gold patch also adds `import time` and two `refit_time_ : float` docstring
Attributes entries. These are non-behavioural: the import merely makes the timer
available (modeled by the `clock_after` axiom), and the docstrings document the
new attribute (the F2P test checks the attribute *value*, never its docstring).
They carry no observable behaviour, so they need no failing prepatch variant;
the single timing-site prepatch already exercises the one tested behaviour.

## C. No kind-3 (unexpressible-changed-op) steps

Every step above is R, A-consumed, or A-reference, or I — no kind-3. The one
behaviour that genuinely *changed* — recording the bracketed refit duration when
the refit runs — is modeled **deeply** in the impl (the guarded assignment of the
elapsed interval of the two ordered readings, steps A0–A4), NOT hidden behind an
axiom about the function under change. The two axioms cover **unchanged**
operations the new code merely *invokes*: `time.time()` (the stdlib timer,
A-reference for the `end >= start` ordering) and builtin float subtraction
(A-consumed at A3).

Why `elapsed_between` is an axiom rather than a spelled-out builtin: Nagini 1.2.0
leaves float `+`/`-` essentially uninterpreted even under `--float-encoding=real`
— a minimal `Requires(a >= b); Ensures(a - b >= 0.0)` does not verify (verified
empirically), while float ordering/comparison does. So the timer's monotonicity
and the ordered-difference non-negativity — both *true real-arithmetic facts*,
not oracle answer-keys — are each captured as the weakest sufficient
`@Pure @ContractOnly` contract and validated against the REAL operation by G-AX
(mapping.md §3, axiom_check.py). This is the kind-A discipline (PLAN §3): the
changed behaviour is deep; only unchanged callees are axiomatized.

## E. Grounding (directive 8) — the result is *produced by* the real subtraction, not echoed

The strengthened postcondition (2) pins `Result()` to `elapsed_between(start, end)`
— NOT to an ungrounded answer-key oracle. `elapsed_between` is the kind-A model of
the **real, unchanged builtin subtraction** the gold patch performs
(`refit_end_time - refit_start_time`), grounded in the actual input carriers
`start` and `end` (the two clock readings). The only way to discharge the
postcondition is to return exactly that real-valued difference of the two
readings — i.e. to perform the modeled subtraction on the genuine inputs — which
is precisely what the gold patch does. There is no constant or oracle an impl can
echo: a non-real / int result (`result = 0`, `result = 5`, an int-typed variable)
fails because it is not equal to the float `elapsed_between(start, end)`, and a
fabricated float fails unless it equals the real difference of the supplied
readings. (Adversarial confirmation: atk_9 `result = 0`, atk_10 int-typed
variable, atk_11 `result = 5` all FAIL verification against this spec; the
gold-faithful `result = elapsed_between(start, end)` verifies.)

## D. verify(model) ⇒ resolved

`recorded_refit_duration` verifies only if it reports a value exactly when the
final fit runs (A1/A4, the `present iff refit` postcondition) and that value is
*exactly* the real-valued elapsed interval `elapsed_between(start, end)` of the
two ordered bracketing readings (A0/A3, the `Result() == elapsed_between(start, end)`
postcondition discharged through the `end >= start` precondition and
`elapsed_between` non-negativity). Because the result is pinned to the float-typed
`elapsed_between`, it is provably a non-negative *float* — defeating the int /
non-real counterexamples that a magnitude-only `Result() >= 0.0` postcondition
admitted. By R (`self.refit` ↔ `do_final_fit`, the two `time.time()` readings ↔
`start`/`end`, attribute presence ↔ `Optional[float]`) the verified behaviour
equals the gold patch's `self.refit_time_ = refit_end_time - refit_start_time`
bracketing; by G-AX the real `time.time()` meets the `clock_after` ordering
(A-reference) and real subtraction meets the `elapsed_between` axiom (A-consumed).
Therefore a model satisfying this spec, refined by the map above, is the gold
patch up to type refinement and audited callees — and the gold patch resolves
(G-RESOLVE: F2P `test_search_cv_timing` asserts `hasattr(search, "refit_time_")`,
`isinstance(..., float)`, `>= 0`; the `isinstance(float)` check is now satisfied
by construction because the result is pinned to the float `elapsed_between`). The
trust points are exactly the two of PLAN §1.1: axiom soundness (G-AX) and
refinement fidelity (this document, G-EQ).

# mapping.md — scikit-learn__scikit-learn-11310

Binds every `model.py` symbol to its repository counterpart at
`base_commit = 553b5fb8f84ba05c8397f26dd079deece2b05029`, states the type
abstraction, and gives the provenance of each axiom (callee source + the exact
behaviour the axiom encodes).

Repo file under change: `sklearn/model_selection/_search.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `recorded_refit_duration(do_final_fit, start, end)` | the refit branch of `BaseSearchCV.fit` — `sklearn/model_selection/_search.py:766-771` (`if self.refit:` … the best-estimator refit) | the modeled changed behaviour: record the wall-clock duration of the final refit |
| `do_final_fit` (bool param) | `self.refit` truthiness at `_search.py:766` (`if self.refit:`) | whether the final fit on the whole data is performed |
| `start`, `end` (`float` params, `end >= start`) | the two `time.time()` readings `refit_start_time` (`_search.py:770` post-patch, before the fit) and `refit_end_time` (`_search.py:772` post-patch, after the fit) | the two ordered wall-clock readings bracketing the refit fit, abstracted as inputs (carrier R); ordered because the second is taken after the first (timer monotonicity, modelled by `clock_after`) |
| `Result()` (`Optional[float]`) | the new instance attribute `self.refit_time_` (`_search.py:773` post-patch) | the reported refit duration (present iff the final fit ran), pinned to the real-valued elapsed interval `elapsed_between(start, end)` |
| `clock_after(reference)` *(axiom — A-reference)* | `time.time()` — CPython stdlib `time` module (called at `_search.py:770,772` post-patch as `refit_start_time`/`refit_end_time`) | unchanged stdlib timer the patch reads twice, bracketing the refit fit; models the monotonicity that justifies the `end >= start` precondition. The proof does NOT consume its `Ensures` (the readings are inputs); axiom_check.py validates real `time.time()` against it (A-reference). |
| `elapsed_between(earlier, later)` *(axiom — A-consumed)* | the real subtraction `refit_end_time - refit_start_time` (`_search.py:773` post-patch) | unchanged builtin float subtraction of the two ordered readings; the proof consumes its `Ensures` and the postcondition pins `Result()` to it |

The new attribute is also documented in two class docstrings the gold patch
edits (`GridSearchCV` near `_search.py:1076`, `RandomizedSearchCV` near
`_search.py:1387` — the `refit_time_ : float` Attributes entries). These are
pure documentation; they carry no behaviour and are not modeled (the F2P test
exercises only the attribute value, not its docstring).

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| `self.refit` (truthy/falsy: bool, str scorer name, or callable) | `do_final_fit: bool` | the branch at `_search.py:766` is taken iff `self.refit` is truthy; the modeled behaviour depends only on this truth value, so the carrier is the bool `do_final_fit`. The F2P test uses the default `refit=True`, a truthy value. |
| `self.refit_time_` (a `float` attribute set on the estimator) ; absence of the attribute when `refit` is falsy | `Optional[float]` `Result()` | "attribute present with value v" ↔ `Result() == v` (a `float`); "attribute not set" ↔ `Result() is None`. The F2P test asserts the attribute is present (`hasattr`), is a `float` (`isinstance`), and is `>= 0` when `refit` is truthy. The postcondition `Result() == elapsed_between(start, end)` pins the result to the float-typed elapsed interval, so the `isinstance(..., float)` check is met by construction (a non-real / int result is not equal to that float and fails verification). |
| the two `time.time()` readings (`float`, seconds since the epoch) bracketing the fit | `start`, `end` (`float` params, `Requires(end >= start)`) | the two wall-clock readings are interpreted real numbers (verified with `--float-encoding=real`), abstracted as the two ordered inputs; ordering = timer monotonicity. |
| `refit_end_time - refit_start_time` (`float`) | `elapsed_between(start, end)` (`float`) | real subtraction of the later reading minus the earlier reading. |

Floating-point note: Nagini 1.2.0 leaves float `+`/`-` essentially
**uninterpreted even under `--float-encoding=real`** (a minimal
`Requires(a >= b); Ensures(a - b >= 0)` does not verify; comparison/ordering
*does*). The two builtin operations the proof needs over reals — the timer's
monotonicity and the non-negativity of the ordered difference — are therefore
each captured by a `@Pure @ContractOnly` axiom whose weakest sufficient
property is what the proof consumes, and whose soundness is checked by
executing the REAL operation (axiom_check.py / G-AX). See refinement.md §C.

## 3. Callee provenance (kind-A — checked by G-AX / axiom_check.py)

### 3.1 `clock_after` ↔ `time.time()` (A-reference)
**Callee:** CPython `time.time()` — "Return the time in seconds since the epoch
as a floating point number." The gold patch reads it twice
(`refit_start_time = time.time()` before the best-estimator fit,
`refit_end_time = time.time()` after). Docs:
https://docs.python.org/3/library/time.html#time.time.

**Encoded property (weakest sufficient):** a reading taken after a reference
instant is never earlier than it — `clock_after(reference) >= reference`. The
two readings are abstracted as the inputs `start`, `end`, and their ordering
`end >= start` (the second reading, taken after the fit, is never earlier than
the first) is the model's precondition. This is exactly the timer monotonicity
`clock_after` encodes: the precondition `end >= start` is the modeled
`clock_after`-ordering of the two bracketing reads. The proof does **not**
consume `clock_after`'s `Ensures` (the readings are inputs satisfying
`end >= start` directly), so `clock_after` is **A-reference**: axiom_check.py
validates that the REAL `time.time()` produces `end >= start` across many
back-to-back pairs, grounding the precondition. The benchmark's F2P assertion
(`refit_time_ >= 0`) needs nothing stronger.

**Soundness check (G-AX):** `axiom_check.py` runs the REAL `time.time()` in
200 000 back-to-back pairs and asserts the later reading is never earlier than
the reference reading (0 violations observed).

### 3.2 `elapsed_between` ↔ `refit_end_time - refit_start_time` (A-consumed)
**Callee/operation:** the builtin real subtraction `later - earlier` the gold
patch computes at `self.refit_time_ = refit_end_time - refit_start_time`. This
is an *unchanged* arithmetic builtin, not the behaviour under change (the
behaviour under change is *recording the bracketed duration when refit runs*).

**Encoded property (weakest sufficient):** for an ordered pair
(`later >= earlier`) the difference is non-negative —
`Requires(later >= earlier) ⇒ Ensures(Result() >= 0.0)`. Its `Requires` is
discharged at the call site by the `end >= start` precondition (the modeled
timer ordering, §3.1). The postcondition pins `Result() == elapsed_between(start,
end)`, so the reported duration is genuinely *produced by* the real subtraction
of the two bracketed clock readings (not an unconstrained constant, and not a
non-real / int stand-in): a wrong impl cannot satisfy the postcondition by
inventing a value, because the result must equal the float-typed
`elapsed_between(start, end)` of the supplied ordered readings. (Grounding,
directive 8: `elapsed_between` models the REAL subtraction, not an answer-key
oracle — see refinement.md §E.)

**Soundness check (G-AX):** `axiom_check.py` asserts `later - earlier >= 0` on
7 boundary pairs (incl. the zero-length interval `(0.0, 0.0)` — the trivial-X
F2P case where no measurable time passes), ~2 000 real `time.time()` ordered
pairs, and 200 000 randomized ordered pairs over `[-1e12, 1e12]`. 0 violations.

Both callees import only the standard-library `time` module — the very module
the gold patch adds (`import time`) and calls; nothing repo-specific.

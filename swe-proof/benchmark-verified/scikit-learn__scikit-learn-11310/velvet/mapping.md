# mapping.md — scikit-learn__scikit-learn-11310

Instance: `scikit-learn/scikit-learn` @ `553b5fb8f84ba05c8397f26dd079deece2b05029`.
Provenance: **cold** (spec derived from `problem_statement` + gold `patch` + repo
source at `base_commit` only).

## 1. Symbol binding (file:line @ base_commit)

| concept | repo symbol | location @ base_commit |
|---|---|---|
| function under spec | `BaseSearchCV.fit` | `sklearn/model_selection/_search.py:579` (refit slice at `:766–773`) |
| refit gate | `if self.refit:` | `sklearn/model_selection/_search.py:766` |
| the work being timed | `self.best_estimator_.fit(X, y, …)` / `.fit(X, …)` | `_search.py:769–772` |
| wall-clock reading (callee) | `time.time()` | `time` stdlib; imported by gold patch (`import time`) |
| recorded attribute | `self.refit_time_` | set at `_search.py:773` (gold-patched); **absent** at base_commit |

The patch (gold) brackets the existing refit `fit(...)` call with two
`time.time()` reads and assigns the elapsed difference to a new instance
attribute `self.refit_time_`, guarded by the pre-existing `if self.refit:`.

The behavior the dataset checks (`test_search_cv_timing`, the sole FAIL_TO_PASS):
after `fit` with refit enabled (the default), the search object
(a) has the attribute, (b) it is a `float`, (c) it is `>= 0`.

## 2. Lean ↔ Python type bijection

| Lean (Solution.lean) | Python (repo) | notes |
|---|---|---|
| `refit : Bool` | truthiness of `self.refit` | the pre-existing refit gate; read-only |
| `refitTime : Option Rat` | the instance attribute `self.refit_time_` | `none` ⇔ attribute **absent** (`hasattr` False); `some t` ⇔ present with value `t`. `mut` (genuinely written none→some). |
| `startT : Rat`, `endT : Rat` | the two `time.time()` return values | environment-provided readings, modeled as read-only inputs (exact rationals model the float clock readings) |
| `endT - startT : Rat` | `refit_end_time - refit_start_time` (a `float`) | the recorded duration — the spec pins `refitTime = some (endT - startT)` EXACTLY (not merely "some non-negative value") |
| `require startT ≤ endT` | monotone-clock contract on consecutive `time.time()` readings | the G-AX-validated axiom domain (§3) |
| `t ≥ 0` | `search.refit_time_ >= 0` | the non-negativity the test asserts; follows from the exact-value pin + the monotone precondition |

**Float model (per SPEC_GUIDE §2 / plan §10 Q1).** The clock readings and their
difference are modeled as exact `Rat`. The recorded observable is a single
subtraction of the two readings — no further arithmetic. The pinned properties
are (a) the exact subtraction `endT - startT` (differential-tested bit-exact
against the verbatim patch line by G-CONF over 200k reading pairs including
NaN/inf/0.0/subnormal sentinels) and (b) its sign on the monotone domain, an
order-only fact that depends solely on `startT ≤ endT` and never on
floating-point rounding. An exact ordered carrier is therefore faithful; no ULP
tolerance is needed.

**Why the readings are INPUTS (spec strengthening, repair 2026-08-05).** An
earlier revision drew the two readings inside the impl via non-deterministic
`:|` choices and pinned only `∃ t, refitTime = some t ∧ t ≥ 0`. That
sign-only postcondition admitted constant-recording wrong impls
(`refitTime := some 0` / `some 999`) — flagged spec-too-weak by the audit
(G-PANEL-1 WEAK). The readings are environment-provided values of an unchanged
callee, so they are now modeled as read-only inputs `startT`/`endT` and the
postcondition pins the recorded value to EXACTLY their difference,
`refitTime = some (endT - startT)` — the identical subtraction the patched
source performs. A constant-recording impl can no longer verify (it fails for
any reading pair with `endT - startT` different from the constant), while every
faithful implementation still does. This mirrors the patched code shape
one-for-one: gate, subtraction, absent-when-not-requested.

## 3. Callee provenance + the load-bearing axiom

`time.time()` is the only callee the timed slice depends on; it is **unchanged**
by the patch (the patch only adds `import time` and two calls). Its two readings
enter the model as the inputs `startT` (before the refit work) and `endT` (after
it), and its contract is stated as the **precondition**

- `require startT ≤ endT` — two consecutive readings of the process wall clock,
  taken across a synchronous unit of work, are **non-decreasing** (monotone
  clock).

This is the WEAKEST contract sufficient to prove `endT - startT ≥ 0` and it is
exactly the property the gold patch relies on for `refit_time_ >= 0`. The proof
obligation is universally quantified over ALL input pairs satisfying the
precondition, so nothing stronger than non-decrease is assumed (e.g. we do not
pin how much time elapsed). A precondition narrows the input domain to the
axiom's validated domain and cannot over-strengthen the postcondition.

**Caveat (documented, not hidden):** `time.time()` reads `CLOCK_REALTIME`, which
can in principle step backwards under an NTP adjustment. The patch and its test
nonetheless rely on consecutive in-process readings being non-decreasing across a
short refit; this is the observed behavior. `axiom_check.py` (G-AX) validates it
by reading the real `time.time()` callee twice in immediate succession over many
iterations (with and without a unit of intervening work) and asserting each pair
is non-decreasing — exactly the contract the precondition claims.

The intervening `best_estimator_.fit(...)` call is **not** represented as a
do-block op: it is unchanged repo work whose only effect on the modeled property
is to advance the wall clock between the two readings — already captured by the
`startT ≤ endT` domain. It pins no observable that the spec constrains, so it is
intentionally elided (noted in refinement.md), not axiomatized (no dead axiom).

Flag dependency: the recording fires only under the truthy `refit` gate; the
default in `test_search_cv_timing` is `refit=True`, so the `refit = true` branch
is the one the FAIL_TO_PASS observes.

## 4. G-CONF fuzz seed (pinned)

`SEED = 11310`, `N_FUZZ = 200000`. `conformance_check.py` differential-tests the
R leg (`endT - startT`, the recorded duration) of the do-block shadow against the
verbatim patch line `self.refit_time_ = refit_end_time - refit_start_time` over
fuzzed `(startT, endT)` reading pairs (boundary + sentinel + random floats),
asserting bit-exact agreement (NaN-aware) and that the modeled non-negativity
holds exactly on the monotone domain `startT ≤ endT` (the G-AX-validated axiom
domain).

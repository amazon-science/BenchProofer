# refinement.md — scikit-learn__scikit-learn-14710

Each operation of `implementation_scoreEarlyStop` mapped to its `patch.diff`
counterpart. Tags: **R** (type refinement), **A-consumed** (proof uses an axiom's
property), **A-reference** (deep model validated == real callee by G-AX), **I**
(identical concrete op).

| # | Lean impl op | patch.diff / repo counterpart | tag | note |
|---|---|---|---|---|
| 1 | `let mut trainScores := trScores` / `let mut valScores := vlScores` | the running histories `self.train_score_` / `self.validation_score_` referenced before append | I | state threading; the lists exist on entry. |
| 2 | `let mut yT : Targets := Sum.inl yTrain; if isClf then let ls ← readLabels labels; let decoded ← relabelTargets ls yTrain; yT := Sum.inr decoded` | **THE patched behavior (train site):** `if is_classifier(self): y_small_train = self.classes_[y_small_train.astype(int)]` | R + A-reference | the added gather, and the *read* of the class-label table that feeds it. **R half (the read):** `labels` is `Option`, and `readLabels` turns reading an absent table into `Except.error EarlyStopError.absentClassLabels` — the model of `AttributeError: 'HistGradientBoostingRegressor' object has no attribute 'classes_'`, since `self.classes_` is assigned only in `HistGradientBoostingClassifier._encode_y` (`gradient_boosting.py:1029`). The read sits **inside** the `is_classifier(self)` guard, as in the method. See **Reading an absent class-label table** below. **R half (the gather):** the gather is itself partial — `relabelTargets : Array String → Array Int → Except EarlyStopError (Array String)`, bound with `←` — because a fancy index numpy cannot answer for is an `IndexError`, not a value; modeled as `Except.error EarlyStopError.codeOutOfRange`. See **Performing the decode on a stand-in pair** below. **A-reference half:** `relabelTargets ls codes` deeply models `self.classes_[codes.astype(int)]` — element-wise `result[i] = ls[codeIndex ls.size codes[i]]` over the codes the table has an entry for (`codesIndexLabels`), where `codeIndex` resolves a NEGATIVE code from the end of the table (`size + c`), as numpy does, and `.error codeOutOfRange` outside `[-size, size)`, which is numpy's raise; validated `==` the real numpy fancy-index by G-AX in both directions and on both sides of zero. Flag dep: applied iff `isClf`. |
| 3 | `let trScore ← scorer xTrain yT` / `trainScores := trainScores ++ [trScore]` | `self.train_score_.append(self.scorer_(self, X_binned_small_train, y_small_train))` | R + A-reference | `scorer` is the unchanged fitted scorer; `append` ↔ `++ [·]`. No property of `scorer` is consumed (the proof only threads its result). **R half:** `scorer` is `Except`-valued and the call is bound with `←`, so a refusal of the pair it is handed becomes `Except.error EarlyStopError.scoringRefused` — the model of `ValueError: Found input variables with inconsistent numbers of samples`, which `check_consistent_length` raises inside every scorer when the design matrix and the target array describe different numbers of samples. The bind site is the call site: an implementation that computes `scorer x t` without binding it has, in Python, not yet made the call. See **Consulting the scoring function about an unnamed pair** below. |
| 4 | `if useVal then …` | `if self._use_validation_data:` | I | identical branch guard. |
| 5 | `let xv ← readValData xVal` / `let codes ← readValCodes yVal` | the *reads* of `X_binned_val` / `y_val`, which the method performs only inside the `self._use_validation_data` branch | R | the arguments are `Option`, and reading an absent one yields `Except.error EarlyStopError.absentValidationData` — the model of `AttributeError: 'NoneType' object has no attribute 'astype'`. See **Reading an absent validation argument** below: `gradient_boosting.py:147-149` sets `X_val, y_val = None, None` and `:167` sets `X_binned_val = None` whenever `validation_fraction is None`, so on the no-validation path these arguments carry nothing and touching them raises. |
| 6 | `let mut yV : Targets := Sum.inl codes; if isClf then let ls ← readLabels labels; let decoded ← relabelTargets ls codes; yV := Sum.inr decoded` | **THE patched behavior (val site):** `if is_classifier(self): y_val = self.classes_[y_val.astype(int)]` | R + A-reference | same read and same gather as op 2, validation targets. Sits **inside** the `useVal` branch and, within it, inside the `is_classifier(self)` guard, as in the method — and the postcondition now enforces all three, because op 5 has made an out-of-branch validation read observable, op 2's `readLabels` has made an out-of-guard class-label read observable, and the gather's own `codeOutOfRange` has made an out-of-guard DECODE observable even when nothing absent is read. |
| 7 | `let vlScore ← scorer xv yV` / `valScores := valScores ++ [vlScore]` | `self.validation_score_.append(self.scorer_(self, X_binned_val, y_val))` | R + A-reference | as op 3, validation site — including the `←` bind, which is what makes this the *second* and only other scoring call the contract names. |
| 8 | `return { … stop := shouldStop valScores }` (val branch) / `return { … stop := shouldStop trainScores }` (else) | `return self._should_stop(self.validation_score_)` / `return self._should_stop(self.train_score_)` | A-reference | `shouldStop` unchanged; the spec applies it to the just-extended history, mirroring the code's use of the appended list. |

Control flow: an `Except EarlyStopError` `do` block with mutable score histories,
a guarded re-encode before each score whose body performs the only reads of the
class-label table, a `useVal` branch whose body performs the only reads of the
validation arguments, and an early `return` on that branch — a line-for-line
skeleton of the imperative method (the two added `if is_classifier(self):`
re-encodes, two `append`s, the `_use_validation_data` branch, the two
`_should_stop` returns).

Every **R** half (ops 2, 3, 5, 6, 7) is the same shape and carries no independent
VALUE transformation: it turns a Python operation that may RAISE into an
`Except`-valued one — an `Option`→value read (ops 2, 5, 6) whose failure models
the `AttributeError` the real method raises off-guard, a call to a partial
callee (ops 3, 7) whose failure models the `ValueError` the real scorer raises on
a mismatched pair, or the gather's own domain (ops 2, 6) whose failure models the
`IndexError` numpy raises for a code the class-label table has no entry for. The
gather's `Except` wrapper adds no value transformation of its own: on a
non-negative in-range code array it returns exactly the array the earlier total
version returned, and what it changes elsewhere is only where numpy disagreed with
that version — a refusal outside `[-size, size)` where the total version invented
an entry, and the END-resolved position for a negative code where the total
version's `Int.toNat` clamped to `0`. None is a scalar computation with a
Python-side shadow to differential-test. Op 1 and op 4 are likewise pure state/branch glue. The sole
value transformation is the A-reference `relabelTargets`. There is therefore no
standalone R/I shadow to build a Python differential against ⇒ `conf_skip = true`
(G-CONF skip stub); `relabelTargets` is validated by `axiom_check.py` (G-AX)
against the real `self.classes_[y.astype(int)]`.

No **A-consumed** rows ⇒ the proof consumes no callee property axiom; it closes by
case analysis on `isClf`, `labels`, `useVal`, `xVal` and `yVal` (2⁵ = 32 cases) and
reduction of the `do` block.

## Reading an absent validation argument

`_check_early_stopping_scorer` is called with `X_binned_val` and `y_val` that are
`None` unless the estimator holds out a validation split:
`gradient_boosting.py:147-149` sets `X_val, y_val = None, None` when
`validation_fraction is None`, and `:167` sets `X_binned_val = None` with them.
`self._use_validation_data` *is* `validation_fraction is not None`, so the branch
flag and the presence of the arguments move together, and the method's guard is
what keeps `self.classes_[y_val.astype(int)]` off a `None`.

That is why the validation arguments are modeled as `Option` and read through
`readValData` / `readValCodes` into an `Except EarlyStopError`, rather than as
total values. The measured reason, recorded here because it is a property of the
model and not of the harness:

* An earlier version of this contract typed `xVal : XData` and
  `yVal : Array Int` total and constrained the validation score only under
  `useVal = true`. Because `scorer` and `relabelTargets` are total pure functions,
  *when* the validation targets were decoded was then unobservable, and an impl
  could hoist the decode (and the scorer call) above the `if useVal` guard and
  remain provably equal — the hoisted value is dead on the no-validation branch.
* Machine-checked on 2026-08-16 by the live G-EQ reviewer: two such impls
  (`atk_2.lean`, hoisting the read + decode; `atk_3.lean`, additionally hoisting
  the scorer call) had `same_spec=True`, `verifies=True`, and
  `#print axioms correct_scoreEarlyStop` = `[propext, Quot.sound]`.
* Their faithful refined patches were run in the official instance image.
  `patch_atk2.diff` — the gold patch with the val-site decode lifted out of
  `if self._use_validation_data:` — FAILS two PASS_TO_PASS tests:
  `test_early_stopping_classification[accuracy-None-5-0.1-data0]` and
  `[…-data1]`, parameters `('accuracy', None, 5, 1e-1)` (a classifier with
  `validation_fraction=None`), with
  `AttributeError: 'NoneType' object has no attribute 'astype'`.
* The gold control PASSES those same two tests in the same image, same command,
  same session (`2 passed, 12 deselected` in 305.62s), so the failures belong to
  the attack's patch and not to the instance, the image, or the host. Both tests
  are in this instance's 63-entry PASS_TO_PASS list, so that patch cannot resolve.

So the old contract admitted an impl whose faithful patch does not resolve:
verify ⇏ correct. Strengthening the old clauses could not close it — hoisting a
pure computation is semantics-preserving, so no relation over a single total
`result` can forbid it. The absence had to enter the model. `Option` alone would
also not have been enough (an impl can hoist `relabelTargets labels (yVal.getD
#[])`, whose value is again dead); the error propagation is the part that does the
work, and it is the faithful model of `None.astype` raising.

The current postcondition therefore distinguishes three situations and demands a
**successful** result when validation data is not in use, which an impl can
deliver only by leaving the validation arguments untouched on that path. Both
attacks are carried in `properties.py` as the reject cases
`weak-val-read-hoisted` and `weak-val-score-hoisted`; both now fail to verify,
each refuted by an unconditional witness at a no-validation input
(`Except.error … ≠ Except.ok …`).

The complementary bound matters too, and is tested: the clause forbids *reading*
an absent argument, not precomputing from a present one. `pos-option-map-precompute`
computes the decoded validation targets above the guard under `Option.map` — the
model of a defensive
`y_val = self.classes_[y_val.astype(int)] if y_val is not None else None`, which
does not raise on the no-validation path — and is required to VERIFY.

## Reading an absent class-label table

The same defect on the other conditional argument, closed the same way, and it is
the reason `labels` is `Option` rather than a total `Array String`.

`self.classes_` is assigned in exactly one place: `_encode_y` of
`HistGradientBoostingClassifier` (`gradient_boosting.py:1029`,
`self.classes_ = label_encoder.classes_`). `HistGradientBoostingRegressor._encode_y`
(`:804-808`) only converts the targets to `Y_DTYPE` and defines no such attribute.
And a regressor **does** reach `_check_early_stopping_scorer`: `fit` dispatches
`if self.scoring == 'loss': … else: … self._check_early_stopping_scorer(…)` at
`:214`/`:236`/`:252` (first iteration) and `:339`/`:356` (each later iteration),
with no classifier guard. So the `if is_classifier(self):` guard is what keeps
`self.classes_` off an `AttributeError`, exactly as `_use_validation_data` guards
the validation arguments.

The measured reason, recorded here because it is a property of the model:

* An earlier version of this contract typed `labels : Array String` total. Reading
  the table is a pure projection, so *when* it was read was unobservable: an impl
  could hoist the read above `if isClf` — keeping both decodes inside the guard,
  hence recording exactly gold's scores at every input — and remain provably equal
  to the spec. On the non-categorical branch the hoisted table is simply dead.
* Its faithful refined patch — the gold patch with `classes = self.classes_`
  lifted above `if is_classifier(self):` and both gathers rewritten to index
  `classes` under the guard — was run in the official instance image
  (`swebench/sweb.eval.x86_64.scikit-learn_1776_scikit-learn-14710`, digest
  `sha256:e68930db25c0…`) on 2026-08-16 against all seven
  `test_early_stopping_regression` parametrizations, which are all PASS_TO_PASS:
  **4 failed, 3 passed** (417.71s). The four failures are
  `[neg_mean_squared_error-0.1-5-1e-07]`, `[neg_mean_squared_error-None-5-0.1]`,
  `[None-0.1-5-1e-07]` and `[None-None-5-0.1]`, each with
  `> classes = self.classes_` /
  `E AttributeError: 'HistGradientBoostingRegressor' object has no attribute 'classes_'`
  at `gradient_boosting.py:429`. The three that pass are the two `[loss-…]`
  parametrizations, which take the `_check_early_stopping_loss` path instead, and
  `[None-None-None-None]`, which sets `n_iter_no_change=None` and so does not early
  stop at all — i.e. exactly the three that never reach this method.
* The gold control PASSES all seven in the same image, same command, same session
  (`7 passed, 71 deselected, 1 warning in 659.15s`), so the failures belong to the
  attack's patch and not
  to the instance, the image, or the host. All four are in this instance's 63-entry
  PASS_TO_PASS list, so that patch cannot resolve.

So the old contract admitted a second impl whose faithful patch does not resolve:
verify ⇏ correct, on a different clause and a different argument from the
validation one. It is closed the same way — `labels : Option (Array String)`, read
through `readLabels` (and `targetFor`) into `Except EarlyStopError`, so the first
clause of the postcondition demands
`Except.error EarlyStopError.absentClassLabels` at `isClf = true, labels = none`
and a plain success on the raw codes at `isClf = false`, whatever `labels` holds.
The attack is carried in `properties.py` as the reject case
`weak-labels-hoisted`, refuted by an unconditional witness at
`isClf = false, labels = none` (`Except.error … ≠ Except.ok …`).

The complementary bound is tested here too: the clause forbids *reading* an absent
table, not precomputing from the table the caller supplied.
`pos-labels-map-precompute` computes the decoded training targets above the guard
under `Option.map` — the model of a defensive
`dec = self.classes_[y.astype(int)] if hasattr(self, 'classes_') else None`, which
does not raise on a regressor — and is required to VERIFY.

Read that bound narrowly: "not precomputing from a present one" is the whole of it.
Precomputing from a **stand-in** table — an `Option.getD` default in place of a
table the estimator does not have — is a different act, it is the Python operation
that raises, and it is forbidden by the fourth lane below. What makes
`pos-labels-map-precompute` admissible is that the gather it performs runs on
`labels` itself, under `Option.map`, so on a regressor no gather happens at all;
what makes the fourth lane's rivals inadmissible is that the gather happens anyway,
on `#[]`.

## Consulting the scoring function about an unnamed pair

The third lane, and the reason `scorer` is `Except`-valued
(`Scorer := XData → Targets → Except EarlyStopError Score`) rather than
`XData → Targets → Score`. Making the two conditional arguments `Option` and
their reads observable closed the two lanes above; it did **not** close the
scoring call, because an implementation need not read an absent argument to
consult the scorer about the wrong pair — it can build a stand-in out of
`Option.getD` defaults.

* Machine-checked on 2026-08-16 by the live G-EQ reviewer against the
  Option-plus-error contract: `atk_8.lean` keeps BOTH guarded validation reads,
  computes
  `hoistedTargets := if isClf then Sum.inr (relabelTargets (labels.getD #[]) (yVal.getD #[])) else Sum.inl (yVal.getD #[])`
  and `hoistedScore := scorer (xVal.getD xTrain) hoistedTargets` ABOVE the
  `useVal` guard, and inside the guard — where the `getD` defaults coincide with
  the real arguments — records the answer it already holds. It had
  `same_spec=True`, `verifies=True`, and
  `#print axioms correct_scoreEarlyStop` = `[propext]`. Every value it records is
  gold's at every input and it reads nothing absent, so no clause about reads or
  about recorded scores can see it: with a TOTAL `scorer` the hoisted call is a
  dead pure value on the no-validation path.
* Its faithful refined patch — the gold patch with
  `_hoisted_targets` / `_hoisted_score = self.scorer_(self, X_binned_val if X_binned_val is not None else X_binned_small_train, _hoisted_targets)`
  lifted above `if self._use_validation_data:` and recorded inside it — was run in
  the official instance image
  (`swebench/sweb.eval.x86_64.scikit-learn_1776_scikit-learn-14710`, digest
  `sha256:e68930db25c0…`) on the three PASS_TO_PASS parametrizations that reach
  this method with `validation_fraction=None`: **3 failed, 75 deselected,
  1 warning in 1.91s**. The three are
  `test_early_stopping_regression[neg_mean_squared_error-None-5-0.1]`,
  `test_early_stopping_classification[accuracy-None-5-0.1-data0]` and
  `[…-data1]`, each with
  `ValueError: Found input variables with inconsistent numbers of samples: [0, 50]`
  (and `[0, 30]` for the two classification cases) raised from
  `sklearn/utils/validation.py:206`. The stand-in target array is empty while the
  training design matrix it is paired with has 50 (resp. 30) rows, so
  `check_consistent_length` inside the scorer rejects the pair.
* The gold control PASSES all three in the same image, same command, same session
  (`3 passed, 75 deselected, 1 warning in 248.03s`), so the failures belong to the
  attack's patch and not to the instance, the image, or the host. All three are in
  this instance's 63-entry PASS_TO_PASS list, so that patch cannot resolve.

So the Option-plus-error contract admitted a third impl whose faithful patch does
not resolve: verify ⇏ correct, on the scoring CALL rather than on a read.
Strengthening a clause about the recorded scores could not close it — the rival
records exactly gold's scores. What had to enter the model is the scorer's own
**partiality**: `self.scorer_` compares its target array against predictions it
derives from its design matrix (`_BaseScorer.__call__` → `_PredictScorer._score`
→ `metric(y_true, y_pred)` → `check_consistent_length`), so a pair that does not
describe the same samples is a `ValueError`, not a value. With `scorer`
`Except`-valued and each call bound with `←`, every branch of the postcondition
names its outcome as an `Except.bind`/`Except.map` over the scorer's answer about
the pair *that branch names*; an implementation that consults the scorer about any
other pair is answerable for the answer it draws. The rival is carried in
`properties.py` as `weak-val-scorecall-hoisted`, refuted unconditionally at
`isClf = false, useVal = false, xVal = none, yVal = none, yTrain = #[0]` by a
scoring function that refuses exactly the empty-target stand-in.

The bind site is the call site, and that is what keeps the clause honest rather
than merely strong. A Lean term `scorer x t : Except EarlyStopError Score` that is
never bound has, in Python, not yet made the call — its faithful refinement
defers the call to where the `Except` is consumed. So the contract does not forbid
naming a scorer application above the guard; it forbids *making* the call there,
which is exactly the Python operation that raises.

The complementary bound for THIS lane is `pos-unbound-consult`, described under
**The bind-site claim, attacked directly** below: it names a scorer application on
the same `getD` stand-in pair above the guard without making the call, its faithful
patch resolves, and it is required to VERIFY. So the scoring clause bites on the
call and not on the mention.

For one round the bound was carried instead by `atk_6.lean` — which hoists the
validation TARGET computation with the same `getD` stand-ins but leaves both
scoring calls inside the guard — shipped as the positive
`pos-getd-decode-precompute` on the strength of a three-test resolve measurement
(`3 passed, 75 deselected, 1 warning in 250.70s`) and the argument that the hoisted
`getattr(self, 'classes_', np.array([]))[…]` is "a value no scorer ever sees". That
was wrong, and the next G-EQ round measured it wrong: the deselected 75 include the
four `test_early_stopping_regression` parametrizations on which that gather raises
`IndexError` before any scorer is reached. The construct is a break, not an echo;
it is now a REJECT case, and the section below is the lane that rejects it. This
paragraph is kept rather than deleted because the retraction is the finding: a
too-strong control blessed on a deselected subset had been holding a hole open.

### The bind-site claim, attacked directly

The paragraph above is the one claim in this lane that rests on an argument rather
than on a measurement, so it was put to an adversary. A live G-EQ reviewer,
running against the contract exactly as shipped (its snapshot of `Solution.lean`
is byte-identical to the file outside the impl region), authored **fourteen**
attacks and verified each one. Thirteen were REJECTED (verifier exit 1),
including two it reached independently of this file:

* `atk_13` — the same `getD` stand-in pair as `atk_8`, with the consult `←`-bound
  above the guard. This is `weak-val-scorecall-hoisted`'s shape found from
  scratch, and its rejection is a second, independent measurement that the
  scoring clause bites on the call.
* `atk_14` — reads nothing absent and records exactly gold's scores, but consults
  the scorer an EXTRA time, INSIDE the branch, about the raw validation pair
  `Sum.inl codes` that no clause names, and throws the answer away. Bound, so the
  refusal propagates: rejected.

The fourteenth, `atk_12`, VERIFIES. It is the bind-site boundary aimed at
deliberately — its own comment says so ("refinement.md claims the contract
permits this because an unbound `Except` term 'has, in Python, not yet made the
call'. This tests that claim"). It names

```lean
  let unboundAnswer : Except EarlyStopError Score :=
    scorer (xVal.getD xTrain) standInTargets
```

above the guard and `←`-binds `unboundAnswer` only inside it.

That reviewer then settled its own attack with the oracle instead of an argument,
and settled it against itself: the faithful patch it shipped for `atk_12` defers
the call,

```python
  _hoisted_answer = lambda: self.scorer_(self, _stand_in_X, _stand_in_y)
```

invoked only inside `if self._use_validation_data:`, and that patch was run in the
official instance image on the same three PASS_TO_PASS parametrizations as every
other measurement in this file: **3 passed, 75 deselected, 1 warning in 399.63s**
(2026-08-16, after the scoring clause landed;
`~/audit_14710l_results/v5/p2p_atk12.log`). So `atk_12` is a correct echo, the
contract is right to admit it, and the bind-site claim survives its own test. It
is shipped as the positive `pos-unbound-consult`, which puts the boundary — bind,
not mention — under a case of its own, next to the reject rival that differs from
it in exactly the `←`.

An eager Python call in `atk_12`'s position is not an alternative refinement of
it: under `useVal = false` the Lean impl RETURNS `.ok`, and a call that raises
does not refine a normal return. The two Python programs that do refine it are the
deferred lambda above and a `try`/`except ValueError` that captures the refusal
into a value — both of which return normally on the no-validation path, exactly as
the impl does.

This audit round was interrupted before it recorded a verdict (the cell's spec
view took a one-word prose correction for G-LEAK — "is fixed by" → "is determined
by" — which voids `same_spec` for every attack authored against the earlier
bytes), so its numbers are cited here as measurements and NOT as a gate result;
G-EQ and G-PANEL-1 are re-derived from scratch against the final bytes. The
fourteen attack files and their verifier logs are retained under
`~/audit_14710l_results/v5/eq_agent_atks/`.

## Performing the decode on a stand-in pair

The fourth lane, and the reason `relabelTargets` returns
`Except EarlyStopError (Array String)` rather than a bare `Array String`. This one
was not argued for in advance: it is a break the corpus recorded, and the previous
version of this document was holding it open.

The three lanes above made the two conditional READS observable and the scoring
CALL observable. They left the **gather itself** total, so performing it on a table
the estimator does not have was invisible — exactly as reading an absent table had
been invisible before `labels` became an `Option`. Machine-checked by the live G-EQ
role against the Option-plus-partial-scorer contract (see this bundle's verdict.md,
role G-EQ, whose eight attacks include these two):

* `atk_6.lean` — spec byte-for-byte, the TRAINING decode hoisted above the
  `isClf` guard and taken from a DEFAULTED table,
  `let hoistedDecoded := relabelTargets (labels.getD #[]) yTrain`, consumed only
  inside the guard, with the guarded `readLabels` left exactly where it was:
  `rc=0 VERIFIES`, `#print axioms correct_scoreEarlyStop` = `[propext]`.
* `atk_7.lean` — the same defect at the validation site, with BOTH conditional
  arguments defaulted, `relabelTargets (labels.getD #[]) (yVal.getD yTrain)`
  hoisted above the `useVal` guard: `rc=0 VERIFIES`, axioms `[propext]`.

In the repository neither hoist is dead. The faithful patch of each lifts
`getattr(self, 'classes_', np.array([]))[y.astype(int)]` out of its guard, and that
is a numpy fancy-index gather on an **empty** table, which raises
`IndexError: index 12 is out of bounds for axis 0 with size 0` before any scorer is
reached. Measured in the official instance image, one run at a time:

* gold control — `resolved=True, completed=True, F2P 1/1, P2P 63/63, 231.7s`,
  `note='resolved'`, so the image, host and oracle are healthy and the verdicts
  below are attributable to their patches;
* `atk_6` — `resolved=False, completed=True, F2P 1/1, P2P 59 success / 4 FAILURE,
  253.1s`, `'patch did not resolve in 1 attempts (consistent - not flaky)'`;
* `atk_7` — `resolved=False, completed=True, F2P 1/1, P2P 59 success / 4 FAILURE,
  70.3s`, same note.

The four failures are identical for both attacks and all four are in this
instance's 63-entry PASS_TO_PASS list:
`test_early_stopping_regression[neg_mean_squared_error-0.1-5-1e-07]`,
`[neg_mean_squared_error-None-5-0.1]`, `[None-0.1-5-1e-07]` and
`[None-None-5-0.1]` — exactly the four regressor parametrizations that reach
`_check_early_stopping_scorer`, i.e. the estimator that has no `classes_` at all.
Both attacks still PASS the FAIL_TO_PASS, so the break is a P2P regression rather
than a lost fix. G-EQ recorded the spec `BROKEN (verify⇏correct)`.

Why the three earlier lanes could not see it: nothing absent is READ (`getD`
supplies the default and the guarded `readLabels` stays in place), every recorded
value is gold's (the hoisted decode is consumed only inside the guard, where the
default coincides with the real table), and the scorer is consulted about nothing
but the two named pairs. What was unmodeled is that the gather can FAIL: the Lean
model returned the `Inhabited` default for an out-of-range code
(`relabelTargets #[] #[12,-3,480,0]` = `#["","","",""]`) where numpy raises, and
G-AX could not catch that because `axiom_check.py` fuzzed codes only in
`range(0, n-1)` with `n ≥ 1` and never paired an empty table with a non-empty code
array.

Closed by giving the gather exactly numpy's domain, which is the same move the
other three lanes made for absence:

```lean
def codeIndex (size : Nat) (c : Int) : Int :=
  if c < 0 then c + (size : Int) else c

def codesIndexLabels (labels : Array String) (codes : Array Int) : Bool :=
  codes.all (fun c => 0 ≤ codeIndex labels.size c
                      ∧ codeIndex labels.size c < (labels.size : Int))

def relabelTargets (labels : Array String) (codes : Array Int) :
    Except EarlyStopError (Array String) :=
  if codesIndexLabels labels codes then
    .ok (codes.map (fun c => labels[(codeIndex labels.size c).toNat]!))
  else .error .codeOutOfRange
```

`codeIndex` **resolves** a code the way numpy does — a negative index counts from
the END of the table (`size + c`) — and `codesIndexLabels` is the resulting domain,
`[-size, size)`, outside which the result is `.error codeOutOfRange`, numpy's
`IndexError`. The wrap is modeled rather than dodged: narrowing the domain to
non-negative codes would close the same rivals while quietly dropping a case numpy
answers, and a spec that dodges a case is what this lane exists to catch. (The
earlier total model got the negative side wrong twice over: `labels[c.toNat]!`
CLAMPS a negative code to position `0`, so it returned the first label where numpy
returns the last.) The correspondence is machine-checked by `axiom_check.py` in
both directions and on both sides of zero — front-indexed, end-indexed, and
out-of-range codes are each drawn and each asserted, and the run fails if the model
declines where numpy returns a value or returns a value where numpy raises.

`targetFor` therefore returns `(relabelTargets ls codes).map Sum.inr` on the
categorical branch, the impl binds the decode with `←` inside the guard, and the
postcondition binds the TRAINING decode first — `(relabelTargets ls yTrain).bind
(fun yT => …)` — so a `codeOutOfRange` from the pair the contract names is the
result whatever the scorer would have said, and a `codeOutOfRange` the named pair
does NOT produce refutes the impl that produced it. Against that contract both
attacks fail to verify. They are carried in `properties.py` as
`weak-getd-train-decode-hoisted` (= `atk_6`) and `weak-getd-val-decode-hoisted`
(= `atk_7`), sharing one unconditional witness at
`isClf = false, labels = none, useVal = false, xVal = none, yVal = none,
yTrain = #[0]`: there the contract demands the raw-code SUCCESS and each rival
returns `Except.error EarlyStopError.codeOutOfRange`, and
`Except.error ≠ Except.ok` needs no assumption about the opaque carriers. Under
the previous total decode that same input returned the very success the contract
demands, which is precisely why the attacks verified.

G-EQ's advisory added that a repair must keep admitting
`pos-getd-decode-precompute`'s "genuinely safe shape (a val-site hoist whose
defaulted gather is in range)" or it would overshoot into SPEC-TOO-STRONG. The
in-range qualification is where that shape fails: its defaulted gather is in range
only when the code array it is handed is EMPTY, and the construct the positive
actually shipped meets non-empty codes on the four regressor parametrizations —
which is the break above. So the shape is not admitted, and the overshoot is
guarded by three controls instead, all required to VERIFY:

* `pos-unbound-consult` NAMES a defaulted stand-in decode (and a scorer
  application on it) above the guard without performing either; its faithful patch
  resolves (`3 passed, 75 deselected, 1 warning in 399.63s`);
* `pos-labels-map-precompute` precomputes the TRAINING decode above the `isClf`
  guard under `Option.map`, so the gather runs on the table the caller supplied and
  a regressor performs no gather at all;
* `pos-option-map-precompute` does the same for the validation decode.

The boundary this lane draws is therefore *performing* the gather, not mentioning
it — the same bind-site boundary as the scoring lane, one operation earlier. A
`relabelTargets ls cs` an impl never binds is a gather numpy has not yet attempted,
exactly as an unbound `scorer x t` is a call not yet made.

## Prepatch discriminator

`Solution_prepatch.lean` drops ops 2 and 6 (the re-encodes): both target arrays
are forwarded as `Sum.inl yTrain` / `Sum.inl codes` regardless of `isClf`. Because
it never decodes, it also never reads the class-label table; the validation
arguments are still read only inside the `useVal` branch, so the twin isolates the
missing decode. On the `isClf = true, labels = some ls` branch the spec binds the
decode and scores its result —
`(relabelTargets ls yTrain).bind (fun yT => … scorer xTrain (Sum.inr yT) …)` —
while the pre-patch impl appends `scorer xTrain (Sum.inl yTrain)` without decoding
at all. `Sum.inr …` and `Sum.inl …` are distinct constructors, and the twin has no
`bind` over the decode to match the spec's, so the carried gold proof's `rfl`
cannot close the training-score clause — G-DIFF satisfied.

Measured on the current interface: the twin fails with exit 1 and **16** unclosed
`rfl` goals out of the proof's 2⁵ = 32 cases — exactly the sixteen `isClf = true`
cases, and none of the sixteen `isClf = false` ones. They split into the two
clauses the twin misses:

* **8 goals — the (C_lbl) disposition** (cases `true.none.*`: `isClf = true,
  labels = none`, all eight `useVal`/`xVal`/`yVal` combinations). Every one reports
  the same required right-hand side,
  `Except.error EarlyStopError.absentClassLabels`, against a left-hand side that is
  the twin's own reduction. The twin never reads the table, so it can never report
  that the table is absent.
* **8 goals — the missing decode** (cases `true.some.*`: `isClf = true,
  labels = some ls`, all eight combinations). Every one reports a right-hand side
  that OPENS with `(relabelTargets ls yTrain).bind fun yT => …` and scores
  `Sum.inr yT`, against a twin side that never mentions `relabelTargets` and scores
  `Sum.inl yTrain` — the decoded pair the contract names versus the raw codes the
  twin hands over. The three shapes, as the twin reports them (`ls` appears as the
  `cases`-introduced `val✝`):
  * the four `useVal = false` combinations report
    ```
    (relabelTargets val✝ yTrain).bind fun yT =>
      Except.map (fun trScore => { trainScores := trScores ++ [trScore],
                                   valScores := vlScores,
                                   stop := shouldStop (trScores ++ [trScore]) })
        (scorer xTrain (Sum.inr yT))
    ```
  * `useVal = true, xVal = some, yVal = some` reports the two-decode/two-call
    chain, ending in `scorer val✝¹ (Sum.inr yV)` — it misses the validation-site
    decode as well as the training one;
  * the three `useVal = true` combinations with a validation argument absent report
    the training decode and the training scoring call, then the validation-codes
    read and the validation decode, and only then the absence. The
    `xVal = none, yVal = none` case, where `ls` is `val✝`:
    ```
    (relabelTargets val✝ yTrain).bind fun yT =>
      (scorer xTrain (Sum.inr yT)).bind fun x =>
        (readValCodes none).bind fun codes =>
          (relabelTargets val✝ codes).bind fun x =>
            Except.error EarlyStopError.absentValidationData
    ```
    The other two are identical except that `readValCodes` is instantiated at the
    `yVal` they were given — `readValCodes (some val✝)` where only the design matrix
    is absent, so the decode there is on codes the caller did supply.
    These three did NOT discriminate under the previous, total-`scorer` contract:
    both spec and twin then reduced to a bare `absentValidationData` and closed by
    `rfl`. They discriminate now because the contract names the training decode, the
    training scoring call and the validation decode *before* the absence is
    reported, so which pair each of those operations was about is still observable
    on a path that ends in an error.

  Note the decode's own partiality is what puts `relabelTargets` at the HEAD of all
  eight right-hand sides rather than inside a `scorer` argument: since the gather
  may refuse, the contract has to sequence it, and a twin that omits it cannot
  produce that `bind` by reduction. The four `useVal = false` goals therefore also
  changed shape when the decode became partial — they previously read
  `Except.map (fun trScore => …) (scorer xTrain (Sum.inr …))` with no leading
  `bind` at all.

The second group is exactly the F2P scenario: a classifier with string targets,
where handing the scorer the raw integer codes (`Sum.inl`) instead of the decoded
labels (`Sum.inr`) is the defect.

## Excluded case: divergence

The frozen solution sets no termination-semantics option and the variant scope
check admits a `partial def` in the impl region, so an impl may introduce an
unbounded recursion. Measured: an impl that adds
`partial def spin (n : Nat) : Nat := spin (n + 1)` and evaluates it into a
discarded binding, while computing the result exactly as gold, VERIFIES (build
exit 0, scope check clean) — the discarded binding is erased before the obligation
is reduced, so the frozen proof closes unchanged. No witness can refute it: its
returned value is gold's at every input, so any claim true of it is true of gold
and the case would be recorded `witness-vacuous`. Nothing is therefore shippable
in the reject lane and no case is offered; the exclusion is recorded here rather
than papered over. (The neighbouring shape, where the diverging helper's result IS
consumed, is a value-level rival rather than a divergence one — it is rejected,
exit 1, because the recorded result is then not gold's — and adding it would test
clauses the existing rivals already pin, not termination.)

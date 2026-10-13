# mapping.md — scikit-learn__scikit-learn-14710

## Symbol binding (file:line @ base_commit 4b6273b)

Modeled function: `BaseHistGradientBoosting._check_early_stopping_scorer`
- File: `sklearn/ensemble/_hist_gradient_boosting/gradient_boosting.py`
- `def _check_early_stopping_scorer(self, X_binned_small_train, y_small_train,
  X_binned_val, y_val):` at line 422 @ base_commit.
- Body (pre-patch), lines 428–439:
  ```python
  self.train_score_.append(self.scorer_(self, X_binned_small_train, y_small_train))
  if self._use_validation_data:
      self.validation_score_.append(self.scorer_(self, X_binned_val, y_val))
      return self._should_stop(self.validation_score_)
  else:
      return self._should_stop(self.train_score_)
  ```
- Gold-patch edit (hunk @@ -426,11 +426,15 @@): inserts, immediately before each
  `self.scorer_(...)` call, a guarded re-encoding of the target array:
  ```python
  if is_classifier(self):
      y_small_train = self.classes_[y_small_train.astype(int)]   # before train scoring
  ...
  if is_classifier(self):
      y_val = self.classes_[y_val.astype(int)]                   # before val scoring
  ```

- Caller context, load-bearing for the model's input domain: `:147-149` sets
  `X_val, y_val = None, None` when `validation_fraction is None`, and `:167` sets
  `X_binned_val = None` with them; `self._use_validation_data` *is*
  `validation_fraction is not None`. So on the no-validation path both validation
  arguments this method receives are `None`, and the `if self._use_validation_data:`
  guard is what keeps `self.classes_[y_val.astype(int)]` off a `None`.

- Attribute context, equally load-bearing: `self.classes_` is assigned in exactly
  one place, `HistGradientBoostingClassifier._encode_y` at `:1029`
  (`self.classes_ = label_encoder.classes_`).
  `HistGradientBoostingRegressor._encode_y` (`:804-808`) only converts the targets
  to `Y_DTYPE` and defines no such attribute. And a regressor *does* reach this
  method: `fit` dispatches `if self.scoring == 'loss': … else: …
  self._check_early_stopping_scorer(…)` at `:214`/`:236`/`:252` (first iteration)
  and `:339`/`:356` (each later iteration), with no classifier guard. So on a
  regressor with `scoring != 'loss'`,
  the `if is_classifier(self):` guard is what keeps `self.classes_` off an
  `AttributeError`, exactly as `_use_validation_data` guards the validation
  arguments.

## The changed operation

`self.classes_[y.astype(int)]` is numpy fancy indexing: it produces the array
`[ self.classes_[int(y[0])], self.classes_[int(y[1])], … ]` — i.e. each
integer-encoded target code is mapped back to its original class label by
indexing the label table `self.classes_`. This is the operation the patch adds
(only when the estimator is a classifier). It is modeled DEEPLY as
`relabelTargets` (a gather/map), NOT axiomatized (§3, directive 7).

The gather is **partial**, and the model says so: numpy fancy indexing answers for
an index in `[-size, size)` only — a negative index counts backwards from the end
of the table — and RAISES `IndexError` for anything outside that window, so it
produces no array at all. `relabelTargets` therefore returns
`Except EarlyStopError (Array String)`: `.ok` of the gathered entries when every
code indexes, and `.error EarlyStopError.codeOutOfRange` — the model of that
`IndexError` — when some code does not. `codeIndex size c = if c < 0 then c + size
else c` is the wrap, modeled rather than dodged (clamping a negative code to `0`
would invent `classes_[0]` where numpy returns the last entry), and
`codesIndexLabels ls cs` is the decode's domain. G-AX validates the
correspondence in both directions and on both sides of zero.

Callees the function uses but does NOT change (modeled as opaque A-reference
signatures): `self.scorer_(self, X, y)` (the fitted scorer, a function of the X
data and the y targets it is handed) and `self._should_stop(scores)` (the
score-history stopping rule). `is_classifier(self)` / `self._use_validation_data`
are modeled as the boolean flags `isClf` / `useVal`. `self.train_score_` /
`self.validation_score_` are the threaded score-history lists.

## Lean ↔ Python type bijection

| Lean | Python |
|---|---|
| `labels : Option (Array String)` | the `self.classes_` attribute: `some ls` on a classifier, which sets it in `_encode_y` (`:1029`; string labels in the F2P scenario, `str`→`String` per the cheatsheet), `none` on a regressor, which never defines it |
| `readLabels` | the *read* `self.classes_` — an attribute access that succeeds on a classifier and raises on a regressor |
| `EarlyStopError.absentClassLabels` | the exception raised by reading the class-label table off the `is_classifier(self)` guard: `AttributeError: 'HistGradientBoostingRegressor' object has no attribute 'classes_'` |
| `codes : Array Int` | an integer-encoded target array (`y_small_train` / `y_val`); for a classifier these are the label codes `0..n_classes-1` (cf. `y.astype(int)`) |
| `codeIndex size c : Int` | where one code lands in a table of `size` entries under numpy fancy indexing: `int(c)` itself when non-negative, `int(c) + size` when negative (numpy counts a negative index backwards from the end). `int(c)` is `astype(int)`, i.e. truncation toward zero, so `-0.4` lands at the front (`0`) while `-1.4` lands on the last entry |
| `codesIndexLabels ls codes : Bool` | the gather's domain: every code resolves inside the table, `0 ≤ codeIndex ls.size c < ls.size` — exactly the codes `self.classes_[codes.astype(int)]` answers for, i.e. `codes` within `[-len(classes_), len(classes_))` |
| `relabelTargets ls codes : Except EarlyStopError (Array String)` | `self.classes_[codes.astype(int)]` — element-wise gather, `result[i] = self.classes_[codeIndex(len(self.classes_), codes[i])]`, as a **partial** operation: `.ok` of the gathered array when `codesIndexLabels` holds, and `.error codeOutOfRange` when it does not, which is numpy's refusal to gather |
| `EarlyStopError.codeOutOfRange` | the exception raised by gathering a code the label table has no entry for: `IndexError: index 12 is out of bounds for axis 0 with size 0` (measured; the `size 0` case is the empty stand-in table a hoisted decode builds with `Option.getD #[]`). Raised on either side of the window — a code `≥ len(classes_)` or `< -len(classes_)` |
| `targetFor isClf labels codes` | the guarded re-encode as a whole: `.ok (Sum.inl codes)` if not a classifier, the gather's own answer mapped through `Sum.inr` if a classifier (so `.error codeOutOfRange` when a code does not index), and `.error absentClassLabels` if a classifier without the attribute |
| `Targets := Array Int ⊕ Array String` | the y-array actually handed to the scorer: `Sum.inl` = raw codes (regressor / not a classifier, untouched), `Sum.inr` = decoded string labels (classifier) |
| `XData` (opaque) | the binned design matrix `X_binned_small_train` / `X_binned_val` passed to the scorer (held fixed per call site) |
| `xVal : Option XData` | the `X_binned_val` argument: `some x` when the estimator holds out a validation split, `none` when `validation_fraction is None` (`gradient_boosting.py:167` sets it to `None`) |
| `yVal : Option (Array Int)` | the `y_val` argument: `some codes` with a validation split, `none` otherwise (`:147-149` sets `y_val = None`) |
| `readValData` / `readValCodes` | the *read* of `X_binned_val` / `y_val` — a plain attribute/array use in Python, which succeeds on a real array and raises on `None` |
| `EarlyStopError.absentValidationData` | the exception raised by using an absent validation argument: `AttributeError: 'NoneType' object has no attribute 'astype'` from `self.classes_[y_val.astype(int)]` (and, for a hoisted scorer call, `self.scorer_(self, None, None)`) |
| `EarlyStopError.scoringRefused` | the exception raised by `self.scorer_(self, X, y)` itself when `X` and `y` do not describe the same samples: `ValueError: Found input variables with inconsistent numbers of samples: [0, 50]`, from `sklearn/utils/validation.py:206` via `check_consistent_length` inside every scorer's `_score` path. Measured, in the official instance image, from a patch that consults the scorer above the validation guard on a stand-in target array — see refinement.md, "Consulting the scoring function about an unnamed pair" |
| `Except EarlyStopError CheckResult` | the method's outcome: `.ok r` = it returned normally with post-state/decision `r`; `.error e` = it raised — because it read an argument the caller never created (`absentValidationData` for a validation argument, `absentClassLabels` for the class-label table), because the scorer it called refused the pair it was handed (`scoringRefused`), or because a decode it performed asked the label table for a code the table has no entry for (`codeOutOfRange`). Modeling the raise as a *value* is what makes the timing of each read, the arguments of each scoring call, and the pair each decode is performed on observable in a pure model — see refinement.md, the four lanes "Reading an absent validation argument", "Reading an absent class-label table", "Consulting the scoring function about an unnamed pair" and "Performing the decode on a stand-in pair" |
| `Score` (opaque) | one scalar score value (`float`) appended to a score history |
| `scorer : Scorer := XData → Targets → Except EarlyStopError Score` | `self.scorer_(self, X, y)` — `self` fixed; a deterministic *partial* function of the X data and the y targets it is handed. Partial because the scorer compares `y` against predictions it derives from `X`: `_BaseScorer.__call__` → `_PredictScorer._score` → `metric(y_true, y_pred)` → `check_consistent_length`, which raises `ValueError` when the two lengths disagree. `Except`-valued rather than total, so that WHICH pair the procedure consults the scorer about is observable, and not merely which score it records |
| `shouldStop : List Score → Bool` | `self._should_stop(scores)` |
| `isClf : Bool` | `is_classifier(self)` |
| `useVal : Bool` | `self._use_validation_data` |
| `trScores : List Score` | `self.train_score_` before this call |
| `vlScores : List Score` | `self.validation_score_` before this call |
| `CheckResult { trainScores, valScores, stop }` | the post-call `(self.train_score_, self.validation_score_)` and the returned bool |

`codes` typed `Array Int` for BOTH branches is a faithful abstraction: the
re-encoding only fires when `isClf`, and on the non-classifier branch the array
is passed through untouched (`Sum.inl`), so its concrete element type is
irrelevant to the modeled transformation.

`useVal` and the presence of the validation arguments are separate binders even
though the repository moves them together (`_use_validation_data` *is*
`validation_fraction is not None`). Keeping them separate is what lets the
contract say something at the `useVal = false, xVal = none, yVal = none` point the
repository actually reaches, and it makes the third clause
(`useVal = true` with an argument absent) a state the caller never produces — a
disposition the contract pins so that an impl cannot satisfy it by conflating the
flag with the presence. Nothing is weakened by the extra points: the two clauses
that the repository does reach are exactly the two the method's own guard
distinguishes.

`isClf` and the presence of `labels` are separate binders for the same reason and
with the same faithfulness argument: the repository moves them together (only a
classifier defines `classes_`), so `isClf = false, labels = none` and
`isClf = true, labels = some ls` are the two points it reaches, and they are exactly
the two the `if is_classifier(self):` guard distinguishes. `isClf = true,
labels = none` is the state the caller never produces, and pinning its disposition
(the `absentClassLabels` error) is what makes *when* the table is read observable;
`isClf = false, labels = some ls` is admitted as an ordinary success on the raw
codes, since a table that is present but not needed is simply not read.

## Callee provenance + flag deps

- `relabelTargets` — **A-reference** (deep model of the changed op). Validated
  `== self.classes_[y.astype(int)]` by G-AX over boundary + fuzz, in both
  directions and over all three parts of the domain: codes indexed from the front,
  codes indexed from the END (numpy's negative-index wrap, which `codeIndex`
  reproduces), and codes outside `[-size, size)`, where the model's
  `.error codeOutOfRange` must land exactly where numpy's `IndexError` does. Flag dep: the
  gather is applied iff `is_classifier(self)` is true, and so is the *read* of the
  table it gathers from — only classifier estimators define `classes_`
  (`:1029`), so on regressors the targets are forwarded unchanged and the table is
  never touched. `readLabels` is the model of that read, not a callee.
- `scorer`, `shouldStop` — **A-reference** (unchanged callees, opaque signatures;
  no property of them is consumed — the proof only threads their results, so the
  modeled behavior is just "deterministic function of the given arguments,"
  trivially matched by the real callees). `scorer` is `Except`-valued: the modeled
  behavior is "deterministic function of the given arguments, which may refuse
  them", and the real `self.scorer_` does refuse them
  (`check_consistent_length`). Nothing in the proof depends on WHEN it refuses —
  the contract quantifies over every partial scorer, so the total ones the
  repository's well-formed call sites see are a special case.

## Proof obligations

`correct_scoreEarlyStop` closes by case analysis on `isClf`, `labels`, `useVal`,
`xVal` and `yVal` (2⁵ = 32 cases, one `rfl` each) followed by reduction of the
`Except` do-block. The postcondition names each branch's outcome as an
`Except.bind`/`Except.map` over the decode's answer about the array that branch
decodes and then over the scorer's answer about the pair that branch names, which
is definitionally what the impl's `←` binds on the same two partial operations
compute, so no case analysis on either answer is needed and every case is `rfl`.
It consumes NO property axiom — every `_prop` slot is empty (the proof
agent should not need the axiom-propose loop).

An impl that arranges the same two binds differently may need to reassociate them
first: `(Except.map Sum.inr x) >>= k` and `x >>= fun d => k (Sum.inr d)` are equal
but not definitionally so while `x` is stuck, so such an impl proves a one-line
`have … := by intro …; cases x <;> rfl` in its own proof region and rewrites with
it. That is a proof-region matter only; the frozen body closes gold unchanged.

## G-CONF fuzz seed

Pinned seed: `20240630`. (The impl region's only value transformation is the
A-reference `relabelTargets`; the remaining ops are control-flow/state-threading
glue with no independent R/I shadow ⇒ `conf_skip = true`, G-CONF skip stub. Seed
recorded for the stub manifest and reused by `axiom_check.py`.)

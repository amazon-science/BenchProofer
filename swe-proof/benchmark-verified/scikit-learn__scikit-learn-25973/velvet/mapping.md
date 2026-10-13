# mapping.md — scikit-learn__scikit-learn-25973

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = 10dbc142bd17ccf7bd38eec2ac04b52ce0d1009e`, states the type
abstraction (the bijection G-AX uses to bridge Lean↔Python), and gives the
provenance of the one deep-model reference.

Repo file under change: `sklearn/feature_selection/_sequential.py`.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `runScoringRounds (source : CvSource) (k : Nat)` | the `for _ in range(n_iterations):` greedy loop in `SequentialFeatureSelector.fit` — `sklearn/feature_selection/_sequential.py:283-289`, which on each round calls the per-candidate scorer that reads the cross-validation split source — `sklearn/feature_selection/_sequential.py:298-322` | the modeled changed control flow: `k = n_iterations` consecutive scoring rounds, each reading the split source |
| `CvSource` (`splits`, `reusable`, `consumed`) | the value bound to the `cv` argument that flows into `cross_val_score(..., cv=...)` — a `cv_object`, splitter, or **iterable of `(train, test)` splits** (incl. a one-shot generator); see the `cv` parameter doc `_sequential.py:80-95` and `_parameter_constraints["cv"] == ["cv_object"]` (`_sequential.py:166`) | abstract model of a split source and its read/consume state |
| `materialize` *(deep model — A-reference)* | `check_cv(self.cv, y, classifier=is_classifier(self.estimator))` — `sklearn/model_selection/_split.py:check_cv`; for a raw iterable it returns `_CVIterableWrapper(cv)`, whose `__init__` stores `self.cv = list(cv)` (`_split.py`) | pure spec: buffer a possibly single-pass source into a re-readable one carrying the same split sequence; deep model of the UNCHANGED helper `check_cv`, validated == real `check_cv` by axiom_check.py (G-AX), NOT consumed as an axiom |
| `readObs` / `advance` | one read of the split source: `cross_val_score(estimator, X_new, y, cv=<source>, ...)` internally calls `cv.split(...)` / iterates the source (`sklearn/model_selection/_validation.py`); a generator yields its splits once then is exhausted | pure spec: the splits one read observes, and the source state after that read |

The pre-patch behaviour the change repairs (refinement audit only, not in the
consumer spec view): `fit` passed `self.cv` (the raw source) into every round's
`cross_val_score` call, so a single-pass `self.cv` was exhausted by the first
round and observed empty thereafter — `_aggregate_score_dicts([])` then raised
`IndexError`. The patch inserts one `check_cv(...)` call before the loop and
threads its result (`cv`) through `_get_best_new_feature_score`.

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-AX uses to translate values between the Lean value domain and
the Python repo types.

| repo reality | Lean carrier | bijection |
|---|---|---|
| a cross-validation split source (splitter / iterable / generator) | `CvSource` | the underlying train/test split sequence ↔ `splits : List Nat` (each split abstracted to a token `Nat`; only its presence/position is observed, not its array contents); "is re-readable" ↔ `reusable = true`; "has been exhausted" ↔ `consumed = true` |
| number of greedy selection rounds `n_iterations` | `k : Nat` | `n_iterations` (`_sequential.py:280`) ↔ `k` |
| the splits one scoring round sees | `readObs source : List Nat` | the sequence `cross_val_score` iterates for that round ↔ `readObs`; exhausted ⇒ `[]` |
| `check_cv(cv, …)` (raw iterable case) | `materialize` | `_CVIterableWrapper(list(cv))` is re-readable and yields the same splits every call ↔ `materialize s = { splits := s.splits, reusable := true, consumed := false }` |

A `CvSource` whose `reusable = false` and `consumed = false` models a fresh
single-pass generator; the first `readObs` returns its full sequence and
`advance` flips `consumed`, after which `readObs` returns `[]` — the exhaustion
that produced the empty-splits failure.

## 3. Callee provenance (kind-A — checked by G-AX / axiom_check.py)

### 3.1 `materialize` deep model ↔ `check_cv` (A-reference)
**Callee:** `sklearn.model_selection.check_cv(cv, y=None, *, classifier=...)`.
The buffering step the patch adds is modeled **deeply** by `materialize` in the
`pure` region; there is **no consumed axiom** about it. The key invariant the
spec relies on: after `check_cv`, the returned cross-validator is re-readable —
calling `.split(...)` returns the *full* split sequence every time, even when the
input `cv` was a one-shot generator. This holds because, for a raw iterable,
`check_cv` returns `_CVIterableWrapper(cv)` whose `__init__` does `self.cv =
list(cv)` (materializes the generator into a list once) and whose `split()`
re-iterates that stored list on every call. For an already-reusable splitter or
integer, `check_cv` returns an object that was already re-readable.

**Soundness check (G-AX):** `axiom_check.py` runs the REAL `check_cv` on a
one-shot generator of `(train, test)` splits and asserts (a) reading the
materialized result TWICE yields the identical full split sequence both times
(re-readability — the property `materialize` claims), and (b) the split sequence
the materialized object yields equals the original generator's full sequence (no
splits dropped/added). It also confirms the un-buffered baseline (reading the raw
generator twice) loses the splits on the second read — establishing the
discriminator is real. Imports only `numpy` + `sklearn.model_selection` (the same
module the gold patch imports `check_cv` from). Exit 0 iff sound.

`is_classifier(self.estimator)` (the other import the patch adds) only selects
`StratifiedKFold` vs `KFold` for the integer/None `cv` case; it does not affect
the iterable/generator path that the bug and the F2P test exercise, so it is not
modeled (it is observationally irrelevant to the discriminating behaviour). This
is recorded as a flag dependency: G-AX fuzzes the iterable path (`classifier`
irrelevant there).

## 4. G-CONF fuzz seed

`conf_skip = true` (meta.json): the impl region's discriminating observable is a
STATEFUL side effect (one-shot-generator exhaustion across repeated reads), not a
pure, input→output R/I shadow this gate can fuzz deterministically without
standing up the real `cross_val_score` / CV machinery and a live generator. See
`conformance_check.py` (status=skip) for the full justification; the A-reference
soundness is covered by `axiom_check.py` (G-AX). The G-AX RNG seed is pinned to
**`25973`** for a reproducible verdict.

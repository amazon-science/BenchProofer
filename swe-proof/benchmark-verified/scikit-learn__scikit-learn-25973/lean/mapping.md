# mapping.md — scikit-learn__scikit-learn-25973

## Symbol binding (file:line @ base_commit 10dbc142bd17ccf7bd38eec2ac04b52ce0d1009e)

- Modeled function: `SequentialFeatureSelector.fit`, repeated-scoring mechanism.
  `sklearn/feature_selection/_sequential.py:189-292` (the candidate-evaluation
  loops), with the scoring consultation in `_get_best_new_feature_score`,
  `sklearn/feature_selection/_sequential.py:294-317`.
- Patched lines (gold): import `is_classifier` / `check_cv`
  (`_sequential.py:11,16`); `cv = check_cv(self.cv, y, classifier=is_classifier(self.estimator))`
  inserted at `_sequential.py:262`; `_get_best_new_feature_score` gains a `cv`
  parameter and uses `cv=cv` instead of `cv=self.cv` (`_sequential.py:294,312`).
- Real callee driving the fix: `check_cv` and `_CVIterableWrapper`,
  `sklearn/model_selection/_split.py:2406-2462` and `:2353-2403`.
  `check_cv` wraps a non-splitter iterable in `_CVIterableWrapper`, whose
  `__init__` does `self.cv = list(cv)` (`:2357`) — the single materialisation
  that makes the splits reusable; `.split()` re-yields `self.cv` every call.

## Lean ↔ Python type bijection (used by G-CONF; G-AX is a skip)

| Lean | Python |
|---|---|
| `folds : List Nat` | the sequence of split tokens the cv source yields; token `n` ↔ split `([n],[n])`, recovered as `train[0]` |
| `oneShot : Bool` | the cv source is a single-traversal generator (`True`) vs a re-readable list (`False`) |
| `numEvals : Nat` | total number of `cross_val_score` consultations across the nested candidate/iteration loops in `fit` |
| `result : List (List Nat)` | per-evaluation observed split set, in evaluation order |

The numeric cross-validation scores are NOT modeled: they are downstream of the
splits and orthogonal to the bug (which is about splits vanishing on reuse).

## Callee provenance + flag deps

- `check_cv(cv, y, classifier=...)` — UNCHANGED callee the fix CALLS. Not
  axiomatized: its reuse-making effect (`list(cv)` once, re-yield every
  `.split()`) is modeled deeply by `let shared := folds` + observing `shared`
  every evaluation. G-CONF drives the REAL `check_cv`/`_CVIterableWrapper`.
- Flag dependency: the wrapping happens only when `cv` is an iterable that is not
  itself a splitter (`not hasattr(cv, "split")`). G-CONF therefore feeds a raw
  generator / list (no `.split`), exercising the `_CVIterableWrapper` path — the
  configuration the issue's `LeaveOneGroupOut().split(...)` generator hits.

## G-CONF fuzz seed

Pinned seed: **25973**. N = 100_000. Fuzzes `folds` (length 0–6, tokens 0–9),
`oneShot` (50/50), `numEvals` (0–6) — covering empty collections, zero
evaluations, and the multi-evaluation reuse case where the pre-fix path drains.

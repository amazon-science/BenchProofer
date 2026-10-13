# refinement.md — scikit-learn__scikit-learn-25973

Maps every op in `implementation_repeatedEvaluations` (Solution.lean) to its
`patch.diff` counterpart. Tags: **R** type-refinement, **A-consumed** axiom used
by proof, **A-reference** deep model validated == real callee by G-AX, **I**
identical concrete op.

The modeled function is the repeated-scoring mechanism of
`SequentialFeatureSelector.fit`: it performs many candidate-feature evaluations,
and every evaluation calls `cross_val_score(..., cv=...)`, which consults the
cross-validation source for the splits to run. The fix concerns ONE behaviour:
the splits must be reusable, so every evaluation sees the complete split set.
The fix is modeled deeply (no axioms).

| # | Lean impl op | patch.diff / repo counterpart | tag | note |
|---|---|---|---|---|
| 1 | `let shared := folds` | `cv = check_cv(self.cv, y, classifier=is_classifier(self.estimator))` (added before the loop) | R | `folds : List Nat` ↔ the split tokens the cv source yields. `check_cv` wraps a one-shot iterable in `_CVIterableWrapper`, whose `__init__` runs `self.cv = list(cv)` — i.e. it materialises the collection ONCE into a reusable value. `shared := folds` models that single capture. |
| 2 | (`oneShot` deliberately NOT consulted) | the source's single-vs-multi traversal nature no longer affects behaviour after capture | R | The whole point of the fix: whether the source was a single-traversal generator is now irrelevant. Modeled by omission — `oneShot` is an input that never affects the result. |
| 3 | `for _ in [0:numEvals] do observed := observed ++ [shared]` | the candidate-feature loop: `for _ in range(n_iterations): ... self._get_best_new_feature_score(... cv ...)` and within it `for feature_idx in candidate_feature_indices: cross_val_score(..., cv=cv, ...)` | R | `numEvals : Nat` ↔ the total number of `cross_val_score` consultations across the nested loops. Each consultation reads `cv` (the reusable `check_cv` result) and thus observes the complete split set `shared`. The numeric scores `cross_val_score` returns are downstream of the splits and irrelevant to the bug, so they are not modeled. |
| 4 | `return observed` | the loop completes without the `_aggregate_score_dicts` IndexError; every evaluation produced a full score | R | the result records the split set observed per evaluation; pre-fix, a drained source yields an empty set on later evaluations → empty scores → IndexError. |

The signature change `_get_best_new_feature_score(self, estimator, X, y, current_mask)`
→ `(self, estimator, X, y, cv, current_mask)` and the `cv=self.cv` → `cv=cv`
substitution are the plumbing that threads the once-captured reusable `cv` into
each evaluation; both are captured by op #1 (single capture) + op #3 (every
evaluation reads the captured value).

No changed op is inexpressible. No row is A-tagged ⇒ `axiom_check.py` is a skip
stub and `meta.json axioms`/`deep_model_references` are empty.

## Prepatch correspondence (G-DIFF)

- `Solution_prepatch.lean` carries the real bug: the source is consulted
  directly inside each evaluation (`remaining`, drained when `oneShot=true`),
  mirroring the pre-fix `cv=self.cv` passed straight to each `cross_val_score`.
  With `oneShot=true, numEvals=2, folds=[a]` the impl yields `[[a], []]`: the
  second observation is empty, contradicting the spec clause
  `∀ s ∈ result, s = folds`. The carried gold proof cannot close it ⇒ fails
  G-VERIFY. This is exactly the `IndexError: list index out of range` the issue
  reports (later folds drained → empty scores).

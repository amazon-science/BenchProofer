# refinement.md — scikit-learn__scikit-learn-13496

The operation-by-operation correspondence between `model.py`'s implementation
(`refit_to_size` dispatching over `reuse_and_extend` / `rebuild_all`, plus the
deep pure model `fresh_run`/`effective_reuse`) and `patch.diff` (the gold
patch). Each step is tagged **R** (type refinement), **A-consumed** (proof uses
an axiom's `Ensures`), **A-reference** (a deep model validated == the real
callee by axiom_check.py / G-AX), or **I** (identical concrete operation). The
claim: any implementation that verifies against this frozen spec, refined per
the map below, is behaviourally equal to the gold patch on the tested inputs, so
it resolves.

`patch.diff` is the gold patch **verbatim** (it applies cleanly at
`base_commit` and is the real correctness oracle, G-RESOLVE).

## A. What the gold patch changes

The gold patch touches only `IsolationForest.__init__` in
`sklearn/ensemble/iforest.py`:

```
  def __init__(self, ..., random_state=None,
-              verbose=0):
+              verbose=0,
+              warm_start=False):
       super().__init__(
           ...,
           max_features=max_features,
+          warm_start=warm_start,
           n_jobs=n_jobs, random_state=random_state, verbose=verbose)
```

(plus a docstring/glossary paragraph for the new parameter — documentation
only, no observable behaviour). The behavioural delta is: the caller's
`warm_start` option is now ACCEPTED and FORWARDED to the parent
`BaseBagging.__init__`, where it is stored as `self.warm_start`
(`bagging.py:213`) and later read by the UNCHANGED `BaseBagging._fit`
(`bagging.py:338-385`) to decide whether to keep or discard the existing
roster. Pre-patch the option is dropped, so `self.warm_start` keeps its
inherited default `False` and every fit rebuilds.

## B. The correspondence

| # | model.py impl op | patch.diff / repo op | tag | justification |
|---|---|---|---|---|
| B1 | `existing : List[int]` | `self.estimators_` (a list of fitted sub-estimators) | R | object list ↔ `List[int]` of `id(...)` identities (mapping.md §2). |
| B2 | `requested_reuse : bool` | the `warm_start` value the caller passes to `IsolationForest(...)` | R | identity on bools; this is the option the patch's `+ warm_start=False` parameter and `+ warm_start=warm_start,` forwarding make reachable. |
| B3 | `target_count : int` | `self.n_estimators` | R | identity on ints. |
| B4 | `if requested_reuse and len(existing) > 0:` (the dispatch in `refit_to_size`) | `self.warm_start` forwarded by `__init__`, then read by `_fit`'s `if not self.warm_start or not hasattr(self,'estimators_'): self.estimators_=[]` and `if self.warm_start and len(self.estimators_)>0:` (`bagging.py:338, 362`) | A-reference | the changed *forwarding* is modeled deeply: `effective_reuse(requested_reuse, len(existing)>0)` IS the fit-time predicate. The gold patch's only job is to make `self.warm_start == requested_reuse` instead of the dropped-to-`False`; once forwarded, the branch is the unchanged parent's. Validated == real `IsolationForest` by axiom_check.py. |
| B5 | `reuse_and_extend(existing, target_count)`: keep `existing` as a prefix, append `target_count - len(existing)` fresh members | `_fit` warm path: `self.estimators_` left intact, `n_more_estimators = self.n_estimators - len(self.estimators_)` new members appended via `self.estimators_ += [...]` (`bagging.py:343, 382-385`) | A-reference | unchanged parent code; the deep model spells out the keep-prefix-then-extend. `ToSeq(Result()) == ToSeq(existing) + fresh_run(target_count-len(existing))` captures both the preserved prefix (so `estimators_[0]` survives) and the freshly-built tail. G-AX checks it == real behaviour. |
| B6 | `rebuild_all(target_count)`: build `target_count` fresh members | `_fit` cold path: `self.estimators_ = []` then a full forest of `self.n_estimators` is built (`bagging.py:340, 368-385`) | A-reference | unchanged parent code; `ToSeq(Result()) == fresh_run(target_count)` — every member fresh, no prior member survives. G-AX checks it == real behaviour. |
| B7 | `fresh_run(n)` — pure run of `n` freshly-built members; `FRESH_MEMBER()` sentinel | a freshly-built sub-estimator clone (`_parallel_build_estimators`), whose object identity is new | A-reference + I | the fresh tail is per-member identity-distinct from the prior roster; modeled by the sentinel `-1` (distinct from non-negative existing identities). The `lemma_fresh_snoc` step is proof-only (I, no repo op). |
| B8 | `return result` (a `List[int]`) | `self.estimators_` after `_fit` returns `self` | R | the observable roster; the F2P test reads `len(clf.estimators_)` and `clf.estimators_[0] is tree_1`, both content/identity facts the `List[int]` model preserves. |

## C. The discriminator (what makes verify ⟹ correct)

The F2P test `test_iforest_warm_start` fits 10 trees with `warm_start=True`,
remembers `tree_1 = clf.estimators_[0]`, enlarges to `n_estimators=20`, fits
again, and asserts `len(clf.estimators_) == 20` **and**
`clf.estimators_[0] is tree_1`. Both facts are pinned by the reuse-case
postcondition

```
Implies(effective_reuse(requested_reuse, len(existing) > 0),
        ToSeq(Result()) == ToSeq(existing) + fresh_run(target_count - len(existing)))
```

— the `ToSeq(existing)` prefix forces `Result()[0] == existing[0]` (the
preserved first member: `estimators_[0] is tree_1`), and `len(Result()) ==
target_count` forces the count (`== 20`). The pre-patch behaviour — the
constructor drops `warm_start`, so `self.warm_start` stays `False` and `_fit`
always rebuilds — is reproduced by `model_prepatch.py` (`refit_to_size` ignores
`requested_reuse` and always calls `rebuild_all`). It produces an all-fresh
roster (`fresh_run(target_count)`), whose first element is `FRESH_MEMBER() ==
-1 != existing[0] >= 0`, so it **fails** exactly the reuse-case postcondition
(G-DIFF). That is precisely the spec sensing the change.

## D. No kind-3 (unexpressible-changed-op) steps

Every step is R, A-reference, or I. There is **no consumed `@ContractOnly`
axiom** in this bundle: the option-forwarding (the actual change) and the two
`_fit` roster paths it re-enables are all modeled DEEPLY (`effective_reuse`,
`reuse_and_extend`, `rebuild_all`, `fresh_run`), then validated == the real
`sklearn.ensemble.IsolationForest` by axiom_check.py (G-AX, A-reference). The
only trust points are deep-model fidelity (G-AX) and refinement fidelity (this
document, G-EQ).

## E. verify(model) ⇒ resolved

`refit_to_size` verifies only if it preserves the existing roster prefix and
size under reuse (B5) and rebuilds afresh otherwise (B6), with the reuse
decision faithfully carried from `requested_reuse` (B4). By R (object list ↔
`List[int]` of identities; `is` ↔ identity equality) the verified roster equals
the real `clf.estimators_` after a warm-started refit; by G-AX the deep model
equals the real `IsolationForest` incremental behaviour (A-reference). The gold
patch makes `self.warm_start == warm_start` (the forwarding), which is the only
thing needed to reach that behaviour — and the gold patch resolves (G-RESOLVE).

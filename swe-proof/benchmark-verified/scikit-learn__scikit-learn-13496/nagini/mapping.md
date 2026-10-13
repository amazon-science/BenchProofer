# mapping.md — scikit-learn__scikit-learn-13496

Binds every `model.py` symbol to its repository counterpart at
`base_commit = 3aefc834dce72e850bff48689bea3c7dff5f3fad`, states the type
abstraction, and documents the provenance of the deep model (there are no
consumed axioms in this bundle).

Repo files involved:
- `sklearn/ensemble/iforest.py` — the changed file (`IsolationForest.__init__`).
- `sklearn/ensemble/bagging.py` — the UNCHANGED parent (`BaseBagging.__init__`
  and `BaseBagging._fit`) whose incremental-roster behaviour the change exposes.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `refit_to_size(existing, target_count, requested_reuse)` | the data-flow `IsolationForest.__init__`'s `warm_start` option → `self.warm_start` → the reuse branch of `BaseBagging._fit` (`bagging.py:338-385`) | the modeled behaviour: rebuild-or-extend the roster, gated by the construction-time reuse option the constructor must carry through |
| `requested_reuse` parameter | the `warm_start` value the caller passes to `IsolationForest(...)` and that `__init__` must forward in its `super().__init__(...)` call (`iforest.py:177-190`) | the option whose faithful forwarding IS the fix |
| `reuse_and_extend(existing, target_count)` | `_fit` with `self.warm_start and hasattr(self,'estimators_')`: the existing `self.estimators_` are kept and only `n_more_estimators = self.n_estimators - len(self.estimators_)` new members are appended (`bagging.py:338-385`, esp. 343, 382-385) | the warm-start fit path (UNCHANGED parent code) |
| `rebuild_all(target_count)` | `_fit` with `not self.warm_start`: `self.estimators_ = []` is reset (`bagging.py:338-341`) and a whole forest of `self.n_estimators` members is built afresh | the cold fit path (UNCHANGED parent code) |
| `effective_reuse(requested_reuse, have_members)` | the fit-time predicate `self.warm_start and hasattr(self,'estimators_') and len(self.estimators_) > 0` controlling whether existing members are kept (`bagging.py:338, 362`) | pure spec: the reuse decision |
| `fresh_run(n)` | the run of `n` freshly-built sub-estimators a fit appends/produces (`_parallel_build_estimators` outputs, reduced into `self.estimators_`, `bagging.py:368-385`) | pure spec: a run of freshly-built members |
| `FRESH_MEMBER()` | the identity of a freshly-built sub-estimator object (a brand-new `ExtraTreeRegressor` clone, distinct from any pre-existing one) | pure spec: the fresh-member sentinel identity |
| `lemma_fresh_snoc(n)` | (proof-only) — bridges the back-append fold to the front-recursive `fresh_run` | pure lemma, no repo counterpart |

The single changed line of the gold patch is the constructor's forwarding of
`warm_start=warm_start` into `super().__init__(...)` (`iforest.py:185-190`, the
`+ warm_start=warm_start,` hunk) plus the new `warm_start=False` parameter
(`iforest.py:176`). Everything `refit_to_size` dispatches to is UNCHANGED
parent-class code that the forwarded option merely re-enables.

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| `self.estimators_` : a Python `list` of fitted sub-estimator objects | `List[int]` of member identities | `estimators_[k]` ↔ `existing[k] == id(estimators_[k])`; `len(estimators_)` ↔ `len(existing)`; the result roster ↔ `Result()` |
| object identity (`a is b`) — the property the F2P test checks via `clf.estimators_[0] is tree_1` | integer equality of identities | a preserved member keeps its identity; a freshly-built member gets a NEW identity, modeled by the sentinel `FRESH_MEMBER() == -1`, which the precondition forces distinct from every already-present (non-negative) identity |
| `self.n_estimators` (the requested total) | `target_count : int` | identity on ints |
| `self.warm_start` (the construction-time option, after forwarding) | `requested_reuse : bool` | identity on bools |
| `str` docstring / glossary text added by the patch | (omitted) | documentation only; no observable behaviour, not modeled |

`str`/object identity are banned in Nagini, so member identities are `int` and
the roster is `List[int]`; the specification is carried over `PSeq[int]` via
`ToSeq`. A freshly-built member's identity is the sentinel `-1`; already-present
identities are non-negative (precondition), so "the existing prefix is
preserved" is a non-vacuous structural fact (a rebuilt roster is all `-1`, hence
its first element differs from any `existing[0] >= 0`).

## 3. Deep model provenance (A-reference — checked by G-AX / axiom_check.py)

This bundle has **no consumed `@ContractOnly` axiom**. The reuse decision and
the roster update are modeled DEEPLY:

- `effective_reuse` spells out the fit-time predicate `self.warm_start and
  len(self.estimators_) > 0` (`bagging.py:338, 362`).
- `reuse_and_extend` / `rebuild_all` spell out the two `_fit` paths: keep the
  existing prefix and append `target_count - len(existing)` fresh members, vs.
  reset and build `target_count` fresh members (`bagging.py:338-385`).
- `fresh_run(n)` is the pure run of `n` freshly-built members.

The deep model is validated **== the real callee** out-of-band by
`axiom_check.py` (G-AX): it constructs the real post-patch
`sklearn.ensemble.IsolationForest`, fits with `warm_start=True` then enlarges
`n_estimators` and fits again, and asserts the exact structural predicates the
post-conditions encode — final size `== target_count`, the existing roster
preserved verbatim as the prefix (`estimators_[0]` survives), the tail freshly
built — and symmetrically that `warm_start=False` rebuilds the whole forest (no
member survives). Member identity is the real object `id(...)`. The check
imports only `numpy` and `sklearn` (the library under change), nothing
repo-private.

### Flag dependency
The behaviour is gated by `warm_start`. The gold patch's contribution is to
expose `warm_start` on `IsolationForest.__init__` (default `False`) and forward
it to `BaseBagging.__init__` (`iforest.py:176, 185-190`), so the previously
inaccessible warm-start path becomes reachable. Pre-patch, `IsolationForest`
never forwards `warm_start`, so `self.warm_start` keeps the inherited default
`False` (`bagging.py:200`) and every fit rebuilds — exactly the
`rebuild_all`-always behaviour of `model_prepatch.py`. The default
`warm_start=False` keeps all PASS_TO_PASS scenarios (which never opt in)
behaviourally identical, matching `effective_reuse(False, _) == False`.

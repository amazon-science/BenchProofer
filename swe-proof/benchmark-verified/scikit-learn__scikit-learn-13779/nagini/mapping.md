# mapping.md — scikit-learn__scikit-learn-13779

Binds every `model.py` symbol to its repository counterpart at
`base_commit = b34751b7ed02b2cfcc36037fb729d4360480a299`, states the type
abstraction, and gives the provenance of the axiomatized callee.

Repo file under change: `sklearn/ensemble/voting.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `check_weighting_support(roster)` | the weighted-fit pre-check loop inside `_BaseVoting.fit(self, X, y, sample_weight=None)` — `sklearn/ensemble/voting.py:79-83` (`if sample_weight is not None: for name, step in self.estimators: ... if not has_fit_parameter(step, 'sample_weight'): raise ValueError(...)`) | the modeled changed function (the per-estimator weighting pre-check) |
| `accepts_weighting(status)` *(axiom — A-consumed)* | `has_fit_parameter(step, 'sample_weight')` — `sklearn/utils/validation.py:784` (`return parameter in signature(estimator.fit).parameters`), called at `sklearn/ensemble/voting.py:81` | the unchanged capability probe the pre-check invokes per present estimator |
| `WeightingUnsupported` (exception) | the `ValueError('Underlying estimator \'%s\' does not support sample weights.' % name)` raised at `sklearn/ensemble/voting.py:82-83` | the rejection the pre-check surfaces when a present estimator does not accept weighting |
| `config_supports(roster)` | the conjunction of the per-present-estimator probe results over the loop (`every present step has has_fit_parameter(step,'sample_weight')`) | pure spec: whether the whole roster's present estimators all accept weighting |

Pre-patch source under change (`sklearn/ensemble/voting.py:79-83`):
```python
if sample_weight is not None:
    for name, step in self.estimators:
        if not has_fit_parameter(step, 'sample_weight'):
            raise ValueError('Underlying estimator \'%s\' does not'
                             ' support sample weights.' % name)
```
The gold patch inserts two lines before the probe call (line 80→):
```python
        for name, step in self.estimators:
            if step is None:
                continue
            if not has_fit_parameter(step, 'sample_weight'):
```
i.e. an absent estimator (`step is None`, set via `set_params(name=None)`) is
skipped before the probe is consulted.

The rest of `_BaseVoting.fit` (the `estimators`-empty check, the
`weights`-length check, `_validate_names`, the all-None check, the parallel
`clone`/`fit`) is UNCHANGED by the patch and not part of the pinned behaviour;
only the `sample_weight is not None` pre-check loop is modeled (skeleton-faithful
to the single changed hunk).

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| `self.estimators` — a list of `(name, step)` tuples | `roster: List[int]` — one status tag per entry | the `i`-th `(name, step)` ↦ `roster[i]`: `step is None` ↦ 0 (absent); `step is not None and has_fit_parameter(step,'sample_weight')` ↦ 1 (present-accepts); `step is not None and not has_fit_parameter(step,'sample_weight')` ↦ 2 (present-rejects). The `name` is irrelevant to the pinned control flow (it only formats the error message text, which the F2P tests do not observe) and is dropped. |
| `step is None` test | `roster[i] == 0` | the absent-estimator guard the patch adds; an absent entry must be skipped, never passed to the probe. |
| `has_fit_parameter(step, 'sample_weight')` (a `bool`) | `accepts_weighting(status)` (a `bool`) | the probe result for a present entry; `True` ↦ status 1, `False` ↦ status 2 (axiom §3). The probe is meaningful only for a present `step`; on `step is None` it raises (`None.fit` → AttributeError), so its model is undefined for status 0 — encoded as the axiom precondition `status in {1,2}`. |
| `raise ValueError('Underlying estimator ... does not support sample weights.')` | `raise WeightingUnsupported()` | a builtin exception in an `Exsures` crashes the Nagini translator (SPEC_GUIDE §2), so the rejection is a user-defined stand-in. The discriminating observable is the exception's identity (a weighting-unsupported rejection vs. the un-fixed `AttributeError` crash), which the stand-in preserves; the message string is unobserved by the tests. |

`str` indexing/iteration is banned in Nagini, so the roster is carried as a
`List[int]` of status tags; the specification is phrased over `PSeq[int]` via
`ToSeq`. There is no per-character observable here — the only observables of the
bug are (a) whether the pre-check crashes/errors when an absent estimator is
present, and (b) whether it rejects exactly when some present estimator does not
accept weighting — both functions of the per-entry status tags alone.

## 3. Callee provenance (kind-A — checked by G-AX / axiom_check.py)

### 3.1 `accepts_weighting` ↔ `has_fit_parameter(step, 'sample_weight')` (A-consumed)
**Callee:** `sklearn.utils.validation.has_fit_parameter(estimator, parameter)`
(`sklearn/utils/validation.py:784`), whose body is
```python
return parameter in signature(estimator.fit).parameters
```
The pre-check invokes it as `has_fit_parameter(step, 'sample_weight')`
(`sklearn/ensemble/voting.py:81`). The axiom encodes the WEAKEST facts the proof
needs:

- **precondition `status in {1, 2}`** — the probe inspects `estimator.fit`'s
  signature, so it is meaningful ONLY for a present estimator. Applied to an
  absent entry (`estimator is None`, status 0) it raises `AttributeError`
  (`'NoneType' object has no attribute 'fit'`) — exactly the crash in the issue.
  The precondition therefore admits only the present statuses; consulting the
  probe on an absent entry is out of contract. (This is the load-bearing fact:
  the pre-patch impl violates it by consulting the probe on every entry; the
  patched impl honours it by skipping absent entries.)
- **`Ensures(Result() == (status == 1))`** — a present estimator that declares
  `sample_weight` in its `fit` signature returns `True` (status 1); one that
  does not returns `False` (status 2). `has_fit_parameter` returns a plain
  `bool`; the weakest fact the proof needs is that this bool distinguishes the
  two present statuses.

**The axiom is the weakest sufficient contract**, not a model of
`inspect.signature`'s full behaviour. It is NEVER stronger than the real callee.

**Soundness check (G-AX):** `axiom_check.py` runs the REAL `has_fit_parameter`
in-container against real sklearn estimators whose `fit` signatures are known at
this commit:
- status 1 (declares `sample_weight`): `LogisticRegression`, `LinearRegression`,
  `RandomForestClassifier`, `RandomForestRegressor`, `DecisionTreeClassifier`,
  `DecisionTreeRegressor`, `SVC`, `GaussianNB` — every `fit` here is
  `def fit(self, X, y, sample_weight=None ...)` (verified in the worktree:
  `sklearn/linear_model/logistic.py:1466`, `sklearn/linear_model/base.py:438`,
  `sklearn/ensemble/forest.py:217`, `sklearn/tree/tree.py:776/1118`,
  `sklearn/svm/base.py:105`, `sklearn/naive_bayes.py:167`) → probe returns `True`.
- status 2 (no `sample_weight`): `KNeighborsClassifier` (`fit(self, X, y)`,
  `sklearn/neighbors/base.py:878`) and a hand-rolled estimator → probe returns
  `False`.
- status 0 (absent): `has_fit_parameter(None, 'sample_weight')` RAISES — the
  check asserts the raise, confirming the precondition `status in {1,2}` is a
  faithful restriction (the probe genuinely cannot be consulted on an absent
  entry), not an arbitrary one. This is the exact bug the fix avoids.
Plus 2000 fuzz over synthesized weight-accepting / weight-rejecting estimators.
Exit 0 iff every obligation holds.

**Flag/configuration dependency:** none. `has_fit_parameter` takes the single
parameter name `'sample_weight'`; the result is a function of the estimator's
`fit` signature alone, independent of any global configuration. The F2P test
`test_none_estimator_with_weights` fits a `VotingClassifier`/`VotingRegressor`
with one estimator set to `None` and `sample_weight=np.ones(...)`; the patched
pre-check must skip the `None` entry and consult only the present one
(`RandomForestClassifier`/`RandomForestRegressor`, status 1), returning normally.

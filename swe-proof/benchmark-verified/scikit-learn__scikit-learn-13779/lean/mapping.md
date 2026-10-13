# mapping.md — scikit-learn__scikit-learn-13779

## Instance
- repo: `scikit-learn/scikit-learn`
- base_commit: `b34751b7ed02b2cfcc36037fb729d4360480a299`
- modeled file: `sklearn/ensemble/voting.py` — the `sample_weight`-support
  validation loop inside `_BaseVoting.fit` (the changed region).
- F2P tests:
  `sklearn/ensemble/tests/test_voting.py::test_none_estimator_with_weights[X0-y0-voter0]`,
  `[X1-y1-voter1]`
- pinned G-CONF fuzz seed: **13779**

## What the fix does (issue + gold patch)
A voting ensemble's `fit`, when per-sample weights are supplied, first walks its
roster of `(name, estimator)` pairs and checks that each estimator's `fit`
accepts a `sample_weight` parameter; the first estimator that does not triggers a
`ValueError` naming it. An individual estimator slot may be set to `None`
(removed via `set_params(lr=None)`); such a slot has no `fit` method. Pre-patch
the loop called the support check unconditionally, so a `None` slot raised an
`AttributeError` ('NoneType' object has no attribute 'fit'). The gold patch adds
a guard that passes over a `None` slot before the support check:

```python
# voting.py:79-83  (_BaseVoting.fit)
if sample_weight is not None:
    for name, step in self.estimators:
        if step is None:          # <-- added
            continue              # <-- added
        if not has_fit_parameter(step, 'sample_weight'):
            raise ValueError('Underlying estimator \'%s\' does not'
                             ' support sample weights.' % name)
```

The discriminating input is a roster containing a `None` slot together with
supplied weights: POST-patch validation passes over it and succeeds; PRE-patch
validation reaches the support check on `None` and fails.

## Symbol binding
| Lean symbol | Python | provenance (file:line @ base) |
|---|---|---|
| `implementation_checkWeightSupport` | the `sample_weight`-support validation loop in `_BaseVoting.fit` | voting.py:79-83 |
| `estimators : List (String × Option Bool)` | `self.estimators` (a list of `(name, step)` pairs) under `sample_weight is not None` | voting.py:80 |
| `Option Bool` slot value | `step`: `None` ↔ `none`; a present estimator ↔ `some b` where `b = has_fit_parameter(step, 'sample_weight')` | voting.py:80-81 |
| `firstUnsupported` | the index of the first present estimator failing the support check (the one that raises) | voting.py:81-82 |
| `errMsg name` | `'Underlying estimator \'%s\' does not support sample weights.' % name` | voting.py:82-83 |
| `Except String Unit` result | validation outcome: `.ok ()` ↔ loop completes without raising; `.error msg` ↔ the `ValueError(msg)` raised | voting.py:81-83 |

## Lean ↔ Python type bijection (used by G-CONF)
- `self.estimators` is a Python list of `(str, estimator-or-None)` pairs. It is
  modeled by `List (String × Option Bool)`:
  - the pair's first component (`name`) ↔ a Lean `String`;
  - the pair's second component (`step`) is projected to `Option Bool`:
    `step is None` ↔ `none`; otherwise ↔ `some (has_fit_parameter(step,
    'sample_weight'))`. The estimator object's only property consumed by the
    modeled region is the boolean `has_fit_parameter(step, 'sample_weight')`, so
    the projection to `Option Bool` is lossless for this region.
- The validation result is `Except String Unit`: `.ok ()` ↔ the loop finishes
  with no exception (`fit` proceeds); `.error msg` ↔ a raised `ValueError(msg)`.
  A `None` slot raising `AttributeError` pre-patch is modeled as a non-`.ok`
  outcome (the exception *type* is not pinned, only that validation does not pass
  cleanly — see refinement.md).

## Callee provenance + flag deps
- `has_fit_parameter(estimator, 'sample_weight')`
  (`sklearn/utils/validation.py:784-808`) is an UNCHANGED callee. The patch does
  not change it; it is invoked identically on every present estimator. Its result
  is a pure boolean and is treated as a **free boolean input** to the model (the
  fuzzer ranges over both values per present slot), NOT as a deep-modeled value
  to validate against the real callee. Hence there is **no consumed axiom and no
  A-reference**: `axiom_check.py` (G-AX) is a skip stub.
- Flag dependency: the whole loop runs only under `sample_weight is not None`
  (voting.py:79). The model is exactly that guarded loop; the no-weights path is
  out of scope (it never touches the support check).

## G-CONF fuzz seed
Seed **13779**. G-CONF runs (`conf_skip=false`): the impl region is real R/I
control flow (ordered walk, `None`-skip, first-failure error) with no A-tagged
op, so it is differential-tested against the post-patch loop over fuzzed rosters.

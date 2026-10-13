# refinement.md — scikit-learn__scikit-learn-10908

Operation correspondence between `implementation_getFeatureNames`
(Solution.lean) and the gold `patch.diff`. Tags: **R** (type refinement),
**A-consumed** (proof uses an axiom's property), **A-reference** (deep model
validated == real callee by G-AX), **I** (identical concrete op).

## Modeled function: `get_feature_names`

The gold patch inserts, before the availability check, a step that establishes a
vocabulary from the constructor-supplied parameter when none is already present:

```python
def get_feature_names(self):
    if not hasattr(self, 'vocabulary_'):
        self._validate_vocabulary()
    self._check_vocabulary()
    return [t for t, i in sorted(six.iteritems(self.vocabulary_), key=itemgetter(1))]
```

| # | `implementation_getFeatureNames` op | `patch.diff` counterpart | tag | justification |
|---|---|---|---|---|
| 1 | `match st.learned with \| some v => voc := v` | `if not hasattr(self, 'vocabulary_'): …` taking the **false** branch (attribute already present) — `vocabulary_` is used as-is | R | `hasattr(self, 'vocabulary_')` ↔ `st.learned.isSome`; `some v` carries the dict's (term,index) pairs (mapping.md type bijection). |
| 2 | `\| none => match st.param with …` | `if not hasattr(...): self._validate_vocabulary()` taking the **true** branch — establish a vocabulary | R | the absence of an available vocabulary (`learned = none`) is the condition under which the patch runs `_validate_vocabulary`. |
| 3 | `\| none => return Except.error VErr.notFitted` | `_validate_vocabulary()` sets no `vocabulary_` when `self.vocabulary is None`, so the subsequent `_check_vocabulary()` raises `NotFittedError` | R / A-reference | when no constructor vocabulary was supplied, validation leaves the object unfitted and `_check_vocabulary` rejects it. `_validate_vocabulary`'s list branch is modeled deeply; the `None`-parameter case yields `notFitted` via `_check_vocabulary`. |
| 4 | `\| some p => match validateList p with …` | `self._validate_vocabulary()` on a list vocabulary | A-reference | `validateList` deeply models `_validate_vocabulary`'s list branch (empty→`empty`, repeated term→`dup`, else term↦position map). G-AX validates `validateList` == the real `_validate_vocabulary` over fuzzed lists. |
| 5 | `\| Except.error e => return Except.error e` | `_validate_vocabulary` raising `ValueError` (empty / duplicate) | A-reference | the validation errors surface unchanged as the function's error. Validated by G-AX. |
| 6 | `\| Except.ok v => voc := v` | `_validate_vocabulary` setting `self.vocabulary_` | A-reference | the validated term↦index mapping becomes the working vocabulary. |
| 7 | `if voc.isEmpty then return Except.error VErr.empty` | `self._check_vocabulary()` → `if len(self.vocabulary_) == 0: raise ValueError("Vocabulary is empty")` | I / A-reference | the empty-vocabulary guard `_check_vocabulary` performs after `vocabulary_` exists. (A supplied list cannot be empty here — `validateList` already rejected empty — so this fires only for an empty `learned` dict; both modeled.) |
| 8 | `return Except.ok (featureNames voc)` | `return [t for t, i in sorted(six.iteritems(self.vocabulary_), key=itemgetter(1))]` | A-reference | `featureNames` deeply models the index-ordered name extraction (terms by increasing index). G-AX validates it == the real comprehension. |

No op in `implementation_getFeatureNames` is changed-inexpressible: the inserted
validation step and the unchanged extraction are both modeled deeply. There is
**no consumed axiom** and **no opaque callee** (the `axioms` region is empty); the
proof discharges by case analysis on `st.learned` / `st.param` / `validateList`.

## Independently-observable fixed behavior (G-DIFF)

The single discriminating behavior the patch fixes: with `learned = none` and
`param = some p` (a valid supplied vocabulary), the result must be
`Except.ok (featureNames v)` rather than `Except.error VErr.notFitted`. The
pre-patch impl (`Solution_prepatch.lean`) returns `notFitted` in that state, so
its `correct_getFeatureNames` is unclosable on the `param = some …` clause — one
failing prepatch for the one fixed behavior.

## Modeling decisions (faithfulness notes)

- **Value-only model.** `_validate_vocabulary()` also mutates the object
  (`self.vocabulary_`, `self.fixed_vocabulary_`). The modeled observable is the
  function's *return* (the index-ordered names, or the raised error) — the
  F2P-distinguishing behavior is precisely the return (`NotFittedError` vs a name
  list). The mutation is a means to that return, captured by the `validateList`
  A-reference; it is not separately modeled (as in the value-only exemplars).
- **No invariant on `learned`.** The real code does not re-validate an
  already-available `vocabulary_`; `get_feature_names` sorts its items by index
  unconditionally. The `learned = some v` branch therefore carries no `NoDup` /
  contiguous-index precondition — modeling one would be *less* faithful. The
  theorem is `∀ st` (no precondition binder), matching the total real function.
- **Helpers shared by spec and impl are G-AX-grounded.** `validateList` /
  `featureNames` appear in both `problem_spec` and `implementation`; they are
  A-references validated == the real callees by G-AX (axiom_check.py), so pinning
  the result to them is grounded in the real computation, not an ungrounded
  oracle (SPEC_GUIDE §0.8).

## Out-of-scope gold-patch content

The `test_patch` also renames a test (`…repeated_indeces` → `…repeated_indices`)
and adds `fixed_vocabulary_` assertions; tests are not modeled (they are the
harness's concern, not the spec's). `patch.diff` is the gold source patch
verbatim.

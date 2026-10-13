# refinement.md — django__django-15277

Maps every operation in `implementation_buildFieldValidators` to its `patch.diff`
counterpart. Tags: **R** (type refinement), **A-consumed** (proof uses an axiom's
property), **A-reference** (deep model validated == real callee by G-AX), **I**
(identical concrete op). Every step is R, A, or I.

## Modeled function: `buildFieldValidators` (`CharField.__init__`)

Post-patch repo code (`patch.diff`):
```python
def __init__(self, *args, db_collation=None, **kwargs):
    super().__init__(*args, **kwargs)
    self.db_collation = db_collation
    if self.max_length is not None:
        self.validators.append(validators.MaxLengthValidator(self.max_length))
```

Lean impl (`implementation_buildFieldValidators`):
```lean
def implementation_buildFieldValidators
    (maxLength : Option Int) (base : List Validator) : List Validator := Id.run do
  let mut validators := base
  if maxLength.isSome then
    validators := validators ++ [Validator.lengthBound maxLength]
  return validators
```

| # | Lean op | patch.diff / real-code counterpart | tag | justification |
|---|---|---|---|---|
| 1 | `maxLength : Option Int` | `self.max_length` (set in `Field.__init__`; defaults to `None`) | **R** | the declared maximum length. `None` ↔ `none`, a positive int `n` ↔ `some n` (mapping.md bijection). Only the `is None` / `is not None` distinction is observable to the modeled behavior. |
| 2 | `base : List Validator` | `self.validators` immediately BEFORE the append — `[*default_validators, *_validators]` (`Field.validators` cached_property) | **R** | the pre-existing validators. Each ↔ one element; `Validator.basic tag` abstracts validators whose internals are irrelevant; `Validator.lengthBound` is reserved for the one this function attaches. The list is ordered and the append goes at the end (`list.append`), which the model preserves. |
| 3 | `let mut validators := base` | the implicit `self.validators` being mutated | **I** | the working list starts as the pre-existing validators. |
| 4 | `if maxLength.isSome then` | `if self.max_length is not None:` | **I** | the guard the patch ADDS. `Option.isSome` ↔ `is not None`. This is the fixed control-flow edit. |
| 5 | `validators := validators ++ [Validator.lengthBound maxLength]` | `self.validators.append(validators.MaxLengthValidator(self.max_length))` | **I** (deep model of the gated op) | **the gated operation.** Appends a single length-bound validator carrying the declared length as its limit. `MaxLengthValidator(self.max_length)` ↔ `Validator.lengthBound maxLength`: the validator's `limit_value` IS `self.max_length`. Under the `isSome` guard `maxLength = some n`, so the appended value is `Validator.lengthBound (some n)`. The construction is modeled deeply (presence + carried bound), NOT axiomatized — it is the operation the fix governs (§3, §0.7). |
| 6 | `return validators` | the post-state of `self.validators` | **I** | the function's observable effect is the resulting validator list. |

All impl-region ops are **R/I** — there is NO A-tagged (axiom) content, so the
impl is NOT all-A-tagged: `conf_skip = false`, and `conformance_check.py`
mechanically differential-tests the R/I shadow against an in-process replica of
the patched `__init__` list-construction behavior.

## Soundness check (verify ⟹ correct)

- `problem_spec_buildFieldValidators maxLength base result := result = base ++
  (match maxLength with | none => [] | some n => [Validator.lengthBound (some
  n)])` pins the result EXACTLY (full list equality to an input-grounded
  expression) — directive 5 (frame): the output is fully determined by the
  optional length and the incoming validator list. No output component is left
  unconstrained (the prefix is pinned to `base`, the suffix to the conditional
  append); no ungrounded oracle (directive 8) — dischargeable only by actually
  constructing the list.
- The prepatch impl (`validators := base ++ [Validator.lengthBound maxLength]`,
  unconditional) reproduces the pre-patch unconditional `append`. It violates the
  spec on the discriminating clause `maxLength = none`: it returns `base ++
  [Validator.lengthBound none]` (a length-bound validator carrying no usable
  bound — the very `MaxLengthValidator(None)` whose `.clean()` raises) but the
  spec requires `base` unchanged. Its carried gold proof cannot close (G-DIFF /
  G-PANEL); the failing case is the `none` branch.
- This discriminating case is precisely what the FAIL_TO_PASS test
  (`test_output_field_does_not_create_broken_validators`) exercises: a
  `Value('test')._resolve_output_field()` produces a string field with NO
  declared maximum length (`max_length is None`), then `field.clean(...)` is
  called; pre-patch, the unconditionally-attached `MaxLengthValidator(None)`
  raises `TypeError` during clean, while post-patch no such validator is present.
- G-CONF confirms the R/I shadow == the in-process replica of the patched
  `__init__` list construction over hand-picked edge cases (including
  `max_length = None`) plus ≥1e5 fuzzed (max_length, base-list) inputs.

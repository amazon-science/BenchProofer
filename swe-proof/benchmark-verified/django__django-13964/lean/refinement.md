# refinement.md — django__django-13964

Maps every operation in `implementation_foreignKeyValueOnSave` to its
`patch.diff` counterpart. Tags: **R** (type refinement), **A-consumed** (proof
uses an axiom's property), **A-reference** (deep model validated == real callee
by G-AX), **I** (identical concrete op). Every step is R, A, or I.

## Modeled function: `foreignKeyValueOnSave` (the FK key-value adoption decision in `_prepare_related_fields_for_save`)

Post-patch repo code (`patch.diff`), inside the per-field loop of
`Model._prepare_related_fields_for_save` (`django/db/models/base.py`):

```python
if obj.pk is None:
    ...
    raise ValueError(...)
elif getattr(self, field.attname) in field.empty_values:   # gold change
    # Use pk from related object if it has been saved after an assignment.
    setattr(self, field.attname, obj.pk)
```

Pre-patch the `elif` guard is `getattr(self, field.attname) is None`.

Lean impl (`implementation_foreignKeyValueOnSave`): starting from the stored key
value `fkValue`, if it is empty (`fkValueIsEmpty`), adopt the related object's
primary key `objPk`; otherwise keep `fkValue`.

| # | Lean op | patch.diff / real-code counterpart | tag | justification |
|---|---|---|---|---|
| 1 | `fkValue : Option String` | the stored FK key value `getattr(self, field.attname)` (line 936) | **R** | a string scalar that may be `None` ↔ `Option String` (mapping.md bijection). |
| 2 | `objPk : String` | `obj.pk`, the related object's primary key (line 938) | **R** | a present primary key (the `obj.pk is None` branch returned first) ↔ a present `String`. |
| 3 | `let mut result := fkValue` | the stored key value before the branch | **I** | the key value is unchanged unless the adoption branch fires. |
| 4 | `if fkValueIsEmpty result then` | `elif getattr(self, field.attname) in field.empty_values:` (line 936, **the fix**) | **I** (the changed guard, deeply modeled) | **the fixed behavior.** Post-patch the guard treats the stored key value as eligible for adoption when it is in `field.empty_values` = `[None, '', [], (), {}]`; for a scalar FK key value the reachable members are `None` and `''`, so the guard is `value is None or value == ''` = `fkValueIsEmpty`. The prepatch impl uses `result.isNone` (`value is None` only), matching the pre-patch `is None` guard. |
| 5 | `result := some objPk` | `setattr(self, field.attname, obj.pk)` (line 939) | **I** | adopt the related object's primary key as the stored key value. |
| 6 | `return result` | the stored key value `getattr(self, field.attname)` after the branch | **R** | result modeled as the single observable scalar the fix changes (mapping.md result-type note). |

All impl-region ops are **R/I** — there is NO A-tagged (axiom) content, so the
impl is NOT all-A-tagged: `conf_skip = false`, and `conformance_check.py`
mechanically differential-tests the R/I shadow against an in-process replica of
the post-patch adoption decision (using the real `field.empty_values` membership
semantics).

## Soundness check (verify ⟹ correct)

- `problem_spec_foreignKeyValueOnSave` pins the result to
  `if fkValueIsEmpty fkValue then some objPk else fkValue` — grounded entirely in
  the two inputs (directive 5 frame: both `fkValue` and `objPk` appear and the
  result is fully determined; directive 8: grounded in the actual inputs, not an
  ungrounded oracle). A verifying impl must adopt `objPk` on EVERY empty stored
  value — including the empty string `some ""`, not just `none`.
- The discriminating behavior: on `fkValue = some ""` (a non-numeric/CharField PK
  scalar starting empty), the spec demands `result = some objPk`. The prepatch
  impl returns `some ""` (it only adopts when `result.isNone`), so the carried
  gold proof, after `simp only [Id.run, bind, pure]; split <;> rfl`, is left with
  the unprovable goal `some "" = some objPk` (G-DIFF/G-PANEL).
- This is exactly what `test_save_fk_after_parent_with_non_numeric_pk_set_on_child`
  exercises: a `ChildStringPrimaryKeyParent` whose parent's `name` (the CharField
  PK) is set to `'jeff'` after assignment; post-save `child.parent_id` must equal
  `'jeff'`, but pre-patch it stays `''` because the stored key value is the empty
  string (not `None`) and the `is None` guard skips the adoption.
- G-CONF confirms the R/I shadow == an in-process replica of the post-patch
  adoption decision over the full grid of stored-value forms (`None` / `''` /
  non-empty string) crossed with various `objPk` values, plus ≥1e5 fuzzed points
  (0 disagreements).

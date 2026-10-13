# refinement.md — django__django-16950

Maps every operation in `implementation_clearParentKeyDefault` to its
`patch.diff` counterpart. Tags: **R** (type refinement), **A-consumed** (proof
uses an axiom's property), **A-reference** (deep model validated == real callee
by G-AX), **I** (identical concrete op). Every step is R, A, or I.

## Modeled function: `clearParentKeyDefault` (`BaseInlineFormSet.add_fields`)

Post-patch repo code (`patch.diff`), the modeled block:
```python
def add_fields(self, form, index):
    ...
    # If we're adding a new object, ignore a parent's auto-generated key
    # as it will be regenerated on the save request.
    if self.instance._state.adding:
        if kwargs.get("to_field") is not None:
            to_field = self.instance._meta.get_field(kwargs["to_field"])
        else:
            to_field = self.instance._meta.pk
        if to_field.has_default() and (
            # Don't ignore a parent's auto-generated key if it's not the
            # parent model's pk and form data is provided.
            to_field.attname == self.fk.remote_field.model._meta.pk.name
            or not form.data
        ):
            setattr(self.instance, to_field.attname, None)

    form.fields[name] = InlineForeignKeyField(self.instance, **kwargs)
```

Lean impl (`implementation_clearParentKeyDefault`):
```lean
def implementation_clearParentKeyDefault {V : Type}
    (adding hasDefault isParentPk hasFormData : Bool) (current : V) :
    Option V := Id.run do
  let mut keyAttr : Option V := some current
  if adding then
    if hasDefault && (isParentPk || !hasFormData) then
      keyAttr := none
  return keyAttr
```

| # | Lean op | patch.diff / real-code counterpart | tag | justification |
|---|---|---|---|---|
| 1 | `keyAttr : Option V := some current` | the initial value of `self.instance.<to_field.attname>` (its existing value before the block) | **R** | the attribute's value ↔ `Option V`; `some current` = "has its existing value", `none` = "cleared to None". Only this one attribute is touched, names are distinct ⇒ lossless (mapping.md). |
| 2 | `if adding then …` | `if self.instance._state.adding:` | **I** | the outer guard. `adding : Bool` ↔ `self.instance._state.adding`. Unchanged by the patch; the entire reset block is inside it. |
| 3 | `if hasDefault && (isParentPk || !hasFormData) then keyAttr := none` | `if to_field.has_default() and (to_field.attname == self.fk.remote_field.model._meta.pk.name or not form.data): setattr(self.instance, to_field.attname, None)` | **I** (deep model of the changed op) | **the fixed operation.** `hasDefault` ↔ `to_field.has_default()`; `isParentPk` ↔ `to_field.attname == self.fk.remote_field.model._meta.pk.name`; `!hasFormData` ↔ `not form.data`. The added `(… or not form.data)` factor is reproduced exactly. The PRE-FIX guard had only `to_field.has_default()`. The `to_field` resolution (`get_field(kwargs["to_field"])` vs `_meta.pk`) is unchanged context folded into the `hasDefault`/`isParentPk` observables (mapping.md). |
| 4 | `return keyAttr` | the (mutated) value of `self.instance.<to_field.attname>` after the block; consumed by the subsequent `InlineForeignKeyField(self.instance, **kwargs)` (unchanged) | **R** | the resulting attribute value ↔ `Option V`. The trailing `form.fields[name] = InlineForeignKeyField(...)` is unchanged and reads the attribute via `self.instance`; its effect is fully determined by `keyAttr` (none/some), so it carries no additional modeled state. |

All impl-region ops are **R/I** — there is NO A-tagged (axiom) content, so the
impl is NOT all-A-tagged: `conf_skip = false`, and `conformance_check.py`
mechanically differential-tests the R/I shadow against an in-process replica of
the patched `add_fields` reset decision.

## Soundness check (verify ⟹ correct)

- `problem_spec_clearParentKeyDefault adding hasDefault isParentPk hasFormData
  current result := result = (if shouldReset … then none else some current)`
  pins the result EXACTLY (full equality to an input-grounded expression) —
  directive 5 (frame): when the reset does NOT fire, the result equals
  `some current`, the input value carried through unchanged; when it fires, the
  result is `none`. No output component is left unconstrained; no ungrounded
  oracle (directive 8) — the postcondition is dischargeable only by actually
  evaluating `shouldReset` over the inputs and either clearing or retaining the
  carried value. `shouldReset = adding && hasDefault && (isParentPk ||
  !hasFormData)` folds in the unchanged outer `adding`/`hasDefault` factors and
  the post-fix `(isParentPk || !hasFormData)` factor.
- The prepatch impl reproduces the PRE-FIX guard, which lacks the second factor:
  it clears the attribute on `adding && hasDefault` alone. It violates the spec
  on the discriminating clause
  `adding = true, hasDefault = true, isParentPk = false, hasFormData = true` (a
  parent being added, an alternate key with a default, and a form that carries
  submitted data): the spec requires the attribute be RETAINED
  (`shouldReset = false`, because `isParentPk = false` and `hasFormData = true`
  ⇒ `isParentPk || !hasFormData = false`), but the prepatch clears it to `none`.
  Its carried-over proof cannot close (G-DIFF/G-PANEL); the failing case is
  exactly that branch.
- This discriminating case is precisely the FAIL_TO_PASS scenario added by the
  test patch
  (`test_inlineformset_factory_nulls_default_pks_alternate_key_relation_data`):
  with an alternate UUID key (`ParentWithUUIDAlternateKey`/`ChildRelatedViaAK`),
  a default on that key, and submitted form data, the parent's `uuid` must SURVIVE
  (post-fix, `formset.instance.uuid is not None` and the child's `parent_id`
  equals it) rather than be nulled (pre-fix bug). The companion PASS_TO_PASS
  tests confirm that when the key IS the parent pk, or when no form data is
  provided, the attribute is still cleared — matching the other three input
  combinations of the second factor.
- G-CONF confirms the R/I shadow == the in-process replica of the patched
  `add_fields` reset decision over the full exhaustive enumeration of the 16
  boolean combinations (incl. the alternate-key-with-data fix case) plus ≥1e5
  fuzzed inputs.

# refinement.md — django__django-11740

Maps every operation in `implementation_generateAlteredFields` to its
`patch.diff` counterpart. Tags: **R** (type refinement), **A-consumed** (proof
uses an axiom's property), **A-reference** (deep model validated == real callee
by G-AX), **I** (identical concrete op). Every step is R, A, or I.

## Modeled function: `generateAlteredFields` (`MigrationAutodetector.generate_altered_fields`)

Post-patch repo code (`patch.diff`, `autodetector.py`, the touched portions of
the per-field loop):
```python
for app_label, model_name, field_name in sorted(self.old_field_keys & self.new_field_keys):
    ...
    new_field = self.new_apps.get_model(app_label, model_name)._meta.get_field(field_name)
    dependencies = []                                              # added
    if hasattr(new_field, "remote_field") and getattr(new_field.remote_field, "model", None):
        ...   # rename handling (unchanged)
        dependencies.extend(self._get_dependencies_for_foreign_key(new_field))   # added
    if hasattr(new_field, "remote_field") and getattr(new_field.remote_field, "through", None):
        ...   # rename handling (unchanged)
    ...
    if old_field_dec != new_field_dec:
        both_m2m = ...; neither_m2m = ...
        if both_m2m or neither_m2m:
            ...
            self.add_operation(
                app_label,
                operations.AlterField(model_name=..., name=..., field=field,
                                      preserve_default=preserve_default),
                dependencies=dependencies,                          # added
            )
        else:
            ...
```

Lean impl (`implementation_generateAlteredFields`):
```lean
def implementation_generateAlteredFields (fields : List AlteredField) : List AlterFieldOp := Id.run do
  let mut result := []
  for f in fields do
    let mut dependencies := []
    if f.isRelation then
      dependencies := dependencies ++ getDependenciesForForeignKey f.fk
    result := result ++ [({ field := f, dependencies := dependencies } : AlterFieldOp)]
  return result
```

The result is a list of emitted operations (`AlterFieldOp`), each pairing the
field it alters with the dependency list it carries — modeling the
`add_operation(AlterField(...), dependencies=dependencies)` call itself, not just
the intermediate dependency list. This pins (directive 5, frame) that each
operation alters precisely its own field AND carries precisely its own
dependencies.

| # | Lean op | patch.diff / real-code counterpart | tag | justification |
|---|---|---|---|---|
| 1 | `fields : List AlteredField` (input carrier) | the per-key `new_field` sequence over `sorted(self.old_field_keys & self.new_field_keys)` that reaches the `AlterField` branch | **R** | each element ↔ one altered field's touched aspects: `isRelation` ↔ `hasattr(new_field,"remote_field") and getattr(new_field.remote_field,"model",None)`; `fk` ↔ the FK reference-target data read by `_get_dependencies_for_foreign_key`. See mapping.md. |
| 2 | `for f in fields do` | the `for app_label, model_name, field_name in sorted(...)` loop, one iteration per altered field | **R** | the loop iterates altered fields in order; the result list element `i` ↔ the `dependencies` passed to `add_operation` for altered field `i`. |
| 3 | `let mut dependencies := []` | `dependencies = []` (added line `autodetector.py:912`+) | **I** | per-iteration initialization to the empty constraint list. |
| 4 | `if f.isRelation then dependencies := dependencies ++ getDependenciesForForeignKey f.fk` | `if hasattr(new_field,"remote_field") and getattr(new_field.remote_field,"model",None): ... dependencies.extend(self._get_dependencies_for_foreign_key(new_field))` (added line `:940`+) | **A-reference** (deep model of the changed-behavior callee) | **the fix.** The relation guard ↔ `f.isRelation`; `_get_dependencies_for_foreign_key(new_field)` ↔ `getDependenciesForForeignKey f.fk`, modeled deeply (swappable-setting branch, remote app/object name, optional non-auto-created through dep) and validated == the real callee by G-AX. `.extend(...)` onto the `[]` from step 3 ↔ `[] ++ getDependenciesForForeignKey f.fk`. |
| 5 | `result := result ++ [{ field := f, dependencies := dependencies }]` | `self.add_operation(app_label, operations.AlterField(...), dependencies=dependencies)` | **R** | emitting the `AlterField` operation for field `f` carrying the assembled `dependencies` (`add_operation` sets `operation._auto_deps = dependencies or []`, `:439`). The modeled `AlterFieldOp.field` ↔ the field the operation alters (its identity); `AlterFieldOp.dependencies` ↔ `operation._auto_deps`. The observable change is precisely which dependency list each emitted operation carries; the operation's other attributes (model_name/name/field/preserve_default) are unchanged by the patch and not modeled (they are pinned by the unchanged code). |
| 6 | `return result` | end of the loop / the resulting sequence of emitted `AlterField` operations | **R** | the result ↔ the emitted operations, in emission order, each pairing its altered field with its attached dependency list. |
| 7 | `getDependenciesForForeignKey` (pure helper) | `_get_dependencies_for_foreign_key` | **A-reference** | base dep `("__setting__", swappable_setting, None, True)` when swappable, else `(remote app_label, remote object_name, None, True)`; plus the through dep `(through app_label, through object_name, None, True)` when `through and not through._meta.auto_created`. G-AX validates it == the real callee. |

There is NO consumed axiom (no `axiom <callee>_prop`): the changed-behavior
callee `_get_dependencies_for_foreign_key` is modeled DEEPLY (A-reference,
G-AX-validated), and the loop/assembly is structural over the field list
(R/I). `conf_skip = false`; `conformance_check.py` differential-tests the R/I
shadow (with `getDependenciesForForeignKey` left as the deep model, which G-AX
independently pins to the real callee) against an in-process replica of the
post-patch loop behavior.

## Soundness check (verify ⟹ correct)

- `problem_spec_generateAlteredFields` pins the result EXACTLY, element-wise, to
  the input field list (`result = fields.map (fun f => { field := f,
  dependencies := if f.isRelation then getDependenciesForForeignKey f.fk else
  [] })`) — directive 5 (frame): every emitted operation is determined by its
  input field, BOTH which field it alters (`field := f`) AND the dependency list
  it carries; no component is left unconstrained. The non-relation case is pinned
  to `[]` dependencies, the relation case to the full FK-induced dependency list.
  Modeling the emitted operation (not just the bare dependency list) closes the
  hole where a wrong impl computes the right dependency lists but drops them /
  attaches them to the wrong field when constructing operations. No ungrounded
  oracle (directive 8): the RHS is computed structurally from the input, not
  echoed from an answer-key.
- The prepatch impl emits `[]` for EVERY altered field regardless of
  `isRelation` (modeling the base_commit `add_operation` call that passes no
  `dependencies`). It violates the spec on the discriminating clause `isRelation
  = true`: the spec requires the FK-induced dependency list, the prepatch
  produces `[]`. Its carried `correct_*` cannot close (G-DIFF/G-PANEL).
- This discriminating case is exactly the FAIL_TO_PASS assertion
  (`test_alter_field_to_fk_dependency_other_app`): a field in `otherapp` is
  altered from a plain integer field to a `ForeignKey` to `testapp.Author`; the
  test asserts the emitted `AlterField` migration in `otherapp` depends on
  `[('testapp', '__first__')]` (the FK-induced dependency). Pre-fix it carried no
  dependency; post-fix `_get_dependencies_for_foreign_key` supplies it.
- G-AX validates `getDependenciesForForeignKey` == the real
  `_get_dependencies_for_foreign_key` over constructed FK/M2M/swappable fields.
  G-CONF confirms the R/I shadow == an in-process replica of the post-patch loop
  over edge cases (relation vs non-relation, swappable, through-with/without
  auto_created, mixed sequences) plus ≥1e5 fuzzed field sequences.

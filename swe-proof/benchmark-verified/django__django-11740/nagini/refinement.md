# refinement.md — django__django-11740

The operation-by-operation correspondence between `model.py`'s implementation
(the `altered_field_dependencies` impl region) and `patch.diff` (the gold
patch). Each step is tagged **R** (type refinement), **A** (axiomatized callee —
split into **A-consumed**, where the proof uses the axiom's `Ensures`, and
**A-reference**, where a deep model is validated == the real callee by
axiom_check.py / G-AX), or **I** (identical concrete operation). The claim:
*any implementation that verifies against this frozen spec, refined per the map
below, is behaviourally equal to the gold patch on the tested inputs, so it
resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## The change

Gold hunks (`django/db/migrations/autodetector.py`, `generate_altered_fields`):
```
  old_field = ...
  new_field = ...
+ dependencies = []
  # Implement any model renames on relations ...
  if hasattr(new_field, "remote_field") and getattr(new_field.remote_field, "model", None):
      ... (rename / to_field / from_field handling, unchanged) ...
+     dependencies.extend(self._get_dependencies_for_foreign_key(new_field))
  ...
  self.add_operation(
      app_label,
      operations.AlterField(
          model_name=model_name,
          name=field_name,
          field=field,
          preserve_default=preserve_default,
-     )
+     ),
+     dependencies=dependencies,
  )
```

The change seeds an empty `dependencies` list, extends it with the new field's
foreign-key dependencies when the new field is relational, and passes that list
to the emitted `AlterField` operation. Previously the operation was created with
no dependencies (so `add_operation` recorded `_auto_deps = []`), and altering a
plain field into one that references another model declared no dependency on
that model — the migration could not be ordered (`ValueError: Related model ...
cannot be resolved`).

## Operation correspondence

| # | model.py impl op (`altered_field_dependencies`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| 1 | parameter `new_field: FieldDef` (only `is_relation`) | the `new_field` field object | R | `FieldDef.is_relation` ↔ `hasattr(new_field, "remote_field") and getattr(new_field.remote_field, "model", None)` (mapping.md §2); no other attribute of `new_field` is observed by the dependency value. |
| 2 | `dependencies = PSeq()` | `dependencies = []` (added line) | I + R | empty initialisation; `[]` (list of dep tuples) ↔ empty `PSeq[int]` (mapping.md §2). |
| 3 | `if new_field.is_relation:` | `if hasattr(new_field, "remote_field") and getattr(new_field.remote_field, "model", None):` (the existing relation guard the patch extends) | R | the relation test ↔ `is_relation` (mapping.md §2). This is the guard under which the new `dependencies.extend(...)` line sits. |
| 4 | `dependencies = dependencies + fk_dependencies(new_field)` | `dependencies.extend(self._get_dependencies_for_foreign_key(new_field))` (the added line) | A-consumed + R | `fk_dependencies` is the weakest contract on the unchanged helper `_get_dependencies_for_foreign_key` the proof needs: for a relational field it returns a NON-EMPTY dependency list (mapping.md §3.1). `list.extend(callee)` from an empty list ↔ `PSeq + callee` (R). The proof consumes the axiom's `Ensures(len(Result()) > 0)` to discharge the relational postcondition. G-AX confirms the real helper meets it. |
| 5 | `return dependencies` (the value the operation is created with) | `dependencies` flows into `self.add_operation(app_label, operations.AlterField(...), dependencies=dependencies)` — `add_operation` stores it as `operation._auto_deps` (autodetector.py:439) | R | the operation's attached dependency list ↔ `Result()` (mapping.md §2). `add_operation`/`AlterField(...)` are unchanged plumbing that store the list verbatim; the modeled observable is exactly that stored list, which the F2P test reads back as `migration.dependencies`. |

## The discriminating clause (G-DIFF)

The behavioural delta is steps 2+4+5: a relational new field must yield a
non-empty dependency list. The spec senses it through the postcondition

```
Implies(new_field.is_relation,
        Result() == fk_dependencies(new_field) and len(Result()) > 0)
```

`model_prepatch.py` (byte-identical spec) reproduces the pre-patch behaviour —
the operation is created with no dependencies, i.e. the dependency list is
unconditionally empty (`dependencies = PSeq()`, never extended). It therefore
**fails** the relational postcondition (`len(Result()) > 0` is violated when
`new_field.is_relation`). This is exactly the F2P observation
`test_alter_field_to_fk_dependency_other_app`: after altering a plain
`IntegerField` into a `ForeignKey`, the migration's dependencies must equal
`[('testapp', '__first__')]` (a non-empty dependency on the referenced app),
which the pre-patch produced as the empty set.

The non-relational case (`Implies(not new_field.is_relation, len(Result()) == 0)`)
is the same in both: a non-relational alter carries no dependency (the P2P
altered-field tests, e.g. `test_alter_field_to_not_null_*`, that assert no extra
dependency). It pins the spec so a wrong impl cannot satisfy the relational
clause by emitting dependencies unconditionally.

## No kind-3 (unexpressible-changed-op) steps

Every step above is R, A-consumed, or I. The operation that genuinely *changed*
— seeding `dependencies = []`, extending it with the relational dependencies
under the relation guard, and passing it to the operation — is modeled
**deeply** in the impl/spec (steps 2-5: the control flow and the relation-keyed
emptiness/non-emptiness of the dependency list), NOT hidden behind an axiom. The
one consumed axiom (`fk_dependencies`) covers only the **unchanged** helper
`_get_dependencies_for_foreign_key` the new line calls; there is no A-reference
and no dead axiom.

## verify(model) ⇒ resolved

`altered_field_dependencies` verifies only if the dependency list it returns is
NON-EMPTY (and equals the field's relational dependencies) when the new field is
relational, and EMPTY when it is not. By R (`is_relation` ↔ the relation guard;
empty list ↔ empty `PSeq`; `list.extend` ↔ `+`; the operation's stored
`_auto_deps` ↔ `Result()`) and the A-consumed axiom (G-AX: the real
`_get_dependencies_for_foreign_key` returns a non-empty list for any relational
field), the verified function equals the gold patch on the tested inputs —
including the F2P `test_alter_field_to_fk_dependency_other_app` (non-empty
dependency on the referenced app) and the P2P altered-field tests (no spurious
dependency for non-relational alters). The gold patch resolves (G-RESOLVE). The
trust points are exactly the two of PLAN §1.1: axiom soundness (G-AX) and
refinement fidelity (this document, G-EQ).

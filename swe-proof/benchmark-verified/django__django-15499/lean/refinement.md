# refinement.md — django__django-15499

Maps every operation in `implementation_optimizeCreateThenAlterManagers` to its
`patch.diff` counterpart — the new `elif` arm added to `CreateModel.reduce`
(`django/db/migrations/operations/models.py`). Tags: **R** type-refinement,
**A-consumed** proof uses a callee axiom, **A-reference** deep-modeled changed op
validated == real callee, **I** identical concrete op.

## Patch (added arm)
```python
elif (
    isinstance(operation, AlterModelManagers)
    and self.name_lower == operation.name_lower
):
    return [
        CreateModel(
            self.name,
            fields=self.fields,
            options=self.options,
            bases=self.bases,
            managers=operation.managers,
        ),
    ]
```
The modeled value is what `CreateModel.reduce` returns for the pairing of a
creation step (`self`) with a following `AlterModelManagers` operation: the
collapsed `[CreateModel(...)]` when the names match, else (no arm fires for this
pairing) no CreateModel reduction is produced.

## Operation correspondence
| # | Lean op (`implementation_optimizeCreateThenAlterManagers`) | patch.diff op | tag | note |
|---|---|---|---|---|
| 1 | `if sameModel model.name targetName then` | `isinstance(operation, AlterModelManagers) and self.name_lower == operation.name_lower` | R | the operation type is fixed to `AlterModelManagers` by the modeled pairing; the remaining guard is the same-model name test. `self.name_lower == operation.name_lower` = `self.name.lower() == operation.name.lower()` ↔ `model.name.toLower = targetName.toLower` = `sameModel model.name targetName`. Type bijection in mapping.md. |
| 2 | `return [{ model with managers := newManagers }]` | `return [CreateModel(self.name, fields=self.fields, options=self.options, bases=self.bases, managers=operation.managers)]` | R/I | the collapsed creation step copies name/fields/options/bases from `self` (the structure-update frame keeps those four fixed = `model`'s) and substitutes `managers := operation.managers` ↔ `newManagers`. `CreateModel(...)` ↔ the `ModelState` record; the singleton list ↔ `[...]`. |
| 3 | `return []` (fall-through) | the arm does not fire; `reduce` returns `super().reduce(...) or can_reduce_through(...)` — a boolean, NOT a `[CreateModel]` reduction | R | "no CreateModel reduction produced for this pairing" ↔ the empty result list `[]`. mapping.md result-type note documents the `list | bool` ↦ `List ModelState` modeling (`[merged]` vs `[]`). |

Every op is R or R/I; **no A row** (no axiom consumed, no deep-model reference of
an unchanged callee). `name.lower()` and the record construction are modeled
deeply (`String.toLower`, structure update), not axiomatized. Therefore
`meta.json axioms = []`, `deep_model_references = []`, and `axiom_check.py` is a
skip stub.

## R/I legs ⇒ G-CONF
The whole impl is R/I, so `conformance_check.py` mechanically differential-tests
the impl shadow against `patch.diff` behavior over ≥10^5 fuzzed inputs.
`conf_skip = false`.

## Prepatch = the real bug
Pre-patch, `CreateModel.reduce` has NO `AlterModelManagers` arm: the pairing
falls through the `elif` chain to `super().reduce(operation, app_label) or
self.can_reduce_through(operation, app_label)`. `super().reduce` returns `False`
(neither op is elidable), and `can_reduce_through` returns `not
operation.references_model(self.name, app_label)` = `False` (the AlterModelManagers
references the same model). So `reduce` returns `False` — no collapse — i.e. the
two steps are kept separate. The prepatch impl
(`implementation_optimizeCreateThenAlterManagers := return []`, unconditionally)
is exactly this "no reduction produced" behavior. It therefore cannot satisfy
`problem_spec_optimizeCreateThenAlterManagers` on the discriminating clause
(`sameModel model.name targetName = true → result = [{ model with managers :=
newManagers }]`) — `[] ≠ [merged]` — precisely the case the FAIL_TO_PASS test
`test_create_alter_model_managers` exercises (`CreateModel("Foo", fields=[])`
followed by `AlterModelManagers("Foo", managers=[("objects", …), ("things", …)])`
must optimize to a single `CreateModel("Foo", fields=[], managers=[…])`). The
carried gold proof leaves the goal `⊢ False` in that clause and fails to
typecheck against the buggy impl (G-DIFF).

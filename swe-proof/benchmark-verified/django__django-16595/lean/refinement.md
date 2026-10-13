# refinement.md — django__django-16595

Maps every operation in `implementation_reduceAlter` to its `patch.diff`
counterpart. Tags: **R** (type refinement), **A-consumed** (proof uses an axiom's
property), **A-reference** (deep model validated == real callee by G-AX), **I**
(identical concrete op). Every step is R, A, or I.

## Modeled function: `reduceAlter` (`AlterField.reduce`)

Post-patch repo code (`patch.diff`), the relevant arms of `reduce`:
```python
def reduce(self, operation, app_label):
    if isinstance(
        operation, (AlterField, RemoveField)
    ) and self.is_same_field_operation(operation):
        return [operation]
    elif (
        isinstance(operation, RenameField)
        and self.is_same_field_operation(operation)
        and self.field.db_column is None
    ):
        return [
            operation,
            AlterField(
                model_name=self.model_name,
                name=operation.new_name,
                field=self.field,
            ),
        ]
    return super().reduce(operation, app_label)
```

and the `super().reduce(...)` fall-through it delegates to
(`FieldOperation.reduce`, `fields.py:69-72` → `Operation.reduce`,
`base.py:129-139`):
```python
# FieldOperation.reduce
return super().reduce(operation, app_label) or not operation.references_field(
    self.model_name, self.name, app_label
)
# Operation.reduce
if self.elidable:
    return [operation]
elif operation.elidable:
    return [self]
return False
```
The elidable branches return NON-EMPTY lists, which short-circuit the trailing
`or` in `FieldOperation.reduce`; only when neither step is elidable does the
chain produce a bool ("no replacement list").

Lean impl (`implementation_reduceAlter`): a list-valued dispatch with the same
arm structure and the same guards, including the elidable fall-through.

| # | Lean op | patch.diff / real-code counterpart | tag | justification |
|---|---|---|---|---|
| 1 | `self op : Op` (`kind`, `modelName`, `name`, `newName`, `field`) | the receiver `AlterField` `self` and the following `operation` argument, observed through the components the arms read (mapping.md bijection) | **R** | `isinstance(operation, …)` ↔ the `op.kind : OpKind` tag; `model_name`/`name`/`new_name` ↔ the `String` fields; `self.field` ↔ `FieldInfo` (only `db_column` is inspected; the rest is the opaque `repr` token, only ever copied). |
| 2 | `if (op.kind == OpKind.alterField \|\| op.kind == OpKind.removeField) && sameField self op then return [op]` | `if isinstance(operation, (AlterField, RemoveField)) and self.is_same_field_operation(operation): return [operation]` | **I** (the changed op, deeply modeled) | **the fixed operation.** The patch widens the `isinstance` tuple from `RemoveField` to `(AlterField, RemoveField)`; the Lean guard's left disjunct `op.kind == OpKind.alterField` is the added case, matching post-patch exactly. The prepatch impl tests only `op.kind == OpKind.removeField` (pre-patch). `is_same_field_operation` modeled deeply as `sameField` (row below). |
| 3 | `sameField self op = self.modelName.toLower == op.modelName.toLower && self.name.toLower == op.name.toLower` | `self.is_same_field_operation(operation)` = `self.model_name_lower == operation.model_name_lower and self.name_lower == operation.name_lower`, where `*_lower` is `str.lower()` | **I** | identical boolean expression; `str.lower()` ↔ `String.toLower` over ASCII model/field identifiers (mapping.md name-lower bijection). |
| 4 | `if op.kind == OpKind.renameField && sameField self op && self.field.dbColumn.isNone then return [op, {alterField, modelName := self.modelName, name := op.newName, elidable := false, field := self.field}]` | `elif isinstance(operation, RenameField) and self.is_same_field_operation(operation) and self.field.db_column is None: return [operation, AlterField(model_name=self.model_name, name=operation.new_name, field=self.field)]` | **I** | identical guard + identical replacement list. `self.field.db_column is None` ↔ `self.field.dbColumn.isNone` (`Option.none`). The constructed `AlterField` copies `self.model_name` and `self.field` verbatim and takes the rename's `new_name` (directive 5 frame); a freshly constructed operation carries the class-default `elidable = False` (`base.py:32`) ↔ `elidable := false`. Unchanged by the patch — carried for faithfulness so the modeled `reduce` value is total over the operand kinds. |
| 5 | `if self.elidable then return [op]` | `Operation.reduce`: `if self.elidable: return [operation]` (`base.py:135-136`), reached via `super().reduce(...)`; the non-empty list short-circuits `FieldOperation.reduce`'s `or` | **I** (deeply modeled fall-through) | identical guard (`self.elidable : Bool` ↔ `self.elidable : bool`) and identical replacement list `[operation]`. Unchanged by the patch — carried for faithfulness. |
| 6 | `if op.elidable then return [self]` | `Operation.reduce`: `elif operation.elidable: return [self]` (`base.py:137-138`); non-empty list, short-circuits the `or` | **I** (deeply modeled fall-through) | identical guard and identical replacement list `[self]`. This is exactly the pairing G-PANEL-2 exhibited (`AlterField.reduce(self, elidable RunPython, "app") == [self]`); the model now returns `[self]` there, matching the real callee. |
| 7 | `return []` | `return False` (`Operation.reduce`, `base.py:139`) then `False or not operation.references_field(...)` → bool | **R** | when neither step is elidable the `super().reduce(...)` chain returns a bool (`False`/`True` — "cannot optimize across" / "may commute"), never a replacement list. Modeled as `[]` ("no replacement list produced"); see mapping.md result-type note. The bool's exact value is not part of the modeled reduction outcome. |
| 8 | `Id.run do … return …` (`List Op`) | `reduce` returns a `list` of operations or a bool | **R** | result modeled as `List Op`; replacement lists are the singleton/pair/fall-through lists, the bool case is `[]`. |

All impl-region ops are **R/I** — there is NO A-tagged (axiom) content, so the
impl is NOT all-A-tagged: `conf_skip = false`, and `conformance_check.py`
mechanically differential-tests the R/I shadow against an in-process replica of
the post-patch `AlterField.reduce` decision.

## Soundness check (verify ⟹ correct)

- `problem_spec_reduceAlter` pins the result for ALL exhaustive,
  mutually-exclusive cases (directive 5 — frame: no output is left unconstrained;
  directive 8 — every output is grounded in the inputs `self`/`op`, no ungrounded
  oracle). A verifying impl must therefore return `[op]` on an
  alter/remove-same-field pairing, the rename-floated pair on a rename-same-field
  pairing with no explicit column, and otherwise the elidable fall-through
  outcome: `[op]` when `self` is elidable, `[self]` when only `op` is elidable,
  and `[]` when neither is.
- The discriminating clause is the first conjunct: when `op.kind =
  OpKind.alterField` and `sameField self op`, the spec demands `result = [op]`.
  The prepatch impl's first guard fires only on `removeField`, so for a
  non-elidable alter-against-alter same-field pairing it falls through to `[]`
  — disagreeing with the spec. Hence the carried gold proof fails to typecheck
  against the prepatch impl (the first-conjunct branch's closing step cannot
  reduce the un-fired guard) (G-DIFF/G-PANEL).
- This is exactly what `test_alter_alter_field` exercises: two `AlterField` ops
  on the same `Foo.name` field collapse into the second (post-patch `[op]`);
  pre-patch they did not reduce.
- G-CONF confirms the R/I shadow == an in-process replica of the post-patch
  `reduce` decision (collapse arm, rename arm, elidable fall-through, bool),
  exhaustively over the modeled abstraction (4 op kinds × case-varying ASCII
  names × db_column present/absent × new_name choices × both elidable flags)
  plus ≥1e5 fuzzed points (0 disagreements). The replica was additionally
  differential-tested against the REAL post-patch repo (`$SCRATCH`,
  gold patch applied at f9fe062de5) over the same exhaustive grid with real
  `AlterField`/`RemoveField`/`RenameField`/`RunPython` operations and both
  elidable flags: 7776 pairings, 0 mismatches.

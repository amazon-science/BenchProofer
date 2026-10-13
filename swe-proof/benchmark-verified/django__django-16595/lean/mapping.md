# mapping.md — django__django-16595

## Symbol binding (file:line @ base_commit f9fe062de5)
Modeled function: the reduction decision in
`AlterField.reduce(self, operation, app_label)`,
`django/db/migrations/operations/fields.py:249-267` (the `if/elif/else` chain on
the receiver `AlterField` `self` and the following `operation`). The gold patch
widens the first arm's type guard so that it fires not only when `operation` is a
`RemoveField` on the same field, but also when `operation` is itself an
`AlterField` on the same field; in both cases the pair collapses into just
`operation`.

Lean modeled function name: `reduceAlter` (names the *behavior* — "reduce an
alter-field step against the operation that follows it" — at the abstract level;
the public `problem_statement` already names `AlterField`, `RemoveField`,
`RenameField`, and `reduce`).

| Lean symbol | Python binding (file:line @ base) |
|---|---|
| `self : Op` (the receiver) | the `AlterField` instance `self`; observed via `self.model_name`, `self.name`, `self.field` (`FieldOperation.__init__`, `fields.py:9-12`; `AlterField.__init__`, `fields.py:204-206`) |
| `self.modelName` | `self.model_name` (`fields.py:10`) |
| `self.name` | `self.name` (`fields.py:11`) |
| `self.field.dbColumn` | `self.field.db_column` (read by the rename arm, `fields.py:257`) — `None` ↔ `none` |
| `op : Op` | the following `operation` argument to `reduce` (`fields.py:249`) |
| `op.kind` | the runtime class of `operation` tested by `isinstance` (`AlterField` / `RemoveField` / `RenameField` / anything else) (`fields.py:250-256`) |
| `op.modelName` | `operation.model_name` |
| `op.name` | `operation.name` — for a `RenameField`, this is its `old_name` (`RenameField.__init__` passes `old_name` as `name` to super, `fields.py:273-276`) |
| `op.newName` | `operation.new_name` of a `RenameField` (`fields.py:275`); read only on the rename arm (`fields.py:264`) |
| `self.elidable`, `op.elidable` | `self.elidable` / `operation.elidable` (`Operation.elidable`, `base.py:32`, default `False`), read by the fall-through `Operation.reduce` (`base.py:135-138`) |
| `sameField self op` | `self.is_same_field_operation(operation)` = `self.model_name_lower == operation.model_name_lower and self.name_lower == operation.name_lower` (`FieldOperation.is_same_field_operation`, `fields.py:25-29`; `model_name_lower`/`name_lower` are `.lower()`, `fields.py:14-19`) |
| result | the value `reduce` returns for this pairing: `[operation]` (collapse arm), `[operation, AlterField(model_name=self.model_name, name=operation.new_name, field=self.field)]` (rename arm), or the `super().reduce(...)` fall-through — `Operation.reduce`'s elidable branches `[operation]` / `[self]`, else a bool (modeled as the empty list `[]`, "no replacement-list produced") |

## Lean ↔ Python type bijection (used by G-CONF and G-AX)
| Python | Lean |
|---|---|
| `operation`'s class ∈ {AlterField, RemoveField, RenameField, other} | `op.kind : OpKind` ∈ {`alterField`, `removeField`, `renameField`, `otherOp`} |
| `self.model_name : str`, `operation.model_name : str` (ASCII model labels) | `self.modelName`, `op.modelName : String` |
| `self.name : str`, `operation.name : str` (ASCII field labels) | `self.name`, `op.name : String` |
| `operation.new_name : str` | `op.newName : String` |
| `self.elidable : bool`, `operation.elidable : bool` | `self.elidable`, `op.elidable : Bool` |
| `self.field.db_column` (`None` or a column-name str) | `self.field.dbColumn : Option String` |
| the rest of `self.field` (copied verbatim, never inspected) | `self.field.repr : String` (opaque token) |
| `self.model_name.lower() == operation.model_name.lower() and self.name.lower() == operation.name.lower()` | `sameField self op = (self.modelName.toLower == op.modelName.toLower && self.name.toLower == op.name.toLower)` |
| `[operation]` | `[op]` |
| `[operation, AlterField(model_name=self.model_name, name=operation.new_name, field=self.field)]` | `[op, { kind := OpKind.alterField, modelName := self.modelName, name := op.newName, newName := "", elidable := false, field := self.field }]` |
| `super().reduce(...)` fall-through: `Operation.reduce`'s `if self.elidable: return [operation]` | `[op]` (when `self.elidable`) |
| `super().reduce(...)` fall-through: `Operation.reduce`'s `elif operation.elidable: return [self]` | `[self]` (when `op.elidable`, `self` not) |
| `super().reduce(...)` returns a bool (no replacement list) | `[]` (neither step elidable) |

### Result-type modeling note
The real `reduce` returns *either* a `list` of replacement operations *or* a
bool (`Operation.reduce` / `FieldOperation.reduce` return `False`/`True` to
signal "cannot optimize across" / "may commute"). For the modeled pairing the
outcomes are: a one-element `[operation]` (collapse arm), a two-element
`[operation, AlterField(...)]` (rename arm), or the `super()` fall-through:
`FieldOperation.reduce` evaluates `super().reduce(operation, app_label) or not
operation.references_field(...)`, and `Operation.reduce` (`base.py:129-139`)
first checks the elidable flags — `if self.elidable: return [operation]`,
`elif operation.elidable: return [self]` — each a NON-EMPTY list that
short-circuits the `or`; only when neither step is elidable does the chain
yield a bool. We model the result as `List Op` and map "no replacement list
produced" to `[]`, and carry the elidable branches as `[op]` / `[self]`
(faithfulness: the real callee returns `[self]`, not a bool, when the following
step is elidable — G-PANEL-2's diverging input `AlterField.reduce(self,
elidable RunPython, "app") == [self]`). The re-expressed alter step built on
the rename arm is a freshly constructed `AlterField`, whose `elidable` is the
class default `False` (`base.py:32`) — hence `elidable := false` in the record
literal. For an `AlterField` `self` followed by an `AlterField` `operation` on
the same field (neither elidable), the pre-patch code falls through every arm
to the bool `False` — i.e. no replacement list (`[]` in the model); the
post-patch code returns `[operation]` (`[op]`). That is the discriminating
behavior the F2P test exercises.

### Name-lower bijection
`str.lower()` is modeled by `String.toLower`. Faithful for the ASCII model/field
identifiers migrations use (`"Foo"`, `"name"`, app labels); the bijection is
asserted only over ASCII identifier strings, the only domain the optimizer's
name comparison sees.

## Callee provenance + flag deps
- **No unchanged callee is consumed as an axiom.** The reduction performs only
  (a) a runtime type test of `operation` (modeled as the `OpKind` tag), (b) a
  case-insensitive model+field name comparison (`is_same_field_operation`,
  modeled deeply as `String.toLower` equality), (c) a `db_column is None` test
  (modeled as `Option.none` equality), (d) the `super().reduce` fall-through's
  elidable-flag tests (`Operation.reduce`, `base.py:135-138`, modeled deeply as
  `Bool` field reads), and (e) construction of replacement operations copying
  carried-over components (modeled as record literals / structure copies). All
  are modeled directly, so no `opaque`/`axiom` callee contract is required ⇒
  `axioms = []`, `deep_model_references = []`, `axiom_check.py` is a skip stub
  (G-AX skips).
- Flag dependency: the arms fire on the operand's type tag plus the same-field
  name guard (and, for the rename arm, `self.field.db_column is None`); the
  fall-through additionally reads each step's `elidable` flag (modeled as the
  `Op.elidable : Bool` component).

## G-LEAK
The solver-visible `problem_statement` publicly names `AlterField`, `AddField`,
`RemoveField`, `RenameField`, the migration `optimizer`/`optimize`, and
`reduce`. The only `def`/`class` name appearing on the gold diff's hunk header
is `migration_name_fragment` (an unrelated neighbouring property) — that token
appears NOWHERE in the spec view (no identifier embeds it; no comment names it).
No gold-diff line is reproduced, no diff marker, no patched file path, and no
bug→fix mechanism is narrated; the docstring states the abstract reduction
behavior only.

## Pinned G-CONF fuzz seed
`16595`.

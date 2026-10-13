# mapping.md — django__django-15268

Binds every `model.py` symbol to its repository counterpart at
`base_commit = 0ab58c120939093fea90822f376e1866fc714d1f`, states the type
abstraction, and gives the provenance of each modelled decision. There are **no
axiomatized callees** in this bundle: the changed decision is a pure
integer/boolean computation, modelled deeply.

Repo files under change: `django/db/migrations/operations/models.py` (the
patched hunks); the decision is consumed by
`django/db/migrations/optimizer.py` and the base
`django/db/migrations/operations/base.py` (unchanged callers).

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `commutes_through(self_op, other)` | `AlterTogetherOptionOperation.can_reduce_through(self, operation, app_label)` — the method ADDED at `models.py` (gold hunk 2, after `migration_name_fragment`, line 529) PLUS the boolean path of `ModelOperation.reduce` it feeds (`models.py:34-38`) | the modelled changed function: the boolean "this constraint-altering operation may be commuted across `other`" |
| `pair_collapses_through(first, between, second)` | the optimizer's left-reduction guard `all(op.reduce(other, app_label) is True for op in in_between)` at `optimizer.py:53`, applied to the redundant same-family pair `(first, second)` separated by the cross-family `between` | the observable consequence: the redundant clear/set pair collapses iff the in-between step commutes through the surviving step |
| `Operation` (class, fields `kind`, `model_id`) | a migration `Operation` instance, of which only two attributes are read by the decision: its concrete class (the constraint family) and its target model name | minimal object carrying only the touched attributes |
| `is_constraint_alteration(kind)` | `isinstance(operation, AlterTogetherOptionOperation)` (`models.py:470`, the abstract base of `AlterUniqueTogether`/`AlterIndexTogether`) | pure spec: the operation is a constraint-altering operation |
| `touches_model(op_model, name)` | `operation.references_model(name, app_label)` for these model-scoped operations — `ModelOperation.references_model` returns `name.lower() == self.name_lower` (`models.py:31-32`) | pure spec: the unchanged neighbour predicate, on the same-model case it decides |
| `base_commutes_through(self_model, other_kind, other_model)` | `ModelOperation.reduce`'s boolean fallback `not operation.references_model(self.name, app_label)` (`models.py:37`) = the base `can_reduce_through` ADDED at gold hunk 1 (`return not operation.references_model(self.name, app_label)`) | pure spec: the base commute rule (clause 1) |
| `alter_commutes_through(self_kind, self_model, other_kind, other_model)` | `AlterTogetherOptionOperation.can_reduce_through` body (gold hunk 2): `super().can_reduce_through(...) or (isinstance(operation, AlterTogetherOptionOperation) and type(operation) is not type(self))` | pure spec: the constraint-altering commute rule (clauses 1 + 2) |

`FAMILY_UNIQUE = 0` ↔ `AlterUniqueTogether` (`option_name = 'unique_together'`,
`models.py:532,537`); `FAMILY_INDEX = 1` ↔ `AlterIndexTogether`
(`option_name = 'index_together'`, `models.py:543,548`). `kind < 0` ↔ any
operation that is not an `AlterTogetherOptionOperation`.

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| the concrete class of an `Operation` (`AlterUniqueTogether` / `AlterIndexTogether` / anything else) | `kind: int` | `AlterUniqueTogether` ↔ `0`, `AlterIndexTogether` ↔ `1`, non-`AlterTogetherOptionOperation` ↔ a negative tag. `isinstance(op, AlterTogetherOptionOperation)` ↔ `kind >= 0`; `type(a) is type(b)` ↔ `a.kind == b.kind` (the two subclasses have distinct `option_name`, hence distinct tags). |
| `self.name` / `operation.name` (the target model, compared case-insensitively via `name_lower`) | `model_id: int` | distinct model names ↔ distinct ints; `references_model(name)` for these operations is `name_lower == self.name_lower`, modelled as `op_model == name`. |
| `operation.references_model(name, app_label)` | `touches_model(op_model, name)` | `references_model` for `ModelOperation`/`AlterTogetherOptionOperation` is exactly `name.lower() == self.name_lower`; the `app_label` argument is unused by these operations. The `True`-returning generic `Operation.references_model` default (base.py:90-100, "if in doubt return True") is the conservative over-approximation; the operations in the tested sequence all use the exact same-model comparison, so `touches_model` models that path. |
| `self.reduce(other, app_label)` boolean path | `commutes_through(self_op, other)` returning `bool` | `ModelOperation.reduce` returns `super().reduce(...) or can_reduce_through(...)`. `super().reduce()` (`Operation.reduce`, base.py:123-133) returns `False` for these non-elidable operations (the elidable/`ModelOptionOperation` list paths fire only for elidable ops or same-class+same-name merges, which are not the cross-family commute the fix governs), so the boolean path equals `can_reduce_through`. |

No `str`/`float`/sequence modelling is needed: the decision reads only a class
tag and a model identifier, both abstracted to `int`.

## 3. Callee provenance

**None.** The changed operation — `can_reduce_through`'s different-family
allowance — is a pure boolean computation over the two read attributes, modelled
deeply in `model.py`'s `pure` region (`is_constraint_alteration`,
`touches_model`, `base_commutes_through`, `alter_commutes_through`) and the two
verified functions. There is no `@ContractOnly` axiom and therefore no
`axiom_check.py`/G-AX obligation. `super().can_reduce_through` (the base rule)
and `references_model` are themselves modelled deeply (they are simple equality
tests), not axiomatized, so they are not A-consumed callees either.

The optimizer's surrounding loop (`optimizer.py:40-69`) and `Operation.reduce`'s
elidable handling (`base.py:123-133`) are unchanged context: the fix only
changes which boolean `reduce`/`can_reduce_through` returns on the cross-family
same-model case, which is exactly the `pair_collapses_through` observable.

# mapping.md — django__django-15268

## Symbol binding (file:line @ base_commit 0ab58c12)

| Lean symbol | Python symbol | location @ base_commit |
|---|---|---|
| `implementation_canOptimizeAcross` / `problem_spec_canOptimizeAcross` | `AlterTogetherOptionOperation.can_reduce_through` (NEW in patch) | `django/db/migrations/operations/models.py:531-538` (post-patch) |
| `affectsModel` (opaque) | `Operation.references_model(name, app_label)` (UNCHANGED callee) | `django/db/migrations/operations/base.py:90-100`; concrete `ModelOperation.references_model` at `models.py:31-32` |
| `OpType.alterUnique` | `AlterUniqueTogether` | `models.py:532` |
| `OpType.alterIndex` | `AlterIndexTogether` | `models.py:543` |
| `OpType.other` | any other `Operation` subclass | — |
| `Kind.unique` / `Kind.index` | `self.option_name == 'unique_together' / 'index_together'`; equivalently `type(self) is AlterUniqueTogether / AlterIndexTogether` | `models.py:537,548` |

## What the modeled function is

The patch is two edits to `django/db/migrations/operations/models.py`:

1. `ModelOperation.reduce` (line 34): `not operation.references_model(self.name, app_label)`
   → `self.can_reduce_through(operation, app_label)`, and a NEW
   `ModelOperation.can_reduce_through(self, operation, app_label) =
   not operation.references_model(self.name, app_label)`. **Behavior-preserving
   refactor** for the base class (the new method returns exactly the old inline
   expression). Tagged `I` (delegation) in refinement.md; not separately modeled.

2. A NEW `AlterTogetherOptionOperation.can_reduce_through` override (line 531):
   ```python
   def can_reduce_through(self, operation, app_label):
       return (
           super().can_reduce_through(operation, app_label) or (
               isinstance(operation, AlterTogetherOptionOperation) and
               type(operation) is not type(self)
           )
       )
   ```
   This is the ENTIRE behavioral delta of the patch. `super().can_reduce_through`
   is `not operation.references_model(self.name, app_label)`. The new disjunct
   lets an alter-together op be optimized across an alter-together op of a
   *different* concrete type. This is the function modeled by the triple.

The optimizer (`optimizer.py`, unchanged) consumes `reduce`'s result; the F2P
behavior (collapsing 4 AlterFooTogether ops → 2) follows mechanically from this
`can_reduce_through` returning `True` for the cross-kind pair. Since `reduce`
and the optimizer are unchanged, a correct `can_reduce_through` ⟹ the gold
optimizer output ⟹ harness `resolved`.

## Lean ↔ Python type bijection (used by G-CONF / G-AX)

| Python | Lean | bijection |
|---|---|---|
| `self` : an `AlterTogetherOptionOperation` | `selfKind : Kind`, `selfName : String` | `selfKind = unique` ⟺ `type(self) is AlterUniqueTogether`; `selfKind = index` ⟺ `type(self) is AlterIndexTogether`. `selfName = self.name`. |
| `operation` : an `Operation` | `operation : Op` (`ty : OpType`, `name : String`) | `ty = alterUnique` ⟺ `isinstance(operation, AlterUniqueTogether)` and `type` is exactly it; `ty = alterIndex` ⟺ exactly `AlterIndexTogether`; `ty = other` ⟺ any other class (incl. `DeleteModel`, `AddField`, …). `operation.name` = `operation.name` if it is a `ModelOperation`, else unused. |
| `operation.references_model(self.name, app_label)` : `bool` | `affectsModel operation selfName : Bool` | exact value bijection (opaque, real callee) |
| return `bool` | `Bool` | identity |
| `isinstance(operation, AlterTogetherOptionOperation)` | `isAlterTogether operation.ty` | `ty ∈ {alterUnique, alterIndex}` |
| `type(operation) is not type(self)` | `operation.ty != kindTag selfKind` | `kindTag unique = alterUnique`, `kindTag index = alterIndex` |

`app_label` is threaded only into `references_model`; modeled as folded into
`affectsModel`'s value (the callee takes it but the decision logic never
branches on it).

## Callee provenance + flag deps

- `references_model` (→ `affectsModel`): UNCHANGED by the patch. For
  `ModelOperation` subclasses it is `name.lower() == self.name_lower`
  (`models.py:31`); `CreateModel`/`RenameModel` override it. Modeled opaque; the
  proof consumes NO property of it (its boolean value is used symbolically), so
  it is an **A-reference** with no `_prop` axiom. No flag dependency.
- `type(operation) is not type(self)`: exact-type identity, NOT `isinstance` —
  `AlterUniqueTogether` vs `AlterIndexTogether` are siblings, neither subclasses
  the other, so exact-type inequality == "different kind". Captured by
  `operation.ty != kindTag selfKind` (only reached when `isAlterTogether`).

## Closed-world invariant (faithfulness of the OpType model)

The model `operation.ty ≠ kindTag selfKind` faithfully represents Python's
`type(operation) is not type(self)` (under the `isAlterTogether` guard) ONLY
because at `base_commit` the concrete subclasses of `AlterTogetherOptionOperation`
are EXACTLY two: `AlterUniqueTogether` (`models.py:532`) and `AlterIndexTogether`
(`models.py:543`) — verified by `grep "class .*(AlterTogetherOptionOperation)"`.
Therefore:
- `isAlterTogether ty` (i.e. `ty ∈ {alterUnique, alterIndex}`) ⟺
  `isinstance(operation, AlterTogetherOptionOperation)`;
- `kindTag` is injective onto `{alterUnique, alterIndex}`, so for two
  alter-together ops, tag inequality ⟺ exact-type inequality ⟺ different flavour.
Any genuinely non-alter-together op (e.g. `DeleteModel`, `AddField`) maps to
`other`; the patch routes those entirely through `super().can_reduce_through`
(the `affectsModel` baseline leg), so modeling them via `affectsModel` alone is
faithful. G-CONF's "other" draws use `DeleteModel` to exercise this leg with the
real `references_model`.

## G-CONF fuzz seed

Pinned seed: `15268`. Fuzz domain: `operation.ty ∈ {alterUnique, alterIndex,
other}` × `name ∈ {'book','Book','author', random ascii}` × `selfKind ∈
{unique, index}` × `selfName ∈ same name pool}`, ≥10⁵ draws. `affectsModel` is
A-tagged → evaluated by the REAL `references_model` of a constructed operation.

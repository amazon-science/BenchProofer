# refinement.md — django__django-15268

Operation-by-operation correspondence between `Solution.lean`'s impl regions
(the methods `reorderableBase`, `reorderableTogether`, `optimizeAgainst`, plus
the pure helpers `affectsModel` / `isTogetherOp` / `sameKind` / `mergeable`) and
`patch.diff` (the gold patch). Each step is tagged **R** (type refinement; state
the bijection), **A-consumed** / **A-reference** (none in this bundle), or **I**
(identical concrete op). EVERY step is R or I.

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`,
§4.1); the narrative is audited by **G-EQ**. Claim: any impl verifying against
this frozen spec, refined per the map below, is behaviourally equal to the gold
patch on the tested inputs, so it resolves.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## Background — what the gold patch changes

Two hunks in `django/db/migrations/operations/models.py`:

Hunk 1 (`ModelOperation.reduce`, behaviour-preserving extraction):
```
 def reduce(self, operation, app_label):
     return (
         super().reduce(operation, app_label) or
-        not operation.references_model(self.name, app_label)
+        self.can_reduce_through(operation, app_label)
     )
+
+def can_reduce_through(self, operation, app_label):
+    return not operation.references_model(self.name, app_label)
```

Hunk 2 (`AlterTogetherOptionOperation.can_reduce_through`, the NEW override —
the only behavioural change):
```
+def can_reduce_through(self, operation, app_label):
+    return (
+        super().can_reduce_through(operation, app_label) or (
+            isinstance(operation, AlterTogetherOptionOperation) and
+            type(operation) is not type(self)
+        )
+    )
```

`reduce` is consumed by `MigrationOptimizer.optimize_inner`
(`django/db/migrations/optimizer.py`): a list result means "replace with these"
(merge); `True` means "may optimize across `other`" (advance/reorder); `False`
means "stop" (blocked). The new override lets an `Alter{Unique,Index}Together`
operation optimize **across** a *different-type* AlterTogether on the same model,
which is what collapses the remove-then-re-add quadruple to a pair (the issue's
worked example).

## A. The baseline independence test — `ModelOperation.can_reduce_through`

Modeled by `reorderableBase` (and the pure `affectsModel`).

| # | Solution.lean op | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | param `selfName : Nat` | `self.name` (compared via `self.name_lower`) | R | model name ↔ `Nat` identity; only equality is observed (`references_model` is `name.lower() == self.name_lower`). mapping.md §2. |
| A2 | param `other : OtherOp` | `operation` | R | a neighbouring migration `Operation` ↔ the `OtherOp` carrier of the features `reduce`/`can_reduce_through` observe. mapping.md §2. |
| A3 | `return !affectsModel selfName other` | `return not operation.references_model(self.name, app_label)` | I | `affectsModel` IS `references_model(self.name)` transliterated: name-equality for `together` operations (`ModelOperation.references_model`, `models.py:31`); **always `True`** for `deleteModel` (`DeleteModel.references_model` returns `True` unconditionally, `models.py:279`); and the free unchanged result `refsSelf` for any `generic refsSelf elidable` operation (the `elidable` bit is not consulted here). The `not` is identical. G-CONF runs the real `references_model` (it caught the DeleteModel case on the M1 self-check). |

## B. The widened test for together-options — `AlterTogetherOptionOperation.can_reduce_through`

Modeled by `reorderableTogether` (and the pure `isTogetherOp` / `sameKind`).

| # | Solution.lean op | patch.diff op | tag | justification |
|---|---|---|---|---|
| B1 | `let base ← reorderableBase selfName other` | `super().can_reduce_through(operation, app_label)` | I | the `super()` call resolves to `ModelOperation.can_reduce_through`, modeled by `reorderableBase` and applied **as a proved callee** (`reorderableBase_correct`), not an axiom — callee-under-spec (SPEC_GUIDE §3). |
| B2 | `isTogetherOp other` | `isinstance(operation, AlterTogetherOptionOperation)` | I | the `isinstance` test ↔ the `OtherOp.together` constructor tag. mapping.md §2. |
| B3 | `!sameKind selfKind other` | `type(operation) is not type(self)` | I | `type(self)` is fixed by `selfKind ∈ {unique, index}`; `type(operation) is not type(self)` ↔ the `other`-together flavour differs from `selfKind`. Both `AlterUniqueTogether` and `AlterIndexTogether` derive `option_name`/`type` 1:1 from the flavour, and only these two concrete subclasses of `AlterTogetherOptionOperation` exist, so the flavour bijects with the Python `type`. mapping.md §2. |
| B4 | `return base \|\| (isTogetherOp other && !sameKind selfKind other)` | `return (super()... or (isinstance(...) and type(...) is not type(self)))` | I | the disjunction/conjunction structure is identical op-for-op. |

`selfKind : TogetherKind` (param) ↔ `type(self) ∈ {AlterUniqueTogether,
AlterIndexTogether}` — R (mapping.md §2). `selfName`, `selfKind`, `other` are all
read-only (directive 5); no method mutates an input.

## C. The optimizer verdict — `reduce` through the MRO

Modeled by `optimizeAgainst` (and the pure `mergeable`). This composes the merge
branch (`ModelOptionOperation.reduce`, `models.py:409`) with the
`can_reduce_through` boolean to yield the three-valued result the optimizer
consumes.

| # | Solution.lean op | patch.diff op (MRO of `AlterFooTogether.reduce`) | tag | justification |
|---|---|---|---|---|
| C1 | `if mergeable selfName selfKind other then .merge` | `ModelOptionOperation.reduce`: `if isinstance(operation, (self.__class__, DeleteModel)) and self.name_lower == operation.name_lower: return [operation]` — **or** `Operation.reduce` (`base.py:123`): `elif operation.elidable: return [self]` | I | `mergeable` IS the union of the two list-returning branches: (a) same-flavour together (`self.__class__`) OR `DeleteModel`, same model name ⇒ `[operation]`; (b) an **elidable neighbour** ⇒ `[self]` — `super().reduce` runs before the boolean disjunct, and `operation.elidable` is only ever `True` for a `generic` neighbour (AlterTogether/DeleteModel classes leave the class default `elidable = False`, `base.py:32`; only `RunSQL`/`RunPython` take an `elidable=` kwarg), which is exactly `mergeable`'s `.generic _ elidable => elidable` arm. Either list result collapses the pair to one op ⇒ `OptimizeOutcome.merge`. (`Operation.reduce`'s FIRST branch `if self.elidable: return [operation]` IS dead — `self` is an AlterTogether op, never elidable — so it carries no node.) mapping.md §2. |
| C2 | `else if canReorder then .reorderable` | `... or self.can_reduce_through(operation, app_label)` returning `True` | I | once the merge branches fail (no same-flavour/delete merge, neighbour not elidable), the `super().reduce(...)` disjunct is `False`, so `reduce` returns exactly the boolean `can_reduce_through` value; `True` ⇒ the optimizer may advance across ⇒ `OptimizeOutcome.reorderable`. |
| C3 | `else .blocked` | `can_reduce_through` returns `False` | I | `False` ⇒ the optimizer stops scanning ⇒ `OptimizeOutcome.blocked`. |

`canReorder ← reorderableTogether ...` is the proved callee (`reorderableTogether_correct`).

## D. The discriminating content — what the spec senses (G-DIFF)

The behavioural change is B4's added disjunct. For `self =
AlterFooTogether(name=m, kind=k)` reducing against `other =
AlterFooTogether(name=m, kind=k')` with `k' ≠ k` (the issue's
remove-then-re-add pattern: `AlterUniqueTogether(set())` then
`AlterIndexTogether(set())` then the re-adds):

- pre-patch: `can_reduce_through` does not exist; `reduce`'s bool disjunct is
  `not other.references_model(m)` = `not (m==m)` = `False` ⇒ `blocked`. The
  optimizer cannot move the unique-together op across the index-together op, so
  the four operations stay four.
- post-patch: `can_reduce_through` = `base or (isTogether and differentType)` =
  `False or (True and True)` = `True` ⇒ `reorderable`. The optimizer advances
  the remove past the other-flavour op, the same-flavour remove/re-add pair then
  merges, and four operations become two.

`Solution_prepatch.lean` reproduces the pre-patch `reorderableTogether` (the
`return base` body, no different-type disjunct) and **fails** verification on
exactly the clause
`result = ((!affectsModel selfName other) || (isTogetherOp other && !sameKind selfKind other))`
(confirmed unsolved goal at `prove_correct reorderableTogether`). `optimizeAgainst`'s
prepatch likewise diverges (`reorderable` vs `blocked`) on this input. This is
precisely the divergence the F2P tests (`test_foo_together_ordering`,
`test_remove_field_and_foo_together`, `test_rename_field_and_foo_together`)
observe as a drop from 4 AlterTogether ops to 2 (G-DIFF).

## E. No kind-3 (inexpressible-changed-op) steps

Every step is R or I. The operation that genuinely changed — the eligibility
disjunct that lets an AlterTogether op optimize across a different-flavour
AlterTogether op — is modeled **deeply** (B2/B3/B4 spell out `isinstance` +
`type` differs as `isTogetherOp` + `!sameKind`), not hidden behind an axiom. The
unchanged facts consulted about a *non-together* operation (`references_model`
and the `elidable` attribute) are carried as free inputs
(`OtherOp.generic refsSelf elidable`), so they need no axiom and **no G-AX**.
There are no consumed axioms and no A-references (`axiom_check.py` records
`status="skip"`).

## E². Termination semantics

The file uses `loom.semantics.termination "total"` (total correctness). The
real eligibility decision is a straight-line boolean/branch computation that
always terminates and returns a value the optimizer consumes, so total
correctness is the faithful semantics. Partial correctness would admit a
same-spec implementation that diverges (an infinite loop vacuously satisfies
every `ensures`) — a wrong impl the tests would fail — so it would leave the
spec too weak.

## F. verify(Solution) ⇒ resolved

`optimizeAgainst` verifies only if its result equals the exact modeled verdict
(C1–C3) built from `mergeable` and `reorderableTogether`, and
`reorderableTogether` verifies only if it equals the widened disjunction (B1–B4)
— i.e. the post-patch `can_reduce_through`. By R (the `Nat`/`TogetherKind`/
`OtherOp` bijections, mapping.md §2) the verified decision equals the
gold-patched `reduce`/`can_reduce_through` on every operation pair. By G-CONF the
R/I transliteration agrees with the **real** patched operation classes' `reduce`
on ≥10⁵ checks (seed 15268, 0 disagreements), including the different-flavour
same-model scenario the F2P tests exercise. Therefore a model satisfying this
spec, refined by the map above, is the gold patch up to type refinement — and
the gold patch resolves (G-RESOLVE). The sole trust point is refinement fidelity
(this doc, G-EQ + G-CONF); there are no axioms (G-AX skips).

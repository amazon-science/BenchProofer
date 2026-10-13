# mapping.md — django__django-16595

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = f9fe062de5fc0896d6bbbf3f260b5c44473b3c77`, states the type
abstraction (the bijection G-CONF and G-AX use to bridge Lean↔Python), and
gives the provenance of every modeled operation.

Repo file under change: `django/db/migrations/operations/fields.py`.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `reduceAlterField (op : ReduceInput)` | `AlterField.reduce(self, operation, app_label)` — `django/db/migrations/operations/fields.py:249` | the modeled changed function (decide how this field alteration combines with the operation that immediately follows it) |
| `ReduceInput.incomingIsAlter` | `isinstance(operation, AlterField)` — `fields.py:251` post-patch (the **added** member of the kind tuple) | the following operation is itself an alteration of a model field's definition |
| `ReduceInput.incomingIsRemove` | `isinstance(operation, RemoveField)` — `fields.py:251` (the kind already tested pre-patch) | the following operation removes a model field |
| `ReduceInput.sameField` | `self.is_same_field_operation(operation)` — `fields.py:24` (`is_same_model_operation` ∧ `self.name_lower == operation.name_lower`, both case-insensitive) | the following operation targets the same model field (same model, same field name) |
| `reduceDecision (op : ReduceInput)` | the post-patch first branch `if isinstance(operation, (AlterField, RemoveField)) and self.is_same_field_operation(operation): return [operation]` vs the `elif`/`return super().reduce(...)` fall-through (`fields.py:250-257`) | per-pair decision: collapse onto the later operation, else defer to the pre-existing dispatch (I — identical concrete op) |
| `ReduceResult.keepLater` | the reducer returns exactly `[operation]` (`fields.py:254`) | the two operations collapse onto the later one (the earlier alteration is dropped) |
| `ReduceResult.deferToInherited` | any other reducer return: the `RenameField` 2-element list (`fields.py:255-263`) or `super().reduce(...)`'s list / `[self]` / bool (`base.py:131-139`) | no special combination applies; the pre-existing dispatch (unchanged) decides |

The surrounding `MigrationOptimizer.optimize` / `optimize_inner` loop
(`django/db/migrations/optimizer.py`), the `elif isinstance(operation,
RenameField) ...` branch, and the `return super().reduce(operation, app_label)`
fall-through are **unchanged** by the patch; only the first branch's kind test
widened (one class added to the `isinstance` tuple). The optimizer loop applies
`reduce` pairwise and acts on its return, so the per-pair decision is the
observable the F2P test reads — the loop is therefore a type refinement (R), not
an axiom, and the bundle models exactly one `reduce` call.

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4.1) and G-AX use to translate values between the
Lean value domain and the Python repo types. A wrong entry surfaces as spurious
G-CONF disagreements (the falsifiability the plan §4 trust statement refers to).

| repo reality | Lean carrier | bijection |
|---|---|---|
| the following migration operation `operation` passed to `reduce` | `ReduceInput` | one operation ↔ one `ReduceInput`, summarized by the three booleans the first branch consults |
| `isinstance(operation, AlterField)` | `ReduceInput.incomingIsAlter : Bool` | `True` ↔ `incomingIsAlter = true`; `False` ↔ `false` |
| `isinstance(operation, RemoveField)` | `ReduceInput.incomingIsRemove : Bool` | `True` ↔ `incomingIsRemove = true`; `False` ↔ `false` |
| `self.is_same_field_operation(operation)` (only defined for `FieldOperation` subclasses; a non-field operation, e.g. `CreateModel`, never reaches this test because the real first branch guards it behind the `isinstance(operation, (AlterField, RemoveField, RenameField))` checks, and is treated as not-same-field) | `ReduceInput.sameField : Bool` | same model (case-insensitive) ∧ same field name (case-insensitive) ↔ `sameField = true`; otherwise ↔ `false` |
| the reducer's return value | `ReduceResult` | return is exactly `[operation]` ↔ `keepLater`; every other return (2-element list, `[self]`, bool from `super().reduce`) ↔ `deferToInherited` |

`AlterField.reduce` returns either a list of operations (the optimizer splices
it in) or a bool (whether the optimizer may reorder across `operation`). The
observable the F2P `test_alter_alter_field` reads is whether the
optimizer collapses an `AlterField` followed by another same-field `AlterField`
into the later one alone — i.e. whether `reduce` returns `[operation]`. The
desired behaviour distinguishes only that outcome from every other, so the
carrier is the binary `ReduceResult`. `op` is read-only (`reduce` does not mutate
`operation` or `self`); `ReduceInput` is passed by value and `reduceAlterField`
declares no `mut` parameter (directive 5).

## 3. Callee provenance

**No axioms; no deep-model references (A-reference); no consumed axioms
(A-consumed).** The single operation the patch changes — the first branch's kind
test widening — is modeled **identically** (`reduceDecision`'s `incomingIsAlter`
disjunct). The unchanged pre-existing dispatch (the `RenameField` branch and the
`super().reduce` fall-through) is represented by the abstract tag
`ReduceResult.deferToInherited`, about which the proof asserts nothing; its
concrete behaviour is left entirely to G-CONF, which runs the **real** reducer.
Every step is therefore R or I (see refinement.md), all mechanically checked by
G-CONF against the real patched `AlterField.reduce`. There is no unchanged opaque
callee whose contract the proof must assume, so `axiom_check.py` (G-AX) has no
axiom to validate and exits 0 after confirming the bundle declares none and that
the operations the refinement leans on (`isinstance` over `AlterField`/
`RemoveField`, `is_same_field_operation`) carry the fixed semantics the §2
bijection claims.

G-CONF exercises the decision on fuzzed real migration operations — following
operations of every kind (`AlterField`, `RemoveField`, `RenameField`, `AddField`,
`CreateModel`), same/different model, same/different field name (incl.
case-insensitive matches) — so the §2 bijection is falsifiable, not merely
asserted. It disagrees with the unpatched reducer exactly at the same-field
alteration-then-alteration case.

## 4. G-CONF fuzz seed (pinned for deterministic eval — plan §4.1, §11.3)

`conformance_check.py` seeds its `random.Random` with **`16595`** so the
consumer-side verdict (§11.3) is reproducible. The R/I shadow it builds
transliterates `reduceDecision` (R/I-tagged ops) to Python and compares the
resulting decision against the real patched `AlterField.reduce`'s return-value
classification (`[operation]` ⇒ `keepLater`, else `deferToInherited`) over
fuzzed real Django migration operations. There are no A-tagged callees to leave
as real-callee calls (§3).

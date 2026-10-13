# refinement.md — django__django-16595

The operation-by-operation correspondence between `model.py`'s `reduce` impl
region and `patch.diff` (the gold patch). Each step is tagged **R** (type
refinement), **A** (axiomatized callee — **A-consumed** / **A-reference**), or
**I** (identical concrete operation). The claim: *any implementation that
verifies against this frozen spec, refined per the map below, is behaviourally
equal to the gold patch on the tested inputs, so it resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## The change

Gold hunk (`AlterField.reduce`, `django/db/migrations/operations/fields.py`):
```
-        if isinstance(operation, RemoveField) and self.is_same_field_operation(
-            operation
-        ):
+        if isinstance(
+            operation, (AlterField, RemoveField)
+        ) and self.is_same_field_operation(operation):
             return [operation]
```
The guard on the first branch of `AlterField.reduce` widens from
`isinstance(operation, RemoveField)` to `isinstance(operation, (AlterField,
RemoveField))`. The branch body (`return [operation]`) and the rest of the
method (the `RenameField` carry-across branch and the `super().reduce(...)`
fall-through) are unchanged.

## Operation correspondence

| # | model.py impl op (`reduce`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| 1 | `this.kind == KIND_ALTER` (precondition) | the method is `AlterField.reduce`, i.e. `self` is an `AlterField` | R | the bound instance's class ↔ its kind tag (mapping.md §2). |
| 2 | `operation.kind == KIND_ALTER or operation.kind == KIND_REMOVE` | `isinstance(operation, (AlterField, RemoveField))` | R | the post-patch `isinstance` tuple ↔ the kind disjunction (mapping.md §2). This is the **changed** guard; it is widened to include `KIND_ALTER`, exactly mirroring the added `AlterField`. |
| 3 | `is_same_field(this, operation)` | `self.is_same_field_operation(operation)` | I | `is_same_field` is the UNCHANGED predicate spelled out (same model+field, lower-cased) — `@Pure`, modeled directly, not an axiom (mapping.md §1). Same concrete comparison. |
| 4 | `res = [operation]; return res, False` | `return [operation]` | R | Python list of operations ↔ `List[Operation]`; `operation` is returned by identity (`Result()[0][0] is operation`). The paired verdict is normalised to `False`: returning steps IS the reduction, so no reordering question is asked (mapping.md §2). |
| 5 | `elif operation.kind == KIND_RENAME and is_same_field(...) and not this.has_explicit_column:` | `elif isinstance(operation, RenameField) and self.is_same_field_operation(operation) and self.field.db_column is None:` | R | unchanged rename branch; class ↔ kind tag, `self.field.db_column is None` ↔ `not this.has_explicit_column` (mapping.md §1). |
| 6 | `carried = Operation(KIND_ALTER, ...); res2 = [operation, carried]; return res2` | `return [operation, AlterField(model_name=self.model_name, name=operation.new_name, field=self.field)]` | R | unchanged: `[rename, AlterField(...)]` ↔ `[operation, <fresh KIND_ALTER op>]`. The carried operation is CONSTRUCTED at `fields.py:258-264`, so it is neither operand; the spec pins `Result()[0] is operation`, `len == 2`, and `Result()[0][1] is not operation and Result()[0][1] is not this` (freshness on both sides), AND the carry's CONTENT: `kind == KIND_ALTER` (the constructed class), `model_name_lower == this.model_name_lower` (`model_name=self.model_name`), `name_lower == operation.new_name_lower` (`name=operation.new_name`), `has_explicit_column == this.has_explicit_column` (`field=self.field`, the same field object, hence the same `db_column`), and `not elidable` (`AlterField` inherits `Operation.elidable = False`, `base.py:32`, and the construction passes no `elidable=`). Those are ALL the facets an `AlterField` carries — mirroring `AlterField(model_name=self.model_name, name=operation.new_name, field=self.field)` exactly — so the carried step is determined outright. It carries NO new name (`new_name` is a `RenameField`-only attribute, `fields.py:270-284`; measured `hasattr(carried,'new_name') is False`), so there is no such pin and nothing to read off it; see "## The operand's new name is a PARTIAL facet" below for why a value pin on that slot was unsound. (The content pins were added after a G-EQ audit exhibited verifying impls that returned an arbitrary distinct second step on this branch.) |
| 7 | `elif this.elidable: return [operation], False` / `elif operation.elidable: return [this], False` / `return None, not nxt_references_altered_field` | `return super().reduce(operation, app_label)` | R | the fall-through is a **four-state**, not a bare flag and not a tri-state. `super()` from `AlterField.reduce` binds **`FieldOperation.reduce`** (`fields.py:69-72`, unchanged by the patch), not `Operation.reduce`: AlterField's MRO is `[AlterField, FieldOperation, Operation, object]`. `FieldOperation.reduce` is `super().reduce(...) or not operation.references_field(self.model_name, self.name, app_label)`, so it post-processes `Operation.reduce` (`base.py:129-139`). Its two list arms — `[operation]` when `self.elidable`, `[self]` when `operation.elidable` (the earlier operand's mark taking precedence, since the first test wins) — are truthy and pass through, modeled as the corresponding singleton `List[Operation]` distinguished by IDENTITY (`Result()[0][0] is operation` vs `is this`) rather than by length. Otherwise the answer is `not operation.references_field(...)`: **TRUE when the later step does not reference the altered field, FALSE when it does**, both reachable. That bit is a REORDERING VERDICT the optimizer acts on (`optimizer.py:46-47` and, decisively, `:50`'s `is True` test, which is what lets two collapsible same-field alterations separated by a third operation still collapse), so it is modeled as the `bool` component of the result. Modelling it as a single `None` would be over-strong: no constant reproduces the real method — measured, a constant `False` leaves the issue's own 3-`AlterField` sequence at length 3, and a constant `True` drops an operation gold keeps. |
| 8 | the fall-through clauses are guarded by `not joined_by_field_rule(this, operation)` | the fall-through is reached exactly when none of `AlterField.reduce`'s own guards returned (`fields.py:250-259`) | I | the negation of the method's own early-return condition, spelled out. Guarding on "different field" instead would be WRONG: a SAME-field pair also reaches `super().reduce` when the rename arm is rejected because `self.field.db_column is not None`. |

## The discriminating clause (G-DIFF)

The single behavioural change is step 2: the guard now also fires for a
same-field `AlterField` follow-up. The spec pins this in the postcondition
```
Implies(operation.kind == KIND_ALTER and is_same_field(this, operation),
        Result()[0] is not None and len(Result()[0]) == 1
        and Result()[0][0] is operation)
```
`model_prepatch.py` reverts step 2 to `operation.kind == KIND_REMOVE` only (the
pre-patch `isinstance(operation, RemoveField)`); the alter-then-alter case then
falls through and yields the reordering verdict instead of the collapse, so it
**fails** exactly that postcondition (verifier output:
`Postcondition of reduce might not hold ... (operation.kind == KIND_ALTER) and
is_same_field ...`). That is the spec sensing the bug. The F2P test
`test_alter_alter_field` (two same-field `AlterField`s collapse to the second)
passes post-gold and fails pre-patch — the same observable.

## A new name is a PARTIAL facet — on every step, handed in or built — and that is an obligation

`MigrationStep` is one flat carrier for several operation classes, so it has a
`new_name_lower` slot on every step. The repository does not: `new_name` is
defined only by `RenameField.__init__` (`fields.py:273-284`), and an `AlterField`
or `RemoveField` operand has no such attribute at all — reading it is an
`AttributeError`, not a value. With the patch applied, `AlterField.reduce`
(`fields.py:249-267`) reads `operation.new_name` exactly once, at
`fields.py:263`, and only under the `isinstance(operation, RenameField)` test at
`fields.py:255`.

The class, not the provenance, is what decides whether the facet is there, so the
same partiality governs a step the reduction BUILDS. The carried operation
constructed at `fields.py:258-264` is an `AlterField`, and `AlterField.__init__`
(`fields.py:204`) sets only `preserve_default` on top of `FieldOperation`'s
`model_name` / `name` / `field`: it has no `new_name` either.

Modelling that slot as TOTAL with an unconditional `Acc(nxt.new_name_lower, 1/2)`
in the precondition would make the model claim something false of every operand:
that a new name is always there to be read. It is unobservable in the value
domain — an impl that consults the operand's new name before establishing that
the operand is a rename can still return exactly gold's answers, so no
postcondition of any strength separates it — and its faithful refinement raises
on the first pair whose later operation is an alteration or a removal. Measured
on the patched worktree over the instance's 38 optimizer tests, such a
refinement fails exactly `test_alter_alter_field` (F2P) and
`test_alter_field_delete_field` (P2P, "RemoveField should absorb AlterField"),
both with `AttributeError`.

The partiality is therefore modelled as a RESOURCE rather than a value:

* the pre-conditions region lends the facet conditionally —
  `Requires(Implies(nxt.kind == KIND_RENAME, Acc(nxt.new_name_lower, 1 / 2)))` —
  so a read of `nxt.new_name_lower` is a proof obligation discharged only after
  the operand's kind is known to be `KIND_RENAME`, mirroring the guard at
  `fields.py:255`;
* the reducing step is lent no such facet at all (there is no
  `Acc(this.new_name_lower)` conjunct), mirroring `AlterField` (`fields.py:198`)
  defining no `new_name`;
* the CONSTRUCTOR grants the slot on the same condition —
  `Ensures(Implies(kind == KIND_RENAME, Acc(self.new_name_lower) and
  self.new_name_lower == new_name_lower))` — so a step built as an alteration
  yields nothing to read back on that facet, mirroring the constructed
  `AlterField` at `fields.py:258-264` having no `new_name`;
* the post-conditions region returns the facet under the same condition, so the
  caller's frame is exactly restored and nothing else in the contract changes.

This is a strengthening, not a narrowing: the admissible input domain is
unchanged in the value dimension (every pair of steps that was admissible before
still is — G-PBT's `admiss-f2p-shaped-input` witnesses the alter/alter pair, the
elidable fall-through pair, and now a rename-shaped operand for which the
antecedent holds and the facet is genuinely required), while an implementation
that reads a facet the operand does not carry is now rejected for INSUFFICIENT
PERMISSION. Both shapes of that rival are pinned as `expect: "reject"` cases in
the battery: `uniq-eager-new-name` (the bare unguarded consultation, gold's body
following verbatim) and `uniq-eager-carry-name` (the same consultation made
load-bearing, VALUE-IDENTICAL to gold on every input, so nothing but the
resource discipline can reject it).

Step 6 used to pin the CONSTRUCTED step's `new_name_lower` to a VALUE instead,
on the argument that the slot is written by the reduction and never read back.
That argument was refuted by measurement: the pin only says what the value IS
*given* a permission the constructor was handing out unconditionally, so it
licensed reading the slot back, and an impl that named the carried step by its
own new-name slot (`carried.new_name_lower`) verified against the pin. Refined
faithfully it reads `carried.new_name`, which the constructed `AlterField` does
not have: measured over the instance's 38 optimizer tests that refinement
errors on `test_alter_field_rename_field` with `AttributeError: 'AlterField'
object has no attribute 'new_name'` (1 error / 38; gold 38/38 OK), and the G-EQ
harness recorded the same rival as PASS_TO_PASS 1/37 failing, "RenameField
should optimize to the other side of AlterField". So the slot on a constructed
ALTER step is now governed by the resource, not by a value: the constructor's
grant is conditional on `kind == KIND_RENAME`, the postcondition claims neither
permission nor value for it, and the carried step's identity was pinned harder
in exchange (`is not nxt` **and** `is not this`, both true of a construction at
`fields.py:258-264`). Nothing observable was un-pinned — every facet a real
`AlterField` carries is still pinned, and the read that the value pin used to
admit is now rejected for insufficient permission (battery cases
`uniq-read-back-carried-name`, `uniq-eager-built-name`).

## The pinned-column status is partial for the same reason, one facet over

Whether an explicit stored column is pinned is not a facet of a step: it is a
facet of the FIELD DEFINITION a step carries. `FieldOperation.__init__(self,
model_name, name, field=None)` stores it (`fields.py:9-12`); `AlterField`
requires a definition (`fields.py:204`) and `RemoveField` (`fields.py:154`)
inherits the optional parameter, so both may carry one — but
`RenameField.__init__(self, model_name, old_name, new_name)`
(`fields.py:273-276`) takes no field at all and calls
`super().__init__(model_name, old_name)`, so a rename's `field` is always `None`
and `self.field.db_column` is an `AttributeError`; a bare `Operation`
(`base.py`) has no `field` attribute whatsoever. The real method reads the facet
exactly once, `self.field.db_column is None` at `fields.py:257`, and only off
`self` — never off the operand, and never off a step it built.

The model matches that shape in three places: the reducing step is lent the facet
(it is an `AlterField`), the operand is lent none, and the constructor grants it
only for the kinds that carry a definition —

```python
        Ensures(Implies(kind == KIND_ALTER or kind == KIND_REMOVE,
                        Acc(self.has_explicit_column)
                        and self.has_explicit_column == has_explicit_column))
```

The last of the three was missing while the first two were in place, and a G-EQ
audit broke exactly that gap: with a total constructor grant an impl could build
a step of rename kind (or of some other kind) purely to read its column status
back, satisfy every clause with gold's own values, and verify. Measured on the
patched worktree over the instance's 38 optimizer tests: a rename-kind probe
gives 1 error, `test_alter_field_rename_field`, `AttributeError: 'NoneType'
object has no attribute 'db_column'` — the same P2P line, "RenameField should
optimize to the other side of AlterField" — and an other-kind probe
(`Operation()`) gives 3 errors including the F2P itself, `AttributeError:
'Operation' object has no attribute 'field'`. Both shapes and the
guard-load-bearing variant are pinned as `expect: "reject"`
(`uniq-rename-probe-column`, `uniq-guard-rename-probe-column`,
`uniq-other-probe-column`).

The grant stops at `KIND_ALTER or KIND_REMOVE` and not one kind further, and that
boundary is measured too: a removal CAN be given a definition, so
`RemoveField(model_name=…, name=…, field=self.field).field.db_column` is a value
and an impl that reads a removal-kind probe's column back resolves 38/38.
Conditioning that out would reject a resolving rival, so it is pinned as an
ACCEPT case (`pos-remove-probe-column`) — the two lanes together fix the
condition rather than merely satisfying the failing audit.

**Why the conditioning stops there** (it is calibrated, not applied to every
slot). `model_name_lower` is also partial in the repository — measured,
`CreateModel`/`DeleteModel` have `name_lower` but no `model_name_lower`, so
`is_same_field_operation` raises on such an operand — yet an implementation that
evaluates the same-field test BEFORE the `isinstance` guard is a *resolving*
implementation: measured over the same 38 optimizer tests it passes 38/38,
because no test pairs an alteration with an operation that lacks the attribute.
Conditioning that slot would therefore reject a correct alternative (it is the
battery's `pos-hoist` accept case, and the audit's own attack 8 — reordered
guards — verifies and RESOLVES), i.e. it would be SPEC-TOO-STRONG. The OPERAND's
`has_explicit_column` needs no new clause because it was never granted at all:
the real method reads only `self.field.db_column`, a `RenameField` operand has
`field is None`, and an impl consulting the operand's column instead errors on
`test_alter_field_rename_field` (measured). What DID need a clause is the same
facet on a step the reduction BUILDS (the section above), and there the condition
is `kind == KIND_ALTER or kind == KIND_REMOVE` — exactly the kinds whose class
accepts a field definition — with the removal side pinned as an ACCEPT case so
the condition is fixed from both directions rather than merely tightened until
the failing audit stopped. So each slot is granted exactly on the condition under
which the real method can read it, and the conditioning is added only where the
premature read is observable in the repository's own tests.

## No kind-3 (unexpressible-changed-op) steps

Every step above is R or I. There is no axiomatized callee (A): the changed
operation is pure control flow Nagini expresses directly, so it is modeled
**deeply** (the `isinstance`/same-field guard spelled out), never hidden behind
an axiom. `axiom_check.py` (G-AX) therefore performs a *structural* soundness
check: it runs the real `AlterField.reduce` — from a faithful, dependency-free
transcription of the repo classes, including the `FieldOperation.reduce`
fall-through it really delegates to and the `references_field` post-processing
that wrapper applies — on boundary + fuzz operation pairs and asserts the
model's `reduce` returns the same list shape, the same surviving operation by
identity, and the same reordering verdict, i.e. the R refinements of steps 2 and
7 are faithful; that the fall-through's four-state, its earlier-step precedence
and both values of the verdict are what the real chain does; and that the
pre-patch guard genuinely differs on the alter-then-alter case (with both
operands non-elidable, so the difference is not masked by a fall-through that
would return a list on both sides).

## verify(model) ⇒ resolved

`reduce` verifies only if its result collapses BOTH same-field `KIND_REMOVE`
(unchanged) AND same-field `KIND_ALTER` (the change) to `[operation]` (steps 2,
4) and preserves the rename/fall-through arms (steps 5–8), including the
carried step's full content on the rename branch (step 6: kind, owning model,
renamed field name, pinned-column status and the absence of an elidable mark all
pinned to the gold construction) and the fall-through's real four-state with its
earlier-step precedence AND the reordering verdict's VALUE (steps 7–8), and only
if it reaches those results WITHOUT consulting a facet the operand does not carry
(the conditional lending of `nxt.new_name_lower`, above — a read of the operand's
new name is admitted only where the real method's `isinstance(operation,
RenameField)` guard admits it, so a verifying impl cannot be one whose refinement
raises; and the same discipline on a step the reduction BUILDS, whose new name is
readable only if it was built as a rename and whose pinned-column status only if
it was built as an alteration or a removal, so an answer reached through a facet
the constructed operation's class does not define is not an answer this method may
give). By the R
refinements (class ↔ kind tag, case-folded `str` ↔ `int`, Python list ↔
`List[Operation]`, `op.elidable` ↔ `elidable`,
`operation.references_field(self.model_name, self.name, app_label)` ↔ the
`nxt_references_altered_field` ARGUMENT (a query over the PAIR, which is why it
is a parameter and not step state — no operation caches the answer), the fall-through's
`[operation]`/`[self]`/`True`/`False` ↔
`([nxt], False)`/`([this], False)`/`(None, True)`/`(None, False)`) the verified
method equals the gold `AlterField.reduce` on every operation pair the optimizer
feeds it. That equality is not merely argued here: G-CONF measures it against
the real patched chain, called, over 101 670 operation pairs with 0
disagreements, comparing the reordering verdict's value rather than erasing it
(mapping.md "## G-CONF"). The gold
patch resolves (G-RESOLVE). The only trust point is refinement fidelity (this
document, G-EQ); there is no axiom trust point.

The quantifier above ("any implementation that verifies") ranges over
implementations that RETURN, and the spec makes that a proof obligation rather
than an assumption: the pre-conditions region carries `Requires(MustTerminate(6))`,
so the statement is TOTAL correctness. Without it every `Ensures` would constrain
only the runs that reach the return, and a `reduce` that diverged — recursing on
the same pair, or spinning before it decides — would satisfy the whole
postcondition vacuously while the optimizer it is called from hung. Both
divergence channels are pinned as `expect: "reject"` cases in the G-PBT battery
(`uniq-diverging-self-call`, `uniq-diverging-loop`); each was measured to verify
with the obligation removed from the pre-conditions region and to be rejected by
the obligation system with it present, so the obligation is load-bearing and not
decorative. `reduce` itself is loop-free and call-free apart from the
`MigrationStep` construction on the rename branch (a constructor that stores its
six arguments and returns, obligated at level 2, i.e. strictly below the method's
own level 6, which is what lets an obligated caller construct the carried step),
so the gold impl discharges the obligation directly.

# refinement.md — django__django-15278

The operation-by-operation correspondence between `model.py`'s implementation
(the `add_column` impl region, the pure `needs_full_rebuild` predicate, and the
live `has_effective_default` axiom) and `patch.diff` (the gold patch). Each step
is tagged **R** (type refinement), **A** (axiomatized callee — split into
**A-consumed**, where the proof uses the axiom, and **A-reference**, where a
deep model is validated == the real callee by axiom_check.py / G-AX), or **I**
(identical concrete operation). The claim: *any implementation that verifies
against this frozen spec, refined per the map below, makes the same in-place-vs-
rebuild routing decision as the gold patch, so it resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## A. The routing site — `add_field()` (`django/db/backends/sqlite3/schema.py:325`)

Gold hunk:
```
-        # Fields with default values cannot by handled by ALTER TABLE ADD
-        # COLUMN statement because DROP DEFAULT is not supported in
-        # ALTER TABLE.
-        if not field.null or self.effective_default(field) is not None:
+        if (
+            # Primary keys and unique fields are not supported in ALTER TABLE
+            # ADD COLUMN.
+            field.primary_key or field.unique or
+            # Fields with default values cannot by handled by ALTER TABLE ADD
+            # COLUMN statement because DROP DEFAULT is not supported in
+            # ALTER TABLE.
+            not field.null or self.effective_default(field) is not None
+        ):
             self._remake_table(model, create_field=field)
         else:
             super().add_field(model, field)
```

| # | model.py impl op (`add_column`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `col: ColumnSpec` with fields `primary_key`, `unique`, `nullable` (bool) | the `field` argument of `add_field` (a model `Field`) | R | the rich `Field` object ↔ a minimal `ColumnSpec` carrying only the three touched boolean attributes `field.primary_key`, `field.unique`, `field.null` (mapping.md §1–2). |
| A2 | `col.primary_key` | `field.primary_key` | R | bool attribute, identity correspondence. |
| A3 | `col.unique` | `field.unique` | R | bool attribute, identity correspondence. The NEW disjunct that fixes the bug (a nullable unique field). |
| A4 | `not col.nullable` | `not field.null` | R + I | `col.nullable` ↔ `field.null` (bool); `not` is the identical concrete operation. |
| A5 | `has_effective_default(col)` | `self.effective_default(field) is not None` | A-consumed | `has_effective_default` is the WEAKEST stand-in (no `Ensures`, only a pure read permission) for the unchanged backend observation `effective_default(field) is not None`. The proof consumes only that it is a stable boolean read of the column; the routing equation `needs_full_rebuild` uses it as the fourth disjunct exactly as the gold predicate does. G-AX (axiom_check.py) confirms against the real backend that `effective_default(field) is not None` is a deterministic, side-effect-free boolean and that the real predicate == the model's. |
| A6 | `if (col.primary_key or col.unique or (not col.nullable) or has_effective_default(col))` | the gold `if (field.primary_key or field.unique or not field.null or self.effective_default(field) is not None)` | I | the boolean disjunction is the identical concrete control-flow expression (same operands in the same order, by A2–A5). |
| A7 | `return 1` (full-rebuild route) | `self._remake_table(model, create_field=field)` | R | the rebuild branch is denoted by the route discriminator `1`; `_remake_table` is the unchanged action taken on that branch (mapping.md §2). Its side effects are not part of the modelled behaviour — only the routing decision is changed by the patch. |
| A8 | `return 0` (in-place append route) | `super().add_field(model, field)` | R | the append branch is denoted by `0`; `super().add_field` (the base `ALTER TABLE ADD COLUMN` path) is the unchanged action on that branch. |

The discriminating content of the change — that a nullable, defaultless column
which is **unique** (or a **primary key**) must take the full-rebuild route
rather than the in-place append route — lives in the two NEW disjuncts
`col.primary_key or col.unique` (model, A2/A3) ⇔ `field.primary_key or
field.unique` (gold). The pre-patch predicate omitted them;
`model_prepatch.py` reproduces that omission and **fails** the postcondition
`(Result() == 1) == needs_full_rebuild(col)` — exactly the spec sensing the
change (G-DIFF). The F2P witness (a nullable `OneToOneField`, which is
`unique=True, null=True, primary_key=False`, no default) is the input on which
the pre-patch and post-patch routes differ: pre-patch route `0`
(`ALTER TABLE … ADD COLUMN … UNIQUE`, which SQLite rejects), post-patch route
`1` (rebuild). G-AX exercises that exact field.

## B. The axiom is about an UNCHANGED callee

`self.effective_default(field)` is NOT changed by the patch (it is identical in
the pre- and post-patch predicate). It is therefore a legitimate kind-A callee:
`has_effective_default` (**A-consumed**). It is the weakest possible contract —
it has **no `Ensures`**, so it cannot over-claim the callee's value; the proof
relies only on it being a pure boolean observation, and the model never assumes
which value it returns (every routing postcondition that mentions it is an
`Implies` guarded by the observed value, or the routing equation itself). G-AX
validates against the real backend that `effective_default(field) is not None`
is deterministic and side-effect-free and that the four-way real predicate
equals the model's `needs_full_rebuild`.

There is **no A-reference** in this bundle: the changed operation (the routing
predicate) is modelled deeply and directly (the boolean disjunction is spelled
out, step A6, kind I), not validated as an opaque equality.

## C. No kind-3 (unexpressible-changed-op) steps

Every step above is R, A-consumed, or I. The operation that genuinely *changed*
— the routing predicate gaining the `primary_key`/`unique` disjuncts — is
modelled **directly** as the identical boolean expression (A6, kind I) over
refined boolean carriers (A2–A4, kind R). The only consumed axiom,
`has_effective_default` (A-consumed), covers an **unchanged** backend callee the
predicate invokes in both pre- and post-patch code.

## D. verify(model) ⇒ resolved

`add_column` verifies only if its returned route equals `needs_full_rebuild(col)`
(the postcondition `(Result() == 1) == needs_full_rebuild(col)`), i.e. only if it
chooses the full-rebuild route for exactly the columns that are a key, unique,
non-nullable, or default-carrying — and the in-place append route for no other.
By R (the `Field`↔`ColumnSpec` boolean correspondence, A1–A4) and I (the
identical disjunction, A6) the verified routing decision equals the gold
predicate `field.primary_key or field.unique or not field.null or
self.effective_default(field) is not None`; by A-consumed + G-AX the stand-in
`has_effective_default` faithfully tracks the unchanged `effective_default(field)
is not None`. On the F2P witness (nullable `OneToOneField`) the verified route
is `1` (rebuild), matching the gold patch, which resolves (G-RESOLVE). The trust
points are exactly the two of PLAN §1.1: axiom soundness (G-AX) and refinement
fidelity (this document, G-EQ).

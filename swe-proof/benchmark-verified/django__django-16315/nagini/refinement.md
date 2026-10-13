# refinement.md — django__django-16315

The operation-by-operation correspondence between `model.py`'s implementation
(the `conflict_columns` / `lookup` impl regions and the deep `column_for` model)
and `patch.diff` (the gold patch). Each step is tagged **R** (type refinement),
**A** (axiomatized callee — split into **A-consumed**, where the proof uses the
axiom's `Ensures`, and **A-reference**, where a deep model is validated == the
real callee by axiom_check.py / G-AX), or **I** (identical concrete operation).
The claim: *any implementation that verifies against this frozen spec, refined
per the map below, is behaviourally equal to the gold patch on the tested
inputs, so it resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## A. The change, as two coordinated hunks

The gold patch makes the conflict-resolution clause refer to each field by its
storage **column** rather than its in-memory **name**, via two hunks that act
together:

Hunk 1 — `django/db/models/query.py`, `bulk_create` (and a clean-up of the
now-redundant local conversions in `_check_bulk_create_options`):
```
+        if update_fields:
+            update_fields = [self.model._meta.get_field(name) for name in update_fields]
         unique_fields = [
-            opts.pk.name if name == "pk" else name for name in unique_fields
+            self.model._meta.get_field(opts.pk.name if name == "pk" else name)
+            for name in unique_fields
         ]
```
i.e. `bulk_create` now resolves the requested names to `Field` objects before
they flow into the query, so `self.query.update_fields` /
`self.query.unique_fields` hold **fields**, not name strings.

Hunk 2 — `django/db/models/sql/compiler.py`, `SQLInsertCompiler.as_sql`:
```
-            self.query.update_fields,
-            self.query.unique_fields,
+            (f.column for f in self.query.update_fields),
+            (f.column for f in self.query.unique_fields),
```
i.e. the identifiers handed to `on_conflict_suffix_sql` are now each field's
`.column` (= `db_column or name`), not the field itself / its name.

`model.py` models the COMPOSITE of the two hunks as one transformation
(`conflict_columns`): requested name → resolved field → field column. Both
`update_fields` and `unique_fields` undergo the SAME transformation, so a single
modeled function covers both (they differ only in the input list and the SQL
slot, neither of which changes the identifier-selection behaviour under test).

| # | model.py impl op | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | `requested: List[int]` | one of `update_fields` / `unique_fields` (`list[str]` of requested names) | R | field-name `str` ↔ `int` identifier (mapping.md §2); the modeled transform is identical for both lists. |
| A2 | `field_names`, `field_columns: List[int]` (the registry) | `self.model._meta` field registry (name → `Field`, each carrying `.name` / `.column`) | R | the registry as parallel name/column lists; `field_columns[k] = db_column or name` of field `k` (mapping.md §2,§3.1). |
| A3 | `lookup(name, field_names, field_columns)` returns `column_for(name, ...)` — resolve the requested name to its registry slot, return that slot's **column** | `self.model._meta.get_field(name)` (hunk 1) then `f.column` (hunk 2) | A-reference | the changed operation — selecting the storage **column** of the designated field — is modeled **deeply** (`column_for` walks the name/column registry and returns the matching column). There is **no consumed `get_field`/`column` axiom**. The deep model is validated **== the real pipeline** out-of-band: G-AX (axiom_check.py) runs `_meta.get_field(n).column` on real models incl. mixed-case `db_column` overrides and asserts `conflict_columns == [get_field(n).column for n]` at the identifier level (mapping.md §3.1). |
| A4 | element-wise build: `result[i] = column_for(requested[i], ...)`, `len(result) == len(requested)` | the generator `(f.column for f in self.query.update_fields)` / `unique_fields` consumed by `on_conflict_suffix_sql` — one identifier per requested field, in order | I + R | same length and order as the requested list (the `Ensures` pins `len(Result()) == len(requested)` and `Result()[i] == column_for(requested[i], ...)`); the generator is the same per-element projection over the resolved fields. |
| A5 | `name_present(...)` precondition on every requested name | `get_field` succeeds (the name designates a declared field; else `FieldDoesNotExist`) | R | the patch runs after `_check_bulk_create_options`; the F2P inputs name declared fields, so resolution does not raise (mapping.md §2). |

The discriminating content of the change — the identifier is the field's
**column** (`db_column` when set), not its **name** — lives in `column_for`
returning `columns[j]` (model) ⇔ `f.column` (real). The pre-patch code passed
the field **names** straight through; `model_prepatch.py` reproduces that
(`lookup` returns `field_names[j]`, the name) and **fails** the postcondition
`Result() == column_for(name, field_names, field_columns)` (the column) whenever
a field declares a storage-column override (`column != name`) — which is exactly
the spec sensing the change (G-DIFF). For a field with no override (`column ==
name`) the two impls agree, matching reality: the bug is only observable for
fields with `db_column` set, exactly the F2P
`test_update_conflicts_unique_fields_update_fields_db_column` (`db_column="rAnK"`
/ `"oTheRNaMe"`).

## B. No kind-3 (unexpressible-changed-op) steps

Every step above is R, A-reference, or I. The one operation that genuinely
*changed* — selecting the storage column instead of the field name — is modeled
**deeply** (`column_for` / `lookup`, the spelled-out registry resolution +
column projection), not hidden behind an axiom about the function under change:
there is no consumed `get_field`/`column` axiom. The unchanged callees
(`get_field`, `Field.column`) appear only as the **A-reference** that G-AX
validates the deep model against.

## C. verify(model) ⇒ resolved

`conflict_columns` verifies only if, for every requested name `i`, the produced
identifier equals `column_for(requested[i], field_names, field_columns)` — the
storage **column** of the designated field (A3/A4), with length and order
preserved. By R (field-name/column `str` ↔ `int`; the registry as parallel
lists) the verified transform equals the gold patch's
`[self.model._meta.get_field(n).column for n in requested]` on the tested
inputs; by G-AX the deep model `column_for` equals the real
`get_field(n).column` (A-reference), including the mixed-case `db_column`
discriminator. Therefore an implementation satisfying this spec, refined by the
map above, is the gold patch up to type refinement and the audited
callee-equivalence — and the gold patch resolves (G-RESOLVE). The trust points
are exactly the two of PLAN §1.1: callee-equivalence soundness (G-AX, here the
A-reference) and refinement fidelity (this document, G-EQ).

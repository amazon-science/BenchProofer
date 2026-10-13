# refinement.md — django__django-14434

Operation-by-operation correspondence between `Solution.lean`'s impl region
(the `buildUniqueStatement` `do` block, over the deep `TableSlot` / `ColumnsRef`
/ `Stmt` model of the unchanged `ddl_references` classes) and `patch.diff` (the
gold patch). Each step is tagged **R** (type refinement; state the bijection),
**A-consumed** (proof uses an axiom's `ensures`), **A-reference** (deep model
validated == the real callee by G-AX), or **I** (identical concrete op). Every
step is R, A, or I.

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`,
§4.1); the A-reference deep model is validated == the real classes by **G-AX**
(`axiom_check.py`); the A legs and this narrative are audited by **G-EQ**.
Claim: any impl verifying against this frozen spec, refined per the map below,
is behaviourally equal to the gold patch on the tested inputs, so it resolves.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## A. The constraint-statement construction site — `_create_unique_sql()` (`django/db/backends/base/schema.py:1225`)

Gold hunks (the column-list / F2P path only):
```
- table = Table(model._meta.db_table, self.quote_name)
+ table = model._meta.db_table
  ...
  if columns:
      columns = self._index_columns(table, columns, col_suffixes=(), opclasses=opclasses)
  ...
  return Statement(
      sql,
-     table=table,
+     table=Table(table, self.quote_name),
      ...
  )
```

`_index_columns(table, columns, …)` (`schema.py:1068`) is the unchanged callee
`return Columns(table, columns, self.quote_name, col_suffixes)`. So under the
patch the local `table` is the **bare db-table name string**, threaded into
`Columns` (the `columns=` part of the `Statement`), while the `Statement`'s
`table=` part wraps that same name in a fresh `Table(...)`. The pre-patch code
threaded the `Table(...)` **object** into `Columns`.

| # | Solution.lean impl op (`buildUniqueStatement`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | param `dbTable : String` | `table = model._meta.db_table` (a `str`) | R | `model._meta.db_table` ↔ Lean `String` (mapping.md §2, identity on character content). G-CONF bridges via `s ↔ str`. |
| A2 | param `columns : List String` | the constraint's `columns` (a `list[str]`) | R | `list[str]` ↔ `List String`; `col in self.columns` ↔ `List.contains` (mapping.md §2). |
| A3 | `let tableForColumns : TableSlot := TableSlot.name dbTable` | `table = model._meta.db_table` (bare string), then fed to `_index_columns` → `Columns(table, …)` | R | the carrier threaded into the columns reference is the **bare name string**, modeled as the value-comparable `TableSlot.name` (mapping.md §2/§3). The pre-patch carrier was the `Table(...)` wrapper object (`TableSlot.wrapped`). This is the single discriminating step. |
| A4 | `let cols : ColumnsRef := { tableSlot := tableForColumns, columns := columns }` | `columns = self._index_columns(table, columns, …)` = `Columns(table, columns, quote_name)` | R + I | constructs the real `Columns` reference holding the table slot + column list. `Columns.references_column(t,c) = (self.table == t) ∧ c ∈ self.columns` is the deep model `ColumnsRef.referencesColumn` (A-reference, G-AX-validated). The wiring (which slot, which columns) is I; the predicate equality is the A-reference. |
| A5 | `let out : Stmt := { tableName := dbTable, cols := cols }` | `return Statement(sql, table=Table(table, quote_name), name=…, columns=columns, …)` | R + I | the returned `Statement`'s two reference-bearing parts: `table=` wraps the bare name in a fresh `Table(...)` (`Stmt.tableName : String`, queried via `Table.references_table` = value compare → modeled by the `s.tableName == t` disjunct), and `columns=` is `cols`. `Statement.references_{table,column} = any(part…)` is the deep model's disjunction/lifting (A-reference). Other parts (`name=` a quoted str, `sql`, `condition=…`) are non-`Reference` or contribute `False` to both observables (mapping.md §2, base `Reference`); omitted from the carrier. |
| A5b | `Stmt.renderedColumns out = cols.columns` (pinned by the third `ensures`) | `Columns.__str__` joins `self.columns` (in order, with multiplicity) into `Statement.__str__`'s `%(columns)s` — the column payload of the executed DDL | R | the columns part's stored list IS the rendered column sequence (`ddl_references.py:84`); `', '.join(quote_name(c) …)` ↔ `List String` up to the uniform injective `quote_name` wrap (mapping.md §2). Pins the stored list verbatim: an impl that stores a reordered/truncated/padded list would emit different SQL (hidden tests grade the created constraint) while faking `references_*` membership. Mechanically refuted by G-CONF's rendered-columns observable. |
| A6 | `return out` | `return Statement(...)` | I | return the constructed deferred-DDL statement. |

Discriminating content of the change — the columns reference must store the
**value-comparable bare name** (`TableSlot.name dbTable`), not the
identity-compared `Table` **object** (`TableSlot.wrapped dbTable`). Under the
patch, `Columns.references_column(dbTable, col)` is `(dbTable == dbTable) ∧
col ∈ columns = True` for a listed column; pre-patch, `self.table` is a `Table`
instance and `Table.__eq__` is `object.__eq__`, so `Table(...) == dbTable` is
**always `False`**, making `references_column` always `False` (the issue).

`Solution_prepatch.lean` reproduces the bug exactly — `tableForColumns :=
TableSlot.wrapped dbTable` — and **fails** the frozen postcondition
`∀ t col, out.referencesColumn t col = ((dbTable == t) && columns.contains col)`
on the discriminating clause: at `t = dbTable`, `col ∈ columns`, the spec
requires `True` but the wrapped slot yields `False` (G-DIFF).

The third postcondition, `out.renderedColumns = columns`, pins the column
payload of the emitted DDL (step A5b): it closes the audit-found weakness
where an impl storing a mutated column list (empty, reordered, extra columns)
still answered every `references_*` query correctly for its own carrier and
so verified, yet its refined patch emitted wrong SQL and failed hidden
(PASS_TO_PASS) schema tests.

## B. No consumed axioms

The `axioms` region is empty. The reference classes `Table` / `Columns` /
`Statement` the function instantiates are **unchanged** by the patch; their
`references_table` / `references_column` semantics are modeled **deeply** in the
`pure` region (`slotMatches`, `ColumnsRef.referencesColumn`,
`Stmt.references{Column,Table}`) and validated == the real classes by **G-AX**
(`axiom_check.py`, mapping.md §3.1) — they are **A-reference**, not consumed
axioms. There is no dead `axiom` the proof never uses.

## C. No kind-3 (inexpressible-changed-op) steps

Every step is R, A-reference, or I. The one operation that genuinely *changed* —
which carrier (value-comparable name vs identity-compared object) the columns
reference stores — is modeled **directly** in the impl region (the `TableSlot`
choice, step A3, an R step) over a deeply-modeled (A-reference) predicate, not
hidden behind an axiom about the function under change. The frozen postconditions
ground the observable (`referencesColumn` / `referencesTable`) in the inputs
(`dbTable`, `columns`) so only an impl that stores the value-comparable name can
verify (directive 8).

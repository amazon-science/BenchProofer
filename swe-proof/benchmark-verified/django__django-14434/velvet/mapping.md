# mapping.md — django__django-14434

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = 5e04e84d67da8163f365e9f5fcd169e2630e2873`, states the type
abstraction (the bijection G-CONF and G-AX use to bridge Lean↔Python), and gives
the provenance of each deep-modeled callee.

Repo files in scope:
- `django/db/backends/base/schema.py` — the changed function (file under patch).
- `django/db/backends/ddl_references.py` — the **unchanged** reference classes
  (`Table`, `Columns`, `Statement`, …) the changed function instantiates; their
  `references_table` / `references_column` semantics are modeled deeply and
  validated == the real classes by G-AX (A-reference, not axioms).

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `buildUniqueStatement (dbTable : String) (columns : List String)` | `BaseDatabaseSchemaEditor._create_unique_sql(self, model, columns, name, …)` — `django/db/backends/base/schema.py:1225` (body builds the `Statement` at lines 1243–1265) | the modeled changed function, restricted to the column-list path the F2P test exercises (`fields=['name']`, `name='name_uq'` given) |
| `TableSlot` | the value stored in a reference's `self.table` field — either a bare table-name `str` or a `Table` instance wrapping that name (`ddl_references.py:42` `Table`, `:60` `TableColumns`) | the discriminating carrier: a name-string vs an object-wrapping-a-name |
| `ColumnsRef` | `Columns` (`ddl_references.py:75`), via `TableColumns.references_column` (`:66`) | the `columns=` part of the `Statement`; its `references_column` is the observable the issue is about |
| `Stmt` | `Statement` (`ddl_references.py:165`) restricted to its two reference-bearing parts (`table=`, `columns=`) | the returned deferred-DDL statement |
| `ColumnsRef.referencesColumn` / `Stmt.referencesColumn` | `TableColumns.references_column` (`:66`) lifted through `Statement.references_column` (`:181`, `any(part.references_column …)`) | deep model — A-reference, G-AX-validated |
| `Stmt.referencesTable` | `Table.references_table` (`:48`) lifted through `Statement.references_table` (`:175`) | deep model — A-reference, G-AX-validated |
| `slotMatches` | the `self.table == table` comparison inside `TableColumns.references_column` / `Table.references_table` | deep model of Python `==` between the stored slot and the queried table name |
| `Stmt.renderedColumns` | `Columns.__str__` (`ddl_references.py:84`) — the column list rendered, in order and with multiplicity, into the DDL text via `Statement.__str__`'s `%(columns)s` (`:203`) | the column payload observable: what the executed SQL actually contains |

**Rendered-columns observable** (`Stmt.renderedColumns`): the columns part also
renders into the emitted DDL text — `Statement.__str__` substitutes
`%(columns)s` with `str(self.parts['columns'])`, and `Columns.__str__` joins the
stored column names in order. The hidden tests grade the emitted SQL indirectly
(the constraint is actually created on the DB, then inspected/dropped), so a
statement whose columns part stored a *different* column list (e.g. reordered,
truncated, or padded) would generate wrong SQL even while answering all
`references_*` membership queries identically. The `renderedColumns = columns`
postcondition pins the stored list verbatim, closing the gap the audit
exploited (a spec-satisfying impl whose statement carried the right membership
answers but the wrong column payload translated to a patch that fails hidden
tests).

The pre-image construct the change replaces (refinement audit only, not in the
consumer spec view): the local `table` bound to a `Table(...)` instance and then
threaded into `Columns` via `_index_columns` (`schema.py:1068`,
`return Columns(table, columns, self.quote_name, …)`).

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4.1) and G-AX use to translate values between the
Lean value domain and the Python repo types. A wrong entry surfaces as spurious
G-CONF disagreements (the falsifiability the plan §4 trust statement refers to).

| repo reality | Lean carrier | bijection |
|---|---|---|
| `model._meta.db_table` (a `str`) | `String` (`dbTable`) | identity on the character content; `s` (Python `str`) ↔ Lean `String` |
| the constraint's column names `columns` (a `list[str]` / tuple) | `List String` | `[c₀,c₁,…]` ↔ Python `list`; membership `col in self.columns` ↔ `List.contains` |
| the queried table / column args of `references_table(t)` / `references_column(t,c)` (`str`) | `String` | identity, as above |
| a reference's stored `self.table` slot | `TableSlot` | a bare name string `s` ↔ `TableSlot.name s`; a `Table(s, quote_name)` instance ↔ `TableSlot.wrapped s` |
| `Table(table, quote_name)` instance | `TableSlot.wrapped` (its name field) | `quote_name` is a render-time callback (`Table.__str__`) that does **not** participate in `references_table` / `references_column`; omitted from the carrier (identity) |
| the rendered column sequence `str(columns_part)` (`Columns.__str__`, `', '.join(quote_name(c) …)`) | `Stmt.renderedColumns : List String` | the ordered column-name list, up to the uniform per-column `quote_name` wrapping (which is injective on identifiers and carries no column-list information); `', '.join` ↔ the `List String` in order with multiplicity |
| the `name=` part (`self.quote_name(name)` when `name` is given) | omitted | a plain quoted `str`; it is not a `Reference`, so contributes `False` to both `references_*` (base `Reference`); irrelevant to the observable, omitted |

Python object identity vs string equality is the crux: `Table.__eq__` is not
defined, so a `Table` instance compared to a `str` uses `object.__eq__` →
**always `False`**. The model captures this as
`slotMatches (TableSlot.wrapped _) _ = false` while
`slotMatches (TableSlot.name s) t = (s == t)`.

## 3. Callee provenance (kind-A — checked by G-AX / axiom_check.py)

There are **no consumed axioms** (the `axioms` region is empty). Every callee the
changed function uses on the F2P path is an **unchanged** pure reference class,
modeled **deeply** in the `pure` region and validated == the real class by G-AX:

### 3.1 `referencesColumn` / `referencesTable` deep model ↔ `ddl_references` (A-reference)
**Callees:** `django.db.backends.ddl_references.Table`, `Columns`, `Statement`
(unchanged by the patch). The deep model encodes:

```python
# TableColumns.references_column(self, table, column):
#   return self.table == table and column in self.columns
# Table.references_table(self, table):
#   return self.table == table
# Statement.references_{table,column}: any(part.references_* for part in parts)
```

The single behaviour the issue turns on: when `self.table` is a **`Table`
instance** (object) rather than the bare **name string**, `self.table == table`
(a string) is `False`, so `Columns.references_column` returns `False` for every
column. The model reproduces this exactly via `TableSlot`.

**Soundness check (G-AX):** `axiom_check.py` constructs the **real**
`ddl_references` `Columns` / `Table` / `Statement` objects both ways — built with
a bare name string AND built wrapping a `Table` instance — over boundary tables /
columns plus randomized fuzz, and asserts the deep model's
`referencesColumn` / `referencesTable` predicate equals the real classes'
results on every observation (both slot kinds). Imports only the django repo
module `django.db.backends.ddl_references`. Exit 0 iff sound.

## 4. G-CONF fuzz seed (pinned for deterministic eval — plan §4.1, §11.3)

`conformance_check.py` seeds its `random.Random` with **`14434`** so the
consumer-side verdict (§11.3) is reproducible. The R/I shadow it builds
transliterates the impl region's structure-building wiring (the local `table`
bound to the bare db-table **string**, fed into `Columns`, with the `Statement`
wrapping it in `Table(...)`), and the oracle reconstructs the **patched**
`_create_unique_sql` data-flow for the F2P column-list path using the real
unchanged `ddl_references` classes, comparing `references_column` /
`references_table` over ≥10⁵ fuzzed `(db_table, columns, query_table,
query_column)` tuples.

# mapping.md — django__django-14434

## Symbol binding (file:line @ base_commit 5e04e84d67)

| Lean symbol | Python symbol | location |
|---|---|---|
| `implementation__create_unique_sql` | `BaseDatabaseSchemaEditor._create_unique_sql` | `django/db/backends/base/schema.py:1225-1265` |
| `Statement` (struct) | `Statement` (deferred DDL container) | `django/db/backends/ddl_references.py:166-201` |
| `ColumnsRef` (struct) | `Columns` / its base `TableColumns` | `django/db/backends/ddl_references.py:60-96` |
| `TableId.wrapped` | a `Table` reference object | `django/db/backends/ddl_references.py:42-57` |
| `TableId.name` | a bare `db_table` string | `model._meta.db_table` |
| `Statement.references_column` | `Statement.references_column` | `ddl_references.py:184-188` |
| `Statement.references_table` | `Statement.references_table` | `ddl_references.py:178-182` |
| `ColumnsRef.references_column` | `TableColumns.references_column` | `ddl_references.py:67-68` |
| `Statement.renderedColumns` | `Columns.__str__` (the column list rendered, in order, into the DDL text via `Statement.__str__`'s `%(columns)s`) | `ddl_references.py:84-96` |

## The fixed behavior (single, observable)

`_create_unique_sql` builds a `Statement` whose `columns` part is a `Columns`
(subclass of `TableColumns`). `TableColumns.references_column(table, column)`
returns `self.table == table and column in self.columns`.

- **Pre-fix:** `table = Table(model._meta.db_table, self.quote_name)` — a `Table`
  *object*. `_index_columns(table, columns, …)` → `Columns(table, …)` stores that
  object as `self.table`. Since `Table.__eq__` is identity and the query argument
  is a *string*, `self.table == table_str` is **always False**, so
  `references_column` is always False. (The reported bug.)
- **Post-fix:** `table = model._meta.db_table` — a bare string. `Columns.self.table`
  is now that string, so `self.table == table_str` succeeds and
  `references_column(db_table, col)` is True for `col in columns`.

`references_table` was never broken: the `Statement`'s `table=` part is
`Table(table, self.quote_name)` (post-fix) / `table` (pre-fix), both `Table`
objects wrapping the same `db_table` string; `Table.references_table` compares its
own stored string, so it always matched.

**Rendered-columns observable** (`Statement.renderedColumns`): the columns part
also renders into the emitted DDL text — `Statement.__str__` substitutes
`%(columns)s` with `str(self.parts['columns'])`, and `Columns.__str__` joins the
stored column names in order. The hidden test grades the emitted SQL indirectly
(the constraint is actually created on the DB, then dropped), so a statement
whose columns part stored a *different* column list (e.g. reordered, truncated,
or padded) would generate wrong SQL even while faking the `references_*`
queries. `renderedColumns = columns` pins the stored list verbatim, closing the
gap the audit exploited (a spec-satisfying impl whose statement carried the
right membership answers but the wrong column payload translated to a patch
that fails the hidden test).

## Lean ↔ Python type bijection (used by G-CONF / G-AX)

| Python | Lean |
|---|---|
| `model._meta.db_table : str` | `dbTable : String` |
| `columns : list[str]` (unique-constraint field columns, non-empty) | `columns : List String` |
| `Table` reference object wrapping name `s` | `TableId.wrapped s` |
| bare table-name string `s` (as `Columns.self.table`) | `TableId.name s` |
| `self.table == t` (string arg `t`) | `TableId.matchesName self.table t` |
| `column in self.columns` | `columns.contains col` |
| `Statement.references_column(t, c) : bool` | `Statement.references_column s t c : Bool` |
| `Statement.references_table(t) : bool` | `Statement.references_table s t : Bool` |

`TableId.matchesName (.wrapped _) _ = false` models that a `Table` object never
`==` a string in CPython (no `__eq__`); `(.name s) t = (s == t)` models string
equality.

## Scope / branch selection

The modeled domain is `columns ≠ []` — the `if columns:` branch, which is the
branch the FAIL_TO_PASS test (`fields=['name']`) and the reported bug exercise.
The `else` branch (`Expressions(...)`, when only `expressions` are given) is NOT
an independently-fixed behavior: pre-fix it already received the *string*
`model._meta.db_table`, so the gold edit (`→ table`) is behavior-identical there.
The `IndexName(... )` edit is likewise string→string (no behavior change) and
`IndexName` does not implement `references_column`. Out of scope; documented.

## Callee provenance / flag deps

No unchanged callee is consumed: `Table`, `Columns`/`TableColumns`, `Statement`
are all modeled deeply as Lean structures (A-reference-free — they are spelled
out, not axiomatized). No flag dependency. No `opaque` decls; axioms region empty.

## G-CONF fuzz seed

Pinned seed: `14434`. Fuzzer draws `dbTable` from a small ASCII alphabet and
`columns` as a non-empty list of distinct column-name strings, plus a queried
`(t, c)` drawn to hit both matching and non-matching cases.
</content>
</invoke>

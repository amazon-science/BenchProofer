# refinement.md — django__django-14434

The operation-by-operation correspondence between `model.py`'s implementation
(the `build_constraint_columns` impl region, the `ConstraintPart` constructor, the
deep `member` model, and the pure reference predicates) and `patch.diff` (the
gold patch). Each step is tagged **R** (type refinement), **A** (axiomatized
callee — split into **A-consumed**, where the proof uses an axiom's `Ensures`,
and **A-reference**, where a deep model is validated == the real callee by
axiom_check.py / G-AX), or **I** (identical concrete operation). The claim:
*any implementation that verifies against this frozen spec, refined per the map
below, is behaviourally equal to the gold patch on the tested inputs, so it
resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## A. The change site — `_create_unique_sql` (`django/db/backends/base/schema.py`)

Gold hunk (the load-bearing lines):
```
- table = Table(model._meta.db_table, self.quote_name)
+ table = model._meta.db_table
  ...
- columns = self._index_columns(table, columns, col_suffixes=(), opclasses=opclasses)   # `table` was the Table handle
+ columns = self._index_columns(table, columns, col_suffixes=(), opclasses=opclasses)   # `table` is now the bare name
  ...
- return Statement(sql, table=table, ...)        # table was already the handle
+ return Statement(sql, table=Table(table, self.quote_name), ...)   # wrap only here
```
Effect: the value recorded as the *columns'* table (`Columns.table`, via
`_index_columns` / `Expressions`) changes from a `Table` **handle** to the
**bare `db_table` name**; the `Statement`'s `table=` part stays a `Table`
handle in both versions (so `references_table` already worked).

| # | model.py impl op | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | param `db_table: List[int]` | `model._meta.db_table` (`str`) | R | `str` ↔ `List[int]` code points (mapping.md §2). |
| A2 | param `columns: PSeq[int]` | the `columns`/`fields` sequence of column names | R | column names ↦ distinct int codes under any injective map; only their equality/membership is observed (mapping.md §2). |
| A3 | `ConstraintPart(True, db_table, columns)` records the **bare** identifier (`plain=True`) as the columns' table | `_index_columns(table, …)` with `table = model._meta.db_table` (the bare name) recorded as `Columns.table` | R + I | the constructed object is `Columns` restricted to its two observed facets (`ConstraintPart` ≅ `Columns`/`TableColumns`, mapping.md §1); `plain=True` ⇔ the recorded value is the bare `str` (value-comparable). The gold's whole point is recording the bare name here. |
| A4 | `constrains_column(plain, table, cols, q_table, q_col) = plain and table == q_table and member(q_col, cols)` | `TableColumns.references_column = self.table == table and column in self.columns` | R + A-reference | the recorded-table value comparison `self.table == table` is modeled by `plain and table == q_table`: a bare name value-equals a bare queried name (`plain=True` branch); a `Table` handle never does (it defines no `__eq__`), captured by `plain=False ⇒ False`. Membership `column in self.columns` is the deep model `member` (A4′). G-AX validates `constrains_column == real Columns.references_column` for both wirings. |
| A4′ | `member(q_col, cols)` (front-recursive `@Pure`) | `column in self.columns` | A-reference | the unchanged membership callee is modeled deeply; there is no consumed axiom. G-AX asserts `member(c, cols) == (c in cols)` over boundary + 20 000 fuzz. |
| A5 | `constrains_table(table, q_table) = table == q_table` | `Table.references_table = self.table == table`, and the `Statement.references_table` disjunction over parts | R + A-reference | the `table=` part is a `Table(bare name)` in both versions, so the table reference holds by value comparison; modeled by `constrains_table`, validated == real by G-AX. |

The discriminating content — recording the **bare table name** rather than the
**`Table` handle** against the columns — lives in `ConstraintPart.plain`
(`True` in model, `False` in `model_prepatch`). `model_prepatch.py` records the
handle (`plain=False`), so `constrains_column` is identically `False` and the
postcondition `member(c, columns) ⇒ constrains_column(…)` **fails** — exactly
the spec sensing the change (G-DIFF). This mirrors the gold: pre-patch the
columns held a `Table` handle ⇒ `references_column` always `False` (the issue:
"makes references_column always false").

## B. No kind-3 (unexpressible-changed-op) steps

Every step above is R, A-reference, or I. The one operation that genuinely
*changed* — which value is recorded against the columns and how the subsequent
equality comparison behaves — is modeled **deeply**: the `plain` flag spells out
the bare-name-vs-handle value-equality distinction (the real `Table` class's
lack of `__eq__`), validated against the real `ddl_references` classes by G-AX
(A4, A4′, A5, A-reference). There is **no consumed `@ContractOnly` axiom**: the
membership callee `in` is also modeled deeply (`member`, A-reference), not
hidden behind an axiom about the changed comparison. The framework helpers the
change wires together (`Columns`, `Table`, `Statement`) are unchanged and serve
only as the A-reference G-AX validates the deep model against.

## C. verify(model) ⇒ resolved

`build_constraint_columns` verifies only if the constructed part records a
bare, value-comparable table name (`plain=True`, A3) so that
`constrains_column(plain, table, cols, db_table, c)` is `True` for every
`c ∈ columns` (the first `Forall`) and `False` otherwise (the second `Forall`,
forbidding a constant-`True` cheat), with the companion `constrains_table`
holding (A5). By R (str ↔ List[int], column-name ↦ code, `ConstraintPart` ≅
`Columns`) and the G-AX-validated A-references (A4/A4′/A5: the model predicates
== the real `ddl_references` semantics; the bare wiring == the gold's
`table = model._meta.db_table`), a model satisfying this spec, refined by the
map above, IS the gold patch up to type refinement and audited references — and
the gold patch resolves (G-RESOLVE: the F2P `test_unique_constraint` asserts
`sql.references_column(table, 'name') is True`, which is exactly the first
`Forall` for `c = code('name')`). The trust points are the two of PLAN §1.1:
deep-model/axiom soundness (G-AX) and refinement fidelity (this document,
G-EQ); there is no consumed axiom, so only the A-references carry trust.

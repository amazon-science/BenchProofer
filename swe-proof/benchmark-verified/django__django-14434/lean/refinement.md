# refinement.md — django__django-14434

Maps every op in `implementation__create_unique_sql` to its `patch.diff`
counterpart. Tags: **R** (type refinement), **A-consumed**, **A-reference**,
**I** (identical concrete op).

## Operation correspondence

| # | Lean impl op | patch.diff / repo op | tag | note |
|---|---|---|---|---|
| 1 | `let table : String := dbTable` | `table = model._meta.db_table` (the gold edit, line 1244) | R | `model._meta.db_table : str` ↔ `dbTable : String`. The whole fix: `table` is the bare name string, NOT a `Table(...)` object. |
| 2 | `let columnsPart : ColumnsRef := { tableId := TableId.name table, columns := columns }` | `columns = self._index_columns(table, columns, …)` → `Columns(table, columns, self.quote_name, …)` → `TableColumns.__init__(table, columns)` storing `self.table = table` | R | `Columns`/`TableColumns` modeled as `ColumnsRef`; `self.table` stores the bare string ⇒ `TableId.name`. This is the branch the fix corrects (`if columns:`). |
| 3 | `return { tablePart := { name := table }, columnsPart := columnsPart }` | `return Statement(sql, table=Table(table, self.quote_name), name=name, columns=columns, …)` | R | `Statement` modeled as `Statement` struct with the two reference-bearing parts (`table`, `columns`) that drive `references_table`/`references_column`. Other `Statement` kwargs (`sql`, `name`, `condition`, `deferrable`, `include`) carry no column/table reference and are dropped from the model (they never affect `references_*`). |

## Modeled predicates (deep models, not axioms)

| Lean def | Python counterpart | tag | note |
|---|---|---|---|
| `Statement.references_column` | `Statement.references_column` (`any part.references_column`) | R | The only column-bearing part is `columnsPart`; `tablePart` (a `Table`) has no `references_column`, modeled by it contributing nothing. |
| `Statement.renderedColumns` | `Columns.__str__` → `Statement.__str__`'s `%(columns)s` (the column sequence rendered, in order and with multiplicity, into the executed DDL) | R | Pins the columns part's stored list verbatim. Added after an audit found the membership-only spec admitted impls that store a reordered/duplicated/otherwise-mutated column list — same `references_*` answers, different generated SQL, hidden test fails. |
| `Statement.references_table` | `Statement.references_table` (`any part.references_table`) | R | Both parts can reference a table; `TableRef` and `ColumnsRef` each match by name. |
| `ColumnsRef.references_column` | `TableColumns.references_column` = `self.table == table and column in self.columns` | R | exact model. |
| `TableId.matchesName (.wrapped _) _ = false` | a `Table` object `== ` a `str` is False in CPython | R / A-reference-style | This encodes the bug mechanism: a wrapped reference object never `==` a plain string. Validated empirically by `axiom_check.py` (G-AX) against the real `Table`/`Columns`. |

## Axiom ledger

- **A-consumed:** none. The axioms region is empty; the proof consumes no callee
  contract (everything is a structural fact about the modeled structures).
- **A-reference:** the one nontrivial behavioral fact —
  `Table_object != str ⇒ TableColumns.references_column returns False` — is
  validated by `axiom_check.py` running the real `Columns`/`Table` from
  `ddl_references.py`. It is a *reference* (the modeled op is spelled out), not a
  consumed axiom.
- **I:** none (every op is a type refinement R).

## No changed-inexpressible op

Every changed op is expressible: the fix is a single data-type change
(`Table` object → bare string) flowing into `Columns`' stored `table` field, and
its observable effect (`references_column`) is modeled exactly. No op required
modeling that the type system could not express.
</content>

# refinement.md — operation correspondence (django__django-13807)

Maps every op in `implementation_fkCheckQueries` to its `patch.diff` counterpart.
Tags: **R** type refinement · **A-consumed** proof uses axiom property ·
**A-reference** deep model validated == real callee (G-AX) · **I** identical op.

The patched Python builds three SQL query strings per violating row, substituting
the table / primary-key / foreign-key identifiers via `self.ops.quote_name(...)`
into fixed literal templates. We model `quote_name` deeply as `quoteIdentifier`
and each `%s`-into-literal-template substitution as the equivalent fixed-order
concatenation.

| # | Lean impl op | patch.diff counterpart | tag | justification |
|---|---|---|---|---|
| 1 | `table primaryKey column : List Char` | `table_name`, `primary_key_column_name`, `column_name` strings | R | str ↔ List Char bijection (mapping.md); identifiers passed through unchanged |
| 2 | `quoteIdentifier table` (and `quoteIdentifier primaryKey`, `quoteIdentifier column`) | `self.ops.quote_name(table_name)` (resp. `quote_name(primary_key_column_name)`, `quote_name(column_name)`) | A-reference | the UNCHANGED callee `quote_name` (operations.py:170-173) modeled deeply: wrap in `"…"` unless already double-quoted at both ends. Validated == real callee by G-AX. NOT axiomatized. |
| 3 | `"PRAGMA foreign_key_check(".toList ++ quoteIdentifier table ++ [')']` | `'PRAGMA foreign_key_check(%s)' % self.ops.quote_name(table_name)` | I | `%s`-into-literal substitution = fixed-order concatenation with literal `PRAGMA foreign_key_check(` prefix and `)` suffix |
| 4 | `"PRAGMA foreign_key_list(".toList ++ quoteIdentifier table ++ [')']` | `'PRAGMA foreign_key_list(%s)' % self.ops.quote_name(table_name)` | I | identical concrete op (same shape as #3 with the `foreign_key_list` literal) |
| 5 | `"SELECT ".toList ++ quoteIdentifier primaryKey ++ ", ".toList ++ quoteIdentifier column ++ " FROM ".toList ++ quoteIdentifier table ++ " WHERE rowid = %s".toList` | `'SELECT %s, %s FROM %s WHERE rowid = %%s' % (quote_name(primary_key_column_name), quote_name(column_name), quote_name(table_name))` | I | three-slot `%`-substitution into the literal `SELECT …, … FROM … WHERE rowid = %s` template = fixed-order concatenation; `%%s` is the literal `%s` rowid placeholder, reproduced verbatim |
| 6 | `return (fkCheck, fkList, selectRow)` | the three strings handed to `cursor.execute(...)` | I | grouping the three rendered query strings; the cursor I/O and `IntegrityError` plumbing are unaffected by the fix and out of model scope (mapping.md) |

A-reference rows: #2 (`quote_name` ↔ `quoteIdentifier`), validated by G-AX.
No A-consumed rows: the proof discharges the concatenations and the
`quoteIdentifier` definition directly; no UNCHANGED callee *property* is assumed
(axioms region empty). No changed-inexpressible op.

The discriminating behavior is row 2: each identifier is rendered with
`quoteIdentifier` (double-quoted) rather than interpolated raw. The prepatch impl
interpolates the bare identifier, so e.g. `result.1` becomes
`"PRAGMA foreign_key_check(" ++ table ++ ")"` which differs from the frozen
`problem_spec_fkCheckQueries`
(`… ++ quoteIdentifier table ++ …` = `… ++ "\"" ++ table ++ "\"" ++ …`) whenever
`table` is not already double-quoted (in particular the F2P table `order`). Hence
prepatch `correct_fkCheckQueries` cannot close — the G-DIFF signal.
